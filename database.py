import sqlite3
from datetime import datetime
from typing import List, Optional, Tuple

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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                group_id INTEGER,
                points INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (group_id) REFERENCES groups(id)
            )
        ''')

        # Habits table (shared per group)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (group_id) REFERENCES groups(id)
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

        # Rewards table (each user has their own reward shop)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rewards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                price INTEGER NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (owner_id) REFERENCES users(telegram_id)
            )
        ''')

        # Transactions table (track reward purchases)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                buyer_id INTEGER NOT NULL,
                seller_id INTEGER NOT NULL,
                reward_id INTEGER NOT NULL,
                points INTEGER NOT NULL,
                transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (buyer_id) REFERENCES users(telegram_id),
                FOREIGN KEY (seller_id) REFERENCES users(telegram_id),
                FOREIGN KEY (reward_id) REFERENCES rewards(id)
            )
        ''')

        conn.commit()
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
    def add_habit(self, group_id: int, name: str, description: str = "") -> int:
        """Add a new habit to a group"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO habits (group_id, name, description) VALUES (?, ?, ?)',
                      (group_id, name, description))
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

    def update_habit(self, habit_id: int, name: str, description: str = "") -> bool:
        """Update a habit"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE habits SET name = ?, description = ? WHERE id = ?',
                      (name, description, habit_id))
        conn.commit()
        conn.close()
        return True

    def delete_habit(self, habit_id: int) -> bool:
        """Delete a habit and recalculate points for affected users"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Get all users who completed this habit
        cursor.execute('SELECT DISTINCT user_id FROM habit_completions WHERE habit_id = ?', (habit_id,))
        affected_users = [row[0] for row in cursor.fetchall()]

        # Count how many times each user completed this habit
        for user_id in affected_users:
            cursor.execute('SELECT COUNT(*) FROM habit_completions WHERE user_id = ? AND habit_id = ?',
                         (user_id, habit_id))
            count = cursor.fetchone()[0]
            # Subtract those points
            cursor.execute('UPDATE users SET points = points - ? WHERE telegram_id = ?', (count, user_id))

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
        try:
            cursor.execute('''
                INSERT INTO habit_completions (user_id, habit_id, completion_date)
                VALUES (?, ?, ?)
            ''', (user_id, habit_id, date))

            # Award 1 point for completing the habit
            cursor.execute('UPDATE users SET points = points + 1 WHERE telegram_id = ?', (user_id,))
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
        cursor.execute('''
            DELETE FROM habit_completions
            WHERE user_id = ? AND habit_id = ? AND completion_date = ?
        ''', (user_id, habit_id, date))

        if cursor.rowcount > 0:
            # Remove 1 point
            cursor.execute('UPDATE users SET points = points - 1 WHERE telegram_id = ?', (user_id,))
            conn.commit()
            conn.close()
            return True
        conn.close()
        return False

    def get_user_completions_for_month(self, user_id: int, year: int, month: int) -> List[Tuple]:
        """Get all habit completions for a user in a specific month
        Returns: (id, user_id, habit_id, completion_date, habit_name)
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT hc.id, hc.user_id, hc.habit_id, hc.completion_date, h.name as habit_name
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
    def add_reward(self, owner_id: int, name: str, price: int) -> int:
        """Add a new reward to user's shop"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO rewards (owner_id, name, price) VALUES (?, ?, ?)',
                      (owner_id, name, price))
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

        # Get reward price
        cursor.execute('SELECT price, owner_id FROM rewards WHERE id = ? AND is_active = 1', (reward_id,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            return False

        price, owner_id = result

        # Check if buyer has enough points
        cursor.execute('SELECT points FROM users WHERE telegram_id = ?', (buyer_id,))
        buyer_points = cursor.fetchone()[0]

        if buyer_points < price:
            conn.close()
            return False

        # Process transaction
        cursor.execute('UPDATE users SET points = points - ? WHERE telegram_id = ?', (price, buyer_id))
        cursor.execute('UPDATE users SET points = points + ? WHERE telegram_id = ?', (price, seller_id))
        cursor.execute('''
            INSERT INTO transactions (buyer_id, seller_id, reward_id, points)
            VALUES (?, ?, ?, ?)
        ''', (buyer_id, seller_id, reward_id, price))

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

    def recalculate_all_points(self) -> dict:
        """Recalculate points for all users from scratch
        Returns dict with user_id: (old_points, new_points)
        """
        conn = self.get_connection()
        cursor = conn.cursor()

        results = {}

        # Get all users
        cursor.execute('SELECT telegram_id, points FROM users')
        users = cursor.fetchall()

        for user_id, old_points in users:
            # Count habit completions
            cursor.execute('SELECT COUNT(*) FROM habit_completions WHERE user_id = ?', (user_id,))
            habit_points = cursor.fetchone()[0]

            # Calculate points from selling rewards
            cursor.execute('SELECT SUM(points) FROM transactions WHERE seller_id = ?', (user_id,))
            earned = cursor.fetchone()[0] or 0

            # Calculate points spent on buying rewards
            cursor.execute('SELECT SUM(points) FROM transactions WHERE buyer_id = ?', (user_id,))
            spent = cursor.fetchone()[0] or 0

            # New total
            new_points = habit_points + earned - spent

            # Update
            cursor.execute('UPDATE users SET points = ? WHERE telegram_id = ?', (new_points, user_id))

            results[user_id] = (old_points, new_points)

        conn.commit()
        conn.close()
        return results
