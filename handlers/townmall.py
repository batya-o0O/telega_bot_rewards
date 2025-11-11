"""
Town Mall handlers for the Telegram Rewards Bot

This module handles the town mall shop where users can purchase
items with coins. Supports image display for each item.
"""

import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import Database
from utils import get_main_menu_keyboard, send_group_announcement

# Initialize database
db = Database()


async def town_mall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show town mall main menu with available items"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    user_coins = user_data[10] if len(user_data) > 10 else 0

    items = db.get_town_mall_items(available_only=True)

    text = "🏪 Welcome to Town Mall!\n\n"
    text += f"💰 Your coins: {user_coins}\n\n"

    if not items:
        text += "No items available at the moment.\nCheck back later!"
        keyboard = [[InlineKeyboardButton("Back to Menu", callback_data="back_to_menu")]]
    else:
        text += "Available items:\n\n"

        keyboard = []
        for item in items:
            item_id, name, description, price, image_filename, stock, available = item

            # Format stock display
            if stock == -1:
                stock_text = ""
            elif stock == 0:
                stock_text = " [OUT OF STOCK]"
            else:
                stock_text = f" ({stock} left)"

            # Create button text
            button_text = f"{name} - {price} 💰{stock_text}"

            keyboard.append([InlineKeyboardButton(
                button_text,
                callback_data=f"townmall_view_{item_id}"
            )])

        keyboard.append([InlineKeyboardButton("📜 My Purchases", callback_data="townmall_history")])
        keyboard.append([InlineKeyboardButton("Back to Menu", callback_data="back_to_menu")])

    # Handle both photo and text messages
    try:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception:
        # If edit fails (message is a photo), delete and send new text message
        await query.message.delete()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def view_town_mall_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View specific town mall item with image"""
    query = update.callback_query
    await query.answer()

    item_id = int(query.data.split('_')[-1])
    item = db.get_town_mall_item(item_id)

    if not item:
        await query.edit_message_text(
            "❌ Item not found!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Back to Mall", callback_data="town_mall")
            ]])
        )
        return

    item_id, name, description, price, image_filename, stock, available = item

    # Get user's coins
    user_id = update.effective_user.id
    user_data = db.get_user(user_id)
    user_coins = user_data[10] if len(user_data) > 10 else 0

    # Build caption
    caption = f"🏪 {name}\n\n"
    if description:
        caption += f"{description}\n\n"
    caption += f"💰 Price: {price} coins\n"

    # Stock info
    if stock == -1:
        caption += "📦 Stock: Unlimited\n"
    elif stock == 0:
        caption += "📦 Stock: OUT OF STOCK ❌\n"
    else:
        caption += f"📦 Stock: {stock} remaining\n"

    caption += f"\n💵 Your coins: {user_coins}"

    # Build keyboard
    keyboard = []

    if not available:
        keyboard.append([InlineKeyboardButton("❌ Item Not Available", callback_data="townmall_unavailable")])
    elif stock == 0:
        keyboard.append([InlineKeyboardButton("❌ Out of Stock", callback_data="townmall_outofstock")])
    elif user_coins >= price:
        keyboard.append([InlineKeyboardButton(
            f"✅ Buy for {price} coins",
            callback_data=f"townmall_buy_{item_id}"
        )])
    else:
        needed = price - user_coins
        keyboard.append([InlineKeyboardButton(
            f"❌ Need {needed} more coins",
            callback_data="townmall_notenough"
        )])

    keyboard.append([InlineKeyboardButton("« Back to Mall", callback_data="town_mall")])

    # Try to send with image
    if image_filename:
        image_path = os.path.join("images", "townmall", image_filename)

        if os.path.exists(image_path):
            try:
                # Delete text message and send photo message
                await query.message.delete()
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=open(image_path, 'rb'),
                    caption=caption,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return
            except Exception as e:
                # If image send fails, fall back to text
                print(f"Failed to send image {image_path}: {e}")

    # Fallback: send as text message
    await query.edit_message_text(caption, reply_markup=InlineKeyboardMarkup(keyboard))


async def buy_town_mall_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Purchase item from town mall"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    item_id = int(query.data.split('_')[-1])

    # Get item for announcement
    item = db.get_town_mall_item(item_id)
    if not item:
        await query.edit_message_text(
            "❌ Item not found!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("« Back to Mall", callback_data="town_mall")
            ]])
        )
        return

    item_name = item[1]
    item_price = item[3]

    # Attempt purchase
    success, message = db.purchase_town_mall_item(user_id, item_id)

    if success:
        # Get updated user coins
        user_data = db.get_user(user_id)
        user_coins = user_data[10] if len(user_data) > 10 else 0
        user_name = user_data[2] or user_data[1] or f"User {user_id}"

        text = f"✅ {message}\n\n"
        text += f"💰 Remaining coins: {user_coins}\n\n"
        text += "The item will be delivered soon!"

        # Send group announcement
        group_id = user_data[3]
        if group_id:
            announcement = (
                f"🛍 Town Mall Purchase!\n\n"
                f"👤 {user_name} bought:\n"
                f"🏪 {item_name}\n"
                f"💰 Price: {item_price} coins"
            )
            await send_group_announcement(context, group_id, announcement)

        keyboard = [
            [InlineKeyboardButton("🏪 Continue Shopping", callback_data="town_mall")],
            [InlineKeyboardButton("Back to Menu", callback_data="back_to_menu")]
        ]
    else:
        text = f"❌ {message}"
        keyboard = [
            [InlineKeyboardButton("« Back to Item", callback_data=f"townmall_view_{item_id}")],
            [InlineKeyboardButton("« Back to Mall", callback_data="town_mall")]
        ]

    # Handle both photo and text messages
    try:
        await query.message.delete()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except:
        # Fallback if delete fails (message is already text)
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def town_mall_purchase_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's town mall purchase history"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    purchases = db.get_user_town_mall_purchases(user_id)

    text = "📜 Your Town Mall Purchases\n\n"

    if not purchases:
        text += "You haven't bought anything from Town Mall yet.\n\n"
        text += "Start shopping to see your purchase history!"
    else:
        from datetime import datetime

        total_spent = sum(p[1] for p in purchases)
        text += f"Total items bought: {len(purchases)}\n"
        text += f"Total spent: {total_spent} coins\n\n"
        text += "Recent purchases:\n\n"

        for item_name, price_paid, purchased_at in purchases[:10]:  # Show last 10
            # Parse and format date
            try:
                dt = datetime.strptime(purchased_at, '%Y-%m-%d %H:%M:%S')
                date_str = dt.strftime('%d %b %Y')
            except:
                date_str = purchased_at.split()[0]

            text += f"• {item_name} - {price_paid} 💰\n"
            text += f"  📅 {date_str}\n\n"

    keyboard = [
        [InlineKeyboardButton("« Back to Mall", callback_data="town_mall")],
        [InlineKeyboardButton("Back to Menu", callback_data="back_to_menu")]
    ]

    # Handle both photo and text messages
    try:
        await query.message.delete()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except:
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def town_mall_dummy_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Dummy callback for info buttons (no action needed)"""
    query = update.callback_query
    await query.answer()
