#!/usr/bin/env python3
"""
Script to give all users 50 points of each type for testing purposes
"""

import sqlite3

def give_test_points(db_path="bot.db"):
    """Give all users 50 points of each type"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Get all users
        cursor.execute('SELECT telegram_id, username, first_name FROM users')
        users = cursor.fetchall()

        if not users:
            print("No users found in database.")
            conn.close()
            return

        print(f"Giving 50 points of each type to {len(users)} user(s)...\n")

        # Update all users to have 50 of each point type
        cursor.execute('''
            UPDATE users SET
                points_physical = 50,
                points_arts = 50,
                points_food_related = 50,
                points_educational = 50,
                points_other = 50
        ''')

        conn.commit()

        print("Points updated successfully!\n")
        print("=" * 60)

        # Show updated points for each user
        for user in users:
            telegram_id, username, first_name = user
            display_name = username or first_name or f"User {telegram_id}"
            print(f"\n{display_name} (ID: {telegram_id}):")
            print(f"  Physical: 50")
            print(f"  Arts: 50")
            print(f"  Food Related: 50")
            print(f"  Educational: 50")
            print(f"  Other: 50")
            print(f"  Total: 250 points")

        print("\n" + "=" * 60)
        print("All users now have 50 points of each type!")

    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        raise

    finally:
        conn.close()

if __name__ == '__main__':
    give_test_points()
