# Project Structure

This document explains the modular structure of the Telegram Rewards Bot.

## Current Status: Phase 1 Complete ✅

The bot has been partially refactored to use a modular structure. Helper functions and utilities have been extracted into separate modules, while handlers remain in `bot.py` for now.

## Directory Structure

```
telega_bot_rewards/
├── bot.py                      # Main bot file (handlers + application setup)
├── database.py                 # Database layer
├── constants.py                # Conversation states and constants
├── handlers/                   # Handler modules (for future organization)
│   ├── __init__.py
│   ├── common.py              # back_to_menu, cancel (ready for use)
│   └── start.py               # start, menu commands (ready for use)
├── utils/                      # Utility modules ✅
│   ├── __init__.py
│   ├── keyboards.py           # Keyboard builders
│   ├── formatters.py          # Text formatting helpers
│   └── announcements.py       # Group announcement utilities
└── migrate_*.py                # Database migration scripts
```

## What's Been Refactored

### ✅ Completed (Phase 1)
- **constants.py**: All conversation states extracted
- **utils/keyboards.py**: Keyboard builders
  - `get_main_menu_keyboard()`
  - `get_habit_type_keyboard()`
  - `get_reward_point_type_keyboard()`
- **utils/formatters.py**: Text formatting
  - `format_points_display()`
- **utils/announcements.py**: Group announcements
  - `send_group_announcement()`
- **handlers/common.py**: Common handlers (ready for use)
- **handlers/start.py**: Start handlers (ready for use)

### 🚧 Remaining in bot.py
- All handler functions (51 total):
  - Group management (create, join, group_info)
  - Habit management (CRUD, toggle, calendar)
  - Reward shop (buy, sell, payment)
  - Point conversion
  - Reports and leaderboards

## Benefits Achieved

1. **Cleaner Imports**: Single import statement for all utils
2. **Reusability**: Utils can be imported by future handler modules
3. **Testing**: Utils can be tested independently
4. **Maintainability**: Clear separation of concerns
5. **Reduced Duplication**: No duplicate helper functions

## Usage in Code

### Before
```python
def get_main_menu_keyboard():
    keyboard = [...]
    return InlineKeyboardMarkup(keyboard)

# Used in multiple places
keyboard = get_main_menu_keyboard()
```

### After
```python
from utils import get_main_menu_keyboard

# Used in multiple places
keyboard = get_main_menu_keyboard()
```

## Next Steps (Future Phases)

When ready to continue refactoring:

1. **Phase 2**: Extract handler modules
   - Move group handlers to `handlers/groups.py`
   - Move habit handlers to `handlers/habits.py`
   - Move reward handlers to `handlers/rewards.py`
   - Move point handlers to `handlers/points.py`
   - Move report handlers to `handlers/reports.py`

2. **Phase 3**: Modernize bot.py
   - Convert to minimal entry point
   - Import all handlers from modules
   - Register handlers using imports

## Development Guidelines

- **Adding new utils**: Put them in the appropriate `utils/*.py` file
- **Adding new handlers**: Either add to `bot.py` or create a new handler module
- **Constants**: Add to `constants.py` instead of inline definitions
- **Testing**: Test utils independently before using in handlers

## Migration Notes

- All existing functionality preserved
- Bot behavior unchanged
- Backward compatible with existing code
- Database schema unchanged
