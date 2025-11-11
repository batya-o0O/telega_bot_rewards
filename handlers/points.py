"""
Point conversion handlers for the Telegram bot.

This module handles point conversion between different point types
with a 2:1 conversion ratio.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from database import Database, POINT_TYPES
from constants import CONVERTING_POINTS_FROM, CONVERTING_POINTS_TO, CONVERTING_POINTS_AMOUNT
from utils import format_points_display, get_main_menu_keyboard

# Initialize database
db = Database()


async def convert_points_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start point conversion"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    user_points = db.get_user_points(user_id)

    text = "Convert Points (2:1 ratio)\n\nYour Points:\n"
    text += format_points_display(user_points)
    text += "\n\nSelect the point type you want to convert FROM:"

    keyboard = []
    for ptype, emoji in POINT_TYPES.items():
        if ptype == 'any':  # Skip 'any' for conversions
            continue
        if user_points.get(ptype, 0) >= 2:  # Need at least 2 to convert
            type_name = ptype.replace('_', ' ').title()
            keyboard.append([InlineKeyboardButton(
                f"{emoji} {type_name} ({user_points[ptype]})",
                callback_data=f"convertfrom_{ptype}"
            )])

    if not keyboard:
        keyboard.append([InlineKeyboardButton("Back to Menu", callback_data="back_to_menu")])
        text = "You need at least 2 points of any type to convert.\n\n" + text

    else:
        keyboard.append([InlineKeyboardButton("Cancel", callback_data="back_to_menu")])

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return CONVERTING_POINTS_FROM


async def convert_points_select_to(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Select destination point type"""
    query = update.callback_query
    await query.answer()

    from_type = query.data.replace('convertfrom_', '')
    context.user_data['convert_from_type'] = from_type

    user_id = update.effective_user.id
    user_points = db.get_user_points(user_id)

    from_emoji = POINT_TYPES.get(from_type, '⭐')
    from_name = from_type.replace('_', ' ').title()

    text = f"Converting FROM: {from_emoji} {from_name}\n"
    text += f"Available: {user_points.get(from_type, 0)}\n\n"
    text += "Select the point type you want to convert TO:"

    keyboard = []
    for ptype, emoji in POINT_TYPES.items():
        if ptype == 'any':  # Skip 'any' for conversions
            continue
        if ptype != from_type:  # Can't convert to same type
            type_name = ptype.replace('_', ' ').title()
            keyboard.append([InlineKeyboardButton(
                f"{emoji} {type_name}",
                callback_data=f"convertto_{ptype}"
            )])

    keyboard.append([InlineKeyboardButton("Cancel", callback_data="back_to_menu")])

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return CONVERTING_POINTS_TO


async def convert_points_select_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask for amount to convert"""
    query = update.callback_query
    await query.answer()

    to_type = query.data.replace('convertto_', '')
    context.user_data['convert_to_type'] = to_type

    from_type = context.user_data.get('convert_from_type')
    user_id = update.effective_user.id
    user_points = db.get_user_points(user_id)

    from_emoji = POINT_TYPES.get(from_type, '⭐')
    from_name = from_type.replace('_', ' ').title()
    to_emoji = POINT_TYPES.get(to_type, '⭐')
    to_name = to_type.replace('_', ' ').title()

    available = user_points.get(from_type, 0)

    text = f"Conversion: {from_emoji} {from_name} → {to_emoji} {to_name}\n"
    text += f"Available: {available}\n"
    text += f"Ratio: 2:1\n\n"
    text += f"How many {from_emoji} {from_name} points do you want to convert?\n"
    text += "(Must be an even number, minimum 2)"

    await query.edit_message_text(text)
    return CONVERTING_POINTS_AMOUNT


async def convert_points_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Finish point conversion"""
    try:
        amount = int(update.message.text)
        user_id = update.effective_user.id

        from_type = context.user_data.get('convert_from_type')
        to_type = context.user_data.get('convert_to_type')

        if not from_type or not to_type:
            await update.message.reply_text("Error: Conversion data lost. Please try again.",
                                          reply_markup=get_main_menu_keyboard())
            return ConversationHandler.END

        success = db.convert_points(user_id, from_type, to_type, amount)

        if success:
            converted = amount // 2
            from_emoji = POINT_TYPES.get(from_type, '⭐')
            from_name = from_type.replace('_', ' ').title()
            to_emoji = POINT_TYPES.get(to_type, '⭐')
            to_name = to_type.replace('_', ' ').title()

            user_points = db.get_user_points(user_id)
            text = f"✅ Conversion successful!\n\n"
            text += f"Converted: {amount} {from_emoji} {from_name}\n"
            text += f"Received: {converted} {to_emoji} {to_name}\n\n"
            text += "Your Points:\n" + format_points_display(user_points)

            await update.message.reply_text(text, reply_markup=get_main_menu_keyboard())
        else:
            await update.message.reply_text(
                "❌ Conversion failed!\n\n"
                "Possible reasons:\n"
                "- Not enough points\n"
                "- Invalid amount (must be even number, minimum 2)\n"
                "- Invalid point types",
                reply_markup=get_main_menu_keyboard()
            )

        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text(
            "Invalid amount. Please enter a number.",
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END
