"""
Verify and report on all user streaks

This script:
1. Lists all streaks ordered by current streak length
2. Verifies each streak by counting consecutive completions
3. Identifies mismatches and missing announcements
"""

import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3

def verify_streaks():
    """Generate comprehensive streak report"""

    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()

    # Get all streaks with user info
    cursor.execute('''
        SELECT
            u.first_name,
            u.username,
            h.name as habit_name,
            hs.current_streak,
            hs.best_streak,
            hs.last_completion_date,
            hs.milestone_7_announced,
            hs.milestone_15_announced,
            hs.milestone_30_announced,
            hs.user_id,
            hs.habit_id
        FROM habit_streaks hs
        JOIN users u ON hs.user_id = u.telegram_id
        JOIN habits h ON hs.habit_id = h.id
        ORDER BY hs.current_streak DESC
    ''')

    streaks = cursor.fetchall()

    with open('all_streaks_report.txt', 'w', encoding='utf-8') as f:
        f.write('ALL USER STREAKS REPORT\n')
        f.write('=' * 80 + '\n')
        f.write(f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write(f'Total streaks: {len(streaks)}\n')
        f.write('=' * 80 + '\n\n')

        total_issues = 0

        for i, streak in enumerate(streaks, 1):
            first_name, username, habit_name, current, best, last_date, m7, m15, m30, user_id, habit_id = streak

            user_display = first_name or username or f'User {user_id}'

            f.write(f'{i}. {user_display} - {habit_name}\n')
            f.write(f'   Current Streak: {current} days\n')
            f.write(f'   Best Streak: {best} days\n')
            f.write(f'   Last Completion: {last_date}\n')
            f.write(f'   Milestones: 7d={"YES" if m7 else "NO"}, 15d={"YES" if m15 else "NO"}, 30d={"YES" if m30 else "NO"}\n')

            # Verify the streak by counting consecutive days
            cursor.execute('''
                SELECT completion_date
                FROM habit_completions
                WHERE user_id = ? AND habit_id = ?
                ORDER BY completion_date DESC
                LIMIT 100
            ''', (user_id, habit_id))

            dates = [row[0] for row in cursor.fetchall()]

            if dates:
                # Calculate actual streak
                actual_streak = 1
                for j in range(len(dates)-1):
                    curr = datetime.strptime(dates[j], '%Y-%m-%d')
                    prev = datetime.strptime(dates[j+1], '%Y-%m-%d')
                    if (curr - prev).days == 1:
                        actual_streak += 1
                    else:
                        break

                f.write(f'   Verified Streak: {actual_streak} days')

                if actual_streak != current:
                    f.write(f' [MISMATCH! Database shows {current}]')
                    total_issues += 1

                f.write('\n')

                # Check for milestone issues
                issues = []
                if actual_streak >= 7 and not m7:
                    issues.append('Missing 7-day announcement')
                if actual_streak >= 15 and not m15:
                    issues.append('Missing 15-day announcement')
                if actual_streak >= 30 and not m30:
                    issues.append('Missing 30-day announcement')

                if issues:
                    f.write(f'   ISSUES: {" | ".join(issues)}\n')
                    total_issues += len(issues)

            f.write('\n')

        f.write('=' * 80 + '\n')
        f.write(f'SUMMARY: {total_issues} issue(s) found\n')
        f.write('=' * 80 + '\n')

    print(f'Report written to all_streaks_report.txt')
    print(f'Total streaks analyzed: {len(streaks)}')
    print(f'Issues found: {total_issues}')

    conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("STREAK VERIFICATION REPORT")
    print("=" * 60)
    print()

    verify_streaks()

    print()
    print("=" * 60)
    print("Done! Check all_streaks_report.txt for details")
    print("=" * 60)
