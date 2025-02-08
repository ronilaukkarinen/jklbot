import argparse
from bot import JyvaskylaBot

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Run in test mode with more frequent updates")
    args = parser.parse_args()

    if args.test:
        Config.CHECK_INTERVAL = 1  # Check every minute in test mode
    
    bot = JyvaskylaBot()
    bot.run() 