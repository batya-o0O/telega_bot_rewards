"""
Check streak announcements and diagnose why 7-day streak wasn't announced

This script checks:
1. All habit streaks in the database
2. Which milestones have been announced
3. Identifies any streaks that should have triggered announcements but didn't
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3

def check_streaks():
    """Check all streaks and their announcement status"""

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    print("=" * 70)
    print("STREAK ANNOUNCEMENT DIAGNOSTIC REPORT")
    print("=" * 70)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # Check if habit_streaks table exists
    cursor.execute('''
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='habit_streaks'
    ''')

    if not cursor.fetchone():
        print("[ERROR] habit_streaks table does not exist!")
        print("\nThis table is required for streak tracking.")
        print("You may need to run a migration to create it.")
        conn.close()
        return

    print("[OK] habit_streaks table exists\n")

    # Get all streaks
    cursor.execute('''
        SELECT
            hs.user_id,
            u.first_name,
            u.username,
            hs.habit_id,
            h.name as habit_name,
            hs.current_streak,
            hs.best_streak,
            hs.last_completion_date,
            hs.milestone_7_announced,
            hs.milestone_15_announced,
            hs.milestone_30_announced
        FROM habit_streaks hs
        JOIN users u ON hs.user_id = u.telegram_id
        JOIN habits h ON hs.habit_id = h.id
        ORDER BY hs.current_streak DESC
    ''')

    streaks = cursor.fetchall()

    if not streaks:
        print("[INFO] No streak records found in the database.\n")
        conn.close()
        return

    print(f"[INFO] Found {len(streaks)} streak record(s)\n")
    print("-" * 70)

    issues_found = []

    for streak in streaks:
        user_id, first_name, username, habit_id, habit_name, current, best, last_date, m7, m15, m30 = streak

        user_display = first_name or username or f"User {user_id}"

        print(f"\n👤 User: {user_display} (ID: {user_id})")
        print(f"   Habit: {habit_name} (ID: {habit_id})")
        print(f"   Current Streak: {current} days")
        print(f"   Best Streak: {best} days")
        print(f"   Last Completion: {last_date}")
        print(f"   Milestones Announced:")
        print(f"      7-day:  {'✅ Yes' if m7 else '❌ No'}")
        print(f"      15-day: {'✅ Yes' if m15 else '❌ No'}")
        print(f"      30-day: {'✅ Yes' if m30 else '❌ No'}")

        # Check for issues
        if current >= 7 and not m7:
            issue = f"🔴 {user_display} has {current}-day streak on '{habit_name}' but 7-day milestone NOT announced!"
            issues_found.append(issue)
            print(f"\n   {issue}")

        if current >= 15 and not m15:
            issue = f"🔴 {user_display} has {current}-day streak on '{habit_name}' but 15-day milestone NOT announced!"
            issues_found.append(issue)
            print(f"   {issue}")

        if current >= 30 and not m30:
            issue = f"🔴 {user_display} has {current}-day streak on '{habit_name}' but 30-day milestone NOT announced!"
            issues_found.append(issue)
            print(f"   {issue}")

        # Check for "No Sugar Day" specifically
        if "sugar" in habit_name.lower() and current == 7 and not m7:
            print(f"\n   ⚠️  THIS IS THE REPORTED ISSUE!")
            print(f"   User reached 7-day streak but announcement wasn't sent.")
            print(f"   Milestone flag m7 = {m7} (should be 1 after announcement)")

    print("\n" + "=" * 70)

    if issues_found:
        print(f"\n🔍 ISSUES FOUND: {len(issues_found)}")
        print("\nSummary of Problems:")
        for i, issue in enumerate(issues_found, 1):
            print(f"{i}. {issue}")

        print("\n💡 POSSIBLE CAUSES:")
        print("   1. The habit was completed but toggle_habit handler didn't run properly")
        print("   2. Group chat ID is not set (announcements can't be sent)")
        print("   3. Bot was restarted during completion")
        print("   4. The streak was built up by backdating (yesterday's habits)")
        print("   5. Database migration created streaks but didn't announce them")

        print("\n🔧 RECOMMENDED ACTIONS:")
        print("   1. Check if group has group_chat_id set")
        print("   2. Verify bot has permission to post in the group chat")
        print("   3. Check if announcements are enabled for the group")
        print("   4. Review recent completions to see if they went through toggle_habit")
    else:
        print("\n✅ No issues found. All streaks have appropriate announcements.")

    print("\n" + "=" * 70)

    # Check group chat settings
    print("\n📢 GROUP ANNOUNCEMENT SETTINGS:")
    print("-" * 70)

    cursor.execute('''
        SELECT id, name, group_chat_id
        FROM groups
    ''')

    groups = cursor.fetchall()

    for group in groups:
        group_id, group_name, chat_id = group
        print(f"\nGroup: {group_name} (ID: {group_id})")
        if chat_id:
            print(f"   ✅ Chat ID set: {chat_id}")
        else:
            print(f"   ❌ No chat ID set - announcements CANNOT be sent!")
            print(f"   ℹ️  Use /setgroupchat in the Telegram group to link it")

    print("\n" + "=" * 70)

    # Check recent completions
    print("\n📅 RECENT HABIT COMPLETIONS (Last 10):")
    print("-" * 70)

    cursor.execute('''
        SELECT
            hc.user_id,
            u.first_name,
            hc.habit_id,
            h.name,
            hc.completion_date
        FROM habit_completions hc
        JOIN users u ON hc.user_id = u.telegram_id
        JOIN habits h ON hc.habit_id = h.id
        ORDER BY hc.completion_date DESC
        LIMIT 10
    ''')

    completions = cursor.fetchall()

    for comp in completions:
        user_id, first_name, habit_id, habit_name, comp_date = comp
        print(f"{comp_date}: {first_name} - {habit_name}")

    print("\n" + "=" * 70)

    conn.close()

if __name__ == "__main__":
    check_streaks()
