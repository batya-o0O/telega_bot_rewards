"""
Group announcement utilities
"""

import logging
from telegram.ext import ContextTypes
from database import Database

logger = logging.getLogger(__name__)
db = Database()


async def send_group_announcement(context: ContextTypes.DEFAULT_TYPE, group_id: int, message: str):
    """Send an announcement to the group chat if configured"""
    chat_id = db.get_group_chat_id(group_id)
    if chat_id:
        try:
            await context.bot.send_message(chat_id=chat_id, text=message)
        except Exception as e:
            logger.warning(f"Could not send announcement to group chat {chat_id}: {e}")
