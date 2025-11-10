import os
import logging
import asyncio
import warnings
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from telegram.warnings import PTBUserWarning

from database import Database, POINT_TYPES

# Load environment variables
load_dotenv()

# Suppress PTBUserWarning about per_message in ConversationHandler
warnings.filterwarnings("ignore", category=PTBUserWarning, message=".*per_message.*")

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize database
db = Database()

# Conversation states
CREATING_GROUP, JOINING_GROUP, ADDING_HABIT, ADDING_HABIT_TYPE, EDITING_HABIT, EDITING_HABIT_TYPE, ADDING_REWARD, ADDING_REWARD_TYPE, CONVERTING_POINTS_FROM, CONVERTING_POINTS_TO, CONVERTING_POINTS_AMOUNT = range(11)

# Helper functions
def get_main_menu_keyboard():
    """Generate main menu keyboard"""
    keyboard = [
        [InlineKeyboardButton("My Habits", callback_data="my_habits")],
        [InlineKeyboardButton("My Stats", callback_data="my_stats")],
        [InlineKeyboardButton("Reward Shop", callback_data="reward_shop")],
        [InlineKeyboardButton("My Rewards Shop", callback_data="my_rewards")],
        [InlineKeyboardButton("Convert Points", callback_data="convert_points")],
        [InlineKeyboardButton("Group Info", callback_data="group_info")],
    ]
    return InlineKeyboardMarkup(keyboard)

def format_points_display(points_dict):
    """Format points dictionary for display"""
    lines = []
    for ptype, emoji in POINT_TYPES.items():
        amount = points_dict.get(ptype, 0)
        if amount > 0:
            type_name = ptype.replace('_', ' ').title()
            lines.append(f"{emoji} {type_name}: {amount}")

    if not lines:
        return "No points yet"
    return "\n".join(lines)

