"""
Migration script to add sponsor_id field to town_mall_items

This adds a sponsor field to track which user created/sponsored each Town Mall item.
All existing items will be assigned to Ayan (telegram_id: 499803988) as the sponsor.
"""

import sqlite3
import sys
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB_FILE = 'bot.db'
AYAN_ID = 499803988  # Ayan's telegram_id


def migrate():
    """Add sponsor_id field to town_mall_items and set Ayan as sponsor for existing items"""
    print("🔧 Adding sponsor_id to town_mall_items...\n")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # Add sponsor_id column
        cursor.execute('''
            ALTER TABLE town_mall_items
            ADD COLUMN sponsor_id INTEGER REFERENCES users(telegram_id)
        ''')
        print("✅ Added sponsor_id column\n")

        # Update existing items to have Ayan as sponsor
        cursor.execute('''
            UPDATE town_mall_items
            SET sponsor_id = ?
            WHERE sponsor_id IS NULL
        ''', (AYAN_ID,))

        updated_count = cursor.rowcount
        print(f"✅ Set Ayan as sponsor for {updated_count} existing items\n")

        conn.commit()
        print("✅ Migration completed successfully!\n")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    try:
        migrate()
    except KeyboardInterrupt:
        print("\n\n❌ Migration interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
