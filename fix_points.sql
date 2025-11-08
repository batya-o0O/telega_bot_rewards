-- SQL Script to recalculate all user points from scratch
-- This fixes points that became incorrect due to deleted habits or other issues

-- Step 1: Create a temporary table with correct point calculations
CREATE TEMPORARY TABLE correct_points AS
SELECT
    u.telegram_id,
    u.points as old_points,
    COALESCE(
        (SELECT COUNT(*) FROM habit_completions WHERE user_id = u.telegram_id), 0
    ) +
    COALESCE(
        (SELECT SUM(points) FROM transactions WHERE seller_id = u.telegram_id), 0
    ) -
    COALESCE(
        (SELECT SUM(points) FROM transactions WHERE buyer_id = u.telegram_id), 0
    ) as new_points
FROM users u;

-- Step 2: Show what will change
SELECT
    telegram_id,
    old_points,
    new_points,
    (new_points - old_points) as difference
FROM correct_points
WHERE old_points != new_points;

-- Step 3: Update all user points
UPDATE users
SET points = (
    SELECT new_points
    FROM correct_points
    WHERE correct_points.telegram_id = users.telegram_id
);

-- Step 4: Verify the update
SELECT
    telegram_id,
    username,
    points,
    (SELECT COUNT(*) FROM habit_completions WHERE user_id = telegram_id) as habit_completions,
    (SELECT COALESCE(SUM(points), 0) FROM transactions WHERE seller_id = telegram_id) as earned_from_sales,
    (SELECT COALESCE(SUM(points), 0) FROM transactions WHERE buyer_id = telegram_id) as spent_on_purchases
FROM users;

-- Clean up
DROP TABLE correct_points;