def get_habit_type_keyboard():
    """Generate keyboard for habit type selection"""
    keyboard = []
    for ptype, emoji in POINT_TYPES.items():
        type_name = ptype.replace('_', ' ').title()
        keyboard.append([InlineKeyboardButton(
            f"{emoji} {type_name}",
            callback_data=f"habittype_{ptype}"
        )])
    return InlineKeyboardMarkup(keyboard)

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    db.create_or_update_user(user.id, user.username, user.first_name)

    user_data = db.get_user(user.id)

    if user_data and user_data[3]:  # Has group_id
        await update.message.reply_text(
            f"Welcome back, {user.first_name}!\n\n"
            f"You have {user_data[4]} points.",
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

    await update.message.reply_text(
        f"Main Menu\nPoints: {user_data[4]}",
        reply_markup=get_main_menu_keyboard()
    )

# Group management
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

# Habit management
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
        habit_type = habit[4] if len(habit) > 4 else 'other'  # habit_type is column 4
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

    completed_habit_ids = db.get_completions_for_date(user_id, today)

    if habit_id in completed_habit_ids:
        db.unmark_habit_complete(user_id, habit_id, today)
    else:
        db.mark_habit_complete(user_id, habit_id, today)

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

    habit_type = query.data.split('_')[1]  # Extract type from "habittype_physical"
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
        keyboard.append([InlineKeyboardButton(
            habit[2],
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

async def edit_habit_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Finish editing a habit"""
    new_name = update.message.text
    habit_id = context.user_data.get('editing_habit_id')

    db.update_habit(habit_id, new_name)

    await update.message.reply_text(
        f"Habit updated successfully!",
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
        keyboard.append([InlineKeyboardButton(
            f"❌ {habit[2]}",
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

# Statistics
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
        text += f"No habits completed this month yet.\n\nTotal Points: {user_data[4]}"
    else:
        text = f"Your Stats for {now.strftime('%B %Y')}:\n\n"

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

        text += f"\nTotal Points: {user_data[4]}"

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
    import calendar
    num_days = calendar.monthrange(year, month)[1]
    first_weekday = calendar.monthrange(year, month)[0]  # 0 = Monday, 6 = Sunday

    # Get all completions for the month
    completions = db.get_user_completions_for_month(user_id, year, month)

    # Count completions per day
    from collections import defaultdict
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

    text += f"\nTotal Points: {user_data[4]}"

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
    import calendar
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
        points = member[4]
        text += f"- {name}: {points} points\n"

    keyboard = [[InlineKeyboardButton("Back to Menu", callback_data="back_to_menu")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# Reward shop
async def reward_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show reward shop - list all group members to see their rewards"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    user_data = db.get_user(user_id)

    if not user_data or not user_data[3]:
        await query.edit_message_text("You need to join a group first!")
        return

    group_id = user_data[3]
    members = db.get_group_members(group_id)

    keyboard = []
    for member in members:
        member_id = member[0]
        name = member[2] or member[1] or f"User {member_id}"
        keyboard.append([InlineKeyboardButton(
            f"{name}'s Shop",
            callback_data=f"view_shop_{member_id}"
        )])

    keyboard.append([InlineKeyboardButton("Back to Menu", callback_data="back_to_menu")])

    await query.edit_message_text(
        f"Reward Shop\nYour points: {user_data[4]}\n\nSelect a member to view their rewards:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def view_shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View a specific user's reward shop"""
    query = update.callback_query
    await query.answer()

    owner_id = int(query.data.split('_')[2])
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    owner_data = db.get_user(owner_id)

    owner_name = owner_data[2] or owner_data[1] or f"User {owner_id}"
    rewards = db.get_user_rewards(owner_id)
    user_points = db.get_user_points(user_id)

    if not rewards:
        text = f"{owner_name}'s Shop\n\nNo rewards available."
        keyboard = [[InlineKeyboardButton("Back", callback_data="reward_shop")]]
    else:
        text = f"{owner_name}'s Shop\n\nYour Points:\n{format_points_display(user_points)}\n\n"
        keyboard = []

        for reward in rewards:
            reward_id = reward[0]
            reward_name = reward[2]
            price = reward[3]
            point_type = reward[6] if len(reward) > 6 else 'other'  # point_type column

            type_emoji = POINT_TYPES.get(point_type, '⭐')
            type_name = point_type.replace('_', ' ').title()

            text += f"{reward_name} - {price} {type_emoji} {type_name}\n"

            if user_id != owner_id:  # Can't buy from yourself
                keyboard.append([InlineKeyboardButton(
                    f"Buy: {reward_name} ({price} {type_emoji})",
                    callback_data=f"buy_reward_{reward_id}"
                )])

        keyboard.append([InlineKeyboardButton("Back", callback_data="reward_shop")])

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def buy_reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Buy a reward"""
    query = update.callback_query
    await query.answer()

    reward_id = int(query.data.split('_')[2])
    user_id = update.effective_user.id

    # Get reward info
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT owner_id, name, price FROM rewards WHERE id = ?', (reward_id,))
    reward = cursor.fetchone()
    conn.close()

    if not reward:
        await query.edit_message_text("Reward not found.")
        return

    seller_id, reward_name, price = reward

    success = db.buy_reward(user_id, seller_id, reward_id)

    if success:
        await query.edit_message_text(
            f"Successfully purchased '{reward_name}' for {price} points!\n\n"
            "The seller will fulfill your reward.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Back to Menu", callback_data="back_to_menu")
            ]])
        )
    else:
        await query.edit_message_text(
            f"Not enough points! You need {price} points.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Back", callback_data="reward_shop")
            ]])
        )

# My rewards management
async def my_rewards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's own reward shop"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    rewards = db.get_user_rewards(user_id)

    text = "My Reward Shop:\n\n"

    if not rewards:
        text += "No rewards yet. Add some!"
    else:
        for reward in rewards:
            text += f"- {reward[2]} ({reward[3]} points)\n"

    keyboard = [
        [InlineKeyboardButton("Add Reward", callback_data="add_reward")],
        [InlineKeyboardButton("Delete Reward", callback_data="delete_reward_list")],
        [InlineKeyboardButton("Back to Menu", callback_data="back_to_menu")],
    ]

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def add_reward_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start adding a reward"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "Please enter the reward in format:\n"
        "Name | Price\n\n"
        "Example: Cooking your favourite dish | 30"
    )
    return ADDING_REWARD

async def add_reward_get_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get reward details and ask for point type"""
    text = update.message.text
    user_id = update.effective_user.id

    try:
        parts = text.split('|')
        if len(parts) != 2:
            raise ValueError

        name = parts[0].strip()
        price = int(parts[1].strip())

        if price < 1:
            raise ValueError

        # Store reward details in context
        context.user_data['new_reward_name'] = name
        context.user_data['new_reward_price'] = price

        await update.message.reply_text(
            f"Great! Now select which type of points for '{name}' ({price} points):",
            reply_markup=get_habit_type_keyboard()
        )
        return ADDING_REWARD_TYPE

    except (ValueError, IndexError):
        await update.message.reply_text(
            "Invalid format. Please use: Name | Price\n"
            "Example: Cooking your favourite dish | 30"
        )
        return ADDING_REWARD

async def add_reward_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Finish adding a reward with selected point type"""
    query = update.callback_query
    await query.answer()

    point_type = query.data.split('_')[1]  # Extract from "habittype_physical"
    name = context.user_data.get('new_reward_name')
    price = context.user_data.get('new_reward_price')
    user_id = update.effective_user.id

    db.add_reward(user_id, name, price, point_type)

    type_emoji = POINT_TYPES.get(point_type, '⭐')
    type_name = point_type.replace('_', ' ').title()

    await query.edit_message_text(
        f"Reward '{name}' added for {price} {type_emoji} {type_name} points!",
        reply_markup=get_main_menu_keyboard()
    )
    return ConversationHandler.END

async def delete_reward_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show list of rewards to delete"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    rewards = db.get_user_rewards(user_id)

    if not rewards:
        await query.edit_message_text("No rewards to delete.")
        return

    keyboard = []
    for reward in rewards:
        keyboard.append([InlineKeyboardButton(
            f"❌ {reward[2]} ({reward[3]} pts)",
            callback_data=f"confirm_delete_reward_{reward[0]}"
        )])
    keyboard.append([InlineKeyboardButton("Back", callback_data="my_rewards")])

    await query.edit_message_text(
        "Select a reward to delete:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def delete_reward_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete a reward"""
    query = update.callback_query
    await query.answer()

    reward_id = int(query.data.split('_')[3])
    db.delete_reward(reward_id)

    await query.edit_message_text("Reward deleted successfully!")
    await my_rewards(update, context)

# Navigation
async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Go back to main menu"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    user_data = db.get_user(user_id)

    await query.edit_message_text(
        f"Main Menu\nPoints: {user_data[4]}",
        reply_markup=get_main_menu_keyboard()
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel current conversation"""
    await update.message.reply_text(
        "Cancelled.",
        reply_markup=get_main_menu_keyboard()
    )
    return ConversationHandler.END

def main():
    """Start the bot"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        raise ValueError("No TELEGRAM_BOT_TOKEN found in environment variables")

    application = Application.builder().token(token).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu))

    # Group creation conversation
    create_group_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(create_group_start, pattern="^create_group$")],
        states={
            CREATING_GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, create_group_finish)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )
    application.add_handler(create_group_conv)

    # Join group conversation
    join_group_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(join_group_start, pattern="^join_group$")],
        states={
            JOINING_GROUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, join_group_finish)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )
    application.add_handler(join_group_conv)

    # Add habit conversation
    add_habit_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_habit_start, pattern="^add_habit$")],
        states={
            ADDING_HABIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_habit_get_name)],
            ADDING_HABIT_TYPE: [CallbackQueryHandler(add_habit_finish, pattern=r"^habittype_\w+$")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )
    application.add_handler(add_habit_conv)

    # Edit habit conversation
    edit_habit_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_habit_start, pattern=r"^edit_habit_\d+$")],
        states={
            EDITING_HABIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_habit_finish)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )
    application.add_handler(edit_habit_conv)

    # Add reward conversation
    add_reward_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_reward_start, pattern="^add_reward$")],
        states={
            ADDING_REWARD: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_reward_get_details)],
            ADDING_REWARD_TYPE: [CallbackQueryHandler(add_reward_finish, pattern=r"^habittype_\w+$")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )
    application.add_handler(add_reward_conv)

    # Callback query handlers
    application.add_handler(CallbackQueryHandler(my_habits, pattern="^my_habits$"))
    application.add_handler(CallbackQueryHandler(toggle_habit, pattern=r"^toggle_habit_\d+$"))
    application.add_handler(CallbackQueryHandler(manage_habits, pattern="^manage_habits$"))
    application.add_handler(CallbackQueryHandler(edit_habit_list, pattern="^edit_habit_list$"))
    application.add_handler(CallbackQueryHandler(delete_habit_list, pattern="^delete_habit_list$"))
    application.add_handler(CallbackQueryHandler(delete_habit_confirm, pattern=r"^confirm_delete_habit_\d+$"))

    application.add_handler(CallbackQueryHandler(my_stats, pattern="^my_stats$"))
    application.add_handler(CallbackQueryHandler(calendar_view, pattern="^calendar_view$"))
    application.add_handler(CallbackQueryHandler(habit_calendar_view, pattern=r"^habit_calendar_\d+$"))
    application.add_handler(CallbackQueryHandler(group_info, pattern="^group_info$"))

    application.add_handler(CallbackQueryHandler(reward_shop, pattern="^reward_shop$"))
    application.add_handler(CallbackQueryHandler(view_shop, pattern=r"^view_shop_\d+$"))
    application.add_handler(CallbackQueryHandler(buy_reward, pattern=r"^buy_reward_\d+$"))

    application.add_handler(CallbackQueryHandler(my_rewards, pattern="^my_rewards$"))
    application.add_handler(CallbackQueryHandler(delete_reward_list, pattern="^delete_reward_list$"))
    application.add_handler(CallbackQueryHandler(delete_reward_confirm, pattern=r"^confirm_delete_reward_\d+$"))

    application.add_handler(CallbackQueryHandler(back_to_menu, pattern="^back_to_menu$"))

    # Start the bot
    logger.info("Bot started")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    # Fix for Python 3.14+ event loop issue
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())

    main()
