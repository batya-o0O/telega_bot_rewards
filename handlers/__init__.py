"""
Handler modules for the Telegram Rewards Bot

This package contains all the command and callback handlers organized by feature:
- common: Common handlers (back_to_menu, cancel)
- start: Start and menu commands
- groups: Group management (create, join, group info, setgroupchat)
- habits: Habit management (CRUD, toggle, stats, calendar)
- rewards: Reward shop (browse, buy, sell, custom payment)
- points: Point conversion
- reports: Monthly reports and leaderboards
- townmall: Town mall shop with coins
"""

# Import all handlers for easy access
from .common import back_to_menu, cancel
from .start import start, menu
from .groups import (
    create_group_start,
    create_group_finish,
    join_group_start,
    join_group_finish,
    group_info,
    setgroupchat,
    view_user_stats
)
from .habits import (
    my_habits,
    yesterday_habits,
    toggle_habit,
    toggle_yesterday_habit,
    manage_habits,
    add_habit_start,
    add_habit_get_name,
    add_habit_finish,
    edit_habit_list,
    edit_habit_start,
    edit_habit_get_name,
    edit_habit_finish,
    delete_habit_list,
    delete_habit_confirm,
    my_stats,
    calendar_view,
    habit_calendar_view
)
from .rewards import (
    reward_shop,
    view_shop,
    buy_reward,
    payment_select_type,
    payment_add_amount,
    show_payment_screen,
    payment_clear,
    payment_confirm,
    my_rewards,
    add_reward_start,
    add_reward_get_details,
    add_reward_finish,
    delete_reward_list,
    delete_reward_confirm
)
from .points import (
    convert_points_start,
    convert_points_select_to,
    convert_points_select_amount,
    convert_points_finish
)
from .reports import (
    monthly_report,
    monthlyreport
)
from .townmall import (
    town_mall,
    view_town_mall_item,
    buy_town_mall_item,
    town_mall_purchase_history,
    town_mall_dummy_callback
)

__all__ = [
    # Common
    'back_to_menu',
    'cancel',
    # Start
    'start',
    'menu',
    # Groups
    'create_group_start',
    'create_group_finish',
    'join_group_start',
    'join_group_finish',
    'group_info',
    'setgroupchat',
    'view_user_stats',
    # Habits
    'my_habits',
    'yesterday_habits',
    'toggle_habit',
    'toggle_yesterday_habit',
    'manage_habits',
    'add_habit_start',
    'add_habit_get_name',
    'add_habit_finish',
    'edit_habit_list',
    'edit_habit_start',
    'edit_habit_get_name',
    'edit_habit_finish',
    'delete_habit_list',
    'delete_habit_confirm',
    'my_stats',
    'calendar_view',
    'habit_calendar_view',
    # Rewards
    'reward_shop',
    'view_shop',
    'buy_reward',
    'payment_select_type',
    'payment_add_amount',
    'show_payment_screen',
    'payment_clear',
    'payment_confirm',
    'my_rewards',
    'add_reward_start',
    'add_reward_get_details',
    'add_reward_finish',
    'delete_reward_list',
    'delete_reward_confirm',
    # Points
    'convert_points_start',
    'convert_points_select_to',
    'convert_points_select_amount',
    'convert_points_finish',
    # Reports
    'monthly_report',
    'monthlyreport',
    # Town Mall
    'town_mall',
    'view_town_mall_item',
    'buy_town_mall_item',
    'town_mall_purchase_history',
    'town_mall_dummy_callback',
]
