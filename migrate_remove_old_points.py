"""
Migration script to remove the old 'points' column from users table.
This column is no longer used since we migrated to typed points system.
"""

import sqlite3
import shutil
from datetime import datetime
import sys

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
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
    """Remove the old points column from users table"""
    print("Starting migration: Removing old 'points' column...")

    # Backup first
    backup_file = backup_database()

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # Check if the points column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        has_points_column = any(col[1] == 'points' for col in columns)

        if not has_points_column:
            print("❌ Old 'points' column not found. Migration may have already been applied.")
            conn.close()
            return

        print("Found old 'points' column. Removing it...")

        # SQLite doesn't support DROP COLUMN directly for older versions
        # We need to recreate the table without the points column

        # 1. Create new table without points column
        cursor.execute('''
            CREATE TABLE users_new (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                group_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                points_physical INTEGER DEFAULT 0,
                points_arts INTEGER DEFAULT 0,
                points_food_related INTEGER DEFAULT 0,
                points_educational INTEGER DEFAULT 0,
                points_other INTEGER DEFAULT 0,
                coins INTEGER DEFAULT 0,
                FOREIGN KEY (group_id) REFERENCES groups(id)
            )
        ''')

        # 2. Copy data from old table to new (excluding points column)
        cursor.execute('''
            INSERT INTO users_new (telegram_id, username, first_name, group_id, created_at,
                                   points_physical, points_arts, points_food_related,
                                   points_educational, points_other, coins)
            SELECT telegram_id, username, first_name, group_id, created_at,
                   points_physical, points_arts, points_food_related,
                   points_educational, points_other, coins
            FROM users
        ''')

        # 3. Drop old table
        cursor.execute('DROP TABLE users')

        # 4. Rename new table
        cursor.execute('ALTER TABLE users_new RENAME TO users')

        conn.commit()
        print("✅ Successfully removed old 'points' column from users table")

        # Verify the change
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        print("\nNew users table schema:")
        for col in columns:
            print(f"  {col[1]}: {col[2]}")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        print(f"Database has been restored from backup: {backup_file}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
