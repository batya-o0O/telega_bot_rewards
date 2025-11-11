"""
Common handlers - back_to_menu, cancel
"""

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from utils.keyboards import get_main_menu_keyboard
from utils.formatters import format_points_display
from database import Database

db = Database()


async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle back to menu button"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    user_data = db.get_user(user_id)

    if not user_data or not user_data[3]:
        await query.edit_message_text("Please use /start to set up your account first.")
        return ConversationHandler.END

    user_points = db.get_user_points(user_id)
    total_points = sum(user_points.values())

    text = f"Main Menu\n\n"
    text += f"Your Points ({total_points} total):\n"
    text += format_points_display(user_points)

    await query.edit_message_text(
        text,
        reply_markup=get_main_menu_keyboard()
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the current operation"""
    await update.message.reply_text(
        "Operation cancelled. Use /menu to return to the main menu.",
        reply_markup=get_main_menu_keyboard()
    )
    return ConversationHandler.END
