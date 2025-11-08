# Changelog

## 2025-11-08 - Bug Fixes and Enhancements

### Fixed
- **Stats display showing timestamps instead of habit names**
  - Fixed database query to return correct columns
  - Stats now properly show habit names: `✅ Read 30 pages` instead of `✅ 2025-11-08 08:29:52`

- **Points not updated when deleting habits**
  - `delete_habit()` now recalculates points for all affected users
  - Automatically subtracts points for deleted habit completions

### Added
- **Point recalculation utilities**
  - `fix_points.py` - Python script to recalculate all user points
  - `fix_points.sql` - SQL script for manual point recalculation
  - `recalculate_all_points()` method in Database class

### Enhanced
- **Calendar views with day numbers**
  - Overall calendar shows colored squares with day numbers (e.g., 🟢 8, 🟡15, ⬜22)
  - Better alignment between weekday headers and calendar days
  - Per-habit calendars show completion rate percentage

- **Per-habit statistics**
  - Individual calendar for each habit accessible from Stats view
  - Shows completion rate for each habit
  - Buttons for each habit in the Stats menu

### Database Schema Updates
- Modified `get_user_completions_for_month()` to return explicit columns:
  - Returns: (id, user_id, habit_id, completion_date, habit_name)
  - Previously returned `hc.*` which caused indexing issues

### Documentation
- Updated README.md with maintenance section
- Added troubleshooting for point recalculation
- Documented new utility scripts
