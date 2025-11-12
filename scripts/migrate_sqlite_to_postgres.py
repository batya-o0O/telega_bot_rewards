"""
Migration script to transfer data from SQLite to PostgreSQL/Supabase

This script migrates all data from the local SQLite database (bot.db)
to a PostgreSQL database (Supabase or other PostgreSQL instance).

Usage:
    python scripts/migrate_sqlite_to_postgres.py

Requires:
    - DATABASE_URL environment variable set to PostgreSQL connection string
    - Existing bot.db file with data to migrate
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from database_postgres import Database as PostgresDatabase

def migrate_data():
    """Migrate all data from SQLite to PostgreSQL"""

    # Check if DATABASE_URL is set
    if not os.getenv('DATABASE_URL'):
        print("❌ ERROR: DATABASE_URL environment variable not set!")
        print("Set it with your PostgreSQL connection string:")
        print("  export DATABASE_URL='postgresql://user:password@host:port/database'")
        return False

    # Check if bot.db exists
    if not os.path.exists('bot.db'):
        print("❌ ERROR: bot.db file not found!")
        print("Make sure you're running this from the project root directory.")
        return False

    print("🔄 Starting migration from SQLite to PostgreSQL...\n")

    # Connect to both databases
    sqlite_conn = sqlite3.connect('bot.db')
    sqlite_cursor = sqlite_conn.cursor()

    postgres_db = PostgresDatabase()
    print("✅ Connected to both databases\n")

    try:
        # 1. Migrate groups
        print("📦 Migrating groups...")
        sqlite_cursor.execute('SELECT id, name, group_chat_id, created_at FROM groups')
        groups = sqlite_cursor.fetchall()

        group_id_map = {}  # Map old IDs to new IDs
        for old_id, name, chat_id, created_at in groups:
            new_id = postgres_db.create_group(name)
            if chat_id:
                postgres_db.update_group_chat(new_id, chat_id)
            group_id_map[old_id] = new_id
            print(f"  ✓ Migrated group: {name} (ID: {old_id} → {new_id})")

        print(f"✅ Migrated {len(groups)} groups\n")

        # 2. Migrate users
        print("👤 Migrating users...")
        sqlite_cursor.execute('''
            SELECT telegram_id, username, first_name, group_id,
                   points_physical, points_arts, points_food_related,
                   points_educational, points_other, coins, joined_at
            FROM users
        ''')
        users = sqlite_cursor.fetchall()

        for user in users:
            telegram_id, username, first_name, old_group_id, \
                p_phys, p_arts, p_food, p_edu, p_other, coins, joined_at = user

            # Add user
            postgres_db.add_user(telegram_id, username, first_name)

            # Update group if exists
            if old_group_id and old_group_id in group_id_map:
                new_group_id = group_id_map[old_group_id]
                postgres_db.update_user_group(telegram_id, new_group_id)

            # Update points
            if p_phys: postgres_db.update_user_points(telegram_id, 'physical', p_phys)
            if p_arts: postgres_db.update_user_points(telegram_id, 'arts', p_arts)
            if p_food: postgres_db.update_user_points(telegram_id, 'food_related', p_food)
            if p_edu: postgres_db.update_user_points(telegram_id, 'educational', p_edu)
            if p_other: postgres_db.update_user_points(telegram_id, 'other', p_other)
            if coins: postgres_db.update_user_points(telegram_id, 'coins', coins)

            print(f"  ✓ Migrated user: {first_name or username} (ID: {telegram_id})")

        print(f"✅ Migrated {len(users)} users\n")

        # 3. Migrate habits
        print("✅ Migrating habits...")
        sqlite_cursor.execute('SELECT id, user_id, name, point_type, is_active, created_at FROM habits')
        habits = sqlite_cursor.fetchall()

        habit_id_map = {}
        for old_id, user_id, name, point_type, is_active, created_at in habits:
            new_id = postgres_db.add_habit(user_id, name, point_type)
            if not is_active:
                postgres_db.delete_habit(new_id)
            habit_id_map[old_id] = new_id
            print(f"  ✓ Migrated habit: {name} (ID: {old_id} → {new_id})")

        print(f"✅ Migrated {len(habits)} habits\n")

        # 4. Migrate habit completions
        print("📊 Migrating habit completions...")
        sqlite_cursor.execute('''
            SELECT habit_id, user_id, completed_at, points_earned
            FROM habit_completions
        ''')
        completions = sqlite_cursor.fetchall()

        for old_habit_id, user_id, completed_at, points_earned in completions:
            if old_habit_id in habit_id_map:
                new_habit_id = habit_id_map[old_habit_id]
                completed_datetime = datetime.fromisoformat(completed_at) if completed_at else datetime.now()

                # Note: We already added points when migrating users, so we just record completion
                conn = postgres_db.get_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO habit_completions (habit_id, user_id, completed_at, points_earned)
                    VALUES (%s, %s, %s, %s)
                ''', (new_habit_id, user_id, completed_datetime, points_earned))
                conn.commit()
                cursor.close()
                postgres_db.return_connection(conn)

        print(f"✅ Migrated {len(completions)} habit completions\n")

        # 5. Migrate medals
        print("🏅 Migrating medals...")
        sqlite_cursor.execute('SELECT user_id, habit_id, habit_name, earned_at FROM medals')
        medals = sqlite_cursor.fetchall()

        for user_id, old_habit_id, habit_name, earned_at in medals:
            if old_habit_id in habit_id_map:
                new_habit_id = habit_id_map[old_habit_id]
                postgres_db.award_medal(user_id, new_habit_id, habit_name)
                print(f"  ✓ Migrated medal for habit: {habit_name}")

        print(f"✅ Migrated {len(medals)} medals\n")

        # 6. Migrate rewards
        print("🎁 Migrating rewards...")
        sqlite_cursor.execute('''
            SELECT id, owner_id, name, price, point_type, is_active, created_at
            FROM rewards
        ''')
        rewards = sqlite_cursor.fetchall()

        reward_id_map = {}
        for old_id, owner_id, name, price, point_type, is_active, created_at in rewards:
            new_id = postgres_db.add_reward(owner_id, name, price, point_type)
            if not is_active:
                postgres_db.delete_reward(new_id)
            reward_id_map[old_id] = new_id
            print(f"  ✓ Migrated reward: {name} (ID: {old_id} → {new_id})")

        print(f"✅ Migrated {len(rewards)} rewards\n")

        # 7. Migrate reward purchases
        print("💰 Migrating reward purchases...")
        sqlite_cursor.execute('''
            SELECT reward_id, buyer_id, seller_id, price, point_type, purchased_at
            FROM reward_purchases
        ''')
        purchases = sqlite_cursor.fetchall()

        for old_reward_id, buyer_id, seller_id, price, point_type, purchased_at in purchases:
            if old_reward_id in reward_id_map:
                new_reward_id = reward_id_map[old_reward_id]
                purchased_datetime = datetime.fromisoformat(purchased_at) if purchased_at else datetime.now()

                conn = postgres_db.get_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO reward_purchases (reward_id, buyer_id, seller_id, price, point_type, purchased_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (new_reward_id, buyer_id, seller_id, price, point_type, purchased_datetime))
                conn.commit()
                cursor.close()
                postgres_db.return_connection(conn)

        print(f"✅ Migrated {len(purchases)} reward purchases\n")

        # 8. Migrate Town Mall items
        print("🏪 Migrating Town Mall items...")
        sqlite_cursor.execute('''
            SELECT id, name, price, stock, photo_file_id, sponsor_id, is_active, created_at
            FROM townmall_items
        ''')
        townmall_items = sqlite_cursor.fetchall()

        townmall_id_map = {}
        for old_id, name, price, stock, photo_file_id, sponsor_id, is_active, created_at in townmall_items:
            new_id = postgres_db.add_townmall_item(name, price, stock, sponsor_id, photo_file_id)
            if not is_active:
                postgres_db.delete_townmall_item(new_id)
            townmall_id_map[old_id] = new_id
            print(f"  ✓ Migrated Town Mall item: {name} (ID: {old_id} → {new_id})")

        print(f"✅ Migrated {len(townmall_items)} Town Mall items\n")

        # 9. Migrate Town Mall purchases
        print("🛍️ Migrating Town Mall purchases...")
        sqlite_cursor.execute('''
            SELECT item_id, buyer_id, price, purchased_at
            FROM townmall_purchases
        ''')
        townmall_purchases = sqlite_cursor.fetchall()

        for old_item_id, buyer_id, price, purchased_at in townmall_purchases:
            if old_item_id in townmall_id_map:
                new_item_id = townmall_id_map[old_item_id]
                purchased_datetime = datetime.fromisoformat(purchased_at) if purchased_at else datetime.now()

                conn = postgres_db.get_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO townmall_purchases (item_id, buyer_id, price, purchased_at)
                    VALUES (%s, %s, %s, %s)
                ''', (new_item_id, buyer_id, price, purchased_datetime))
                conn.commit()
                cursor.close()
                postgres_db.return_connection(conn)

        print(f"✅ Migrated {len(townmall_purchases)} Town Mall purchases\n")

        print("=" * 60)
        print("🎉 MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nSummary:")
        print(f"  • {len(groups)} groups")
        print(f"  • {len(users)} users")
        print(f"  • {len(habits)} habits")
        print(f"  • {len(completions)} habit completions")
        print(f"  • {len(medals)} medals")
        print(f"  • {len(rewards)} rewards")
        print(f"  • {len(purchases)} reward purchases")
        print(f"  • {len(townmall_items)} Town Mall items")
        print(f"  • {len(townmall_purchases)} Town Mall purchases")
        print("\n✅ Your data has been migrated to PostgreSQL!")
        print("\nNext steps:")
        print("1. Update bot.py to use database_postgres.py instead of database.py")
        print("2. Test the bot with the new database")
        print("3. Keep bot.db as a backup")

        return True

    except Exception as e:
        print(f"\n❌ ERROR during migration: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        sqlite_conn.close()
        postgres_db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("SQLite to PostgreSQL Migration Tool")
    print("=" * 60)
    print()

    # Check for DATABASE_URL
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        # Hide password in display
        display_url = db_url
        if '@' in display_url and ':' in display_url:
            parts = display_url.split('@')
            if len(parts) == 2:
                before_at = parts[0]
                if ':' in before_at:
                    user_part = before_at.split(':')[0]
                    display_url = f"{user_part}:****@{parts[1]}"

        print(f"📍 Target database: {display_url}")
    else:
        print("⚠️  No DATABASE_URL set")

    print()

    # Confirm before proceeding
    response = input("⚠️  This will copy all data from bot.db to PostgreSQL. Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Migration cancelled")
        sys.exit(0)

    print()
    success = migrate_data()

    sys.exit(0 if success else 1)
