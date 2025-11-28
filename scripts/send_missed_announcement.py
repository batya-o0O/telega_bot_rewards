"""
Send missed 7-day streak announcement for timur's "no sugar day" habit

This script:
1. Sends an apology for the bug
2. Announces the 7-day streak achievement
3. Updates the database to mark the milestone as announced
"""

import sys
import os
import asyncio

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from telegram import Bot
import sqlite3

load_dotenv()

async def send_announcement():
    """Send the missed announcement"""

    # Get bot token
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("ERROR: TELEGRAM_BOT_TOKEN not found in .env file")
        return

    bot = Bot(token=token)

    # Get database info
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    # Get timur's user info and group
    cursor.execute('''
        SELECT u.telegram_id, u.group_id, g.group_chat_id
        FROM users u
        JOIN groups g ON u.group_id = g.id
        WHERE u.first_name = 'timur'
    ''')

    user_data = cursor.fetchone()
    if not user_data:
        print("ERROR: Could not find user 'timur' in database")
        conn.close()
        return

    user_id, group_id, group_chat_id = user_data

    if not group_chat_id:
        print("ERROR: Group chat ID not set. Use /setgroupchat to link the group.")
        conn.close()
        return

    # Get the habit info
    cursor.execute('''
        SELECT h.id, h.name
        FROM habits h
        WHERE h.name = 'no sugar day' AND h.group_id = ?
    ''', (group_id,))

    habit_data = cursor.fetchone()
    if not habit_data:
        print("ERROR: Could not find 'no sugar day' habit")
        conn.close()
        return

    habit_id, habit_name = habit_data

    print(f"Found:")
    print(f"  User: timur (ID: {user_id})")
    print(f"  Group ID: {group_id}")
    print(f"  Group Chat ID: {group_chat_id}")
    print(f"  Habit: {habit_name} (ID: {habit_id})")
    print()

    # Compose the announcement
    announcement = "🔧 Bot Update Notice 🔧\n\n"
    announcement += "We apologize for a bug that prevented some streak announcements from being sent! "
    announcement += "Thanks to timur for helping us catch and fix this issue. 🙏\n\n"
    announcement += "---\n\n"
    announcement += "🎉 Congratulations timur!\n\n"
    announcement += f"You've reached a 7-day streak on '{habit_name}'! 🔥\n"
    announcement += "Keep up the amazing work!\n\n"
    announcement += "✨ The bug has been fixed and future streak announcements will work correctly!"

    print("Sending announcement to group...")
    print("-" * 60)
    print("(Announcement text contains emojis - sending to Telegram...)")
    print("-" * 60)
    print()

    try:
        # Send the announcement
        await bot.send_message(
            chat_id=group_chat_id,
            text=announcement
        )
        print("[OK] Announcement sent successfully!")

        # Update the database to mark 7-day milestone as announced
        cursor.execute('''
            UPDATE habit_streaks
            SET milestone_7_announced = 1,
                current_streak = 7
            WHERE user_id = ? AND habit_id = ?
        ''', (user_id, habit_id))

        conn.commit()
        print("[OK] Database updated - milestone marked as announced")
        print("[OK] Streak corrected to 7 days")

    except Exception as e:
        print(f"[ERROR] Error sending announcement: {e}")
        print("\nMake sure:")
        print("1. The bot is added to the group")
        print("2. The bot has permission to send messages")
        print("3. The group_chat_id is correct")

    conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("MISSED ANNOUNCEMENT SENDER")
    print("=" * 60)
    print()

    asyncio.run(send_announcement())

    print()
    print("=" * 60)
    print("Done!")
    print("=" * 60)
