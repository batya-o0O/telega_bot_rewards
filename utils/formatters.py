"""
Text formatting utilities
"""

from database import POINT_TYPES, Database

db = Database()


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


def format_user_name_with_medals(user_id: int, user_name: str) -> str:
    """Format user name with medal emojis based on medal count"""
    medal_count = db.get_medal_count(user_id)
    if medal_count == 0:
        return user_name

    medal_emoji = "🏅" * medal_count
    return f"{user_name} {medal_emoji}"
