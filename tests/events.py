import sys
import os
from datetime import datetime
import pytz
import logging
import requests
from bs4 import BeautifulSoup

# Add the parent directory to the Python path so we can import the main module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from content_fetchers import ContentFetcher

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class MockDatabase:
    def is_posted(self, content_id):
        return False  # Always return False to see all events

def fetch_event_details(url):
    """Fetch event details by scraping the event page"""
    response = requests.get(url)
    if response.status_code != 200:
        return None
        
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract details using more robust selectors
    title = soup.find('h1', class_=lambda x: x and 'pub_pub_name' in x)
    short_description = soup.find('p', class_=lambda x: x and 'pub_pub_short_descr' in x)
    description = soup.find('p', class_=lambda x: x and 'pub_pub_descr' in x)
    location = soup.find('div', class_=lambda x: x and 'pub_pub_info_address' in x)
    start_time = soup.find('div', class_=lambda x: x and 'pub_pub_info_start' in x)
    
    # Check if we got valid data (not just UUIDs)
    if title and not title.text.strip().startswith('‌') and not title.text.strip().endswith('‌'):
        # Split description into paragraphs and join with double newlines
        desc_text = description.text.strip() if description else None
        if desc_text:
            # Split on newlines and filter out empty lines
            paragraphs = [p.strip() for p in desc_text.split('\n') if p.strip()]
            desc_text = '\n\n'.join(paragraphs)
            
        return {
            'title': title.text.strip() if title else None,
            'short_description': short_description.text.strip() if short_description else None,
            'description': desc_text,
            'location': location.text.strip() if location else None,
            'start_time': start_time.text.strip() if start_time else None
        }
    return None

def main():
    # Initialize the content fetcher with a mock database
    fetcher = ContentFetcher(MockDatabase())
    
    # First, get one event's details to show the format
    url = "https://keskisuomievents.fi/api/items/event"
    params = {
        'start': 'now',
        'end': 'today',
        'limit': 1  # Just get one event
    }
    
    logging.info("Fetching event list...")
    response = requests.get(url, params=params)
    events_list = response.json()
    
    if events_list.get('data'):
        event = events_list['data'][0]
        event_url = f"https://kalenteri.jyvaskyla.fi/fi/tapahtuma/{event['id']}"
        
        logging.info("\nExample event post formats:")
        
        # Get event details
        details = fetch_event_details(event_url)
        if details:
            start_time = datetime.fromisoformat(event['start_time'].replace('Z', '+00:00'))
            description = details['description']
            
            # Show new event format
            logging.info("\n1. New event post:")
            logging.info(
                f"Uusi tapahtuma lisätty:\n\n\n"
                f"{details['title']}\n\n"
                f"{start_time.strftime('%d.%m.%Y klo %H:%M')}\n\n\n"
                f"{description}\n\n\n"
                f"{event_url}\n\n\n"
                f"#Jyväskylä #Jkl #Tapahtumat #KeskiSuomi"
            )
            
            # Show 24h reminder format
            logging.info("\n2. 24h reminder post:")
            logging.info(
                f"Tapahtuma alkaa huomenna:\n\n\n"
                f"{details['title']}\n\n"
                f"{start_time.strftime('%d.%m.%Y klo %H:%M')}\n\n\n"
                f"{description}\n\n\n"
                f"{event_url}\n\n\n"
                f"#Jyväskylä #Jkl #Tapahtumat #KeskiSuomi"
            )
            
            # Show 6h reminder format
            logging.info("\n3. 6h reminder post:")
            logging.info(
                f"Tapahtuma alkaa pian:\n\n\n"
                f"{details['title']}\n\n"
                f"{start_time.strftime('%d.%m.%Y klo %H:%M')}\n\n\n"
                f"{description}\n\n\n"
                f"{event_url}\n\n\n"
                f"#Jyväskylä #Jkl #Tapahtumat #KeskiSuomi"
            )

if __name__ == "__main__":
    # Set logging to DEBUG level for more detailed output
    logging.getLogger().setLevel(logging.DEBUG)
    main() 