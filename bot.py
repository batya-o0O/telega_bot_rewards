"""
Telegram Rewards Bot - Main Entry Point

A modular habit tracking and rewards bot for Telegram.
Features: Habit tracking, points system, reward shop, group management, and leaderboards.
"""

import os
import logging
import asyncio
import warnings
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)
from telegram.warnings import PTBUserWarning

# Import constants
from constants import (
    CREATING_GROUP, JOINING_GROUP, ADDING_HABIT, ADDING_HABIT_TYPE,
    EDITING_HABIT, EDITING_HABIT_TYPE, ADDING_REWARD, ADDING_REWARD_TYPE,
    CONVERTING_POINTS_FROM, CONVERTING_POINTS_TO, CONVERTING_POINTS_AMOUNT,
    ADDING_TOWNMALL_ITEM, ADDING_TOWNMALL_PHOTO,
    EDITING_TOWNMALL_ITEM, EDITING_TOWNMALL_PHOTO
)

# Import all handlers
from handlers import (
    # Common
    back_to_menu, cancel,
    # Start
    start, menu,
    # Groups
    create_group_start, create_group_finish,
    join_group_start, join_group_finish,
    group_info, setgroupchat, view_user_stats,
    # Habits
    my_habits, yesterday_habits, toggle_habit, toggle_yesterday_habit, manage_habits,
    add_habit_start, add_habit_get_name, add_habit_finish,
    edit_habit_list, edit_habit_start, edit_habit_get_name, edit_habit_finish,
    delete_habit_list, delete_habit_confirm,
    my_stats, calendar_view, habit_calendar_view,
    # Rewards
    reward_shop, view_shop, buy_reward,
    payment_select_type, payment_add_amount, show_payment_screen,
    payment_clear, payment_confirm,
    my_rewards, add_reward_start, add_reward_get_details, add_reward_finish,
    delete_reward_list, delete_reward_confirm,
    # Points
    convert_points_start, convert_points_select_to,
    convert_points_select_amount, convert_points_finish,
    # Reports
    monthly_report, monthlyreport,
    # Town Mall
    town_mall, view_town_mall_item, buy_town_mall_item,
    town_mall_purchase_history, town_mall_my_items,
    town_mall_add_start, town_mall_add_get_details, town_mall_add_photo,
    town_mall_edit_start, town_mall_edit_get_details, town_mall_edit_photo,
    town_mall_dummy_callback
)

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


