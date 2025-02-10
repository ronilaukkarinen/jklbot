import requests
from bs4 import BeautifulSoup
import hashlib
from facebook_scraper import get_posts
import feedparser
from datetime import datetime, timedelta
import pytz
import logging

class ContentFetcher:
    def __init__(self, database):
        self.database = database
        self.hashtags = "#Jyväskylä #Jkl #KeskiSuomi #Uutiset"
        self.event_hashtags = "#Jyväskylä #Jkl #Tapahtumat #KeskiSuomi"
        self.timezone = pytz.timezone('Europe/Helsinki')
        self.enable_event_notifications = False

    def fetch_jyvaskyla_website(self):
        try:
            url = "https://www.jyvaskyla.fi/term/103/rss.xml"
            feed = feedparser.parse(url)

            content_list = []
            for entry in feed.entries:
                # Parse the published date
                published = datetime(*entry.published_parsed[:6])
                # Only include entries from the last 24 hours
                if datetime.now() - published < timedelta(hours=24):
                    title = entry.title
                    link = entry.link
                    content_id = hashlib.md5(link.encode()).hexdigest()

                    if not self.database.is_posted(content_id):
                        content = f"{title}\n{link}\n\n{self.hashtags}"
                        content_list.append((content_id, content))

            return content_list
        except Exception as e:
            print(f"Error fetching Jyväskylä RSS feed: {e}")
            return []

    def fetch_facebook_posts(self):
        try:
            content_list = []
            for post in get_posts('jyvaskyla', pages=1):
                # Only include posts from the last 24 hours
                if datetime.now() - post['time'] < timedelta(hours=24):
                    content_id = post['post_id']
                    if not self.database.is_posted(content_id):
                        content = f"{post['text'][:400]}...\n\n{self.hashtags}"
                        content_list.append((content_id, content))
            return content_list
        except Exception as e:
            print(f"Error fetching Facebook posts: {e}")
            return []

    def fetch_test_feed(self):
        try:
            # Use a frequently updating news RSS feed for testing
            url = "https://feeds.yle.fi/uutiset/v1/recent.rss?publisherIds=YLE_UUTISET"
            feed = feedparser.parse(url)

            content_list = []
            for entry in feed.entries:
                title = entry.title
                link = entry.link
                content_id = hashlib.md5(link.encode()).hexdigest()

                if not self.database.is_posted(content_id):
                    content = f"TEST: {title}\n\n{link}\n\n#Test"
                    content_list.append((content_id, content))

            return content_list
        except Exception as e:
            print(f"Error fetching test feed: {e}")
            return []

    def fetch_events(self, start_date=None, end_date=None):
        try:
            url = "https://keskisuomievents.fi/api/items/event"
            now = datetime.now(self.timezone)

            if start_date is None:
                start = 'now'
                end = (now + timedelta(days=30)).strftime('%Y-%m-%d')
            else:
                start = start_date.strftime('%Y-%m-%d')
                end = end_date.strftime('%Y-%m-%d')

            params = {
                'start': start,
                'end': end,
                'limit': 100,
                'sort': 'start_time',
                'filter[start_time][_gte]': start,
                'filter[end_time][_gte]': start
            }

            response = requests.get(url, params=params)
            response.raise_for_status()
            events_list = response.json()

            content_list = []

            for event in events_list.get('data', []):
                try:
                    event_url = f"https://kalenteri.jyvaskyla.fi/fi/tapahtuma/{event['id']}"

                    details = self.fetch_event_details(event_url)
                    if not details:
                        continue

                    start_time = datetime.fromisoformat(event['start_time'].replace('Z', '+00:00')).astimezone(self.timezone)
                    content_id = hashlib.md5(f"{event['id']}".encode()).hexdigest()

                    description = details['description']
                    if description:
                        description = description[:400] + "..." if len(description) > 400 else description

                    # Check for upcoming notifications
                    time_until_event = start_time - now

                    # Only handle reminders if enabled
                    if not self.enable_event_notifications:
                        return []

                    # Only handle reminders, not new events
                    if timedelta(hours=23) < time_until_event <= timedelta(hours=24):
                        reminder_id = hashlib.md5(f"{content_id}_24h".encode()).hexdigest()
                        if not self.database.is_posted(reminder_id):
                            content = (
                                f"Tapahtuma alkaa huomenna:\n\n"
                                f"{details['title']}\n"
                                f"{start_time.strftime('%d.%m.%Y klo %H:%M')}\n\n"
                                f"{description}\n\n"
                                f"{event_url}\n\n"
                                f"{self.event_hashtags}"
                            )
                            content_list.append((reminder_id, content, 'event_24h'))

                    elif timedelta(hours=5) < time_until_event <= timedelta(hours=6):
                        reminder_id = hashlib.md5(f"{content_id}_6h".encode()).hexdigest()
                        if not self.database.is_posted(reminder_id):
                            content = (
                                f"Tapahtuma alkaa pian:\n\n"
                                f"{details['title']}\n"
                                f"{start_time.strftime('%d.%m.%Y klo %H:%M')}\n\n"
                                f"{description}\n\n"
                                f"{event_url}\n\n"
                                f"{self.event_hashtags}"
                            )
                            content_list.append((reminder_id, content, 'event_6h'))

                except Exception as e:
                    logging.error(f"Error processing event {event.get('id', 'unknown')}: {e}")
                    continue

            return content_list
        except Exception as e:
            logging.error(f"Error fetching events from API: {e}")
            return []

    def fetch_event_details(self, event_url):
        try:
            response = requests.get(event_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find the event title (try multiple approaches)
            title = None
            title_elem = soup.find('h1', class_='event-title')
            if title_elem:
                title = title_elem.text.strip()
            else:
                meta_title = soup.find('meta', property='og:title')
                if meta_title:
                    title = meta_title.get('content', '').strip()

            if not title:
                logging.warning(f"Could not find title for event at {event_url}")
                return None

            # Find the event description (try multiple approaches)
            description = None
            desc_elem = soup.find('div', class_='event-description')
            if desc_elem:
                description = desc_elem.text.strip()
            else:
                meta_desc = soup.find('meta', property='og:description')
                if meta_desc:
                    description = meta_desc.get('content', '').strip()
                else:
                    short_desc = soup.find('div', class_='event-short-description')
                    if short_desc:
                        description = short_desc.text.strip()

            logging.info(f"Found event: {title}")

            return {
                'title': title,
                'description': description or '',
                'short_description': description or '',
                'location': '',
                'start_time': ''
            }

        except Exception as e:
            logging.error(f"Error fetching event details from {event_url}: {e}")
            return None

    def fetch_weekly_events(self):
        try:
            url = "https://keskisuomievents.fi/api/items/event"
            now = datetime.now(self.timezone)

            # Calculate end of week (Sunday)
            days_until_sunday = (6 - now.weekday()) % 7
            week_end = now + timedelta(days=days_until_sunday)

            params = {
                'start': now.strftime('%Y-%m-%d'),
                'end': week_end.strftime('%Y-%m-%d'),
                'limit': 100,
                'sort': 'start_time',
                'filter[start_time][_gte]': now.strftime('%Y-%m-%d'),
                'filter[end_time][_gte]': now.strftime('%Y-%m-%d')  # Match test implementation
            }

            logging.info(f"Fetching weekly events from {now.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}")

            response = requests.get(url, params=params)
            response.raise_for_status()
            events_list = response.json()

            event_count = len(events_list.get('data', []))
            logging.info(f"Found {event_count} events in API response")

            if event_count == 0:
                logging.warning("No events returned from API")
                return []

            content_list = []
            events_text = []
            seen_events = set()

            for event in events_list.get('data', []):
                try:
                    event_url = f"https://kalenteri.jyvaskyla.fi/fi/tapahtuma/{event['id']}"
                    start_time = datetime.fromisoformat(event['start_time'].replace('Z', '+00:00')).astimezone(self.timezone)

                    logging.info(f"Processing event {event['id']} starting at {start_time}")

                    if now <= start_time < week_end:  # Match test implementation's date check
                        details = self.fetch_event_details(event_url)
                        if details and details['title']:
                            event_key = f"{details['title']}_{start_time.strftime('%Y%m%d%H%M')}"

                            if event_key not in seen_events:
                                seen_events.add(event_key)
                                events_text.append(
                                    f"- {details['title']}, {start_time.strftime('%d.%m.%Y klo %H:%M')}"
                                )
                                logging.info(f"Added event: {details['title']} at {start_time}")
                        else:
                            logging.warning(f"Could not fetch details for event {event['id']}")

                except Exception as e:
                    logging.error(f"Error processing event {event.get('id', 'unknown')}: {e}")
                    continue

            logging.info(f"Processed {len(events_text)} valid events for the week")

            if events_text:
                content_id = hashlib.md5(f"weekly_{now.strftime('%Y-%W')}".encode()).hexdigest()
                if not self.database.is_posted(content_id):
                    content = (
                        "Tämän viikon tapahtumat:\n\n"
                        f"{chr(10).join(events_text)}\n\n"
                        "https://kalenteri.jyvaskyla.fi\n\n"
                        f"{self.event_hashtags}"
                    )
                    content_list.append((content_id, content, 'weekly_events'))
                    logging.info(f"Created weekly events post with ID: {content_id}")
                else:
                    logging.info(f"Weekly events already posted for week {now.strftime('%Y-%W')}")
            else:
                logging.info("No events found for this week")

            return content_list
        except Exception as e:
            logging.error(f"Error fetching weekly events: {e}")
            return []
