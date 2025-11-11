"""
Reset script for production launch - Fresh start for all users

This script will:
1. Reset all user points to 0 (all types)
2. Reset all user coins to 0
3. Clear all habit completions
4. Clear all streak data
5. Clear monthly stats
6. Change all reward shop items to 'any' point type
7. Keep all habits, rewards, groups, and user accounts intact
"""

import sqlite3
import shutil
from datetime import datetime
import sys
import io

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DB_FILE = 'bot.db'


def backup_database():
    """Create a backup of the database before reset"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'bot_backup_pre_production_{timestamp}.db'
    shutil.copy2(DB_FILE, backup_file)
    print(f"✅ Database backed up to {backup_file}")
    return backup_file


def reset_database():
    """Reset all user progress data for production launch"""
    print("🚀 Starting production reset...\n")

    # Backup first
    backup_file = backup_database()

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    try:
        # 1. Reset all user points to 0
        print("1️⃣ Resetting all user points to 0...")
        cursor.execute('''
            UPDATE users SET
                points_physical = 0,
                points_arts = 0,
                points_food_related = 0,
                points_educational = 0,
                points_other = 0,
                coins = 0
        ''')
        affected_users = cursor.rowcount
        print(f"   ✅ Reset points for {affected_users} users")

        # 2. Clear all habit completions
        print("\n2️⃣ Clearing all habit completions...")
        cursor.execute('SELECT COUNT(*) FROM habit_completions')
        completion_count = cursor.fetchone()[0]
        cursor.execute('DELETE FROM habit_completions')
        print(f"   ✅ Deleted {completion_count} habit completions")

        # 3. Clear all streak data
        print("\n3️⃣ Clearing all streak data...")
        cursor.execute('SELECT COUNT(*) FROM habit_streaks')
        streak_count = cursor.fetchone()[0]
        cursor.execute('DELETE FROM habit_streaks')
        print(f"   ✅ Deleted {streak_count} streak records")

        # 4. Clear monthly stats
        print("\n4️⃣ Clearing monthly statistics...")
        cursor.execute('SELECT COUNT(*) FROM monthly_stats')
        stats_count = cursor.fetchone()[0]
        cursor.execute('DELETE FROM monthly_stats')
        print(f"   ✅ Deleted {stats_count} monthly stat records")

        # 5. Change all rewards to 'any' point type
        print("\n5️⃣ Changing all shop items to 'any' point type...")
        cursor.execute('SELECT COUNT(*) FROM rewards')
        reward_count = cursor.fetchone()[0]
        cursor.execute("UPDATE rewards SET point_type = 'any'")
        print(f"   ✅ Updated {reward_count} rewards to 'any' point type")

        # Commit all changes
        conn.commit()

        # Print summary
        print("\n" + "="*60)
        print("📊 RESET SUMMARY")
        print("="*60)
        print(f"✅ Users reset: {affected_users}")
        print(f"✅ Habit completions cleared: {completion_count}")
        print(f"✅ Streaks cleared: {streak_count}")
        print(f"✅ Monthly stats cleared: {stats_count}")
        print(f"✅ Rewards changed to 'any': {reward_count}")
        print("="*60)

        # Show what's preserved
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM habits')
        habit_count = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM groups')
        group_count = cursor.fetchone()[0]

        print("\n🔒 PRESERVED DATA")
        print("="*60)
        print(f"👥 User accounts: {user_count}")
        print(f"🎯 Habits: {habit_count}")
        print(f"👥 Groups: {group_count}")
        print(f"🎁 Rewards: {reward_count} (now all 'any' type)")
        print("="*60)

        print(f"\n✅ Production reset complete!")
        print(f"📦 Backup saved: {backup_file}")
        print("\n🎉 Ready for production! Users can start tracking habits from today!")

    except Exception as e:
        print(f"\n❌ Reset failed: {e}")
        conn.rollback()
        print(f"Database can be restored from backup: {backup_file}")
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    print("="*60)
    print("🚀 PRODUCTION RESET SCRIPT")
    print("="*60)
    print("\nThis will:")
    print("  • Reset all points and coins to 0")
    print("  • Clear all habit completions and streaks")
    print("  • Clear monthly statistics")
    print("  • Change all rewards to 'any' point type")
    print("  • KEEP all users, habits, rewards, and groups")
    print("\n⚠️  This action will reset all progress data!")
    print("="*60)

    response = input("\nAre you sure you want to continue? (yes/no): ")

    if response.lower() in ['yes', 'y']:
        print("\n")
        reset_database()
    else:
        print("\n❌ Reset cancelled. No changes made.")
