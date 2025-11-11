"""
Monthly report handlers for the Telegram bot.

This module handles monthly leaderboards showing:
- Best Shopkeepers (users who earned the most coins)
- Dungeon Masters (users who earned the most points)
"""

from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import Database
from utils import get_main_menu_keyboard

# Initialize database
db = Database()


async def monthly_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show monthly leaderboards for best shopkeeper and dungeon master (callback handler)"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    user_data = db.get_user(user_id)

    if not user_data or not user_data[3]:
        await query.edit_message_text("You need to join a group first!")
        return

    group_id = user_data[3]
    month_name = datetime.now().strftime('%B %Y')

    leaderboard = db.get_monthly_leaderboard(group_id)

    text = f"📊 Monthly Report - {month_name}\n\n"

    # Best Shopkeepers (most coins earned)
    text += "🏆 Best Shopkeepers (Coins Earned):\n"
    if leaderboard['shopkeepers']:
        medals = ['🥇', '🥈', '🥉']
        for i, (user_id, first_name, username, coins) in enumerate(leaderboard['shopkeepers']):
            medal = medals[i] if i < len(medals) else '  '
            name = first_name or username or f"User {user_id}"
            text += f"{medal} {name}: {coins} coins\n"
    else:
        text += "No sales yet this month!\n"

    text += "\n"

    # Best Dungeon Masters (most points earned)
    text += "⚔️ Dungeon Masters (Points Earned):\n"
    if leaderboard['dungeon_masters']:
        medals = ['🥇', '🥈', '🥉']
        for i, (user_id, first_name, username, points) in enumerate(leaderboard['dungeon_masters']):
            medal = medals[i] if i < len(medals) else '  '
            name = first_name or username or f"User {user_id}"
            text += f"{medal} {name}: {points} points\n"
    else:
        text += "No habits completed yet this month!\n"

    keyboard = [
        [InlineKeyboardButton("« Back to Group Info", callback_data="group_info")],
        [InlineKeyboardButton("Back to Menu", callback_data="back_to_menu")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def monthlyreport(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /monthlyreport command - show monthly leaderboards"""
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)

    if not user_data or not user_data[3]:
        await update.message.reply_text("You need to join a group first! Use /start to set up your account.")
        return

    group_id = user_data[3]
    month_name = datetime.now().strftime('%B %Y')

    leaderboard = db.get_monthly_leaderboard(group_id)

    text = f"📊 Monthly Report - {month_name}\n\n"

    # Best Shopkeepers (most coins earned)
    text += "🏆 Best Shopkeepers (Coins Earned):\n"
    if leaderboard['shopkeepers']:
        medals = ['🥇', '🥈', '🥉']
        for i, (user_id, first_name, username, coins) in enumerate(leaderboard['shopkeepers']):
            medal = medals[i] if i < len(medals) else '  '
            name = first_name or username or f"User {user_id}"
            text += f"{medal} {name}: {coins} coins\n"
    else:
        text += "No sales yet this month!\n"

    text += "\n"

    # Best Dungeon Masters (most points earned)
    text += "⚔️ Dungeon Masters (Points Earned):\n"
    if leaderboard['dungeon_masters']:
        medals = ['🥇', '🥈', '🥉']
        for i, (user_id, first_name, username, points) in enumerate(leaderboard['dungeon_masters']):
            medal = medals[i] if i < len(medals) else '  '
            name = first_name or username or f"User {user_id}"
            text += f"{medal} {name}: {points} points\n"
    else:
        text += "No habits completed yet this month!\n"

    await update.message.reply_text(text, reply_markup=get_main_menu_keyboard())