def main():
    """Start the bot"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        raise ValueError("No TELEGRAM_BOT_TOKEN found in environment variables")

    application = Application.builder().token(token).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("setgroupchat", setgroupchat))
    application.add_handler(CommandHandler("monthlyreport", monthlyreport))

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
            EDITING_HABIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_habit_get_name)],
            EDITING_HABIT_TYPE: [CallbackQueryHandler(edit_habit_finish, pattern=r"^habittype_\w+$")],
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

    # Point conversion conversation
    convert_points_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(convert_points_start, pattern="^convert_points$")],
        states={
            CONVERTING_POINTS_FROM: [CallbackQueryHandler(convert_points_select_to, pattern=r"^convertfrom_\w+$")],
            CONVERTING_POINTS_TO: [CallbackQueryHandler(convert_points_select_amount, pattern=r"^convertto_\w+$")],
            CONVERTING_POINTS_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, convert_points_finish)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )
    application.add_handler(convert_points_conv)

    # Callback query handlers - Habits
    application.add_handler(CallbackQueryHandler(my_habits, pattern="^my_habits$"))
    application.add_handler(CallbackQueryHandler(yesterday_habits, pattern="^yesterday_habits$"))
    application.add_handler(CallbackQueryHandler(toggle_habit, pattern=r"^toggle_habit_\d+$"))
    application.add_handler(CallbackQueryHandler(toggle_yesterday_habit, pattern=r"^toggle_yesterday_\d+$"))
    application.add_handler(CallbackQueryHandler(manage_habits, pattern="^manage_habits$"))
    application.add_handler(CallbackQueryHandler(edit_habit_list, pattern="^edit_habit_list$"))
    application.add_handler(CallbackQueryHandler(delete_habit_list, pattern="^delete_habit_list$"))
    application.add_handler(CallbackQueryHandler(delete_habit_confirm, pattern=r"^confirm_delete_habit_\d+$"))

    # Stats and calendar
    application.add_handler(CallbackQueryHandler(my_stats, pattern="^my_stats$"))
    application.add_handler(CallbackQueryHandler(calendar_view, pattern="^calendar_view$"))
    application.add_handler(CallbackQueryHandler(habit_calendar_view, pattern=r"^habit_calendar_\d+$"))

    # Groups and reports
    application.add_handler(CallbackQueryHandler(group_info, pattern="^group_info$"))
    application.add_handler(CallbackQueryHandler(view_user_stats, pattern=r"^view_user_stats_\d+$"))
    application.add_handler(CallbackQueryHandler(monthly_report, pattern="^monthly_report$"))

    # Reward shop
    application.add_handler(CallbackQueryHandler(reward_shop, pattern="^reward_shop$"))
    application.add_handler(CallbackQueryHandler(view_shop, pattern=r"^view_shop_\d+$"))
    application.add_handler(CallbackQueryHandler(buy_reward, pattern=r"^buy_reward_\d+$"))

    # Payment selection handlers (for 'any' rewards)
    application.add_handler(CallbackQueryHandler(payment_select_type, pattern=r"^payselect_\w+$"))
    application.add_handler(CallbackQueryHandler(payment_add_amount, pattern=r"^payamount_"))
    application.add_handler(CallbackQueryHandler(show_payment_screen, pattern="^payback$"))
    application.add_handler(CallbackQueryHandler(payment_clear, pattern="^payclear$"))
    application.add_handler(CallbackQueryHandler(payment_confirm, pattern="^payconfirm$"))

    # My rewards
    application.add_handler(CallbackQueryHandler(my_rewards, pattern="^my_rewards$"))
    application.add_handler(CallbackQueryHandler(delete_reward_list, pattern="^delete_reward_list$"))
    application.add_handler(CallbackQueryHandler(delete_reward_confirm, pattern=r"^confirm_delete_reward_\d+$"))

    # Town Mall - Add item conversation
    add_townmall_item_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(town_mall_add_start, pattern="^townmall_add$")],
        states={
            ADDING_TOWNMALL_ITEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, town_mall_add_get_details)],
            ADDING_TOWNMALL_PHOTO: [
                MessageHandler(filters.PHOTO, town_mall_add_photo),
                MessageHandler(filters.TEXT & ~filters.COMMAND, town_mall_add_photo),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(add_townmall_item_conv)

    # Town Mall - Edit item conversation
    edit_townmall_item_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(town_mall_edit_start, pattern=r"^townmall_edit_\d+$")],
        states={
            EDITING_TOWNMALL_ITEM: [MessageHandler(filters.TEXT & ~filters.COMMAND, town_mall_edit_get_details)],
            EDITING_TOWNMALL_PHOTO: [
                MessageHandler(filters.PHOTO, town_mall_edit_photo),
                MessageHandler(filters.TEXT & ~filters.COMMAND, town_mall_edit_photo),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(edit_townmall_item_conv)

    # Town Mall
    application.add_handler(CallbackQueryHandler(town_mall, pattern="^town_mall$"))
    application.add_handler(CallbackQueryHandler(view_town_mall_item, pattern=r"^townmall_view_\d+$"))
    application.add_handler(CallbackQueryHandler(buy_town_mall_item, pattern=r"^townmall_buy_\d+$"))
    application.add_handler(CallbackQueryHandler(town_mall_purchase_history, pattern="^townmall_history$"))
    application.add_handler(CallbackQueryHandler(town_mall_my_items, pattern="^townmall_my_items$"))
    application.add_handler(CallbackQueryHandler(town_mall_dummy_callback, pattern="^townmall_(unavailable|outofstock|notenough)$"))

    # Common handlers
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
