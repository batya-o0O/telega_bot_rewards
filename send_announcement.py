"""
Send announcement messages to all group chats

This script allows you to broadcast messages to all groups that have
linked their Telegram chat to the bot (via /setgroupchat).

Usage:
    python send_announcement.py

You'll be prompted to enter your announcement message.
The script will send it to all active group chats.
"""

import asyncio
import sqlite3
import sys
import io
from telegram import Bot
from telegram.error import TelegramError
from dotenv import load_dotenv
import os

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')

# Load environment variables
load_dotenv()

DB_FILE = 'bot.db'


def get_all_group_chats():
    """Get all groups that have linked Telegram chats"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT g.id, g.name, g.telegram_chat_id
        FROM groups g
        WHERE g.telegram_chat_id IS NOT NULL
    ''')

    groups = cursor.fetchall()
    conn.close()
    return groups


async def send_announcement_to_groups(message: str, preview: bool = False):
    """
    Send announcement to all group chats

    Args:
        message: The announcement message to send
        preview: If True, only show which groups would receive the message (dry run)
    """
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("❌ Error: TELEGRAM_BOT_TOKEN not found in .env file")
        return

    bot = Bot(token=token)
    groups = get_all_group_chats()

    if not groups:
        print("📭 No groups with linked Telegram chats found.")
        print("   Groups need to use /setgroupchat command first.")
        return

    print(f"\n📊 Found {len(groups)} group(s) with linked chats:\n")

    for group_id, group_name, chat_id in groups:
        print(f"  • {group_name} (Group ID: {group_id}, Chat ID: {chat_id})")

    if preview:
        print("\n👁️  Preview mode - no messages will be sent.")
        print("\n📝 Message that would be sent:")
        print("=" * 60)
        print(message)
        print("=" * 60)
        return

    print("\n" + "=" * 60)
    print("📝 Message to send:")
    print("=" * 60)
    print(message)
    print("=" * 60)

    confirm = input("\n⚠️  Send this message to all groups? (yes/no): ").strip().lower()

    if confirm not in ['yes', 'y']:
        print("❌ Announcement cancelled.")
        return

    print("\n📤 Sending announcements...\n")

    success_count = 0
    failed_count = 0

    for group_id, group_name, chat_id in groups:
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='Markdown'  # Allows bold, italic, etc.
            )
            print(f"  ✅ Sent to: {group_name}")
            success_count += 1
            await asyncio.sleep(0.5)  # Small delay to avoid rate limits

        except TelegramError as e:
            print(f"  ❌ Failed to send to {group_name}: {e}")
            failed_count += 1

    print("\n" + "=" * 60)
    print("📊 Summary:")
    print(f"  ✅ Successfully sent: {success_count}")
    print(f"  ❌ Failed: {failed_count}")
    print("=" * 60)


def main():
    """Main function"""
    print("=" * 60)
    print("📢 Bot Announcement Sender")
    print("=" * 60)

    print("\nChoose announcement type:")
    print("1. Patch Update / Bug Fix")
    print("2. New Feature")
    print("3. Maintenance Notice")
    print("4. General Announcement")
    print("5. Custom Message")

    choice = input("\nEnter choice (1-5): ").strip()

    templates = {
        '1': "🔧 *Patch Update*\n\n{content}\n\n_Bot has been updated. Restart /menu if needed._",
        '2': "✨ *New Feature*\n\n{content}\n\n_Try it out: /menu_",
        '3': "⚠️ *Maintenance Notice*\n\n{content}\n\n_Thank you for your patience._",
        '4': "📢 *Announcement*\n\n{content}",
        '5': "{content}"
    }

    if choice not in templates:
        print("❌ Invalid choice. Exiting.")
        return

    print("\n📝 Enter your announcement message:")
    print("   (Type your message, then press Enter twice to finish)")
    print("   (Markdown supported: *bold*, _italic_, `code`)")
    print()

    lines = []
    empty_count = 0

    while True:
        line = input()
        if line == "":
            empty_count += 1
            if empty_count >= 2:
                break
        else:
            empty_count = 0
            lines.append(line)

    if not lines:
        print("❌ No message entered. Exiting.")
        return

    content = "\n".join(lines)
    message = templates[choice].format(content=content)

    # Preview mode
    print("\n" + "=" * 60)
    print("👁️  PREVIEW MODE")
    print("=" * 60)

    asyncio.run(send_announcement_to_groups(message, preview=True))

    # Confirm to send
    print("\n" + "=" * 60)
    proceed = input("Proceed with sending? (yes/no): ").strip().lower()

    if proceed in ['yes', 'y']:
        asyncio.run(send_announcement_to_groups(message, preview=False))
    else:
        print("❌ Announcement cancelled.")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user. Exiting.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
