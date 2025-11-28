"""
Fix all broken streaks by recalculating them from habit_completions

This script:
1. Finds all habits with completions
2. Recalculates the correct streak for each user-habit pair
3. Updates the habit_streaks table with correct values
4. Identifies which milestones should have been announced
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3

def fix_streaks():
    """Recalculate and fix all streaks"""

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    # Get all unique user-habit combinations that have completions
    cursor.execute('''
        SELECT DISTINCT hc.user_id, hc.habit_id
        FROM habit_completions hc
    ''')

    user_habits = cursor.fetchall()

    print(f"Found {len(user_habits)} user-habit combinations to check")
    print("=" * 70)

    fixes = []
    announcements_needed = []

    for user_id, habit_id in user_habits:
        # Get all completion dates for this user-habit
        cursor.execute('''
            SELECT completion_date
            FROM habit_completions
            WHERE user_id = ? AND habit_id = ?
            ORDER BY completion_date DESC
        ''', (user_id, habit_id))

        dates = [row[0] for row in cursor.fetchall()]

        if not dates:
            continue

        # Calculate current streak
        current_streak = 1
        best_streak = 1
        temp_streak = 1

        for i in range(len(dates)-1):
            curr = datetime.strptime(dates[i], '%Y-%m-%d')
            prev = datetime.strptime(dates[i+1], '%Y-%m-%d')

            if (curr - prev).days == 1:
                temp_streak += 1
                if i == 0:  # Part of current streak
                    current_streak += 1
                if temp_streak > best_streak:
                    best_streak = temp_streak
            else:
                temp_streak = 1

        last_completion = dates[0]

        # Get current values from database
        cursor.execute('''
            SELECT current_streak, best_streak,
                   milestone_7_announced, milestone_15_announced, milestone_30_announced
            FROM habit_streaks
            WHERE user_id = ? AND habit_id = ?
        ''', (user_id, habit_id))

        db_data = cursor.fetchone()

        if db_data:
            db_streak, db_best, m7, m15, m30 = db_data

            if db_streak != current_streak or db_best < best_streak:
                # Get user and habit names for reporting
                cursor.execute('SELECT first_name, username FROM users WHERE telegram_id = ?', (user_id,))
                user_data = cursor.fetchone()
                user_name = user_data[0] or user_data[1] or f'User {user_id}'

                cursor.execute('SELECT name FROM habits WHERE id = ?', (habit_id,))
                habit_name = cursor.fetchone()[0]

                fixes.append({
                    'user_id': user_id,
                    'user_name': user_name,
                    'habit_id': habit_id,
                    'habit_name': habit_name,
                    'old_streak': db_streak,
                    'new_streak': current_streak,
                    'old_best': db_best,
                    'new_best': best_streak
                })

                # Check for missing announcements
                missing = []
                if current_streak >= 7 and not m7:
                    missing.append(7)
                if current_streak >= 15 and not m15:
                    missing.append(15)
                if current_streak >= 30 and not m30:
                    missing.append(30)

                if missing:
                    announcements_needed.append({
                        'user_name': user_name,
                        'habit_name': habit_name,
                        'streak': current_streak,
                        'missing_milestones': missing
                    })

                # Update the streak
                new_m7 = 1 if current_streak >= 7 else m7
                new_m15 = 1 if current_streak >= 15 else m15
                new_m30 = 1 if current_streak >= 30 else m30

                cursor.execute('''
                    UPDATE habit_streaks
                    SET current_streak = ?,
                        best_streak = ?,
                        last_completion_date = ?,
                        milestone_7_announced = ?,
                        milestone_15_announced = ?,
                        milestone_30_announced = ?
                    WHERE user_id = ? AND habit_id = ?
                ''', (current_streak, best_streak if best_streak > db_best else db_best,
                      last_completion, new_m7, new_m15, new_m30, user_id, habit_id))

        else:
            # No streak record exists, create one
            cursor.execute('''
                INSERT INTO habit_streaks
                (user_id, habit_id, current_streak, best_streak, last_completion_date,
                 milestone_7_announced, milestone_15_announced, milestone_30_announced)
                VALUES (?, ?, ?, ?, ?, 0, 0, 0)
            ''', (user_id, habit_id, current_streak, best_streak, last_completion))

    conn.commit()

    # Report results
    print("\nFIXES APPLIED:")
    print("-" * 70)

    if fixes:
        for fix in fixes:
            print(f"\n{fix['user_name']} - {fix['habit_name']}")
            print(f"  Streak: {fix['old_streak']} -> {fix['new_streak']} days")
            print(f"  Best: {fix['old_best']} -> {fix['new_best']} days")
    else:
        print("No streak mismatches found!")

    print("\n" + "=" * 70)
    print(f"TOTAL FIXES: {len(fixes)}")

    if announcements_needed:
        print("\n" + "=" * 70)
        print("MISSED ANNOUNCEMENTS:")
        print("-" * 70)
        for ann in announcements_needed:
            milestones_str = ", ".join([f"{m}-day" for m in ann['missing_milestones']])
            print(f"\n{ann['user_name']} - {ann['habit_name']}")
            print(f"  Current streak: {ann['streak']} days")
            print(f"  Missing: {milestones_str} announcement(s)")

        print("\n" + "=" * 70)
        print("RECOMMENDATION:")
        print("Create a script to send these missed announcements to the group")

    conn.close()

if __name__ == "__main__":
    print("=" * 70)
    print("STREAK FIX UTILITY")
    print("=" * 70)
    print()

    response = input("This will recalculate ALL streaks. Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled")
        sys.exit(0)

    print()
    fix_streaks()

    print()
    print("=" * 70)
    print("Done! Run verify_all_streaks.py to confirm fixes")
    print("=" * 70)
