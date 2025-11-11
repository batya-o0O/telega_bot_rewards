"""
Reward Shop Handlers

This module contains all handlers related to the reward shop functionality, including:
- Browsing reward shops of group members
- Buying rewards with various payment methods
- Managing personal reward shop (adding/deleting rewards)
- Flexible payment system for 'any' point type rewards
"""

import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from database import Database, POINT_TYPES
from constants import ADDING_REWARD, ADDING_REWARD_TYPE, BUYING_ANY_REWARD
from utils.keyboards import get_main_menu_keyboard, get_reward_point_type_keyboard
from utils.formatters import format_points_display
from utils.announcements import send_group_announcement

logger = logging.getLogger(__name__)
db = Database()


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

    # Calculate total points from typed points
    total_points = sum(user_data[5:10]) if len(user_data) > 9 else 0
    await query.edit_message_text(
        f"Reward Shop\nYour points: {total_points}\n\nSelect a member to view their rewards:",
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
    cursor.execute('SELECT owner_id, name, price, point_type FROM rewards WHERE id = ?', (reward_id,))
    reward = cursor.fetchone()
    conn.close()

    if not reward:
        await query.edit_message_text("Reward not found.")
        return

    seller_id, reward_name, price, point_type = reward

    # If point_type is 'any', let user choose how to pay
    if point_type == 'any':
        # Store reward info for payment flow
        context.user_data['buying_reward_id'] = reward_id
        context.user_data['buying_reward_name'] = reward_name
        context.user_data['buying_reward_price'] = price
        context.user_data['buying_seller_id'] = seller_id
        context.user_data['payment_allocation'] = {}  # Will store {point_type: amount}

        # Show payment selection
        user_points = db.get_user_points(user_id)
        total_points = sum(user_points.values())

        if total_points < price:
            await query.edit_message_text(
                f"Not enough points! You need {price} points but only have {total_points} total.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("Back", callback_data="reward_shop")
                ]])
            )
            return

        text = f"🌟 Flexible Payment for '{reward_name}'\n\n"
        text += f"Total cost: {price} points\n"
        text += f"Your points:\n{format_points_display(user_points)}\n"
        text += f"Total available: {total_points}\n\n"
        text += "Choose how you want to pay:\n"
        text += "Click a point type to allocate points."

        keyboard = []
        for ptype, emoji in POINT_TYPES.items():
            if ptype == 'any':
                continue
            available = user_points.get(ptype, 0)
            if available > 0:
                type_name = ptype.replace('_', ' ').title()
                keyboard.append([InlineKeyboardButton(
                    f"{emoji} {type_name} ({available} available)",
                    callback_data=f"payselect_{ptype}"
                )])

        keyboard.append([InlineKeyboardButton("✅ Confirm Payment (0/{})".format(price), callback_data="payconfirm")])
        keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="reward_shop")])

        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return BUYING_ANY_REWARD

    # Original flow for specific point types
    success = db.buy_reward(user_id, seller_id, reward_id)

    if success:
        # Notify the buyer
        await query.edit_message_text(
            f"Successfully purchased '{reward_name}' for {price} points!\n\n"
            "The seller will fulfill your reward.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Back to Menu", callback_data="back_to_menu")
            ]])
        )

        # Notify the seller
        buyer_name = update.effective_user.first_name or update.effective_user.username or "Someone"
        try:
            await context.bot.send_message(
                chat_id=seller_id,
                text=f"🎉 Great news! {buyer_name} just bought your reward:\n\n"
                     f"'{reward_name}' for {price} points!\n\n"
                     f"Don't forget to fulfill this reward for them."
            )
        except Exception as e:
            logger.warning(f"Could not notify seller {seller_id}: {e}")

        # Announce purchase to group
        user_data = db.get_user(user_id)
        group_id = user_data[3]
        seller_data = db.get_user(seller_id)
        seller_name = seller_data[2] or seller_data[1] or "Someone"

        type_emoji = POINT_TYPES.get(point_type, '⭐')
        type_name = point_type.replace('_', ' ').title()

        announcement = f"💰 Purchase Made!\n\n"
        announcement += f"{buyer_name} bought '{reward_name}' from {seller_name}'s shop\n"
        announcement += f"Price: {price} {type_emoji} {type_name} points"

        await send_group_announcement(context, group_id, announcement)
    else:
        await query.edit_message_text(
            f"Not enough points! You need {price} points.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Back", callback_data="reward_shop")
            ]])
        )


