"""
Send missed 7-day and 15-day announcements for timur's no sugar day habit
"""

import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from telegram import Bot
import sqlite3

load_dotenv()

async def send_announcements():
    """Send the missed milestones"""

    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("[ERROR] TELEGRAM_BOT_TOKEN not found")
        return

    bot = Bot(token=token)
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    # Get group chat ID
    cursor.execute('''
        SELECT g.group_chat_id
        FROM users u
        JOIN groups g ON u.group_id = g.id
        WHERE u.first_name = 'timur'
    ''')

    result = cursor.fetchone()
    if not result or not result[0]:
        print("[ERROR] No group chat ID found")
        conn.close()
        return

    chat_id = result[0]

    # Send announcement for 15-day milestone only
    announcement = "🎊 Congratulations timur!\n\n"
    announcement += "We missed announcing your 15-day streak milestone on 'no sugar day'! 🔥🔥\n\n"
    announcement += "You're now at an incredible 16-day streak!\n"
    announcement += "Keep up the amazing work!\n\n"
    announcement += "---\n\n"
    announcement += "Note: The streak tracking bug has been fixed. ✨"

    print("Sending announcement...")
    try:
        await bot.send_message(chat_id=chat_id, text=announcement)
        print("[OK] Announcement sent successfully!")
    except Exception as e:
        print(f"[ERROR] {e}")

    conn.close()

if __name__ == "__main__":
    asyncio.run(send_announcements())
