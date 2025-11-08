# Telegram Habit Tracker & Rewards Bot

A Telegram bot that helps friends track daily habits together and reward each other with points earned from completing habits.

## Features

### Group Management
- Create groups for friends to track habits together
- Join existing groups using a Group ID
- View group members and their points

### Habit Tracking
- Add shared daily habits for the entire group (e.g., "Read 20 pages", "Morning exercise")
- Edit and delete habits
- Mark habits as completed each day
- Earn 1 point for each completed habit
- Unmark habits if completed by mistake

### Statistics
- View your habit completion history for the current month
- See which habits you completed on each day
- Track your total points

### Reward Shop
- Create your own reward shop with custom rewards
- Set prices for your rewards (e.g., "Cooking your favourite dish - 30 points")
- Browse other group members' reward shops
- Buy rewards from friends using your points
- Transaction history tracking

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- A Telegram account
- A Telegram Bot Token (from [@BotFather](https://t.me/botfather))

### Installation

1. **Clone or download this project**

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv

   # On Windows
   venv\Scripts\activate

   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create a Telegram Bot**
   - Open Telegram and search for [@BotFather](https://t.me/botfather)
   - Send `/newbot` and follow the instructions
   - Choose a name and username for your bot
   - Copy the bot token you receive

5. **Configure environment variables**
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` and add your bot token:
     ```
     TELEGRAM_BOT_TOKEN=your_bot_token_here
     ```

6. **Run the bot**
   ```bash
   python bot.py
   ```

## Usage Guide

### Getting Started

1. **Start the bot**: Send `/start` to your bot in Telegram

2. **Create or Join a Group**:
   - Click "Create Group" to start a new habit tracking group
   - Or click "Join Group" and enter a Group ID to join an existing group
   - Share the Group ID with friends so they can join

### Managing Habits

1. **View Habits**: Click "My Habits" from the main menu
2. **Add a Habit**:
   - Click "Manage Habits" → "Add Habit"
   - Enter the habit name (e.g., "Read 20 pages")
3. **Edit/Delete Habits**:
   - Go to "Manage Habits"
   - Select "Edit Habit" or "Delete Habit"
   - Choose the habit from the list

### Completing Habits

1. Go to "My Habits"
2. Click on any habit to toggle its completion status for today
3. Completed habits show ✅
4. Uncompleted habits show ⬜
5. You earn 1 point for each completed habit

### Viewing Statistics

1. Click "My Stats" from the main menu
2. See all habits you completed this month
3. View your total points

### Reward Shop

**Creating Your Rewards:**
1. Click "My Rewards" from the main menu
2. Click "Add Reward"
3. Enter in format: `Reward Name | Price`
   - Example: `Cooking your favourite dish | 30`

**Buying Rewards:**
1. Click "Reward Shop" from the main menu
2. Select a group member's shop
3. Browse their rewards
4. Click "Buy" if you have enough points
5. Points are transferred automatically

### Group Information

- Click "Group Info" to see:
  - Group name and ID
  - All members and their points

### Commands

- `/start` - Initialize the bot and see welcome screen
- `/menu` - Show the main menu
- `/cancel` - Cancel current operation

## Database Schema

The bot uses SQLite with the following tables:

- **groups** - Group information
- **users** - User profiles and points
- **habits** - Daily habits (shared per group)
- **habit_completions** - Track which habits users completed on which days
- **rewards** - User-created rewards in their shops
- **transactions** - Purchase history

## How Points Work

- **Earning Points**: Complete a habit = +1 point
- **Spending Points**: Buy rewards from other users' shops
- **Point Transfer**: When you buy a reward, points transfer from you to the seller
- **Undo**: If you unmark a habit completion, you lose the point

## Month Tracking

- Statistics show only the current month's data
- Example: If today is November 8th, you'll see completions from November 1st to November 8th
- Each new month starts fresh for statistics (but your total points carry over)

## Tips

1. **Daily Routine**: Check "My Habits" each day and mark what you've completed
2. **Group Coordination**: Discuss with your group what habits to track together
3. **Fair Pricing**: Set reasonable prices for rewards based on their effort
4. **Stay Motivated**: Check "My Stats" regularly to see your progress

## Troubleshooting

**Bot doesn't respond:**
- Make sure the bot is running (`python bot.py`)
- Check your bot token in `.env`
- Ensure your bot is not already running elsewhere

**Can't join a group:**
- Verify the Group ID is correct
- Make sure the group exists (someone must create it first)

**Points not updating:**
- Run the point recalculation script: `python fix_points.py`
- Or manually run the SQL script (see Maintenance section below)

## Maintenance

### Recalculating Points

If points become incorrect (e.g., after deleting habits or manual database edits), you can recalculate them:

**Option 1: Python Script (Recommended)**
```bash
python fix_points.py
```

This will show you the old and new point values for each user.

**Option 2: SQL Script**
```bash
sqlite3 bot.db < fix_points.sql
```

This recalculates points based on:
- Habit completions (+1 point each)
- Reward sales (points earned)
- Reward purchases (points spent)

## File Structure

```
telega_bot_rewards/
├── bot.py              # Main bot logic and handlers
├── database.py         # Database operations
├── fix_points.py       # Utility to recalculate points
├── fix_points.sql      # SQL script to recalculate points
├── requirements.txt    # Python dependencies
├── .env               # Your bot token (create this)
├── .env.example       # Example environment file
├── .gitignore         # Git ignore file
├── README.md          # This file
└── bot.db             # SQLite database (created automatically)
```

## Contributing

Feel free to fork this project and add your own features!

## License

This project is open source and available for personal use.
