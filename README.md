# Telegram Rewards Bot

A feature-rich Telegram bot for tracking habits, managing rewards, and earning points in a group setting.

## Project Structure

```
telega_bot_rewards/
├── bot.py                 # Main bot entry point
├── database.py            # Database operations and schema
├── constants.py           # Constants and conversation states
├── requirements.txt       # Python dependencies
├── bot.db                 # SQLite database (production)
│
├── handlers/              # Bot command and callback handlers
│   ├── common.py         # Common handlers (back, cancel)
│   ├── start.py          # Start and menu commands
│   ├── groups.py         # Group management
│   ├── habits.py         # Habit tracking
│   ├── rewards.py        # Reward shop
│   ├── points.py         # Point conversion
│   ├── reports.py        # Monthly reports
│   └── townmall.py       # Town Mall (coin shop)
│
├── utils/                 # Utility functions
│   ├── announcements.py  # Group announcements
│   ├── formatters.py     # Text formatting helpers
│   └── keyboards.py      # Keyboard layouts
│
├── images/                # Image assets
│   └── townmall/         # Town Mall item images
│
├── migrations/            # Database migration scripts
│   ├── migrate_to_v2.py
│   ├── migrate_to_v3.py
│   ├── migrate_add_medals.py
│   └── ...
│
├── scripts/               # Helper and utility scripts
│   ├── send_announcement.py      # Broadcast to all groups
│   ├── send_bot_intro.py         # Send bot introduction
│   ├── reset_for_production.py  # Production reset
│   ├── give_test_points.py      # Testing utility
│   └── fix_points.py             # Point correction script
│
├── backups/               # Database and code backups
│   ├── bot_backup_*.db
│   ├── bot_monolithic.py
│   └── database_v1_backup.py
│
└── docs/                  # Documentation
    ├── ANNOUNCEMENTS.md           # Announcement system docs
    ├── CHANGELOG.md               # Change history
    ├── COMPLETED_FEATURES.md      # Feature list
    ├── IMPLEMENTATION_STATUS.md   # Implementation tracking
    ├── REFACTORING.md            # Refactoring notes
    ├── GITHUB_SETUP.md           # GitHub setup guide
    ├── UPDATE_NOTES_V2.md        # V2 update notes
    └── PRODUCTION_RESET_SUMMARY.md
```

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your TELEGRAM_BOT_TOKEN
   ```

3. **Run the bot:**
   ```bash
   python bot.py
   ```

## Features

- **Habit Tracking**: Track daily habits with different point types
- **Medal System**: Earn medals for 30-day streaks
- **Reward Shop**: Create and buy rewards using points
- **Bazar**: View all rewards from all users sorted by price
- **Town Mall**: Community shop using coins (not points)
- **Point Conversion**: Convert between different point types
- **Monthly Reports**: Leaderboards and statistics
- **Group Announcements**: Automated announcements for achievements

## Database Migrations

Run migrations in order:
```bash
python migrations/migrate_to_v2.py
python migrations/migrate_to_v3.py
python migrations/migrate_to_v4.py
python migrations/migrate_add_medals.py
python migrations/migrate_add_townmall.py
python migrations/migrate_add_sponsor_to_townmall.py
python migrations/migrate_add_setgroupchat_confirmations.py
python migrations/migrate_remove_old_points.py
```

## Utility Scripts

- **Send announcements**: `python scripts/send_announcement.py`
- **Send bot intro**: `python scripts/send_bot_intro.py`
- **Reset for production**: `python scripts/reset_for_production.py`
- **Give test points**: `python scripts/give_test_points.py`

## Deployment

Ready to host your bot? See [docs/HOSTING.md](docs/HOSTING.md) for comprehensive deployment guides covering:

- **VPS Hosting** (DigitalOcean, Hetzner, Linode) - Recommended for production
- **Railway** - Quick deployment with free tier
- **Docker** - Containerized deployment
- **PythonAnywhere** - Beginner-friendly hosting

Quick deploy with Docker:
```bash
cp .env.example .env
# Edit .env with your bot token
docker-compose up -d
```

## Documentation

See the `docs/` folder for detailed documentation:
- [HOSTING.md](docs/HOSTING.md) - Complete hosting and deployment guide
- Feature implementation status
- Change logs
- Setup guides
- System documentation

## License

Private project - All rights reserved
