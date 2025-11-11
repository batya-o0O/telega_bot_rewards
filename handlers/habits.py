"""
Habit Management Handlers

This module contains all handlers related to habit management, including:
- Viewing and toggling daily habits
- Adding, editing, and deleting habits
- Viewing statistics and calendar views
- Managing habit completions and streaks
"""

import logging
import calendar
from datetime import datetime
from collections import defaultdict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from database import Database, POINT_TYPES
from constants import (
    ADDING_HABIT,
    ADDING_HABIT_TYPE,
    EDITING_HABIT,
    EDITING_HABIT_TYPE,
)
from utils.keyboards import get_main_menu_keyboard, get_habit_type_keyboard
from utils.announcements import send_group_announcement

logger = logging.getLogger(__name__)
db = Database()


async def my_habits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's habits for today"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    user_data = db.get_user(user_id)

    if not user_data or not user_data[3]:
        await query.edit_message_text("You need to join a group first!")
        return

    group_id = user_data[3]
    habits = db.get_group_habits(group_id)

    if not habits:
        keyboard = [[InlineKeyboardButton("Add Habit", callback_data="add_habit")],
                   [InlineKeyboardButton("Back to Menu", callback_data="back_to_menu")]]
        await query.edit_message_text(
            "No habits yet. Add some!",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # Get today's completions
    today = datetime.now().strftime('%Y-%m-%d')
    completed_habit_ids = db.get_completions_for_date(user_id, today)

    # Create keyboard with habits
    keyboard = []
    text = "Today's Habits:\n\n"

    for habit in habits:
        habit_id = habit[0]
        habit_name = habit[2]
        habit_type = habit[5] if len(habit) > 5 else 'other'  # habit_type is column 5
        is_completed = habit_id in completed_habit_ids

        type_emoji = POINT_TYPES.get(habit_type, '⭐')
        status = "✅" if is_completed else "⬜"
        text += f"{status} {type_emoji} {habit_name}\n"

        callback_data = f"toggle_habit_{habit_id}"
        keyboard.append([InlineKeyboardButton(f"{status} {type_emoji} {habit_name}", callback_data=callback_data)])

    keyboard.append([InlineKeyboardButton("Manage Habits", callback_data="manage_habits")])
    keyboard.append([InlineKeyboardButton("Back to Menu", callback_data="back_to_menu")])

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def toggle_habit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle habit completion for today"""
    query = update.callback_query
    await query.answer()

    habit_id = int(query.data.split('_')[2])
    user_id = update.effective_user.id
    today = datetime.now().strftime('%Y-%m-%d')
    current_month = datetime.now().strftime('%Y-%m')

    completed_habit_ids = db.get_completions_for_date(user_id, today)

    if habit_id in completed_habit_ids:
        db.unmark_habit_complete(user_id, habit_id, today)
    else:
        db.mark_habit_complete(user_id, habit_id, today)

        # Update streak and check for milestones
        streak_info = db.update_streak(user_id, habit_id, today)

        # Get user and group info
        user_data = db.get_user(user_id)
        group_id = user_data[3]
        user_name = update.effective_user.first_name or update.effective_user.username or "Someone"

        # Get habit info
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT name FROM habits WHERE id = ?', (habit_id,))
        habit_name = cursor.fetchone()[0]
        conn.close()

        # Check if user reached 30-day streak and award medal
        if streak_info['current_streak'] == 30:
            # Check if user doesn't have medal for this habit yet
            if not db.has_medal_for_habit(user_id, habit_id):
                # Award medal
                db.award_medal(user_id, habit_id)

                # Send medal announcement
                medal_message = f"🏅 {user_name} earned a medal for '{habit_name}'! 30-day streak completed!"
                await send_group_announcement(context, group_id, medal_message)

        # Check if this is the user's 3rd medal total
        medal_count = db.get_medal_count(user_id)
        if medal_count == 3:
            # Send conversion rate improvement announcement
            conversion_message = f"⭐ {user_name} earned 3 medals! Conversion rate improved to 1.5:1!"
            await send_group_announcement(context, group_id, conversion_message)

        # Award coins based on medal status for THIS habit
        if db.has_medal_for_habit(user_id, habit_id):
            # User has medal for this habit, give 0.5 coins
            db.add_coins(user_id, 0.5)
        else:
            # No medal for this habit, give 1 point (already done by mark_habit_complete)
            pass

        # If milestone reached, announce it
        if streak_info['new_milestone']:
            milestone = streak_info['new_milestone']

            message = f"🎉 Congratulations {user_name}!\n\n"
            message += f"You've reached a {milestone}-day streak on '{habit_name}'! 🔥\n"
            message += f"Keep up the amazing work!"

            await send_group_announcement(context, group_id, message)

        # Check for group habit completion
        if db.check_and_award_group_habit_completion(group_id, habit_id, current_month):
            # Send group achievement announcement
            group_message = f"🎉 Group Achievement! '{habit_name}' completed every day this month! Everyone gets 10 coins!"
            await send_group_announcement(context, group_id, group_message)

    # Refresh the habits view
    await my_habits(update, context)


async def manage_habits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show habit management options"""
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("Add Habit", callback_data="add_habit")],
        [InlineKeyboardButton("Edit Habit", callback_data="edit_habit_list")],
        [InlineKeyboardButton("Delete Habit", callback_data="delete_habit_list")],
        [InlineKeyboardButton("Back", callback_data="my_habits")],
    ]

    await query.edit_message_text(
        "Habit Management",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def add_habit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start adding a habit"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Please enter the habit name (e.g., 'Read 20 pages'):")
    return ADDING_HABIT


