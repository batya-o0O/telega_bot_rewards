#!/usr/bin/env python3
"""
Migration script to upgrade database from v3 to v4
Adds support for:
- Coins system (sellers get coins, not points)
- Monthly statistics tracking
- Leaderboards (Best Shopkeeper & Dungeon Master)
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
    """Migrate database to v4"""
    print("Starting migration to database v4...")
    print("-" * 50)

    # Create backup first
    backup_path = backup_database(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if already migrated
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'coins' in columns:
            print("Database is already v4. No migration needed.")
            conn.close()
            return

        print("Migrating users table...")
        # Add coins column
        cursor.execute('ALTER TABLE users ADD COLUMN coins INTEGER DEFAULT 0')
        print("  [OK] Added coins column")

        print("\nCreating monthly_stats table...")
        # Create monthly stats table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monthly_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                month TEXT NOT NULL,
                points_earned INTEGER DEFAULT 0,
                coins_earned INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(telegram_id),
                UNIQUE(user_id, month)
            )
        ''')
        print("  [OK] Monthly stats table created")

        conn.commit()
        print("\n" + "=" * 50)
        print("Migration completed successfully!")
        print("=" * 50)
        print(f"\nBackup saved as: {backup_path}")
        print("\nNew features available:")
        print("1. Coins system:")
        print("   - Sellers receive COINS (not points) from purchases")
        print("   - Coins track your success as a shopkeeper")
        print("2. Monthly leaderboards:")
        print("   - Best Shopkeeper: Most coins earned")
        print("   - Dungeon Master: Most points earned from habits")
        print("3. Use /monthlyreport to see current standings")

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] Migration failed: {e}")
        print(f"Database can be restored from backup: {backup_path}")
        raise

    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
