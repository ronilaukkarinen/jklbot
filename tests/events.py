import sys
import os
from datetime import datetime, timedelta
import pytz
import requests
from bs4 import BeautifulSoup
import time

# Add the parent directory to the Python path so we can import the main module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from content_fetchers import ContentFetcher

class MockDatabase:
    def is_posted(self, content_id):
        return False  # Always return False to see all events

def fetch_event_details(event_url):
    try:
        response = requests.get(event_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Get title and description from meta tags
        title = soup.find('meta', property='og:title')
        description = soup.find('meta', property='og:description')
        
        if title and description:
            return {
                'title': title.get('content', '').strip(),
                'description': description.get('content', '').strip()
            }
        return None
        
    except Exception:
        return None

def main():
    # Initialize the content fetcher with a mock database
    fetcher = ContentFetcher(MockDatabase())
    
    # First, get one event's details to show the format
    url = "https://keskisuomievents.fi/api/items/event"
    now = datetime.now(pytz.timezone('Europe/Helsinki'))
    
    params = {
        'start': now.strftime('%Y-%m-%d'),
        'end': (now + timedelta(days=30)).strftime('%Y-%m-%d'),
        'limit': 1,
        'sort': 'start_time',  # Sort by start time
        'filter[start_time][_gte]': now.strftime('%Y-%m-%d')  # Only get events after today
    }
    
    response = requests.get(url, params=params)
    events_list = response.json()
    
    if events_list.get('data'):
        event = events_list['data'][0]
        start_time = (
            datetime.fromisoformat(event['start_time'].replace('Z', '+00:00'))
            .astimezone(pytz.timezone('Europe/Helsinki'))
        )
        
        # Verify the event is in the future
        if start_time > now:
            event_url = f"https://kalenteri.jyvaskyla.fi/fi/tapahtuma/{event['id']}"
            
            # Get event details
            details = fetch_event_details(event_url)
            if details:
                description = details['description']
                
                # Show new event format
                print("\n1. New event post:")
                print(
                    f"Uusi tapahtuma lisätty:\n\n"
                    f"{details['title']}\n\n"
                    f"{start_time.strftime('%d.%m.%Y klo %H:%M')}\n\n"
                    f"{description}\n\n"
                    f"{event_url}\n\n"
                    f"#Jyväskylä #Jkl #Tapahtumat #KeskiSuomi"
                )
                
                # Show 24h reminder format
                print("\n2. 24h reminder post:")
                print(
                    f"Tapahtuma alkaa huomenna:\n\n"
                    f"{details['title']}\n\n"
                    f"{start_time.strftime('%d.%m.%Y klo %H:%M')}\n\n"
                    f"{description}\n\n"
                    f"{event_url}\n\n"
                    f"#Jyväskylä #Jkl #Tapahtumat #KeskiSuomi"
                )
                
                # Show 6h reminder format
                print("\n3. 6h reminder post:")
                print(
                    f"Tapahtuma alkaa pian:\n\n"
                    f"{details['title']}\n\n"
                    f"{start_time.strftime('%d.%m.%Y klo %H:%M')}\n\n"
                    f"{description}\n\n"
                    f"{event_url}\n\n"
                    f"#Jyväskylä #Jkl #Tapahtumat #KeskiSuomi"
                )

def test_weekly_events():
    # Initialize timezone and use ContentFetcher for consistency
    timezone = pytz.timezone('Europe/Helsinki')
    now = datetime.now(timezone)
    week_end = now + timedelta(days=7)
    
    # Get events for the next week
    url = "https://keskisuomievents.fi/api/items/event"
    params = {
        'start': now.strftime('%Y-%m-%d'),
        'end': week_end.strftime('%Y-%m-%d'),
        'limit': 10,
        'sort': 'start_time',
        'filter[start_time][_gte]': now.strftime('%Y-%m-%d'),
        'filter[end_time][_gte]': now.strftime('%Y-%m-%d')
    }
    
    response = requests.get(url, params=params)
    events_list = response.json()
    
    if events_list.get('data'):
        events = []
        for event in events_list['data'][:10]:
            event_url = f"https://kalenteri.jyvaskyla.fi/fi/tapahtuma/{event['id']}"
            details = fetch_event_details(event_url)
            
            if not details:
                continue
            
            start_time = (
                datetime.fromisoformat(event['start_time'].replace('Z', '+00:00'))
                .astimezone(timezone)
            )
            
            if now <= start_time < week_end:
                events.append((start_time, details['title'], event_url))
            time.sleep(0.5)
        
        if events:
            # Sort events by date
            events.sort()
            
            # Format the weekly events post
            content = "Tämän viikon tapahtumat:\n\n"
            for start_time, title, url in events:
                content += f"- {title}, {start_time.strftime('%d.%m.%Y klo %H:%M')}\n"
            content += "\nhttps://kalenteri.jyvaskyla.fi\n\n#Jyväskylä #Jkl #Tapahtumat #KeskiSuomi"
            print("\nWeekly events post format:")
            print(content)
        else:
            print("No events found for the next week")

if __name__ == "__main__":
    main()
    test_weekly_events()