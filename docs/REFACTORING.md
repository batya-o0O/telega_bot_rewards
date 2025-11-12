# Project Structure

This document explains the modular structure of the Telegram Rewards Bot.

## Current Status: Phase 2 Complete ✅✅

The bot has been fully refactored into a clean modular structure!
- **bot.py**: Reduced from 1693 lines to 208 lines (88% reduction)
- **All handlers**: Organized into feature-based modules
- **Clean imports**: Single import statement per feature
- **Fully tested**: Bot starts and runs successfully

## Directory Structure

```
telega_bot_rewards/
├── bot.py                      # Entry point (208 lines) ✅
├── bot_monolithic.py           # Backup of old bot.py (1693 lines)
├── database.py                 # Database layer
├── constants.py                # Conversation states
├── handlers/                   # Handler modules ✅
│   ├── __init__.py            # Exports all handlers
│   ├── common.py              # back_to_menu, cancel
│   ├── start.py               # start, menu commands
│   ├── groups.py              # Group management
│   ├── habits.py              # Habit tracking and calendar
│   ├── rewards.py             # Reward shop and payment
│   ├── points.py              # Point conversion
│   └── reports.py             # Monthly reports
├── utils/                      # Utility modules ✅
│   ├── __init__.py
│   ├── keyboards.py           # Keyboard builders
│   ├── formatters.py          # Text formatting helpers
│   └── announcements.py       # Group announcement utilities
└── migrate_*.py                # Database migration scripts
```

## What's Been Refactored

### ✅ Phase 1: Infrastructure (Completed)
- **constants.py**: All conversation states
- **utils/** modules: Keyboards, formatters, announcements
- **handlers/**: Directory structure created

### ✅ Phase 2: Full Handler Extraction (Completed)
All 51 handler functions extracted and organized by feature:

- **handlers/common.py** (2 handlers): back_to_menu, cancel
- **handlers/start.py** (2 handlers): start, menu
- **handlers/groups.py** (6 handlers): Group creation, joining, info, setgroupchat
- **handlers/habits.py** (15 handlers): Habit CRUD, toggle, stats, calendar views
- **handlers/rewards.py** (14 handlers): Reward shop, buying, payment system
- **handlers/points.py** (4 handlers): Point conversion with 2:1 ratio
- **handlers/reports.py** (2 handlers): Monthly leaderboards

### 📊 Results
- **bot.py**: 1693 lines → 208 lines (88% reduction)
- **Total modular code**: ~1920 lines across organized modules
- **Maintainability**: Dramatically improved
- **Testing**: Fully functional, all features working

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
