"""
Start and menu command handlers
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.keyboards import get_main_menu_keyboard
from utils.formatters import format_points_display
from database import Database

db = Database()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    db.create_or_update_user(user.id, user.username, user.first_name)

    user_data = db.get_user(user.id)

    if user_data and user_data[3]:  # Has group_id
        user_points = db.get_user_points(user.id)
        total_points = sum(user_points.values())

        text = f"Welcome back, {user.first_name}!\n\n"
        text += f"Your Points ({total_points} total):\n"
        text += format_points_display(user_points)

        await update.message.reply_text(
            text,
            reply_markup=get_main_menu_keyboard()
        )
    else:
        keyboard = [
            [InlineKeyboardButton("Create Group", callback_data="create_group")],
            [InlineKeyboardButton("Join Group", callback_data="join_group")],
        ]
        await update.message.reply_text(
            f"Welcome, {user.first_name}!\n\n"
            "You're not part of any group yet. Would you like to create or join one?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /menu command - show main menu"""
    user = update.effective_user
    user_data = db.get_user(user.id)

    if not user_data or not user_data[3]:
        await update.message.reply_text("Please use /start to set up your account first.")
        return

    user_points = db.get_user_points(user.id)
    total_points = sum(user_points.values())

    text = f"Main Menu\n\n"
    text += f"Your Points ({total_points} total):\n"
    text += format_points_display(user_points)

    await update.message.reply_text(
        text,
        reply_markup=get_main_menu_keyboard()
    )
