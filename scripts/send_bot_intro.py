"""
Send bot introduction/description in batches

This script sends the complete bot description in multiple messages
to avoid Telegram's message length limits.
"""

import asyncio
from send_announcement import send_announcement_to_groups

# Split the description into manageable batches
BATCH_1 = """🤖 *Habit Rewards Bot* - Part 1/5

A gamified habit tracking system with dual economy, marketplace competition, and group achievements!

📊 *Core Features*

*Habit Tracking*
✅ *Daily Habits* - Track habits across 5 types (💪 Physical, 🎨 Arts, 🍽 Food, 📚 Educational, ⭐ Other)
📅 *Yesterday's Habits* - Backdate completions if you forgot to tick before midnight
📈 *Streak Tracking* - Monitor your consistency with daily streaks
📆 *Calendar View* - Visual monthly calendar showing completion history

💎 *Dual Economy System*

*Points* (Habit Currency)
🎯 Earn: Get 1 point per habit completion (by type)
🔄 Convert: Exchange between point types (2:1 ratio)
🛒 Spend: Buy rewards from other users' shops
📊 Track: View all 5 point types separately

*Coins* (Shop Currency)
💰 Earn: Get coins when someone buys from YOUR shop
🏪 Spend: ONLY at Town Mall (official shop)
📈 Strategy: Better shop = more sales = more coins!"""

BATCH_2 = """🤖 *Habit Rewards Bot* - Part 2/5

🔄 *The Economy Flow*
```
Complete Habits → Earn Points → Buy from User Shops
                                        ↓
                              Someone buys YOUR reward
                                        ↓
                                  Earn COINS
                                        ↓
                            Buy from Town Mall
```

*Key Rule:* Points and Coins are separate! You can't convert points to coins - you must run a successful shop!

🛒 *Shopping Features*

*Reward Shop* (User Marketplace)
🎁 *Browse* - See what other group members are selling
💵 *Flexible Pricing* - Sellers set the price and payment type:
  • Specific Type: Pay with exact point type (💪🎨🍽📚⭐)
  • 🌟 Any Type: Pay with ANY combination of your points!
🏪 *Your Shop* - Create rewards and choose payment type
📊 *Earn Coins* - Get coins from each sale!

*Example - "Any" Type Reward:*
Reward: "Movie Ticket" - 50 points (🌟 Any)
You can pay with:
  • 50 Physical points, OR
  • 25 Arts + 25 Food points, OR
  • 10 Physical + 20 Arts + 20 Educational, OR
  • ANY combination totaling 50 points!"""

BATCH_3 = """🤖 *Habit Rewards Bot* - Part 3/5

🏪 *Town Mall* (Premium Shop - Coins Only!)
💰 Exclusive Access - Only coins accepted here
🖼️ Item Images - See photos of real items
📦 Limited Stock - Some items won't last!
📜 Purchase History - Track your Town Mall purchases

*Current Town Mall Items:*
• Гигрометр - 20 coins (10 left)
• Рандомная мягкая игрушка - 40 coins (5 left)
• Рандомная новая настолка с пиндош - 100 coins (3 left)
• Увлажнитель воздуха - 120 coins (5 left)
• Двухместная палатка - 1000 coins (unlimited)

👥 *Group Features*
🏆 Group Creation - Create reward groups and invite friends
📊 *Dual Leaderboards:*
  • 🏪 Best Shopkeepers - Most coins earned from sales
  • ⚔️ Dungeon Masters - Most points earned from habits
👁️ Member Stats - View any member's habit completion history
💬 Telegram Integration - Link chats for group announcements

📈 *Statistics & Reports*
📅 My Stats - Personal monthly habit completion history
🏆 Monthly Leaderboards - Compete in two categories
📊 Group Performance - See who's leading this month
🗓️ Habit Calendars - Visual tracking for each habit
📜 Purchase History - Track Town Mall spending"""

BATCH_4 = """🤖 *Habit Rewards Bot* - Part 4/5

🔔 *Group Announcements*
Real-time notifications in linked Telegram groups:
🔥 Streak milestones (7, 15, 30 days)
🎁 New rewards added to shops
🛍️ Reward purchases
🏪 Town Mall purchases

🎮 *How to Use*
/start - Register and create/join a group
/menu - Access main menu with all features
/setgroupchat - Link Telegram group for announcements
/monthlyreport - Quick access to leaderboards

🎯 *Main Menu*
• My Habits - Today's + Yesterday's habits
• My Stats - Monthly completion history
• Reward Shop - Browse user marketplace (spend points)
• My Rewards Shop - Manage YOUR shop (earn coins!)
• 🏪 Town Mall - Premium shop (spend coins)
• Convert Points - Exchange between point types (2:1)
• Group Info - Members, stats, leaderboards

💡 *Strategy Guide*

*Earning Points*
✅ Complete habits daily to build streaks
🎯 Choose habits you can maintain consistently
📅 Use Yesterday's Habits if you miss a day
🔄 Convert points to the types you need (2:1)"""

BATCH_5 = """🤖 *Habit Rewards Bot* - Part 5/5

*Earning Coins (The Key to Town Mall!)*
🏪 Create Attractive Rewards - Things people actually want
💵 Smart Pricing:
  • 🌟 "Any" Type - More buyers! Easiest to sell!
  • Specific Type - Target users with surplus points
🎨 Offer Variety - Different rewards, different point types
📊 Track Sales - See what sells best

*Pro Tip:* "Any" type rewards sell faster because buyers can pay with whatever points they have!

🏆 *Competition & Gamification*

*Two Ways to Win:*

*Path 1: Habit Master* 🎯
Complete habits consistently → Build long streaks → Earn tons of points → Top the Dungeon Masters leaderboard!

*Path 2: Shop Mogul* 💰
Create irresistible rewards → Price as "Any" for faster sales → Build a thriving shop → Earn massive coins → Top the Best Shopkeepers leaderboard!

*Best Strategy:* Do both!
• Habits give you points to shop
• Shopping builds your coin empire
• Coins unlock Town Mall exclusives

*Perfect for:* Friend groups, families, study groups, fitness communities, creative teams, or anyone wanting to build better habits together!

*The Secret:* Success requires BOTH habit discipline AND shop entrepreneurship. Build habits, create value, earn coins, dominate leaderboards! 🏆"""


async def send_all_batches():
    """Send all 5 batches with delays"""
    batches = [BATCH_1, BATCH_2, BATCH_3, BATCH_4, BATCH_5]

    print("📢 Sending bot introduction in 5 batches...\n")

    for i, batch in enumerate(batches, 1):
        print(f"📤 Sending batch {i}/5...")
        await send_announcement_to_groups(batch, preview=False)

        if i < len(batches):
            print(f"⏳ Waiting 2 seconds before next batch...\n")
            await asyncio.sleep(2)  # Wait 2 seconds between batches

    print("\n✅ All batches sent successfully!")


if __name__ == '__main__':
    try:
        asyncio.run(send_all_batches())
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user. Exiting.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
