"""
Migration script to add setgroupchat_confirmations table

This table stores pending confirmations for /setgroupchat command
to ensure the warning system works reliably across bot restarts.
"""

import sqlite3
import sys
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB_FILE = 'bot.db'


def migrate():
    """Add setgroupchat_confirmations table"""
    print("🔧 Adding setgroupchat_confirmations table...\n")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # Create confirmation tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS setgroupchat_confirmations (
                user_id INTEGER NOT NULL,
                group_id INTEGER NOT NULL,
                new_chat_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, group_id),
                FOREIGN KEY (user_id) REFERENCES users(telegram_id)
            )
        ''')

        conn.commit()
        print("✅ Table created successfully!\n")
        print("This table tracks pending /setgroupchat confirmations.")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    migrate()
