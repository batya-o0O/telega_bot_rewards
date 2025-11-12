"""
Migration script to add medals system

Medals are awarded when a user completes a habit for 30 consecutive days.
Features:
- Track medals per user per habit
- Medaled habits give 0.5 coins instead of 1 point
- 3+ medals changes conversion rate from 2:1 to 1.5:1
- Group habit completion tracking (every day of month completed by group)
"""

import sqlite3
import shutil
from datetime import datetime
import sys
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB_FILE = 'bot.db'


def backup_database():
    """Create a backup of the database before migration"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'bot_backup_{timestamp}.db'
    shutil.copy2(DB_FILE, backup_file)
    print(f"✅ Database backed up to {backup_file}")
    return backup_file


def migrate():
    """Add medals system tables"""
    print("Starting migration: Adding medals system...")

    # Backup first
    backup_file = backup_database()

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # Create medals table
        print("\n1️⃣ Creating medals table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS medals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                habit_id INTEGER NOT NULL,
                awarded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(telegram_id),
                FOREIGN KEY (habit_id) REFERENCES habits(id),
                UNIQUE(user_id, habit_id)
            )
        ''')
        print("   ✅ Medals table created")

        # Create group_habit_completions table for tracking group-wide habit completion
        print("\n2️⃣ Creating group_habit_completions table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS group_habit_completions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                habit_id INTEGER NOT NULL,
                month TEXT NOT NULL,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (group_id) REFERENCES groups(id),
                FOREIGN KEY (habit_id) REFERENCES habits(id),
                UNIQUE(group_id, habit_id, month)
            )
        ''')
        print("   ✅ Group habit completions table created")

        conn.commit()
        print("\n✅ Migration complete!")
        print(f"📦 Backup saved: {backup_file}")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        print(f"Database can be restored from backup: {backup_file}")
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    migrate()
