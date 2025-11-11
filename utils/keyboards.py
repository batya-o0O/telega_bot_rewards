"""
Keyboard builders for the bot
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import POINT_TYPES


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


def get_habit_type_keyboard():
    """Generate keyboard for habit type selection (excludes 'any')"""
    keyboard = []
    for ptype, emoji in POINT_TYPES.items():
        if ptype == 'any':  # Skip 'any' for habits
            continue
        type_name = ptype.replace('_', ' ').title()
        keyboard.append([InlineKeyboardButton(
            f"{emoji} {type_name}",
            callback_data=f"habittype_{ptype}"
        )])
    return InlineKeyboardMarkup(keyboard)


def get_reward_point_type_keyboard():
    """Generate keyboard for reward point type selection (includes 'any')"""
    keyboard = []
    for ptype, emoji in POINT_TYPES.items():
        type_name = ptype.replace('_', ' ').title()
        keyboard.append([InlineKeyboardButton(
            f"{emoji} {type_name}",
            callback_data=f"habittype_{ptype}"
        )])
    return InlineKeyboardMarkup(keyboard)
