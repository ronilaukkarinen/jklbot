# Jyväskylä Bot for Mastodon

Jyväskylä Bot is a Mastodon bot that posts updates city of Jyväskylä news from various sources.

This bot posts:

- Jyväskylä news from RSS feed at jyvaskyla.fi
- Events in Jyväskylä
- Jyväskylä Facebook posts

![image](https://github.com/user-attachments/assets/0afc8d69-f25f-4af9-aae5-67349d28f545)

## Installation

First, make sure python-venv is installed:

```bash
sudo apt-get install python3-venv
```

For the Mastodon bot to work properly, you need the following permissions when creating the application token (_yourinstance.social_/settings/applications):

- `read` - to read public posts (optional, but good for verification)
- `write:statuses` - to post updates to your timeline

Create a virtual environment and activate it:

```bash
cd jklbot
python3 -m venv venv
source venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

Then run the bot:

```bash
python main.py
```

## Systemd service

Add with:

```bash
sudo nano /etc/systemd/system/jklbot.service
```

```ini
[Unit]
Description=Jyväskylä Mastodon Bot
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/jklbot
ExecStart=/path/to/jklbot/venv/bin/python3 /path/to/jklbot/main.py
Restart=always
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable jklbot
sudo systemctl start jklbot
```

Monitor:

```bash
sudo journalctl -u jklbot --all -f
```

## Contributing to the project

1. Fork the repository
2. Create a new branch
3. Make your changes and commit them
4. Push your changes to your fork
5. Create a pull request
