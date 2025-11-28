"""
Group management handlers for the Telegram Rewards Bot

This module contains all handlers related to group creation, joining,
and management functionality.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from datetime import datetime

from database import Database, POINT_TYPES
from constants import CREATING_GROUP, JOINING_GROUP
from utils.keyboards import get_main_menu_keyboard
from utils.formatters import format_points_display, format_user_name_with_medals

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
        member_id = member[0]
        name = member[2] or member[1] or f"User {member_id}"
        # Add medal emojis to name
        name_with_medals = format_user_name_with_medals(member_id, name)
        # Get typed points (columns 5-9: physical, arts, food_related, educational, other)
        points_physical = member[5] if len(member) > 5 else 0
        points_arts = member[6] if len(member) > 6 else 0
        points_food = member[7] if len(member) > 7 else 0
        points_edu = member[8] if len(member) > 8 else 0
        points_other = member[9] if len(member) > 9 else 0
        total_points = points_physical + points_arts + points_food + points_edu + points_other
        # Get coins (column 10)
        coins = member[10] if len(member) > 10 else 0

        text += f"\n👤 {name_with_medals}:\n"
        text += f"   Total: {total_points} pts | {coins} coins\n"
        if total_points > 0:  # Show breakdown only if user has points
            text += f"   💪 Physical: {points_physical} | 🎨 Arts: {points_arts}\n"
            text += f"   🍽 Food: {points_food} | 📚 Educational: {points_edu}\n"
            text += f"   ⭐ Other: {points_other}\n"

    # Add buttons to view each member's stats
    keyboard = []

    # Add "View Stats" buttons for each member
    stats_buttons = []
    for member in members:
        member_id = member[0]
        name = member[2] or member[1] or f"User {member_id}"
        # Limit button text to reasonable length
        button_text = f"📊 {name[:15]}"
        stats_buttons.append(InlineKeyboardButton(button_text, callback_data=f"view_user_stats_{member_id}"))

        # Add 2 buttons per row for better layout
        if len(stats_buttons) == 2:
            keyboard.append(stats_buttons)
            stats_buttons = []

    # Add remaining buttons
    if stats_buttons:
        keyboard.append(stats_buttons)

    # Add other navigation buttons
    keyboard.append([InlineKeyboardButton("📅 Today's Stats", callback_data="todays_stats")])
    keyboard.append([InlineKeyboardButton("📊 Monthly Report", callback_data="monthly_report")])
    keyboard.append([InlineKeyboardButton("Back to Menu", callback_data="back_to_menu")])

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def todays_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show today's habit completions for all group members"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    user_data = db.get_user(user_id)

    if not user_data or not user_data[3]:
        await query.edit_message_text("You need to join a group first!")
        return

    group_id = user_data[3]
    group = db.get_group(group_id)
    completions = db.get_todays_group_completions(group_id)

    today_str = datetime.now().strftime('%B %d, %Y')
    text = f"📅 Today's Stats - {today_str}\n"
    text += f"Group: {group[1]}\n"
    text += "=" * 30 + "\n\n"

    if not completions:
        text += "No habits completed today yet.\n\n"
        text += "Be the first to log a habit! 💪"
    else:
        total_completions = 0
        habit_counts = {}  # Track how many times each habit was completed

        for user_data in completions:
            name = user_data['first_name'] or user_data['username'] or f"User {user_data['telegram_id']}"
            habits = user_data['habits']
            total_completions += len(habits)

            # Add medal decoration to name
            name_with_medals = format_user_name_with_medals(user_data['telegram_id'], name)

            text += f"👤 {name_with_medals}\n"

            # Group habits by type for cleaner display
            habits_by_type = {}
            for habit in habits:
                point_type = habit['point_type']
                habit_name = habit['name']
                if point_type not in habits_by_type:
                    habits_by_type[point_type] = []
                habits_by_type[point_type].append(habit_name)

                # Count habit completions for summary
                if habit_name not in habit_counts:
                    habit_counts[habit_name] = {'count': 0, 'type': point_type}
                habit_counts[habit_name]['count'] += 1

            # Display habits grouped by type
            for point_type, habit_names in habits_by_type.items():
                emoji = POINT_TYPES.get(point_type, '⭐')
                for habit_name in habit_names:
                    text += f"   {emoji} {habit_name}\n"

            text += "\n"

        # Show habit completion summary
        text += "📊 Habit Summary:\n"
        sorted_habits = sorted(habit_counts.items(), key=lambda x: x[1]['count'], reverse=True)
        for habit_name, data in sorted_habits:
            emoji = POINT_TYPES.get(data['type'], '⭐')
            text += f"   {emoji} {habit_name}: {data['count']}x\n"

        text += f"\n🎯 Group Total: {total_completions} completions today!"

    keyboard = [
        [InlineKeyboardButton("🔄 Refresh", callback_data="todays_stats")],
        [InlineKeyboardButton("👥 Group Info", callback_data="group_info")],
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
    current_chat_name = update.effective_chat.title or "this group"

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

    # Check if there's already a linked chat
    existing_chat_id = db.get_group_chat_id(group_id)

    # Check if there's a pending confirmation
    pending_confirmation = db.get_setgroupchat_confirmation(user_id, group_id)

    if existing_chat_id and existing_chat_id != chat_id and not pending_confirmation:
        # There's a different chat already linked - show warning
        await update.message.reply_text(
            f"⚠️ Warning!\n\n"
            f"Reward group '{group_data[1]}' is already linked to another Telegram chat.\n\n"
            f"If you link it to '{current_chat_name}', the previous chat will no longer receive announcements.\n\n"
            f"To confirm linking to this chat, run the command again: /setgroupchat\n\n"
            f"(This is a safety check to prevent accidental relinking)"
        )
        # Store confirmation state in database
        db.set_setgroupchat_confirmation(user_id, group_id, chat_id)
        return

    # Check if user is confirming a relink
    if pending_confirmation and pending_confirmation == chat_id:
        # User confirmed, proceed with relinking
        db.set_group_chat(group_id, chat_id)
        db.clear_setgroupchat_confirmation(user_id, group_id)

        await update.message.reply_text(
            f"✅ Success! Chat relinked.\n\n"
            f"'{current_chat_name}' is now linked to reward group '{group_data[1]}'.\n\n"
            f"I'll post announcements here when:\n"
            f"• Someone adds a new reward to their shop\n"
            f"• Someone buys a reward\n"
            f"• Someone reaches a streak milestone (7, 15, 30 days)"
        )
        return

    # No existing link or same chat - proceed normally
    db.set_group_chat(group_id, chat_id)

    await update.message.reply_text(
        f"✅ Success!\n\n"
        f"'{current_chat_name}' is now linked to reward group '{group_data[1]}'.\n\n"
        f"I'll post announcements here when:\n"
        f"• Someone adds a new reward to their shop\n"
        f"• Someone buys a reward\n"
        f"• Someone reaches a streak milestone (7, 15, 30 days)"
    )


async def view_user_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View another user's statistics (similar to my_stats but for other users)"""
    query = update.callback_query
    await query.answer()

    # Extract the target user ID from callback data
    target_user_id = int(query.data.split('_')[-1])

    # Get target user data
    target_user_data = db.get_user(target_user_id)
    if not target_user_data:
        await query.edit_message_text("User not found!")
        return

    target_name = target_user_data[2] or target_user_data[1] or f"User {target_user_id}"
    # Add medal emojis to name
    target_name_with_medals = format_user_name_with_medals(target_user_id, target_name)

    # Get habit completions for the target user (current month)
    from datetime import datetime
    now = datetime.now()
    year = now.year
    month = now.month

    completions = db.get_user_completions_for_month(target_user_id, year, month)

    if not completions:
        text = f"📊 {target_name_with_medals}'s Stats for {now.strftime('%B %Y')}:\n\n"
        total_points = sum(target_user_data[5:10]) if len(target_user_data) > 9 else 0
        text += f"No habits completed this month yet.\n\nTotal Points: {total_points}"
    else:
        text = f"📊 {target_name_with_medals}'s Stats for {now.strftime('%B %Y')}:\n\n"

        # Group by date
        from collections import defaultdict
        by_date = defaultdict(list)
        for completion in completions:
            date = completion[3]  # completion_date (YYYY-MM-DD format)
            habit_name = completion[4]  # habit_name from join
            by_date[date].append(habit_name)

        for date in sorted(by_date.keys()):
            day = datetime.strptime(date, '%Y-%m-%d').strftime('%d %b')
            habits_on_date = by_date[date]
            text += f"📅 {day}:\n"
            for habit in habits_on_date:
                text += f"  ✅ {habit}\n"

        total_points = sum(target_user_data[5:10]) if len(target_user_data) > 9 else 0
        text += f"\nTotal Points: {total_points}"

    keyboard = [
        [InlineKeyboardButton("« Back to Group Info", callback_data="group_info")],
        [InlineKeyboardButton("Back to Menu", callback_data="back_to_menu")]
    ]

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
