# GitHub Repository Setup Instructions

## Step 1: Create a Private Repository on GitHub

1. Go to [GitHub](https://github.com) and log in
2. Click the **"+"** icon in the top right corner
3. Select **"New repository"**
4. Fill in the details:
   - **Repository name**: `telega_bot_rewards` (or your preferred name)
   - **Description**: "Telegram bot for habit tracking and rewards system"
   - **Privacy**: Select **Private**
   - **DO NOT** initialize with README, .gitignore, or license (we already have these)
5. Click **"Create repository"**

## Step 2: Connect Your Local Repository

After creating the repository, GitHub will show you setup instructions. Use these commands:

### Option 1: Push from Command Line

Replace `YOUR_USERNAME` with your GitHub username:

```bash
git remote add origin https://github.com/YOUR_USERNAME/telega_bot_rewards.git
git branch -M main
git push -u origin main
```

### Option 2: Using SSH (if you have SSH keys set up)

```bash
git remote add origin git@github.com:YOUR_USERNAME/telega_bot_rewards.git
git branch -M main
git push -u origin main
```

## Step 3: Verify Upload

After pushing, refresh your GitHub repository page. You should see all the files:
- bot.py
- database.py
- fix_points.py
- fix_points.sql
- requirements.txt
- README.md
- CHANGELOG.md
- .gitignore
- .env.example

## Important Notes

- The `.env` file (with your bot token) is **NOT** uploaded (it's in .gitignore)
- The `bot.db` database file is **NOT** uploaded (it's in .gitignore)
- The `rewards_bot/` directory is **NOT** uploaded (it's in .gitignore)
- When cloning on another machine, you'll need to:
  1. Copy `.env.example` to `.env`
  2. Add your bot token to `.env`
  3. Run `pip install -r requirements.txt`
  4. Run `python bot.py`

## Future Updates

After making changes to the code:

```bash
git add .
git commit -m "Description of changes"
git push
```

## Troubleshooting

**If you get authentication errors:**
- For HTTPS: GitHub may ask for your username and password
  - Use a [Personal Access Token](https://github.com/settings/tokens) instead of your password
- For SSH: Make sure you've [added your SSH key](https://github.com/settings/keys) to GitHub

**If you get "Permission denied":**
- Make sure you're logged in to the correct GitHub account
- Verify the repository name matches exactly
