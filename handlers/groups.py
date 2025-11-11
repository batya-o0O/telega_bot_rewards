"""
Group management handlers for the Telegram Rewards Bot

This module contains all handlers related to group creation, joining,
and management functionality.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from database import Database
from constants import CREATING_GROUP, JOINING_GROUP
from utils.keyboards import get_main_menu_keyboard
from utils.formatters import format_points_display

# Initialize database
db = Database()


async def create_group_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start group creation"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Please enter a name for your group:")
    return CREATING_GROUP


async def create_group_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Finish group creation"""
    group_name = update.message.text
    user_id = update.effective_user.id

    group_id = db.create_group(group_name)
    db.join_group(user_id, group_id)

    await update.message.reply_text(
        f"Group '{group_name}' created successfully!\n"
        f"Group ID: {group_id}\n\n"
        "Share this ID with friends so they can join!",
        reply_markup=get_main_menu_keyboard()
    )
    return ConversationHandler.END


async def join_group_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start joining a group"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Please enter the Group ID you want to join:")
    return JOINING_GROUP


async def join_group_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Finish joining a group"""
    try:
        group_id = int(update.message.text)
        user_id = update.effective_user.id

        group = db.get_group(group_id)
        if not group:
            await update.message.reply_text("Group not found. Please check the ID and try again.")
            return JOINING_GROUP

        db.join_group(user_id, group_id)
        await update.message.reply_text(
            f"Successfully joined group '{group[1]}'!",
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Invalid Group ID. Please enter a number.")
        return JOINING_GROUP


async def group_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show group information and members"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    user_data = db.get_user(user_id)

    if not user_data or not user_data[3]:
        await query.edit_message_text("You need to join a group first!")
        return

    group_id = user_data[3]
    group = db.get_group(group_id)
    members = db.get_group_members(group_id)

    text = f"Group: {group[1]}\n"
    text += f"Group ID: {group_id}\n\n"
    text += "Members:\n"

    for member in members:
        name = member[2] or member[1] or f"User {member[0]}"
        # Get typed points (columns 5-9: physical, arts, food_related, educational, other)
        points_physical = member[5] if len(member) > 5 else 0
        points_arts = member[6] if len(member) > 6 else 0
        points_food = member[7] if len(member) > 7 else 0
        points_edu = member[8] if len(member) > 8 else 0
        points_other = member[9] if len(member) > 9 else 0
        total_points = points_physical + points_arts + points_food + points_edu + points_other
        # Get coins (column 10)
        coins = member[10] if len(member) > 10 else 0

        text += f"\n👤 {name}:\n"
        text += f"   Total: {total_points} pts | {coins} coins\n"
        if total_points > 0:  # Show breakdown only if user has points
            text += f"   💪 Physical: {points_physical} | 🎨 Arts: {points_arts}\n"
            text += f"   🍽 Food: {points_food} | 📚 Educational: {points_edu}\n"
            text += f"   ⭐ Other: {points_other}\n"

    keyboard = [
        [InlineKeyboardButton("📊 Monthly Report", callback_data="monthly_report")],
        [InlineKeyboardButton("Back to Menu", callback_data="back_to_menu")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def setgroupchat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Link the current Telegram group chat to a reward group
    Usage: /setgroupchat (use this command in the group chat you want to link)
    """
    # Check if this is a group chat
    if update.effective_chat.type not in ['group', 'supergroup']:
        await update.message.reply_text(
            "This command only works in group chats!\n\n"
            "Add me to a Telegram group chat and use /setgroupchat there."
        )
        return

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Get user's reward group
    user_data = db.get_user(user_id)
    if not user_data or not user_data[3]:
        await update.message.reply_text(
            "You need to join a reward group first!\n\n"
            "Use /start in a private chat with me to join or create a group."
        )
        return

    group_id = user_data[3]
    group_data = db.get_group(group_id)

    # Link the chat
    db.set_group_chat(group_id, chat_id)

    await update.message.reply_text(
        f"Success!\n\n"
        f"This Telegram group chat is now linked to reward group '{group_data[1]}'.\n\n"
        f"I'll post announcements here when:\n"
        f"• Someone adds a new reward to their shop\n"
        f"• Someone buys a reward\n"
        f"• Someone reaches a streak milestone (7, 15, 30 days)"
    )
