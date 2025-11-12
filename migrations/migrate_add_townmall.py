"""
Migration script to add Town Mall feature

Creates:
1. town_mall_items table for items available to purchase
2. town_mall_purchases table for tracking user purchases
3. Initial 5 items as specified
"""

import sqlite3
import sys
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB_FILE = 'bot.db'


def migrate():
    """Add town mall tables and initial items"""
    print("🏪 Starting Town Mall migration...\n")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # Create town_mall_items table
        print("1️⃣ Creating town_mall_items table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS town_mall_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price_coins INTEGER NOT NULL,
                image_filename TEXT,
                stock INTEGER NOT NULL DEFAULT -1,
                available BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("   ✅ town_mall_items table created\n")

        # Create town_mall_purchases table
        print("2️⃣ Creating town_mall_purchases table...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS town_mall_purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                item_name TEXT NOT NULL,
                price_paid INTEGER NOT NULL,
                purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(telegram_id),
                FOREIGN KEY (item_id) REFERENCES town_mall_items(id)
            )
        ''')
        print("   ✅ town_mall_purchases table created\n")

        # Check if items already exist
        cursor.execute('SELECT COUNT(*) FROM town_mall_items')
        existing_count = cursor.fetchone()[0]

        if existing_count > 0:
            print(f"⚠️  Town Mall already has {existing_count} items. Skipping initial data.\n")
        else:
            # Insert initial items
            print("3️⃣ Adding initial town mall items...")

            items = [
                ('Гигрометр', 'Измеритель влажности воздуха', 20, 'gigrometr.jpg', 10),
                ('Рандомная мягкая игрушка', 'Случайная мягкая игрушка на выбор', 40, 'plush_toy.jpg', 5),
                ('Рандомная новая настолка с пиндош', 'Новая настольная игра (случайный выбор)', 100, 'board_game.jpg', 3),
                ('Увлажнитель воздуха', 'Прибор для увлажнения воздуха в помещении', 120, 'humidifier.jpg', 5),
                ('Двухместная палатка', 'Палатка для двоих человек', 1000, 'tent.jpg', -1),  # -1 = unlimited
            ]

            cursor.executemany('''
                INSERT INTO town_mall_items (name, description, price_coins, image_filename, stock)
                VALUES (?, ?, ?, ?, ?)
            ''', items)

            for item in items:
                stock_text = f"{item[4]} pcs" if item[4] > 0 else "unlimited"
                print(f"   ✅ {item[0]}: {item[2]} coins, {stock_text}")

            print(f"\n   Total: {len(items)} items added\n")

        conn.commit()

        print("="*60)
        print("✅ Town Mall migration completed successfully!")
        print("="*60)
        print("\n📝 Next steps:")
        print("1. Add item images to images/townmall/ folder:")
        print("   - gigrometr.jpg")
        print("   - plush_toy.jpg")
        print("   - board_game.jpg")
        print("   - humidifier.jpg")
        print("   - tent.jpg")
        print("2. Run the bot and test with /menu → Town Mall")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    migrate()