async def add_habit_get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get habit name and ask for type"""
    habit_name = update.message.text
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)

    if not user_data or not user_data[3]:
        await update.message.reply_text("You need to join a group first!")
        return ConversationHandler.END

    # Store habit name in context
    context.user_data['new_habit_name'] = habit_name

    await update.message.reply_text(
        f"Great! Now select the type for '{habit_name}':",
        reply_markup=get_habit_type_keyboard()
    )
    return ADDING_HABIT_TYPE


async def add_habit_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Finish adding a habit with selected type"""
    query = update.callback_query
    await query.answer()

    habit_type = query.data.replace('habittype_', '')  # Extract type from "habittype_food_related"
    habit_name = context.user_data.get('new_habit_name')
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)

    if not user_data or not user_data[3]:
        await query.edit_message_text("You need to join a group first!")
        return ConversationHandler.END

    group_id = user_data[3]
    db.add_habit(group_id, habit_name, habit_type)

    type_emoji = POINT_TYPES.get(habit_type, '⭐')
    type_name = habit_type.replace('_', ' ').title()

    await query.edit_message_text(
        f"Habit '{habit_name}' added successfully!\nType: {type_emoji} {type_name}",
        reply_markup=get_main_menu_keyboard()
    )
    return ConversationHandler.END


