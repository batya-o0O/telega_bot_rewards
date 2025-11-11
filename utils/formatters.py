"""
Text formatting utilities
"""

from database import POINT_TYPES


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
