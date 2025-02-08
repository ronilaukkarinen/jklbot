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
                        content = f"{title}\n\n{link}\n\n{self.hashtags}"
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

    def fetch_events(self):
        try:
            url = "https://keskisuomievents.fi/api/items/event"
            now = datetime.now(self.timezone)
            
            params = {
                'start': 'now',
                'end': (now + timedelta(days=30)).strftime('%Y-%m-%d'),
                'limit': 100
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
            
            # Find the event title
            title = soup.find('h1', class_='event-title')
            if not title:
                return None
            title = title.text.strip()
            
            # Find the event description
            description = soup.find('div', class_='event-description')
            if description:
                description = description.text.strip()
            
            # Find the short description
            short_description = soup.find('div', class_='event-short-description')
            if short_description:
                short_description = short_description.text.strip()
            
            # Find the location
            location = soup.find('div', class_='event-location')
            if location:
                location = location.text.strip()
            
            # Find the start time
            start_time = soup.find('div', class_='event-start-time')
            if start_time:
                start_time = start_time.text.strip()
            
            return {
                'title': title,
                'description': description,
                'short_description': short_description,
                'location': location,
                'start_time': start_time
            }
            
        except Exception as e:
            logging.error(f"Error fetching event details from {event_url}: {e}")
            return None 