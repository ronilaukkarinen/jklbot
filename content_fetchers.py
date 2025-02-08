import requests
from bs4 import BeautifulSoup
import hashlib
from facebook_scraper import get_posts
import feedparser
from datetime import datetime, timedelta

class ContentFetcher:
    def __init__(self, database):
        self.database = database
        self.hashtags = "#Jyväskylä #Jkl #KeskiSuomi #Uutiset"

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