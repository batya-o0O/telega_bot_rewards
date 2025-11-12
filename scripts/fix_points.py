#!/usr/bin/env python3
"""
Utility script to recalculate all user points from scratch
Run this if points become incorrect due to bugs or manual database edits
"""

from database import Database

def main():
    db = Database()

    print("Recalculating all user points...")
    print("-" * 50)

    results = db.recalculate_all_points()

    if not results:
        print("No users found in database.")
        return

    print(f"Updated {len(results)} users:\n")

    for user_id, (old_points, new_points) in results.items():
        change = new_points - old_points
        change_str = f"+{change}" if change >= 0 else str(change)
        print(f"User {user_id}: {old_points} -> {new_points} ({change_str})")

    print("-" * 50)
    print("Points recalculation complete!")

if __name__ == '__main__':
    main()