async def edit_habit_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of habits to edit"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    group_id = user_data[3]
    habits = db.get_group_habits(group_id)

    if not habits:
        await query.edit_message_text("No habits to edit.")
        return

    keyboard = []
    for habit in habits:
        habit_type = habit[5] if len(habit) > 5 else 'other'
        type_emoji = POINT_TYPES.get(habit_type, '⭐')
        keyboard.append([InlineKeyboardButton(
            f"{type_emoji} {habit[2]}",
            callback_data=f"edit_habit_{habit[0]}"
        )])
    keyboard.append([InlineKeyboardButton("Back", callback_data="manage_habits")])

    await query.edit_message_text(
        "Select a habit to edit:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def edit_habit_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start editing a habit"""
    query = update.callback_query
    await query.answer()

    habit_id = int(query.data.split('_')[2])
    context.user_data['editing_habit_id'] = habit_id

    await query.edit_message_text("Please enter the new name for this habit:")
    return EDITING_HABIT


async def edit_habit_get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get new habit name and ask for type"""
    new_name = update.message.text
    habit_id = context.user_data.get('editing_habit_id')

    # Store new name
    context.user_data['editing_habit_name'] = new_name

    await update.message.reply_text(
        f"Great! Now select the type for '{new_name}':",
        reply_markup=get_habit_type_keyboard()
    )
    return EDITING_HABIT_TYPE


async def edit_habit_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Finish editing a habit with type"""
    query = update.callback_query
    await query.answer()

    habit_id = context.user_data.get('editing_habit_id')
    new_name = context.user_data.get('editing_habit_name')
    habit_type = query.data.replace('habittype_', '')  # Extract type from "habittype_food_related"

    db.update_habit(habit_id, new_name, habit_type)

    type_emoji = POINT_TYPES.get(habit_type, '⭐')
    type_name = habit_type.replace('_', ' ').title()

    await query.edit_message_text(
        f"Habit '{new_name}' updated!\nType: {type_emoji} {type_name}",
        reply_markup=get_main_menu_keyboard()
    )
    return ConversationHandler.END


async def delete_habit_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of habits to delete"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    group_id = user_data[3]
    habits = db.get_group_habits(group_id)

    if not habits:
        await query.edit_message_text("No habits to delete.")
        return

    keyboard = []
    for habit in habits:
        habit_type = habit[5] if len(habit) > 5 else 'other'
        type_emoji = POINT_TYPES.get(habit_type, '⭐')
        keyboard.append([InlineKeyboardButton(
            f"❌ {type_emoji} {habit[2]}",
            callback_data=f"confirm_delete_habit_{habit[0]}"
        )])
    keyboard.append([InlineKeyboardButton("Back", callback_data="manage_habits")])

    await query.edit_message_text(
        "Select a habit to delete:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def delete_habit_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete a habit"""
    query = update.callback_query
    await query.answer()

    habit_id = int(query.data.split('_')[3])
    db.delete_habit(habit_id)

    await query.edit_message_text("Habit deleted successfully!")
    await manage_habits(update, context)


async def my_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user statistics for current month"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    user_data = db.get_user(user_id)

    if not user_data or not user_data[3]:
        await query.edit_message_text("You need to join a group first!")
        return

    group_id = user_data[3]
    habits = db.get_group_habits(group_id)

    now = datetime.now()
    year = now.year
    month = now.month

    completions = db.get_user_completions_for_month(user_id, year, month)

    if not completions:
        text = f"Your Stats for {now.strftime('%B %Y')}:\n\n"
        total_points = sum(user_data[5:10]) if len(user_data) > 9 else 0
        text += f"No habits completed this month yet.\n\nTotal Points: {total_points}"
    else:
        text = f"Your Stats for {now.strftime('%B %Y')}:\n\n"

        # Group by date
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

        total_points = sum(user_data[5:10]) if len(user_data) > 9 else 0
        text += f"\nTotal Points: {total_points}"

    keyboard = [
        [InlineKeyboardButton("📆 Overall Calendar", callback_data="calendar_view")]
    ]

    # Add per-habit calendar buttons
    for habit in habits:
        habit_id = habit[0]
        habit_name = habit[2]
        keyboard.append([InlineKeyboardButton(f"📆 {habit_name}", callback_data=f"habit_calendar_{habit_id}")])

    keyboard.append([InlineKeyboardButton("Back to Menu", callback_data="back_to_menu")])

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def calendar_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show calendar view with colored day numbers for completed habits"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    user_data = db.get_user(user_id)

    if not user_data or not user_data[3]:
        await query.edit_message_text("You need to join a group first!")
        return

    group_id = user_data[3]
    habits = db.get_group_habits(group_id)
    total_habits = len(habits)

    now = datetime.now()
    year = now.year
    month = now.month

    # Get number of days in month
    num_days = calendar.monthrange(year, month)[1]
    first_weekday = calendar.monthrange(year, month)[0]  # 0 = Monday, 6 = Sunday

    # Get all completions for the month
    completions = db.get_user_completions_for_month(user_id, year, month)

    # Count completions per day
    completions_per_day = defaultdict(int)
    for completion in completions:
        date = completion[3]  # completion_date
        day = int(date.split('-')[2])
        completions_per_day[day] += 1

    # Build calendar
    text = f"📆 Overall Calendar - {now.strftime('%B %Y')}\n\n"
    text += "🟢 All done | 🟡 Partial | ⬜ None | ⬛ Future\n\n"

    # Weekday headers - using monospace formatting
    text += "Mo  Tu  We  Th  Fr  Sa  Su\n"

    # Add leading spaces for first week
    today = now.day
    calendar_line = ""
    for i in range(first_weekday):
        calendar_line += "    "  # 4 spaces per empty cell

    for day in range(1, num_days + 1):
        if day > today:
            # Future days - use black square
            day_str = f"⬛{day:>2}"
        elif day in completions_per_day:
            completed = completions_per_day[day]
            if total_habits == 0:
                day_str = f"⬜{day:>2}"
            elif completed >= total_habits:
                day_str = f"🟢{day:>2}"
            else:
                day_str = f"🟡{day:>2}"
        else:
            day_str = f"⬜{day:>2}"

        calendar_line += day_str + " "

        # New line after Sunday
        if (first_weekday + day) % 7 == 0:
            text += calendar_line + "\n"
            calendar_line = ""

    # Add remaining days
    if calendar_line:
        text += calendar_line + "\n"

    total_points = sum(user_data[5:10]) if len(user_data) > 9 else 0
    text += f"\nTotal Points: {total_points}"

    keyboard = [
        [InlineKeyboardButton("📊 Stats View", callback_data="my_stats")],
        [InlineKeyboardButton("Back to Menu", callback_data="back_to_menu")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def habit_calendar_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show calendar view for a specific habit"""
    query = update.callback_query
    await query.answer()

    habit_id = int(query.data.split('_')[2])
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)

    if not user_data or not user_data[3]:
        await query.edit_message_text("You need to join a group first!")
        return

    # Get habit info
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM habits WHERE id = ?', (habit_id,))
    habit = cursor.fetchone()
    conn.close()

    if not habit:
        await query.edit_message_text("Habit not found!")
        return

    habit_name = habit[0]

    now = datetime.now()
    year = now.year
    month = now.month

    # Get number of days in month
    num_days = calendar.monthrange(year, month)[1]
    first_weekday = calendar.monthrange(year, month)[0]

    # Get all completions for this habit
    completions = db.get_user_completions_for_month(user_id, year, month)

    # Get days when this specific habit was completed
    completed_days = set()
    for completion in completions:
        if completion[2] == habit_id:  # habit_id column
            date = completion[3]  # completion_date
            day = int(date.split('-')[2])
            completed_days.add(day)

    # Build calendar
    text = f"📆 Calendar - {habit_name}\n"
    text += f"{now.strftime('%B %Y')}\n\n"
    text += "🟢 Done | ⬜ Not done | ⬛ Future\n\n"

    # Weekday headers
    text += "Mo  Tu  We  Th  Fr  Sa  Su\n"

    # Add leading spaces for first week
    today = now.day
    calendar_line = ""
    for i in range(first_weekday):
        calendar_line += "    "

    for day in range(1, num_days + 1):
        if day > today:
            # Future days
            day_str = f"⬛{day:>2}"
        elif day in completed_days:
            day_str = f"🟢{day:>2}"
        else:
            day_str = f"⬜{day:>2}"

        calendar_line += day_str + " "

        # New line after Sunday
        if (first_weekday + day) % 7 == 0:
            text += calendar_line + "\n"
            calendar_line = ""

    # Add remaining days
    if calendar_line:
        text += calendar_line + "\n"

    # Calculate completion rate
    if today > 0:
        completion_rate = (len(completed_days) / today) * 100
        text += f"\nCompletion Rate: {completion_rate:.1f}% ({len(completed_days)}/{today} days)"

    keyboard = [
        [InlineKeyboardButton("📊 Back to Stats", callback_data="my_stats")],
        [InlineKeyboardButton("Back to Menu", callback_data="back_to_menu")]
    ]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
