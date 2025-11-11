# Announcement Script Guide

This guide explains how to send broadcast messages to all group chats using `send_announcement.py`.

## Overview

The announcement script allows you to send messages from the bot to all groups that have linked their Telegram chats (via `/setgroupchat`).

**Use cases:**
- Patch updates and bug fixes
- New feature announcements
- Maintenance notices
- General announcements

## Usage

### Basic Usage

```bash
python send_announcement.py
```

The script will guide you through an interactive process.

### Step-by-Step Process

1. **Choose announcement type:**
   ```
   1. Patch Update / Bug Fix
   2. New Feature
   3. Maintenance Notice
   4. General Announcement
   5. Custom Message
   ```

2. **Enter your message:**
   - Type your announcement
   - Press Enter twice when done

3. **Preview:**
   - See which groups will receive the message
   - Review the formatted message

4. **Confirm:**
   - Type `yes` to send
   - Type `no` to cancel

## Message Templates

### 1. Patch Update
```
🔧 Patch Update

[Your message here]

Bot has been updated. Restart /menu if needed.
```

### 2. New Feature
```
✨ New Feature

[Your message here]

Try it out: /menu
```

### 3. Maintenance Notice
```
⚠️ Maintenance Notice

[Your message here]

Thank you for your patience.
```

### 4. General Announcement
```
📢 Announcement

[Your message here]
```

### 5. Custom Message
Your message exactly as typed (no template).

## Markdown Formatting

You can use Markdown to format your messages:

| Format | Syntax | Example |
|--------|--------|---------|
| Bold | `*text*` | `*important*` → **important** |
| Italic | `_text_` | `_note_` → _note_ |
| Code | `` `text` `` | `` `code` `` → `code` |
| Link | `[text](url)` | `[Docs](https://...)` |

## Example Sessions

### Example 1: Bug Fix Announcement

```
Choose announcement type: 1

Enter your announcement message:
Fixed error when navigating Town Mall with images.
Now you can smoothly browse between items and go back to the list!

Preview shows: 3 groups will receive message

Proceed with sending? yes

✅ Sent to: Family Group
✅ Sent to: Friends
✅ Sent to: Test Group

Summary: 3 successful, 0 failed
```

### Example 2: New Feature Announcement

```
Choose announcement type: 2

Enter your announcement message:
🏪 *Town Mall is now open!*

Buy exclusive items with your coins:
• Гигрометр - 20 coins
• Мягкая игрушка - 40 coins
• Настольная игра - 100 coins
• And more!

Check it out: /menu → 🏪 Town Mall

Preview shows: 3 groups will receive message

Proceed with sending? yes

✅ Successfully sent to all groups!
```

### Example 3: Medal System Announcement

```
Choose announcement type: 2

Enter your announcement message:
🏅 *New Medal System!*

Earn medals for 30-day habit streaks:
• Medaled habits give 0.5 coins per completion
• 3+ medals = better conversion rate (1.5:1)
• Group achievements unlock 10 coins for everyone!

Medal emojis now show next to your name in leaderboards!

Proceed with sending? yes

✅ Successfully sent to all groups!
```

## Safety Features

1. **Preview Mode:** Always shows groups and message before sending
2. **Confirmation:** Requires explicit "yes" to proceed
3. **Rate Limiting:** 0.5 second delay between messages to avoid Telegram limits
4. **Error Handling:** Catches and reports failed deliveries
5. **Dry Run:** Preview mode doesn't send any messages

## Troubleshooting

### No groups found
```
📭 No groups with linked Telegram chats found.
```
**Solution:** Groups must use `/setgroupchat` command in their Telegram chat first.

### Permission denied
```
❌ Failed to send to [Group]: Forbidden: bot was blocked by the user
```
**Solution:** Bot was removed from the group. This is normal - the script continues with other groups.

### Bot token missing
```
❌ Error: TELEGRAM_BOT_TOKEN not found in .env file
```
**Solution:** Ensure `.env` file exists with `TELEGRAM_BOT_TOKEN=your_token_here`

## Database Check

To see which groups have linked chats:

```bash
sqlite3 bot.db "SELECT name, telegram_chat_id FROM groups WHERE telegram_chat_id IS NOT NULL;"
```

## Best Practices

1. **Test first:** Send to a test group before broadcasting
2. **Keep it short:** Users prefer concise announcements
3. **Use emojis:** Makes messages more engaging
4. **Timing matters:** Send during active hours
5. **Don't spam:** Only send important updates

## Advanced: Direct Database Query

If you need to send to specific groups only, modify the script or use:

```python
# In send_announcement.py, modify get_all_group_chats():
cursor.execute('''
    SELECT g.id, g.name, g.telegram_chat_id
    FROM groups g
    WHERE g.telegram_chat_id IS NOT NULL
    AND g.id IN (1, 2, 3)  -- Specific group IDs
''')
```

## Related Commands

- `/setgroupchat` - Link Telegram chat to reward group (run in group chat)
- `/menu` - Main bot menu
- `/start` - Start the bot

## Script Location

```
d:\telega_bot_rewards\send_announcement.py
```

## Quick Reference

```bash
# Send announcement
python send_announcement.py

# Test bot token
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('OK' if os.getenv('TELEGRAM_BOT_TOKEN') else 'Missing')"

# Check linked groups
sqlite3 bot.db "SELECT COUNT(*) FROM groups WHERE telegram_chat_id IS NOT NULL;"
```
