# Hosting Guide for Telegram Rewards Bot

This guide covers multiple deployment options for hosting your Telegram bot.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Option 1: VPS Hosting (Recommended)](#option-1-vps-hosting-recommended)
3. [Option 2: Railway (Free Tier Available)](#option-2-railway-free-tier-available)
4. [Option 3: Docker Deployment](#option-3-docker-deployment)
5. [Option 4: PythonAnywhere](#option-4-pythonanywhere)
6. [Post-Deployment Setup](#post-deployment-setup)
7. [Monitoring and Maintenance](#monitoring-and-maintenance)

---

## Prerequisites

Before deploying, ensure you have:

- Your bot token from [@BotFather](https://t.me/BotFather)
- Git installed locally
- Your bot code tested locally
- Database backups (if migrating)

---

## Option 1: VPS Hosting (Recommended)

**Best for:** Long-term production use, full control
**Cost:** $4-10/month (DigitalOcean, Linode, Vultr, Hetzner)
**Pros:** Full control, persistent storage, no timeouts
**Cons:** Requires server management knowledge

### Step 1: Get a VPS

Popular providers:
- **DigitalOcean** - $4/month for basic droplet
- **Hetzner** - ~€4/month (very affordable)
- **Linode** - $5/month
- **Vultr** - $3.50/month

Choose **Ubuntu 22.04 LTS** or **Ubuntu 24.04 LTS**

### Step 2: Initial Server Setup

SSH into your server:
```bash
ssh root@your_server_ip
```

Update system:
```bash
apt update && apt upgrade -y
```

Install Python 3.11+ and essentials:
```bash
apt install python3 python3-pip python3-venv git -y
```

Create a non-root user:
```bash
adduser botuser
usermod -aG sudo botuser
su - botuser
```

### Step 3: Deploy Your Bot

Clone your repository:
```bash
cd ~
git clone https://github.com/yourusername/telega_bot_rewards.git
cd telega_bot_rewards
```

Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Create `.env` file:
```bash
nano .env
```

Add your configuration:
```
TELEGRAM_BOT_TOKEN=your_token_here
```

Test the bot:
```bash
python bot.py
```

### Step 4: Keep Bot Running with systemd

Create a service file:
```bash
sudo nano /etc/systemd/system/telegram-bot.service
```

Add this configuration:
```ini
[Unit]
Description=Telegram Rewards Bot
After=network.target

[Service]
Type=simple
User=botuser
WorkingDirectory=/home/botuser/telega_bot_rewards
Environment="PATH=/home/botuser/telega_bot_rewards/venv/bin"
ExecStart=/home/botuser/telega_bot_rewards/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
```

Check status:
```bash
sudo systemctl status telegram-bot
```

View logs:
```bash
sudo journalctl -u telegram-bot -f
```

### Step 5: Automatic Backups

Create backup script:
```bash
nano ~/backup_bot.sh
```

Add:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
cp /home/botuser/telega_bot_rewards/bot.db /home/botuser/backups/bot_backup_$DATE.db
# Keep only last 7 days of backups
find /home/botuser/backups -name "bot_backup_*.db" -mtime +7 -delete
```

Make executable and add to cron:
```bash
chmod +x ~/backup_bot.sh
crontab -e
```

Add this line (backup daily at 3 AM):
```
0 3 * * * /home/botuser/backup_bot.sh
```

---

## Option 2: Railway (Free Tier Available)

**Best for:** Quick deployment, beginners
**Cost:** Free tier available, then ~$5/month
**Pros:** Easy setup, automatic deployments
**Cons:** Free tier has monthly hours limit

### Step 1: Prepare Your Repository

Create `railway.json` in project root:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python bot.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

Create `Procfile`:
```
worker: python bot.py
```

Commit and push to GitHub:
```bash
git add railway.json Procfile
git commit -m "Add Railway deployment config"
git push
```

### Step 2: Deploy on Railway

1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Add environment variable:
   - Key: `TELEGRAM_BOT_TOKEN`
   - Value: Your bot token
6. Railway will automatically deploy

### Step 3: Configure Volume for Database Persistence

1. In Railway dashboard, go to your project
2. Click "Variables" tab
3. Under "Volumes", click "Add Volume"
4. Mount path: `/app`
5. This ensures your `bot.db` persists across restarts

### Step 4: Monitor Deployment

Railway provides:
- Deployment logs
- Resource usage metrics
- Automatic restarts on failure

---

## Option 3: Docker Deployment

**Best for:** Consistent environments, scaling
**Pros:** Portable, reproducible deployments
**Cons:** Requires Docker knowledge

### Step 1: Create Dockerfile

Create `Dockerfile` in project root:
```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create volume mount point for database persistence
VOLUME ["/app/data"]

# Run the bot
CMD ["python", "bot.py"]
```

### Step 2: Create docker-compose.yml

```yaml
version: '3.8'

services:
  telegram-bot:
    build: .
    container_name: telegram-rewards-bot
    restart: unless-stopped
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
    volumes:
      - ./data:/app/data
      - ./bot.db:/app/bot.db
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Step 3: Update database.py for Volume

Modify database path if needed to use `/app/data/bot.db` for persistence.

### Step 4: Deploy with Docker

Build and run:
```bash
docker-compose up -d
```

View logs:
```bash
docker-compose logs -f
```

Stop bot:
```bash
docker-compose down
```

Update and restart:
```bash
git pull
docker-compose down
docker-compose build
docker-compose up -d
```

---

## Option 4: PythonAnywhere

**Best for:** Beginners, Python-focused hosting
**Cost:** Free tier available, $5/month for always-on
**Pros:** Python-friendly, simple setup
**Cons:** Free tier has limitations

### Step 1: Sign Up

1. Go to [pythonanywhere.com](https://www.pythonanywhere.com)
2. Create free account
3. Upgrade to "Hacker" plan ($5/month) for always-on tasks

### Step 2: Upload Code

In PythonAnywhere dashboard:

```bash
# Open Bash console
git clone https://github.com/yourusername/telega_bot_rewards.git
cd telega_bot_rewards
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create `.env` file with your bot token.

### Step 3: Create Always-On Task

1. Go to "Tasks" tab
2. Create new task
3. Command: `/home/yourusername/telega_bot_rewards/venv/bin/python /home/yourusername/telega_bot_rewards/bot.py`
4. Start task

---

## Post-Deployment Setup

### 1. Set Bot Commands

After deployment, set commands for your bot via BotFather:

```
start - Start the bot and show main menu
group - Manage your group
habits - Track your habits
rewards - Manage rewards shop
bazar - View all group rewards
townmall - Visit the Town Mall
points - View and convert points
medals - View your earned medals
report - View monthly statistics
help - Show help information
```

### 2. Database Backups

For VPS hosting, ensure backups run:
```bash
# Check if backup cron is working
crontab -l

# Manually test backup
~/backup_bot.sh
ls -lah ~/backups/
```

### 3. Monitor Bot Health

Create simple health check:
```bash
# Check if bot is running
ps aux | grep bot.py

# Check logs for errors
tail -f bot.log  # if you add logging to file
```

### 4. Set Up Monitoring (Optional)

For production, consider:
- **UptimeRobot** - Free uptime monitoring
- **Sentry** - Error tracking for Python
- **Telegram Bot API getMe** - Health check endpoint

---

## Monitoring and Maintenance

### Regular Maintenance Tasks

1. **Weekly:**
   - Check bot logs for errors
   - Verify database backups exist
   - Monitor disk space usage

2. **Monthly:**
   - Update Python dependencies: `pip install --upgrade -r requirements.txt`
   - Review and clean old backups
   - Check server security updates: `sudo apt update && sudo apt upgrade`

3. **As Needed:**
   - Deploy new features via git pull
   - Run database migrations
   - Restart bot service after updates

### Common Issues and Solutions

**Bot stops responding:**
```bash
# Check if process is running
sudo systemctl status telegram-bot

# Restart service
sudo systemctl restart telegram-bot

# Check logs
sudo journalctl -u telegram-bot -n 50
```

**Database locked errors:**
```bash
# Check for multiple bot instances
ps aux | grep bot.py
# Kill extra processes
kill <PID>
```

**Out of disk space:**
```bash
# Check disk usage
df -h

# Clean old backups
cd ~/backups
rm bot_backup_old*.db

# Clean Python cache
find . -type d -name __pycache__ -exec rm -r {} +
```

### Update Deployment

For VPS:
```bash
cd ~/telega_bot_rewards
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart telegram-bot
```

For Railway:
```bash
git push  # Automatic deployment
```

For Docker:
```bash
docker-compose down
git pull
docker-compose build
docker-compose up -d
```

---

## Security Best Practices

1. **Never commit `.env` file** - Already in .gitignore
2. **Use SSH keys** - Not password authentication
3. **Keep system updated** - Regular security patches
4. **Firewall configuration:**
   ```bash
   sudo ufw allow 22/tcp  # SSH
   sudo ufw enable
   ```
5. **Regular backups** - Automate and test restores
6. **Monitor logs** - Watch for suspicious activity

---

## Cost Comparison

| Option | Free Tier | Paid Cost | Best For |
|--------|-----------|-----------|----------|
| VPS (Hetzner) | No | €4/month | Production, full control |
| Railway | Yes (limited) | ~$5/month | Quick start, auto-deploy |
| Docker (VPS) | No | €4-10/month | Scalability, consistency |
| PythonAnywhere | Yes | $5/month | Beginners, Python focus |

---

## Recommended Approach

**For beginners:** Start with Railway free tier to test
**For production:** Use VPS with systemd (Option 1)
**For teams:** Docker deployment on VPS (Option 3)

---

## Getting Help

If you encounter issues:
1. Check logs first
2. Verify environment variables
3. Test database permissions
4. Review Telegram Bot API status
5. Check server resources (disk, memory)

## Next Steps

After deployment:
1. Test all bot features in production
2. Set up monitoring
3. Configure automatic backups
4. Document your deployment specifics
5. Plan for scaling if needed
