#!/usr/bin/env python3
"""
Migration script to upgrade database from v2 to v3
Adds support for:
- Group chat integration (group_chat_id)
- Habit streak tracking
- Streak milestone announcements
"""

import sqlite3
import shutil
from datetime import datetime

def backup_database(db_path="bot.db"):
    """Create a backup of the database"""
    backup_path = f"bot_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy(db_path, backup_path)
    print(f"Backup created: {backup_path}")
    return backup_path

def migrate(db_path="bot.db"):
    """Migrate database to v3"""
    print("Starting migration to database v3...")
    print("-" * 50)

    # Create backup first
    backup_path = backup_database(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if already migrated
        cursor.execute("PRAGMA table_info(groups)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'group_chat_id' in columns:
            print("Database is already v3. No migration needed.")
            conn.close()
            return

        print("Migrating groups table...")
        # Add group_chat_id column
        cursor.execute('ALTER TABLE groups ADD COLUMN group_chat_id INTEGER')
        print("  [OK] Added group_chat_id column")

        print("\nCreating habit_streaks table...")
        # Create habit streaks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS habit_streaks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                habit_id INTEGER NOT NULL,
                current_streak INTEGER DEFAULT 0,
                best_streak INTEGER DEFAULT 0,
                last_completion_date DATE,
                milestone_7_announced BOOLEAN DEFAULT 0,
                milestone_15_announced BOOLEAN DEFAULT 0,
                milestone_30_announced BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(telegram_id),
                FOREIGN KEY (habit_id) REFERENCES habits(id),
                UNIQUE(user_id, habit_id)
            )
        ''')
        print("  [OK] Habit streaks table created")

        conn.commit()
        print("\n" + "=" * 50)
        print("Migration completed successfully!")
        print("=" * 50)
        print(f"\nBackup saved as: {backup_path}")
        print("\nNew features available:")
        print("1. Link Telegram group chat with /setgroupchat")
        print("2. Automatic announcements in group chat:")
        print("   - New rewards added to shops")
        print("   - Purchases made")
        print("   - Streak milestones (7, 15, 30 days)")
        print("3. Habit streak tracking with milestones")

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] Migration failed: {e}")
        print(f"Database can be restored from backup: {backup_path}")
        raise

    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
