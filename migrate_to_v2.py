#!/usr/bin/env python3
"""
Migration script to upgrade database from v1 to v2
Adds support for:
- Typed points (physical, arts, food_related, educational, other)
- Habit types
- Point conversions
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
    """Migrate database to v2"""
    print("Starting migration to database v2...")
    print("-" * 50)

    # Create backup first
    backup_path = backup_database(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check current schema
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'points_physical' in columns:
            print("Database is already v2. No migration needed.")
            conn.close()
            return

        print("Migrating users table...")
        # Add new point columns
        cursor.execute('ALTER TABLE users ADD COLUMN points_physical INTEGER DEFAULT 0')
        cursor.execute('ALTER TABLE users ADD COLUMN points_arts INTEGER DEFAULT 0')
        cursor.execute('ALTER TABLE users ADD COLUMN points_food_related INTEGER DEFAULT 0')
        cursor.execute('ALTER TABLE users ADD COLUMN points_educational INTEGER DEFAULT 0')
        cursor.execute('ALTER TABLE users ADD COLUMN points_other INTEGER DEFAULT 0')

        # Move old points to 'other' category
        cursor.execute('UPDATE users SET points_other = points WHERE points IS NOT NULL')
        print("  [OK] User points migrated to typed points (moved to 'other' category)")

        print("\nMigrating habits table...")
        # Add habit_type column
        cursor.execute('ALTER TABLE habits ADD COLUMN habit_type TEXT NOT NULL DEFAULT "other"')
        print("  [OK] Habit types added (all set to 'other' by default)")

        print("\nMigrating rewards table...")
        # Add point_type column to rewards
        cursor.execute('ALTER TABLE rewards ADD COLUMN point_type TEXT NOT NULL DEFAULT "other"')
        print("  [OK] Reward point types added (all set to 'other' by default)")

        print("\nMigrating transactions table...")
        # Add point_type column to transactions
        cursor.execute('ALTER TABLE transactions ADD COLUMN point_type TEXT NOT NULL DEFAULT "other"')
        print("  [OK] Transaction point types added")

        print("\nCreating point_conversions table...")
        # Create point conversions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS point_conversions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                from_type TEXT NOT NULL,
                to_type TEXT NOT NULL,
                amount_from INTEGER NOT NULL,
                amount_to INTEGER NOT NULL,
                conversion_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(telegram_id)
            )
        ''')
        print("  [OK] Point conversions table created")

        conn.commit()
        print("\n" + "=" * 50)
        print("Migration completed successfully!")
        print("=" * 50)
        print(f"\nBackup saved as: {backup_path}")
        print("\nNext steps:")
        print("1. Update your code to use database_v2.py instead of database.py")
        print("2. Users can now set habit types when creating habits")
        print("3. Rewards can now specify point type requirements")
        print("4. Users can convert points at 2:1 ratio")

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] Migration failed: {e}")
        print(f"Database restored from backup: {backup_path}")
        raise

    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
