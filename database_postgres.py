"""
PostgreSQL/Supabase database adapter for Telegram Rewards Bot

This is a drop-in replacement for database.py that uses PostgreSQL instead of SQLite.
Compatible with Supabase, Railway PostgreSQL, or any PostgreSQL database.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
from datetime import datetime
from typing import List, Optional, Tuple, Dict
import os

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
    def __init__(self, connection_string: str = None):
        """
        Initialize PostgreSQL connection.

        Args:
            connection_string: PostgreSQL connection string.
                              If None, reads from DATABASE_URL environment variable.
        """
        if connection_string is None:
            connection_string = os.getenv('DATABASE_URL')
            if not connection_string:
                raise ValueError("DATABASE_URL environment variable not set")

        # Create connection pool for better performance
        self.connection_pool = psycopg2.pool.SimpleConnectionPool(
            1, 20,  # min and max connections
            connection_string
        )

        self.init_db()

    def get_connection(self):
        """Get a connection from the pool"""
        return self.connection_pool.getconn()

    def return_connection(self, conn):
        """Return connection to the pool"""
        self.connection_pool.putconn(conn)

    def init_db(self):
        """Initialize database with all required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            # Groups table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS groups (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    group_chat_id BIGINT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Users table - with typed points and coins
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    telegram_id BIGINT PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    group_id INTEGER REFERENCES groups(id),
                    points_physical INTEGER DEFAULT 0,
                    points_arts INTEGER DEFAULT 0,
                    points_food_related INTEGER DEFAULT 0,
                    points_educational INTEGER DEFAULT 0,
                    points_other INTEGER DEFAULT 0,
                    coins INTEGER DEFAULT 0,
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Habits table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS habits (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(telegram_id),
                    name TEXT NOT NULL,
                    point_type TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Habit completions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS habit_completions (
                    id SERIAL PRIMARY KEY,
                    habit_id INTEGER REFERENCES habits(id),
                    user_id BIGINT REFERENCES users(telegram_id),
                    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    points_earned INTEGER DEFAULT 1
                )
            ''')

            # Medals table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS medals (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(telegram_id),
                    habit_id INTEGER REFERENCES habits(id),
                    habit_name TEXT NOT NULL,
                    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, habit_id)
                )
            ''')

            # Rewards table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS rewards (
                    id SERIAL PRIMARY KEY,
                    owner_id BIGINT REFERENCES users(telegram_id),
                    name TEXT NOT NULL,
                    price INTEGER NOT NULL,
                    point_type TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Reward purchases table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reward_purchases (
                    id SERIAL PRIMARY KEY,
                    reward_id INTEGER REFERENCES rewards(id),
                    buyer_id BIGINT REFERENCES users(telegram_id),
                    seller_id BIGINT REFERENCES users(telegram_id),
                    price INTEGER NOT NULL,
                    point_type TEXT NOT NULL,
                    purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Town Mall items table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS townmall_items (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    price INTEGER NOT NULL,
                    stock INTEGER DEFAULT -1,
                    photo_file_id TEXT,
                    sponsor_id BIGINT REFERENCES users(telegram_id),
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Town Mall purchases table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS townmall_purchases (
                    id SERIAL PRIMARY KEY,
                    item_id INTEGER REFERENCES townmall_items(id),
                    buyer_id BIGINT REFERENCES users(telegram_id),
                    price INTEGER NOT NULL,
                    purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Confirmations table for group chat setup
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS setgroupchat_confirmations (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT REFERENCES users(telegram_id),
                    group_id INTEGER REFERENCES groups(id),
                    chat_id BIGINT NOT NULL,
                    chat_title TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL
                )
            ''')

            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_group_id ON users(group_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_habits_user_id ON habits(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_completions_habit_id ON habit_completions(habit_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_completions_user_id ON habit_completions(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_rewards_owner_id ON rewards(owner_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_townmall_sponsor_id ON townmall_items(sponsor_id)')

            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            self.return_connection(conn)

    # User methods
    def add_user(self, telegram_id: int, username: str = None, first_name: str = None):
        """Add a new user or update existing user info"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (telegram_id, username, first_name)
                VALUES (%s, %s, %s)
                ON CONFLICT (telegram_id)
                DO UPDATE SET username = EXCLUDED.username, first_name = EXCLUDED.first_name
            ''', (telegram_id, username, first_name))
            conn.commit()
        finally:
            cursor.close()
            self.return_connection(conn)

    def get_user(self, telegram_id: int) -> Optional[Tuple]:
        """Get user by telegram ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT * FROM users WHERE telegram_id = %s', (telegram_id,))
            return cursor.fetchone()
        finally:
            cursor.close()
            self.return_connection(conn)

    def update_user_group(self, telegram_id: int, group_id: int):
        """Update user's group"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE users SET group_id = %s WHERE telegram_id = %s',
                         (group_id, telegram_id))
            conn.commit()
        finally:
            cursor.close()
            self.return_connection(conn)

    def get_user_points(self, telegram_id: int) -> Dict[str, int]:
        """Get all point types for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT points_physical, points_arts, points_food_related,
                       points_educational, points_other, coins
                FROM users WHERE telegram_id = %s
            ''', (telegram_id,))
            result = cursor.fetchone()
            if result:
                return {
                    'physical': result[0],
                    'arts': result[1],
                    'food_related': result[2],
                    'educational': result[3],
                    'other': result[4],
                    'coins': result[5]
                }
            return {pt: 0 for pt in POINT_TYPES.keys() if pt != 'any'}
        finally:
            cursor.close()
            self.return_connection(conn)

    def update_user_points(self, telegram_id: int, point_type: str, amount: int):
        """Add points to user (can be negative for spending)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            column = f'points_{point_type}' if point_type != 'coins' else 'coins'
            cursor.execute(f'''
                UPDATE users
                SET {column} = {column} + %s
                WHERE telegram_id = %s
            ''', (amount, telegram_id))
            conn.commit()
        finally:
            cursor.close()
            self.return_connection(conn)

    # Group methods
    def create_group(self, name: str) -> int:
        """Create a new group and return its ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO groups (name) VALUES (%s) RETURNING id', (name,))
            group_id = cursor.fetchone()[0]
            conn.commit()
            return group_id
        finally:
            cursor.close()
            self.return_connection(conn)

    def get_group(self, group_id: int) -> Optional[Tuple]:
        """Get group by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT * FROM groups WHERE id = %s', (group_id,))
            return cursor.fetchone()
        finally:
            cursor.close()
            self.return_connection(conn)

    def get_group_by_name(self, name: str) -> Optional[Tuple]:
        """Get group by name"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT * FROM groups WHERE name = %s', (name,))
            return cursor.fetchone()
        finally:
            cursor.close()
            self.return_connection(conn)

    def get_group_members(self, group_id: int) -> List[Tuple]:
        """Get all members of a group"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT * FROM users WHERE group_id = %s', (group_id,))
            return cursor.fetchall()
        finally:
            cursor.close()
            self.return_connection(conn)

    def update_group_chat(self, group_id: int, chat_id: int):
        """Update group's chat ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE groups SET group_chat_id = %s WHERE id = %s',
                         (chat_id, group_id))
            conn.commit()
        finally:
            cursor.close()
            self.return_connection(conn)

    # Habit methods
    def add_habit(self, user_id: int, name: str, point_type: str) -> int:
        """Add a new habit and return its ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO habits (user_id, name, point_type)
                VALUES (%s, %s, %s) RETURNING id
            ''', (user_id, name, point_type))
            habit_id = cursor.fetchone()[0]
            conn.commit()
            return habit_id
        finally:
            cursor.close()
            self.return_connection(conn)

    def get_user_habits(self, user_id: int) -> List[Tuple]:
        """Get all active habits for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT * FROM habits
                WHERE user_id = %s AND is_active = TRUE
                ORDER BY created_at
            ''', (user_id,))
            return cursor.fetchall()
        finally:
            cursor.close()
            self.return_connection(conn)

    def get_habit(self, habit_id: int) -> Optional[Tuple]:
        """Get habit by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT * FROM habits WHERE id = %s', (habit_id,))
            return cursor.fetchone()
        finally:
            cursor.close()
            self.return_connection(conn)

    def complete_habit(self, habit_id: int, user_id: int, completed_at: datetime = None):
        """Mark habit as completed and award points"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Get habit info
            cursor.execute('SELECT point_type FROM habits WHERE id = %s', (habit_id,))
            habit = cursor.fetchone()
            if not habit:
                return

            point_type = habit[0]

            # Record completion
            if completed_at:
                cursor.execute('''
                    INSERT INTO habit_completions (habit_id, user_id, completed_at, points_earned)
                    VALUES (%s, %s, %s, 1)
                ''', (habit_id, user_id, completed_at))
            else:
                cursor.execute('''
                    INSERT INTO habit_completions (habit_id, user_id, points_earned)
                    VALUES (%s, %s, 1)
                ''', (habit_id, user_id))

            # Award points
            column = f'points_{point_type}'
            cursor.execute(f'''
                UPDATE users
                SET {column} = {column} + 1
                WHERE telegram_id = %s
            ''', (user_id,))

            conn.commit()
        finally:
            cursor.close()
            self.return_connection(conn)

    def delete_habit(self, habit_id: int):
        """Soft delete a habit"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE habits SET is_active = FALSE WHERE id = %s', (habit_id,))
            conn.commit()
        finally:
            cursor.close()
            self.return_connection(conn)

    def update_habit(self, habit_id: int, name: str, point_type: str):
        """Update habit name and point type"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE habits
                SET name = %s, point_type = %s
                WHERE id = %s
            ''', (name, point_type, habit_id))
            conn.commit()
        finally:
            cursor.close()
            self.return_connection(conn)

    def check_habit_completed_today(self, habit_id: int, user_id: int, check_date: datetime = None) -> bool:
        """Check if habit was completed on a specific date"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if check_date is None:
                check_date = datetime.now()

            cursor.execute('''
                SELECT COUNT(*) FROM habit_completions
                WHERE habit_id = %s AND user_id = %s
                AND DATE(completed_at) = DATE(%s)
            ''', (habit_id, user_id, check_date))

            count = cursor.fetchone()[0]
            return count > 0
        finally:
            cursor.close()
            self.return_connection(conn)

    def get_habit_streak(self, habit_id: int, user_id: int) -> int:
        """Calculate current streak for a habit"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT DATE(completed_at) as completion_date
                FROM habit_completions
                WHERE habit_id = %s AND user_id = %s
                ORDER BY completed_at DESC
            ''', (habit_id, user_id))

            completions = cursor.fetchall()
            if not completions:
                return 0

            from datetime import timedelta
            today = datetime.now().date()
            streak = 0
            expected_date = today

            for (completion_date,) in completions:
                if completion_date == expected_date:
                    streak += 1
                    expected_date -= timedelta(days=1)
                elif completion_date < expected_date:
                    break

            return streak
        finally:
            cursor.close()
            self.return_connection(conn)

    # Medal methods
    def award_medal(self, user_id: int, habit_id: int, habit_name: str):
        """Award a medal to user for 30-day streak"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO medals (user_id, habit_id, habit_name)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, habit_id) DO NOTHING
            ''', (user_id, habit_id, habit_name))
            conn.commit()
        finally:
            cursor.close()
            self.return_connection(conn)

    def get_user_medals(self, user_id: int) -> List[Tuple]:
        """Get all medals earned by user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT * FROM medals
                WHERE user_id = %s
                ORDER BY earned_at DESC
            ''', (user_id,))
            return cursor.fetchall()
        finally:
            cursor.close()
            self.return_connection(conn)

    # Reward methods
    def add_reward(self, owner_id: int, name: str, price: int, point_type: str) -> int:
        """Add a new reward"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO rewards (owner_id, name, price, point_type)
                VALUES (%s, %s, %s, %s) RETURNING id
            ''', (owner_id, name, price, point_type))
            reward_id = cursor.fetchone()[0]
            conn.commit()
            return reward_id
        finally:
            cursor.close()
            self.return_connection(conn)

    def get_user_rewards(self, owner_id: int) -> List[Tuple]:
        """Get all active rewards owned by user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT * FROM rewards
                WHERE owner_id = %s AND is_active = TRUE
                ORDER BY price ASC
            ''', (owner_id,))
            return cursor.fetchall()
        finally:
            cursor.close()
            self.return_connection(conn)

    def get_all_group_rewards(self, group_id: int) -> List[Tuple]:
        """Get all rewards from all users in a group, sorted by price"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT r.*, u.first_name, u.username
                FROM rewards r
                JOIN users u ON r.owner_id = u.telegram_id
                WHERE u.group_id = %s AND r.is_active = TRUE
                ORDER BY r.price ASC
            ''', (group_id,))
            return cursor.fetchall()
        finally:
            cursor.close()
            self.return_connection(conn)

    def get_reward(self, reward_id: int) -> Optional[Tuple]:
        """Get reward by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT * FROM rewards WHERE id = %s', (reward_id,))
            return cursor.fetchone()
        finally:
            cursor.close()
            self.return_connection(conn)

    def delete_reward(self, reward_id: int):
        """Soft delete a reward"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE rewards SET is_active = FALSE WHERE id = %s', (reward_id,))
            conn.commit()
        finally:
            cursor.close()
            self.return_connection(conn)

    def update_reward(self, reward_id: int, name: str = None, price: int = None):
        """Update reward name and/or price"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if name is not None and price is not None:
                cursor.execute('UPDATE rewards SET name = %s, price = %s WHERE id = %s',
                             (name, price, reward_id))
            elif name is not None:
                cursor.execute('UPDATE rewards SET name = %s WHERE id = %s',
                             (name, reward_id))
            elif price is not None:
                cursor.execute('UPDATE rewards SET price = %s WHERE id = %s',
                             (price, reward_id))
            conn.commit()
        finally:
            cursor.close()
            self.return_connection(conn)

    def buy_reward(self, reward_id: int, buyer_id: int):
        """Process reward purchase"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Get reward info
            cursor.execute('SELECT owner_id, price, point_type FROM rewards WHERE id = %s',
                         (reward_id,))
            reward = cursor.fetchone()
            if not reward:
                return False

            seller_id, price, point_type = reward

            # Deduct points from buyer
            column = f'points_{point_type}'
            cursor.execute(f'''
                UPDATE users
                SET {column} = {column} - %s
                WHERE telegram_id = %s
            ''', (price, buyer_id))

            # Add points to seller
            cursor.execute(f'''
                UPDATE users
                SET {column} = {column} + %s
                WHERE telegram_id = %s
            ''', (price, seller_id))

            # Record purchase
            cursor.execute('''
                INSERT INTO reward_purchases (reward_id, buyer_id, seller_id, price, point_type)
                VALUES (%s, %s, %s, %s, %s)
            ''', (reward_id, buyer_id, seller_id, price, point_type))

            conn.commit()
            return True
        except Exception:
            conn.rollback()
            return False
        finally:
            cursor.close()
            self.return_connection(conn)

    # Town Mall methods
    def add_townmall_item(self, name: str, price: int, stock: int, sponsor_id: int,
                          photo_file_id: str = None) -> int:
        """Add new Town Mall item"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO townmall_items (name, price, stock, sponsor_id, photo_file_id)
                VALUES (%s, %s, %s, %s, %s) RETURNING id
            ''', (name, price, stock, sponsor_id, photo_file_id))
            item_id = cursor.fetchone()[0]
            conn.commit()
            return item_id
        finally:
            cursor.close()
            self.return_connection(conn)

    def get_townmall_items(self) -> List[Tuple]:
        """Get all active Town Mall items"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT * FROM townmall_items
                WHERE is_active = TRUE
                ORDER BY price ASC
            ''')
            return cursor.fetchall()
        finally:
            cursor.close()
            self.return_connection(conn)

    def get_townmall_item(self, item_id: int) -> Optional[Tuple]:
        """Get Town Mall item by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT * FROM townmall_items WHERE id = %s', (item_id,))
            return cursor.fetchone()
        finally:
            cursor.close()
            self.return_connection(conn)

    def buy_townmall_item(self, item_id: int, buyer_id: int) -> bool:
        """Purchase Town Mall item with coins"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Get item info
            cursor.execute('SELECT price, stock FROM townmall_items WHERE id = %s', (item_id,))
            item = cursor.fetchone()
            if not item:
                return False

            price, stock = item

            # Check stock
            if stock != -1 and stock <= 0:
                return False

            # Deduct coins
            cursor.execute('''
                UPDATE users
                SET coins = coins - %s
                WHERE telegram_id = %s
            ''', (price, buyer_id))

            # Decrease stock if not unlimited
            if stock != -1:
                cursor.execute('''
                    UPDATE townmall_items
                    SET stock = stock - 1
                    WHERE id = %s
                ''', (item_id,))

            # Record purchase
            cursor.execute('''
                INSERT INTO townmall_purchases (item_id, buyer_id, price)
                VALUES (%s, %s, %s)
            ''', (item_id, buyer_id, price))

            conn.commit()
            return True
        except Exception:
            conn.rollback()
            return False
        finally:
            cursor.close()
            self.return_connection(conn)

    def update_townmall_item(self, item_id: int, name: str = None, price: int = None,
                            stock: int = None, photo_file_id: str = None):
        """Update Town Mall item"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            updates = []
            values = []

            if name is not None:
                updates.append('name = %s')
                values.append(name)
            if price is not None:
                updates.append('price = %s')
                values.append(price)
            if stock is not None:
                updates.append('stock = %s')
                values.append(stock)
            if photo_file_id is not None:
                updates.append('photo_file_id = %s')
                values.append(photo_file_id)

            if updates:
                values.append(item_id)
                query = f"UPDATE townmall_items SET {', '.join(updates)} WHERE id = %s"
                cursor.execute(query, values)
                conn.commit()
        finally:
            cursor.close()
            self.return_connection(conn)

    def delete_townmall_item(self, item_id: int):
        """Soft delete Town Mall item"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('UPDATE townmall_items SET is_active = FALSE WHERE id = %s', (item_id,))
            conn.commit()
        finally:
            cursor.close()
            self.return_connection(conn)

    # Group chat confirmation methods
    def save_setgroupchat_confirmation(self, user_id: int, group_id: int, chat_id: int,
                                       chat_title: str, expires_at: datetime) -> int:
        """Save group chat setup confirmation"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO setgroupchat_confirmations
                (user_id, group_id, chat_id, chat_title, expires_at)
                VALUES (%s, %s, %s, %s, %s) RETURNING id
            ''', (user_id, group_id, chat_id, chat_title, expires_at))
            confirmation_id = cursor.fetchone()[0]
            conn.commit()
            return confirmation_id
        finally:
            cursor.close()
            self.return_connection(conn)

    def get_setgroupchat_confirmation(self, confirmation_id: int) -> Optional[Tuple]:
        """Get confirmation by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT * FROM setgroupchat_confirmations
                WHERE id = %s AND expires_at > NOW()
            ''', (confirmation_id,))
            return cursor.fetchone()
        finally:
            cursor.close()
            self.return_connection(conn)

    def delete_setgroupchat_confirmation(self, confirmation_id: int):
        """Delete confirmation"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('DELETE FROM setgroupchat_confirmations WHERE id = %s',
                         (confirmation_id,))
            conn.commit()
        finally:
            cursor.close()
            self.return_connection(conn)

    # Statistics methods
    def get_monthly_leaderboard(self, group_id: int, year: int, month: int) -> List[Tuple]:
        """Get leaderboard for a specific month"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT u.telegram_id, u.first_name, u.username,
                       COUNT(hc.id) as completions,
                       SUM(hc.points_earned) as total_points
                FROM users u
                JOIN habit_completions hc ON u.telegram_id = hc.user_id
                WHERE u.group_id = %s
                  AND EXTRACT(YEAR FROM hc.completed_at) = %s
                  AND EXTRACT(MONTH FROM hc.completed_at) = %s
                GROUP BY u.telegram_id, u.first_name, u.username
                ORDER BY total_points DESC, completions DESC
            ''', (group_id, year, month))
            return cursor.fetchall()
        finally:
            cursor.close()
            self.return_connection(conn)

    def close(self):
        """Close all connections in the pool"""
        if hasattr(self, 'connection_pool'):
            self.connection_pool.closeall()
