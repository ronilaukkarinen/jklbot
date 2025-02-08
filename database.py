import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_file="posted_content.db"):
        self.db_file = db_file
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS posted_content
                        (content_id TEXT PRIMARY KEY, 
                         source TEXT, 
                         content TEXT,
                         posted_date TIMESTAMP)''')
            conn.commit()

    def is_posted(self, content_id):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            c.execute('SELECT 1 FROM posted_content WHERE content_id = ?', (content_id,))
            return c.fetchone() is not None

    def add_posted(self, content_id, source, content):
        with sqlite3.connect(self.db_file) as conn:
            c = conn.cursor()
            c.execute('''INSERT INTO posted_content (content_id, source, content, posted_date)
                        VALUES (?, ?, ?, ?)''', 
                        (content_id, source, content, datetime.now()))
            conn.commit() 