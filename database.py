import sqlite3
from datetime import datetime
from typing import List, Optional, Tuple, Dict

# Point types
POINT_TYPES = {
    'physical': '💪',
    'arts': '🎨',
    'food_related': '🍳',
    'educational': '📚',
    'other': '⭐',
    'any': '🌟'
}

class Database:
    def __init__(self, db_path: str = "bot.db"):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        """Initialize database with all required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Groups table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                group_chat_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Users table - now with typed points and coins
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                group_id INTEGER,
                points_physical INTEGER DEFAULT 0,
                points_arts INTEGER DEFAULT 0,
                points_food_related INTEGER DEFAULT 0,
                points_educational INTEGER DEFAULT 0,
                points_other INTEGER DEFAULT 0,
                coins INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (group_id) REFERENCES groups(id)
            )
        ''')

        # Habits table - now with type
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                habit_type TEXT NOT NULL DEFAULT 'other',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (group_id) REFERENCES groups(id),
                CHECK (habit_type IN ('physical', 'arts', 'food_related', 'educational', 'other'))
            )
        ''')

        # Habit completions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS habit_completions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                habit_id INTEGER NOT NULL,
                completion_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, habit_id, completion_date),
                FOREIGN KEY (user_id) REFERENCES users(telegram_id),
                FOREIGN KEY (habit_id) REFERENCES habits(id)
            )
        ''')

        # Rewards table - now with point type
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rewards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                price INTEGER NOT NULL,
                point_type TEXT NOT NULL DEFAULT 'other',
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (owner_id) REFERENCES users(telegram_id),
                CHECK (point_type IN ('physical', 'arts', 'food_related', 'educational', 'other'))
            )
        ''')

        # Transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                buyer_id INTEGER NOT NULL,
                seller_id INTEGER NOT NULL,
                reward_id INTEGER NOT NULL,
                points INTEGER NOT NULL,
                point_type TEXT NOT NULL,
                transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (buyer_id) REFERENCES users(telegram_id),
                FOREIGN KEY (seller_id) REFERENCES users(telegram_id),
                FOREIGN KEY (reward_id) REFERENCES rewards(id)
            )
        ''')

        # Point conversions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS point_conversions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                from_type TEXT NOT NULL,
                to_type TEXT NOT NULL,
                amount_from INTEGER NOT NULL,
                amount_to INTEGER NOT NULL,
                conversion_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(telegram_id)
            )
        ''')

        # Habit streaks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS habit_streaks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                habit_id INTEGER NOT NULL,
                current_streak INTEGER DEFAULT 0,
                best_streak INTEGER DEFAULT 0,
                last_completion_date DATE,
                milestone_7_announced BOOLEAN DEFAULT 0,
                milestone_15_announced BOOLEAN DEFAULT 0,
                milestone_30_announced BOOLEAN DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(telegram_id),
                FOREIGN KEY (habit_id) REFERENCES habits(id),
                UNIQUE(user_id, habit_id)
            )
        ''')

        # Monthly stats table (for tracking leaderboards)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monthly_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                month TEXT NOT NULL,
                points_earned INTEGER DEFAULT 0,
                coins_earned INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(telegram_id),
                UNIQUE(user_id, month)
            )
        ''')

        conn.commit()
        conn.close()

    # Migration helper
    def migrate_from_v1(self):
        """Migrate old database to new schema"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Check if old schema exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'points' in columns and 'points_physical' not in columns:
            print("Migrating database to v2...")

            # Add new point columns
            cursor.execute('ALTER TABLE users ADD COLUMN points_physical INTEGER DEFAULT 0')
            cursor.execute('ALTER TABLE users ADD COLUMN points_arts INTEGER DEFAULT 0')
            cursor.execute('ALTER TABLE users ADD COLUMN points_food_related INTEGER DEFAULT 0')
            cursor.execute('ALTER TABLE users ADD COLUMN points_educational INTEGER DEFAULT 0')
            cursor.execute('ALTER TABLE users ADD COLUMN points_other INTEGER DEFAULT 0')

            # Move old points to 'other' category
            cursor.execute('UPDATE users SET points_other = points')

            # Add habit_type column to habits if not exists
            cursor.execute("PRAGMA table_info(habits)")
            habit_columns = [col[1] for col in cursor.fetchall()]
            if 'habit_type' not in habit_columns:
                cursor.execute('ALTER TABLE habits ADD COLUMN habit_type TEXT NOT NULL DEFAULT "other"')

            # Add point_type column to rewards if not exists
            cursor.execute("PRAGMA table_info(rewards)")
            reward_columns = [col[1] for col in cursor.fetchall()]
            if 'point_type' not in reward_columns:
                cursor.execute('ALTER TABLE rewards ADD COLUMN point_type TEXT NOT NULL DEFAULT "other"')

            # Add point_type column to transactions if not exists
            cursor.execute("PRAGMA table_info(transactions)")
            transaction_columns = [col[1] for col in cursor.fetchall()]
            if 'point_type' not in transaction_columns:
                cursor.execute('ALTER TABLE transactions ADD COLUMN point_type TEXT NOT NULL DEFAULT "other"')

            conn.commit()
            print("Migration complete!")

        conn.close()

    # Group methods
    def create_group(self, name: str) -> int:
        """Create a new group and return its ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO groups (name) VALUES (?)', (name,))
        group_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return group_id

    def get_group(self, group_id: int) -> Optional[Tuple]:
        """Get group by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM groups WHERE id = ?', (group_id,))
        group = cursor.fetchone()
        conn.close()
        return group

    # User methods
    def create_or_update_user(self, telegram_id: int, username: str = None, first_name: str = None):
        """Create or update user information"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (telegram_id, username, first_name)
            VALUES (?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name
        ''', (telegram_id, username, first_name))
        conn.commit()
        conn.close()

    def get_user(self, telegram_id: int) -> Optional[Tuple]:
        """Get user by telegram ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
        user = cursor.fetchone()
        conn.close()
        return user

    def get_user_points(self, telegram_id: int) -> Dict[str, int]:
        """Get user's points by type"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT points_physical, points_arts, points_food_related, points_educational, points_other
            FROM users WHERE telegram_id = ?
        ''', (telegram_id,))
        result = cursor.fetchone()
        conn.close()

        if result:
            return {
                'physical': result[0],
                'arts': result[1],
                'food_related': result[2],
                'educational': result[3],
                'other': result[4]
            }
        return {'physical': 0, 'arts': 0, 'food_related': 0, 'educational': 0, 'other': 0}

    def get_user_total_points(self, telegram_id: int) -> int:
        """Get total points across all types"""
        points = self.get_user_points(telegram_id)
        return sum(points.values())

    def join_group(self, telegram_id: int, group_id: int) -> bool:
        """Add user to a group"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET group_id = ? WHERE telegram_id = ?', (group_id, telegram_id))
        conn.commit()
        conn.close()
        return True

    def get_group_members(self, group_id: int) -> List[Tuple]:
        """Get all members of a group"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE group_id = ?', (group_id,))
        members = cursor.fetchall()
        conn.close()
        return members

    # Habit methods
    def add_habit(self, group_id: int, name: str, habit_type: str, description: str = "") -> int:
        """Add a new habit to a group"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO habits (group_id, name, description, habit_type) VALUES (?, ?, ?, ?)',
                      (group_id, name, description, habit_type))
        habit_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return habit_id

    def get_group_habits(self, group_id: int) -> List[Tuple]:
        """Get all habits for a group"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM habits WHERE group_id = ? ORDER BY id', (group_id,))
        habits = cursor.fetchall()
        conn.close()
        return habits

    def update_habit(self, habit_id: int, name: str, habit_type: str, description: str = "") -> bool:
        """Update a habit"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE habits SET name = ?, description = ?, habit_type = ? WHERE id = ?',
                      (name, description, habit_type, habit_id))
        conn.commit()
        conn.close()
        return True

    def delete_habit(self, habit_id: int) -> bool:
        """Delete a habit and recalculate points for affected users"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Get habit type first
        cursor.execute('SELECT habit_type FROM habits WHERE id = ?', (habit_id,))
        habit = cursor.fetchone()
        if not habit:
            conn.close()
            return False

        habit_type = habit[0]
        point_column = f'points_{habit_type}'

        # Get all users who completed this habit
        cursor.execute('SELECT DISTINCT user_id FROM habit_completions WHERE habit_id = ?', (habit_id,))
        affected_users = [row[0] for row in cursor.fetchall()]

        # Count and subtract points for each user
        for user_id in affected_users:
            cursor.execute('SELECT COUNT(*) FROM habit_completions WHERE user_id = ? AND habit_id = ?',
                         (user_id, habit_id))
            count = cursor.fetchone()[0]
            # Subtract those points from the specific point type
            cursor.execute(f'UPDATE users SET {point_column} = {point_column} - ? WHERE telegram_id = ?',
                         (count, user_id))

        # Delete all completions for this habit
        cursor.execute('DELETE FROM habit_completions WHERE habit_id = ?', (habit_id,))

        # Delete the habit
        cursor.execute('DELETE FROM habits WHERE id = ?', (habit_id,))

        conn.commit()
        conn.close()
        return True

    # Habit completion methods
    def mark_habit_complete(self, user_id: int, habit_id: int, date: str = None) -> bool:
        """Mark a habit as complete for a specific date"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        conn = self.get_connection()
        cursor = conn.cursor()

        # Get habit type
        cursor.execute('SELECT habit_type FROM habits WHERE id = ?', (habit_id,))
        habit = cursor.fetchone()
        if not habit:
            conn.close()
            return False

        habit_type = habit[0]
        point_column = f'points_{habit_type}'

        try:
            cursor.execute('''
                INSERT INTO habit_completions (user_id, habit_id, completion_date)
                VALUES (?, ?, ?)
            ''', (user_id, habit_id, date))

            # Award 1 point of the habit's type
            cursor.execute(f'UPDATE users SET {point_column} = {point_column} + 1 WHERE telegram_id = ?', (user_id,))

            # Track monthly points earned
            current_month = datetime.now().strftime('%Y-%m')
            cursor.execute('''
                INSERT INTO monthly_stats (user_id, month, points_earned)
                VALUES (?, ?, 1)
                ON CONFLICT(user_id, month) DO UPDATE SET
                points_earned = points_earned + 1
            ''', (user_id, current_month))

            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            # Already marked as complete
            conn.close()
            return False

    def unmark_habit_complete(self, user_id: int, habit_id: int, date: str = None) -> bool:
        """Unmark a habit completion"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        conn = self.get_connection()
        cursor = conn.cursor()

        # Get habit type
        cursor.execute('SELECT habit_type FROM habits WHERE id = ?', (habit_id,))
        habit = cursor.fetchone()
        if not habit:
            conn.close()
            return False

        habit_type = habit[0]
        point_column = f'points_{habit_type}'

        cursor.execute('''
            DELETE FROM habit_completions
            WHERE user_id = ? AND habit_id = ? AND completion_date = ?
        ''', (user_id, habit_id, date))

        if cursor.rowcount > 0:
            # Remove 1 point of the habit's type
            cursor.execute(f'UPDATE users SET {point_column} = {point_column} - 1 WHERE telegram_id = ?', (user_id,))

            # Deduct from monthly stats
            current_month = datetime.now().strftime('%Y-%m')
            cursor.execute('''
                UPDATE monthly_stats
                SET points_earned = points_earned - 1
                WHERE user_id = ? AND month = ?
            ''', (user_id, current_month))

            conn.commit()
            conn.close()
            return True
        conn.close()
        return False

    def get_user_completions_for_month(self, user_id: int, year: int, month: int) -> List[Tuple]:
        """Get all habit completions for a user in a specific month
        Returns: (id, user_id, habit_id, completion_date, habit_name, habit_type)
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT hc.id, hc.user_id, hc.habit_id, hc.completion_date, h.name as habit_name, h.habit_type
            FROM habit_completions hc
            JOIN habits h ON hc.habit_id = h.id
            WHERE hc.user_id = ?
            AND strftime('%Y', hc.completion_date) = ?
            AND strftime('%m', hc.completion_date) = ?
            ORDER BY hc.completion_date, h.name
        ''', (user_id, str(year), f'{month:02d}'))
        completions = cursor.fetchall()
        conn.close()
        return completions

    def get_completions_for_date(self, user_id: int, date: str) -> List[int]:
        """Get list of habit IDs completed on a specific date"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT habit_id FROM habit_completions
            WHERE user_id = ? AND completion_date = ?
        ''', (user_id, date))
        completions = [row[0] for row in cursor.fetchall()]
        conn.close()
        return completions

    # Reward methods
    def add_reward(self, owner_id: int, name: str, price: int, point_type: str) -> int:
        """Add a new reward to user's shop"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO rewards (owner_id, name, price, point_type) VALUES (?, ?, ?, ?)',
                      (owner_id, name, price, point_type))
        reward_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return reward_id

    def get_user_rewards(self, owner_id: int) -> List[Tuple]:
        """Get all rewards from a user's shop"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM rewards WHERE owner_id = ? AND is_active = 1', (owner_id,))
        rewards = cursor.fetchall()
        conn.close()
        return rewards

    def delete_reward(self, reward_id: int) -> bool:
        """Delete a reward"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE rewards SET is_active = 0 WHERE id = ?', (reward_id,))
        conn.commit()
        conn.close()
        return True

    def buy_reward(self, buyer_id: int, seller_id: int, reward_id: int) -> bool:
        """Process a reward purchase"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Get reward price and point type
        cursor.execute('SELECT price, owner_id, point_type FROM rewards WHERE id = ? AND is_active = 1', (reward_id,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            return False

        price, owner_id, point_type = result

        # If point_type is 'any', buyer can use any combination of points
        if point_type == 'any':
            # Get all buyer's points
            cursor.execute('''
                SELECT points_physical, points_arts, points_food_related,
                       points_educational, points_other
                FROM users WHERE telegram_id = ?
            ''', (buyer_id,))
            buyer_points = cursor.fetchone()

            if not buyer_points:
                conn.close()
                return False

            total_points = sum(buyer_points)

            if total_points < price:
                conn.close()
                return False

            # Deduct points in order: physical, arts, food_related, educational, other
            remaining = price
            point_types = ['physical', 'arts', 'food_related', 'educational', 'other']
            deductions = {}

            for i, ptype in enumerate(point_types):
                available = buyer_points[i]
                if available > 0 and remaining > 0:
                    deduct = min(available, remaining)
                    deductions[ptype] = deduct
                    remaining -= deduct

            # Apply deductions to buyer
            for ptype, amount in deductions.items():
                cursor.execute(f'UPDATE users SET points_{ptype} = points_{ptype} - ? WHERE telegram_id = ?',
                              (amount, buyer_id))

            # Give COINS to seller (not points!)
            cursor.execute('UPDATE users SET coins = coins + ? WHERE telegram_id = ?',
                          (price, seller_id))

            # Track monthly coins for seller
            from datetime import datetime
            current_month = datetime.now().strftime('%Y-%m')
            cursor.execute('''
                INSERT INTO monthly_stats (user_id, month, coins_earned)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, month) DO UPDATE SET
                coins_earned = coins_earned + ?
            ''', (seller_id, current_month, price, price))

            # Record transaction
            cursor.execute('''
                INSERT INTO transactions (buyer_id, seller_id, reward_id, points, point_type)
                VALUES (?, ?, ?, ?, ?)
            ''', (buyer_id, seller_id, reward_id, price, 'any'))

        else:
            # Original logic for specific point type
            point_column = f'points_{point_type}'

            # Check if buyer has enough points of the correct type
            cursor.execute(f'SELECT {point_column} FROM users WHERE telegram_id = ?', (buyer_id,))
            buyer_points = cursor.fetchone()[0]

            if buyer_points < price:
                conn.close()
                return False

            # Process transaction - buyer loses points, seller gets COINS
            cursor.execute(f'UPDATE users SET {point_column} = {point_column} - ? WHERE telegram_id = ?', (price, buyer_id))
            cursor.execute('UPDATE users SET coins = coins + ? WHERE telegram_id = ?', (price, seller_id))

            # Track monthly coins for seller
            from datetime import datetime
            current_month = datetime.now().strftime('%Y-%m')
            cursor.execute('''
                INSERT INTO monthly_stats (user_id, month, coins_earned)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, month) DO UPDATE SET
                coins_earned = coins_earned + ?
            ''', (seller_id, current_month, price, price))

            cursor.execute('''
                INSERT INTO transactions (buyer_id, seller_id, reward_id, points, point_type)
                VALUES (?, ?, ?, ?, ?)
            ''', (buyer_id, seller_id, reward_id, price, point_type))

        conn.commit()
        conn.close()
        return True

    def buy_reward_custom(self, buyer_id: int, seller_id: int, reward_id: int, allocation: Dict[str, int]) -> bool:
        """Process a reward purchase with custom point allocation (for 'any' type rewards)"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Get reward info
        cursor.execute('SELECT price, owner_id FROM rewards WHERE id = ? AND is_active = 1', (reward_id,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            return False

        price, owner_id = result

        # Verify the allocation totals to the price
        if sum(allocation.values()) != price:
            conn.close()
            return False

        # Verify buyer has enough of each point type
        user_points = self.get_user_points(buyer_id)
        for ptype, amount in allocation.items():
            if user_points.get(ptype, 0) < amount:
                conn.close()
                return False

        # Process the transaction
        for ptype, amount in allocation.items():
            # Deduct from buyer
            cursor.execute(f'UPDATE users SET points_{ptype} = points_{ptype} - ? WHERE telegram_id = ?',
                          (amount, buyer_id))

        # Give COINS to seller (not points!)
        cursor.execute('UPDATE users SET coins = coins + ? WHERE telegram_id = ?',
                      (price, seller_id))

        # Track monthly coins for seller
        from datetime import datetime
        current_month = datetime.now().strftime('%Y-%m')
        cursor.execute('''
            INSERT INTO monthly_stats (user_id, month, coins_earned)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, month) DO UPDATE SET
            coins_earned = coins_earned + ?
        ''', (seller_id, current_month, price, price))

        # Record transaction
        cursor.execute('''
            INSERT INTO transactions (buyer_id, seller_id, reward_id, points, point_type)
            VALUES (?, ?, ?, ?, ?)
        ''', (buyer_id, seller_id, reward_id, price, 'any'))

        conn.commit()
        conn.close()
        return True

    def get_user_transactions(self, user_id: int) -> List[Tuple]:
        """Get all transactions for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT t.*, r.name as reward_name
            FROM transactions t
            JOIN rewards r ON t.reward_id = r.id
            WHERE t.buyer_id = ? OR t.seller_id = ?
            ORDER BY t.transaction_date DESC
        ''', (user_id, user_id))
        transactions = cursor.fetchall()
        conn.close()
        return transactions

    # Point conversion methods
    def convert_points(self, user_id: int, from_type: str, to_type: str, amount: int) -> bool:
        """Convert points from one type to another (2:1 ratio)"""
        if from_type == to_type or from_type not in POINT_TYPES or to_type not in POINT_TYPES:
            return False

        if amount < 2 or amount % 2 != 0:
            return False  # Must be even number and at least 2

        conn = self.get_connection()
        cursor = conn.cursor()

        from_column = f'points_{from_type}'
        to_column = f'points_{to_type}'

        # Check if user has enough points
        cursor.execute(f'SELECT {from_column} FROM users WHERE telegram_id = ?', (user_id,))
        current_points = cursor.fetchone()[0]

        if current_points < amount:
            conn.close()
            return False

        # Perform conversion (2:1 ratio)
        converted_amount = amount // 2

        cursor.execute(f'UPDATE users SET {from_column} = {from_column} - ? WHERE telegram_id = ?', (amount, user_id))
        cursor.execute(f'UPDATE users SET {to_column} = {to_column} + ? WHERE telegram_id = ?', (converted_amount, user_id))

        # Log conversion
        cursor.execute('''
            INSERT INTO point_conversions (user_id, from_type, to_type, amount_from, amount_to)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, from_type, to_type, amount, converted_amount))

        conn.commit()
        conn.close()
        return True

    def get_user_conversions(self, user_id: int) -> List[Tuple]:
        """Get all point conversions for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM point_conversions
            WHERE user_id = ?
            ORDER BY conversion_date DESC
        ''', (user_id,))
        conversions = cursor.fetchall()
        conn.close()
        return conversions

    # Group chat management
    def set_group_chat(self, group_id: int, chat_id: int) -> bool:
        """Link a Telegram group chat to a reward group"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE groups SET group_chat_id = ? WHERE id = ?', (chat_id, group_id))
        conn.commit()
        conn.close()
        return True

    def get_group_chat_id(self, group_id: int) -> Optional[int]:
        """Get the group chat ID for a reward group"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT group_chat_id FROM groups WHERE id = ?', (group_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result and result[0] else None

    def set_setgroupchat_confirmation(self, user_id: int, group_id: int, new_chat_id: int):
        """Store a pending setgroupchat confirmation"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO setgroupchat_confirmations (user_id, group_id, new_chat_id)
            VALUES (?, ?, ?)
        ''', (user_id, group_id, new_chat_id))
        conn.commit()
        conn.close()

    def get_setgroupchat_confirmation(self, user_id: int, group_id: int) -> Optional[int]:
        """Get pending confirmation for setgroupchat"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT new_chat_id FROM setgroupchat_confirmations
            WHERE user_id = ? AND group_id = ?
        ''', (user_id, group_id))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def clear_setgroupchat_confirmation(self, user_id: int, group_id: int):
        """Clear pending confirmation"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM setgroupchat_confirmations
            WHERE user_id = ? AND group_id = ?
        ''', (user_id, group_id))
        conn.commit()
        conn.close()

    # Streak management
    def update_streak(self, user_id: int, habit_id: int, completion_date: str) -> Dict:
        """Update habit streak and return streak info with milestone status"""
        from datetime import datetime, timedelta
        conn = self.get_connection()
        cursor = conn.cursor()

        # Get or create streak record
        cursor.execute('''
            SELECT current_streak, best_streak, last_completion_date,
                   milestone_7_announced, milestone_15_announced, milestone_30_announced
            FROM habit_streaks
            WHERE user_id = ? AND habit_id = ?
        ''', (user_id, habit_id))
        result = cursor.fetchone()

        completion_dt = datetime.strptime(completion_date, '%Y-%m-%d').date()

        if result:
            current_streak, best_streak, last_date_str, m7, m15, m30 = result
            last_date = datetime.strptime(last_date_str, '%Y-%m-%d').date() if last_date_str else None

            # Check if this is a continuation of the streak
            if last_date:
                days_diff = (completion_dt - last_date).days
                if days_diff == 1:
                    # Continuation
                    current_streak += 1
                elif days_diff == 0:
                    # Same day, no change
                    conn.close()
                    return {
                        'current_streak': current_streak,
                        'best_streak': best_streak,
                        'new_milestone': None
                    }
                else:
                    # Broken streak
                    current_streak = 1
                    m7 = m15 = m30 = 0  # Reset milestone announcements
            else:
                current_streak = 1
        else:
            # New streak
            current_streak = 1
            best_streak = 0
            m7 = m15 = m30 = 0

        # Update best streak
        if current_streak > best_streak:
            best_streak = current_streak

        # Check for new milestones
        new_milestone = None
        if current_streak == 30 and not m30:
            new_milestone = 30
            m30 = 1
        elif current_streak == 15 and not m15:
            new_milestone = 15
            m15 = 1
        elif current_streak == 7 and not m7:
            new_milestone = 7
            m7 = 1

        # Update or insert streak record
        cursor.execute('''
            INSERT OR REPLACE INTO habit_streaks
            (user_id, habit_id, current_streak, best_streak, last_completion_date,
             milestone_7_announced, milestone_15_announced, milestone_30_announced)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, habit_id, current_streak, best_streak, completion_date, m7, m15, m30))

        conn.commit()
        conn.close()

        return {
            'current_streak': current_streak,
            'best_streak': best_streak,
            'new_milestone': new_milestone
        }

    def get_habit_streak(self, user_id: int, habit_id: int) -> Optional[Dict]:
        """Get streak info for a specific habit"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT current_streak, best_streak, last_completion_date
            FROM habit_streaks
            WHERE user_id = ? AND habit_id = ?
        ''', (user_id, habit_id))
        result = cursor.fetchone()
        conn.close()

        if result:
            return {
                'current_streak': result[0],
                'best_streak': result[1],
                'last_completion_date': result[2]
            }
        return None

    # Coins management
    def add_coins(self, user_id: int, amount: int) -> bool:
        """Add coins to a user"""
        from datetime import datetime
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('UPDATE users SET coins = coins + ? WHERE telegram_id = ?', (amount, user_id))

        # Track monthly stats
        current_month = datetime.now().strftime('%Y-%m')
        cursor.execute('''
            INSERT INTO monthly_stats (user_id, month, coins_earned)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, month) DO UPDATE SET
            coins_earned = coins_earned + ?
        ''', (user_id, current_month, amount, amount))

        conn.commit()
        conn.close()
        return True

    def get_user_coins(self, user_id: int) -> int:
        """Get user's coin balance"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT coins FROM users WHERE telegram_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0

    def track_points_earned(self, user_id: int, amount: int):
        """Track points earned this month"""
        from datetime import datetime
        conn = self.get_connection()
        cursor = conn.cursor()

        current_month = datetime.now().strftime('%Y-%m')
        cursor.execute('''
            INSERT INTO monthly_stats (user_id, month, points_earned)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, month) DO UPDATE SET
            points_earned = points_earned + ?
        ''', (user_id, current_month, amount, amount))

        conn.commit()
        conn.close()

    def get_monthly_leaderboard(self, group_id: int, month: str = None) -> Dict:
        """Get leaderboards for best shopkeeper (coins) and dungeon master (points)"""
        from datetime import datetime
        if not month:
            month = datetime.now().strftime('%Y-%m')

        conn = self.get_connection()
        cursor = conn.cursor()

        # Get users in this group
        cursor.execute('SELECT telegram_id FROM users WHERE group_id = ?', (group_id,))
        user_ids = [row[0] for row in cursor.fetchall()]

        if not user_ids:
            conn.close()
            return {'shopkeepers': [], 'dungeon_masters': []}

        # Get top shopkeepers (most coins earned)
        placeholders = ','.join('?' * len(user_ids))
        cursor.execute(f'''
            SELECT u.telegram_id, u.first_name, u.username, m.coins_earned
            FROM monthly_stats m
            JOIN users u ON m.user_id = u.telegram_id
            WHERE m.user_id IN ({placeholders}) AND m.month = ?
            ORDER BY m.coins_earned DESC
            LIMIT 3
        ''', user_ids + [month])
        shopkeepers = cursor.fetchall()

        # Get top dungeon masters (most points earned)
        cursor.execute(f'''
            SELECT u.telegram_id, u.first_name, u.username, m.points_earned
            FROM monthly_stats m
            JOIN users u ON m.user_id = u.telegram_id
            WHERE m.user_id IN ({placeholders}) AND m.month = ?
            ORDER BY m.points_earned DESC
            LIMIT 3
        ''', user_ids + [month])
        dungeon_masters = cursor.fetchall()

        conn.close()

        return {
            'shopkeepers': shopkeepers,
            'dungeon_masters': dungeon_masters,
            'month': month
        }

    # Medal methods
    def award_medal(self, user_id: int, habit_id: int) -> bool:
        """Award a medal to a user for completing a habit 30 days in a row"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO medals (user_id, habit_id)
                VALUES (?, ?)
            ''', (user_id, habit_id))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Medal already exists
            return False
        finally:
            conn.close()

    def get_user_medals(self, user_id: int) -> List[Tuple]:
        """Get all medals for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT m.id, m.habit_id, h.name, m.awarded_at
            FROM medals m
            JOIN habits h ON m.habit_id = h.id
            WHERE m.user_id = ?
        ''', (user_id,))
        medals = cursor.fetchall()
        conn.close()
        return medals

    def get_medal_count(self, user_id: int) -> int:
        """Get total number of medals for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM medals WHERE user_id = ?', (user_id,))
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def has_medal_for_habit(self, user_id: int, habit_id: int) -> bool:
        """Check if user has a medal for a specific habit"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM medals
            WHERE user_id = ? AND habit_id = ?
        ''', (user_id, habit_id))
        has_medal = cursor.fetchone()[0] > 0
        conn.close()
        return has_medal

    def get_conversion_rate(self, user_id: int) -> float:
        """Get conversion rate for user based on medal count (2:1 default, 1.5:1 with 3+ medals)"""
        medal_count = self.get_medal_count(user_id)
        return 1.5 if medal_count >= 3 else 2.0

    def check_and_award_group_habit_completion(self, group_id: int, habit_id: int, month: str) -> bool:
        """
        Check if a habit was completed every day of the month by at least one group member.
        If yes, award 10 coins to all members and record the completion.
        Returns True if this is a new completion (announcement needed).
        """
        from datetime import datetime
        import calendar

        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Check if already awarded for this month
            cursor.execute('''
                SELECT COUNT(*) FROM group_habit_completions
                WHERE group_id = ? AND habit_id = ? AND month = ?
            ''', (group_id, habit_id, month))

            if cursor.fetchone()[0] > 0:
                conn.close()
                return False  # Already awarded

            # Parse month (format: YYYY-MM)
            year, month_num = map(int, month.split('-'))
            days_in_month = calendar.monthrange(year, month_num)[1]

            # Check if habit was completed on every day of the month
            cursor.execute('''
                SELECT DISTINCT DATE(completion_date) as day
                FROM habit_completions
                WHERE habit_id = ?
                AND user_id IN (SELECT telegram_id FROM users WHERE group_id = ?)
                AND strftime('%Y-%m', completion_date) = ?
                ORDER BY day
            ''', (habit_id, group_id, month))

            completed_days = {row[0] for row in cursor.fetchall()}

            # Check if all days are covered
            expected_days = {f"{year:04d}-{month_num:02d}-{day:02d}" for day in range(1, days_in_month + 1)}

            if completed_days >= expected_days:
                # Award coins to all group members
                cursor.execute('''
                    UPDATE users
                    SET coins = coins + 10
                    WHERE group_id = ?
                ''', (group_id,))

                # Record completion
                cursor.execute('''
                    INSERT INTO group_habit_completions (group_id, habit_id, month)
                    VALUES (?, ?, ?)
                ''', (group_id, habit_id, month))

                conn.commit()
                conn.close()
                return True  # New completion, announce it

            conn.close()
            return False

        except Exception as e:
            conn.rollback()
            conn.close()
            raise e

    # ==================== Town Mall Methods ====================

    def get_town_mall_items(self, available_only: bool = True):
        """Get all town mall items"""
        conn = self.get_connection()
        cursor = conn.cursor()

        if available_only:
            cursor.execute('''
                SELECT id, name, description, price_coins, image_filename, stock, available
                FROM town_mall_items
                WHERE available = 1
                ORDER BY price_coins ASC
            ''')
        else:
            cursor.execute('''
                SELECT id, name, description, price_coins, image_filename, stock, available
                FROM town_mall_items
                ORDER BY price_coins ASC
            ''')

        items = cursor.fetchall()
        conn.close()
        return items

    def get_town_mall_item(self, item_id: int):
        """Get specific town mall item by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, description, price_coins, image_filename, stock, available
            FROM town_mall_items
            WHERE id = ?
        ''', (item_id,))
        item = cursor.fetchone()
        conn.close()
        return item

    def purchase_town_mall_item(self, user_id: int, item_id: int) -> tuple[bool, str]:
        """
        Purchase item from town mall.
        Returns (success, message)
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Get item details
            cursor.execute('''
                SELECT name, price_coins, stock, available
                FROM town_mall_items
                WHERE id = ?
            ''', (item_id,))

            item = cursor.fetchone()
            if not item:
                conn.close()
                return False, "Item not found"

            item_name, price, stock, available = item

            if not available:
                conn.close()
                return False, "Item is not available"

            # Check stock (stock = -1 means unlimited)
            if stock == 0:
                conn.close()
                return False, "Item is out of stock"

            # Get user's coins
            cursor.execute('SELECT coins FROM users WHERE telegram_id = ?', (user_id,))
            user = cursor.fetchone()
            if not user:
                conn.close()
                return False, "User not found"

            user_coins = user[0]

            if user_coins < price:
                conn.close()
                return False, f"Not enough coins. You have {user_coins}, need {price}"

            # Deduct coins
            cursor.execute('''
                UPDATE users
                SET coins = coins - ?
                WHERE telegram_id = ?
            ''', (price, user_id))

            # Decrease stock (if not unlimited)
            if stock > 0:
                cursor.execute('''
                    UPDATE town_mall_items
                    SET stock = stock - 1
                    WHERE id = ?
                ''', (item_id,))

            # Record purchase
            cursor.execute('''
                INSERT INTO town_mall_purchases (user_id, item_id, item_name, price_paid)
                VALUES (?, ?, ?, ?)
            ''', (user_id, item_id, item_name, price))

            conn.commit()
            conn.close()
            return True, f"Successfully purchased {item_name}!"

        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Purchase failed: {str(e)}"

    def get_user_town_mall_purchases(self, user_id: int):
        """Get user's town mall purchase history"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT item_name, price_paid, purchased_at
            FROM town_mall_purchases
            WHERE user_id = ?
            ORDER BY purchased_at DESC
        ''', (user_id,))
        purchases = cursor.fetchall()
        conn.close()
        return purchases