async def payment_select_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Select a point type to allocate for payment"""
    query = update.callback_query
    await query.answer()

    point_type = query.data.replace('payselect_', '')
    user_id = update.effective_user.id
    user_points = db.get_user_points(user_id)

    available = user_points.get(point_type, 0)
    allocated = context.user_data.get('payment_allocation', {}).get(point_type, 0)
    remaining_available = available - allocated

    price = context.user_data.get('buying_reward_price', 0)
    current_total = sum(context.user_data.get('payment_allocation', {}).values())
    remaining_needed = price - current_total

    if remaining_available <= 0:
        await query.answer("No more of this point type available!", show_alert=True)
        return BUYING_ANY_REWARD

    type_emoji = POINT_TYPES.get(point_type, '⭐')
    type_name = point_type.replace('_', ' ').title()

    text = f"How many {type_emoji} {type_name} points?\n\n"
    text += f"Available: {remaining_available}\n"
    text += f"Already allocated: {allocated}\n"
    text += f"Still needed to reach {price}: {remaining_needed}"

    keyboard = []
    # Quick select buttons for common amounts
    for amount in [1, 5, 10, remaining_available, remaining_needed]:
        if amount > 0 and amount <= remaining_available and amount <= remaining_needed:
            keyboard.append([InlineKeyboardButton(
                f"+ {amount}",
                callback_data=f"payamount_{point_type}_{amount}"
            )])

    keyboard.append([InlineKeyboardButton("« Back to payment", callback_data="payback")])

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return BUYING_ANY_REWARD


async def payment_add_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add specified amount of a point type to payment"""
    query = update.callback_query
    await query.answer()

    parts = query.data.split('_')
    point_type = '_'.join(parts[1:-1])  # Handle food_related
    amount = int(parts[-1])

    user_id = update.effective_user.id
    user_points = db.get_user_points(user_id)

    if 'payment_allocation' not in context.user_data:
        context.user_data['payment_allocation'] = {}

    current_allocated = context.user_data['payment_allocation'].get(point_type, 0)
    available = user_points.get(point_type, 0)

    # Check if we can allocate this amount
    if current_allocated + amount > available:
        await query.answer("Not enough points available!", show_alert=True)
        return BUYING_ANY_REWARD

    price = context.user_data.get('buying_reward_price', 0)
    current_total = sum(context.user_data['payment_allocation'].values())

    if current_total + amount > price:
        await query.answer("This would exceed the total cost!", show_alert=True)
        return BUYING_ANY_REWARD

    # Add the amount
    context.user_data['payment_allocation'][point_type] = current_allocated + amount

    # Return to payment selection screen
    return await show_payment_screen(update, context)


async def show_payment_screen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show the payment allocation screen"""
    query = update.callback_query
    user_id = update.effective_user.id

    reward_name = context.user_data.get('buying_reward_name', 'Unknown')
    price = context.user_data.get('buying_reward_price', 0)
    allocation = context.user_data.get('payment_allocation', {})

    user_points = db.get_user_points(user_id)
    total_allocated = sum(allocation.values())

    text = f"🌟 Flexible Payment for '{reward_name}'\n\n"
    text += f"Total cost: {price} points\n"
    text += f"Allocated: {total_allocated}/{price}\n\n"

    if allocation:
        text += "Your payment breakdown:\n"
        for ptype, amount in allocation.items():
            emoji = POINT_TYPES.get(ptype, '⭐')
            pname = ptype.replace('_', ' ').title()
            text += f"  {emoji} {pname}: {amount}\n"
        text += "\n"

    text += "Available points:\n"
    for ptype, emoji in POINT_TYPES.items():
        if ptype == 'any':
            continue
        available = user_points.get(ptype, 0)
        allocated_this = allocation.get(ptype, 0)
        remaining = available - allocated_this
        if available > 0:
            pname = ptype.replace('_', ' ').title()
            text += f"  {emoji} {pname}: {remaining}/{available}\n"

    keyboard = []

    # Show buttons for types with available points
    for ptype, emoji in POINT_TYPES.items():
        if ptype == 'any':
            continue
        available = user_points.get(ptype, 0)
        allocated_this = allocation.get(ptype, 0)
        remaining = available - allocated_this
        if remaining > 0 and total_allocated < price:
            pname = ptype.replace('_', ' ').title()
            keyboard.append([InlineKeyboardButton(
                f"{emoji} {pname} ({remaining} available)",
                callback_data=f"payselect_{ptype}"
            )])

    # Confirm button (enabled only if exact amount)
    if total_allocated == price:
        keyboard.append([InlineKeyboardButton("✅ Confirm Payment", callback_data="payconfirm")])
    else:
        keyboard.append([InlineKeyboardButton(f"⏸ Need {price - total_allocated} more", callback_data="paynoop")])

    # Clear allocation button
    if allocation:
        keyboard.append([InlineKeyboardButton("🔄 Clear allocation", callback_data="payclear")])

    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="reward_shop")])

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return BUYING_ANY_REWARD


async def payment_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear the payment allocation"""
    query = update.callback_query
    await query.answer("Payment cleared!")

    context.user_data['payment_allocation'] = {}
    return await show_payment_screen(update, context)


