import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MASTODON_INSTANCE = os.getenv('MASTODON_INSTANCE')
    MASTODON_ACCESS_TOKEN = os.getenv('MASTODON_ACCESS_TOKEN')
    CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', 30)) 