from mastodon import Mastodon
import time
import schedule
import logging
from config import Config
from database import Database
from content_fetchers import ContentFetcher
from datetime import datetime
import pytz

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class JyvaskylaBot:
    def __init__(self):
        self.setup_mastodon()
        self.database = Database()
        self.content_fetcher = ContentFetcher(self.database)
        logging.info("Bot initialized successfully")

    def setup_mastodon(self):
        self.mastodon = Mastodon(
            access_token=Config.MASTODON_ACCESS_TOKEN,
            api_base_url=Config.MASTODON_INSTANCE
        )
        logging.info(f"Connected to Mastodon instance: {Config.MASTODON_INSTANCE}")

    def check_and_post_updates(self):
        logging.info("Checking for new updates...")

        # Check if it's Monday to post weekly events
        now = datetime.now(pytz.timezone('Europe/Helsinki'))
        logging.info(f"Current weekday: {now.strftime('%A')}")

        if now.weekday() == 0:  # 0 = Monday
            logging.info("It's Monday - checking for weekly events...")
            for content_id, content, event_type in self.content_fetcher.fetch_weekly_events():
                try:
                    self.mastodon.status_post(content)
                    self.database.add_posted(content_id, event_type, content)
                    logging.info(f"Posted weekly events summary with ID: {content_id}")
                    time.sleep(5)
                except Exception as e:
                    logging.error(f"Error posting weekly events to Mastodon: {e}")

        # Check events
        for content_id, content, event_type in self.content_fetcher.fetch_events():
            try:
                self.mastodon.status_post(content)
                self.database.add_posted(content_id, event_type, content)
                logging.info(f"Posted new {event_type}: {content[:100]}...")
                time.sleep(5)
            except Exception as e:
                logging.error(f"Error posting event to Mastodon: {e}")

        # Check Jyväskylä website
        for content_id, content in self.content_fetcher.fetch_jyvaskyla_website():
            try:
                self.mastodon.status_post(content)
                self.database.add_posted(content_id, 'jyvaskyla_website', content)
                logging.info(f"Posted new content from website: {content[:100]}...")
                time.sleep(5)
            except Exception as e:
                logging.error(f"Error posting to Mastodon: {e}")

        # Check Facebook
        for content_id, content in self.content_fetcher.fetch_facebook_posts():
            try:
                self.mastodon.status_post(content)
                self.database.add_posted(content_id, 'facebook', content)
                logging.info(f"Posted new content from Facebook: {content[:100]}...")
                time.sleep(5)
            except Exception as e:
                logging.error(f"Error posting to Mastodon: {e}")

    def run(self):
        logging.info(f"Starting bot with check interval of {Config.CHECK_INTERVAL} minutes")

        # Schedule checks
        schedule.every(Config.CHECK_INTERVAL).minutes.do(self.check_and_post_updates)

        # Initial check
        logging.info("Performing initial check...")
        self.check_and_post_updates()

        # Run continuously
        while True:
            schedule.run_pending()
            time.sleep(60)