async def payment_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirm and process the custom payment"""
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    reward_id = context.user_data.get('buying_reward_id')
    reward_name = context.user_data.get('buying_reward_name')
    price = context.user_data.get('buying_reward_price')
    seller_id = context.user_data.get('buying_seller_id')
    allocation = context.user_data.get('payment_allocation', {})

    total_allocated = sum(allocation.values())

    if total_allocated != price:
        await query.answer("Payment amount doesn't match price!", show_alert=True)
        return BUYING_ANY_REWARD

    # Process custom payment
    success = db.buy_reward_custom(user_id, seller_id, reward_id, allocation)

    if success:
        # Show success message
        payment_details = "\n".join([
            f"  {POINT_TYPES.get(ptype, '⭐')} {ptype.replace('_', ' ').title()}: {amount}"
            for ptype, amount in allocation.items()
        ])

        await query.edit_message_text(
            f"✅ Successfully purchased '{reward_name}'!\n\n"
            f"Payment breakdown:\n{payment_details}\n\n"
            "The seller will fulfill your reward.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Back to Menu", callback_data="back_to_menu")
            ]])
        )

        # Notify seller
        buyer_name = update.effective_user.first_name or update.effective_user.username or "Someone"
        try:
            await context.bot.send_message(
                chat_id=seller_id,
                text=f"🎉 Great news! {buyer_name} just bought your reward:\n\n"
                     f"'{reward_name}' for {price} points!\n\n"
                     f"Payment breakdown:\n{payment_details}\n\n"
                     f"Don't forget to fulfill this reward for them."
            )
        except Exception as e:
            logger.warning(f"Could not notify seller {seller_id}: {e}")

        # Announce purchase to group
        user_data = db.get_user(user_id)
        group_id = user_data[3]
        seller_data = db.get_user(seller_id)
        seller_name = seller_data[2] or seller_data[1] or "Someone"

        announcement = f"💰 Purchase Made!\n\n"
        announcement += f"{buyer_name} bought '{reward_name}' from {seller_name}'s shop\n"
        announcement += f"Price: {price} points (any combination)"

        await send_group_announcement(context, group_id, announcement)

        # Clear context
        context.user_data.pop('buying_reward_id', None)
        context.user_data.pop('buying_reward_name', None)
        context.user_data.pop('buying_reward_price', None)
        context.user_data.pop('buying_seller_id', None)
        context.user_data.pop('payment_allocation', None)

        return ConversationHandler.END
    else:
        await query.edit_message_text(
            "❌ Payment failed! Please try again.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("Back", callback_data="reward_shop")
            ]])
        )
        return ConversationHandler.END


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
            reply_markup=get_reward_point_type_keyboard()
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

    point_type = query.data.replace('habittype_', '')  # Extract from "habittype_food_related" or "habittype_any"
    name = context.user_data.get('new_reward_name')
    price = context.user_data.get('new_reward_price')
    user_id = update.effective_user.id

    db.add_reward(user_id, name, price, point_type)

    type_emoji = POINT_TYPES.get(point_type, '⭐')
    type_name = point_type.replace('_', ' ').title()

    # Announce new reward to group
    user_data = db.get_user(user_id)
    group_id = user_data[3]
    user_name = update.effective_user.first_name or update.effective_user.username or "Someone"

    announcement = f"🛍️ New Reward Available!\n\n"
    announcement += f"{user_name} added a new reward to their shop:\n"
    announcement += f"'{name}' - {price} {type_emoji} {type_name} points"

    await send_group_announcement(context, group_id, announcement)

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
