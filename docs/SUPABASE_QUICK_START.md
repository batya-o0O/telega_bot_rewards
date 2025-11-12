# Supabase Quick Start Guide

Quick reference for setting up PostgreSQL with Supabase for your Telegram bot.

## Why Supabase?

- **Free tier**: 500MB database, unlimited API requests
- **Automatic backups**: Daily backups included
- **Accessible anywhere**: No file system dependencies
- **Better reliability**: Production-grade PostgreSQL
- **Perfect for PythonAnywhere**: Solves data persistence issues

## 5-Minute Setup

### 1. Create Supabase Account

Go to [supabase.com](https://supabase.com) → Sign up with GitHub

### 2. Create New Project

- Click "New Project"
- Name: `telegram-rewards-bot`
- Generate strong database password (save it!)
- Choose region closest to your server
- Wait ~2 minutes for setup

### 3. Get Connection String

1. Go to **Settings** → **Database**
2. Find **Connection string** section
3. Select **URI** format
4. Copy the string:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxx.supabase.co:5432/postgres
   ```
5. Replace `[YOUR-PASSWORD]` with your actual password

### 4. Update Your Project

**Add to `.env`:**
```bash
DATABASE_URL=postgresql://postgres:your_password@db.xxx.supabase.co:5432/postgres
TELEGRAM_BOT_TOKEN=your_bot_token
```

**Update bot.py:**
```python
# Change this:
from database import Database

# To this:
from database_postgres import Database

# And change initialization:
db = Database()  # Uses DATABASE_URL from environment
```

**Install dependency:**
```bash
pip install psycopg2-binary
```

### 5. Migrate Existing Data (Optional)

If you have data in `bot.db`:

```bash
python scripts/migrate_sqlite_to_postgres.py
```

This copies all users, habits, rewards, and purchases to PostgreSQL.

## Using with Different Hosts

### PythonAnywhere
```bash
# In .env file
DATABASE_URL=postgresql://postgres:password@db.xxx.supabase.co:5432/postgres
TELEGRAM_BOT_TOKEN=your_token

# Update bot.py to use database_postgres
```

### Railway
Add environment variable in dashboard:
- Key: `DATABASE_URL`
- Value: Your Supabase connection string

### VPS/Docker
Same as local - just add `DATABASE_URL` to `.env`

## Viewing Your Data

### Supabase Dashboard

After setup, access Supabase dashboard to:

1. **Table Editor**: Browse all tables
   - View users, habits, rewards, completions
   - Edit data directly if needed
   - Filter and search

2. **SQL Editor**: Run queries
   ```sql
   -- See all users
   SELECT * FROM users;

   -- Check habit completions today
   SELECT * FROM habit_completions
   WHERE DATE(completed_at) = CURRENT_DATE;

   -- View leaderboard
   SELECT u.first_name, COUNT(hc.id) as completions
   FROM users u
   JOIN habit_completions hc ON u.telegram_id = hc.user_id
   GROUP BY u.telegram_id
   ORDER BY completions DESC;
   ```

3. **Database Settings**:
   - View connection info
   - Configure backups
   - Monitor performance

4. **Logs**: Real-time query logs

## Useful SQL Queries

### Check Database Status
```sql
-- Count records in each table
SELECT 'users' as table_name, COUNT(*) FROM users
UNION ALL
SELECT 'habits', COUNT(*) FROM habits
UNION ALL
SELECT 'habit_completions', COUNT(*) FROM habit_completions
UNION ALL
SELECT 'rewards', COUNT(*) FROM rewards
UNION ALL
SELECT 'townmall_items', COUNT(*) FROM townmall_items;
```

### View Recent Activity
```sql
-- Last 10 habit completions
SELECT u.first_name, h.name as habit, hc.completed_at
FROM habit_completions hc
JOIN users u ON hc.user_id = u.telegram_id
JOIN habits h ON hc.habit_id = h.id
ORDER BY hc.completed_at DESC
LIMIT 10;
```

### User Points Summary
```sql
-- See all users with their points
SELECT
    first_name,
    points_physical,
    points_arts,
    points_food_related,
    points_educational,
    points_other,
    coins
FROM users
ORDER BY
    (points_physical + points_arts + points_food_related +
     points_educational + points_other) DESC;
```

## Backups

Supabase free tier includes:
- **Daily automatic backups** (kept for 7 days)
- Point-in-time recovery (paid plans)

To manually backup:
1. Go to Database → Backups
2. Click "Create backup"
3. Or export via SQL:
   ```sql
   -- Backup to CSV
   COPY users TO STDOUT WITH CSV HEADER;
   ```

## Troubleshooting

### Connection Issues

**Error: "connection refused"**
- Check your connection string is correct
- Verify password has no spaces
- Make sure your IP isn't blocked (Supabase allows all by default)

**Error: "SSL required"**
- Add `?sslmode=require` to connection string:
  ```
  postgresql://postgres:password@db.xxx.supabase.co:5432/postgres?sslmode=require
  ```

### Migration Issues

**Error: "DATABASE_URL not set"**
```bash
# Set it before running migration
export DATABASE_URL='postgresql://postgres:password@...'
python scripts/migrate_sqlite_to_postgres.py
```

**Error: "tables already exist"**
- Tables are auto-created on first run
- If migration fails midway, drop tables in Supabase SQL Editor:
  ```sql
  DROP TABLE IF EXISTS
      setgroupchat_confirmations,
      townmall_purchases,
      townmall_items,
      reward_purchases,
      rewards,
      medals,
      habit_completions,
      habits,
      users,
      groups CASCADE;
  ```
- Then run migration again

## Cost

**Free Tier Includes:**
- 500MB database storage
- Unlimited API requests
- Daily backups (7-day retention)
- 2GB bandwidth/month
- Perfect for small to medium bots (hundreds of users)

**When to Upgrade:**
- Database > 500MB
- Need longer backup retention
- Want point-in-time recovery
- Need more bandwidth

## Security Best Practices

1. **Never commit connection strings**
   - Keep `DATABASE_URL` in `.env` only
   - `.env` is already in `.gitignore`

2. **Use strong passwords**
   - Let Supabase generate password
   - Store securely (password manager)

3. **Rotate passwords periodically**
   - Change in Supabase dashboard
   - Update `.env` file

4. **Monitor access logs**
   - Check Supabase logs regularly
   - Watch for suspicious queries

## Next Steps

After setup:
1. Deploy your bot using [HOSTING.md](HOSTING.md)
2. Test all features work with PostgreSQL
3. Set up monitoring in Supabase dashboard
4. Configure automatic backups if on paid plan

## Need Help?

- [Supabase Documentation](https://supabase.com/docs)
- [PostgreSQL Tutorial](https://www.postgresql.org/docs/current/tutorial.html)
- [Full Hosting Guide](HOSTING.md)
