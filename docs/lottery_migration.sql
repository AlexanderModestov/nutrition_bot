-- Migration: Add lottery_participated column to users table
-- Date: 2025-12-28
-- Description: Track whether user has participated in New Year lottery

-- Add lottery_participated column with default value false
ALTER TABLE users
ADD COLUMN IF NOT EXISTS lottery_participated BOOLEAN DEFAULT FALSE NOT NULL;

-- Add comment to the column
COMMENT ON COLUMN users.lottery_participated IS 'Indicates if user has participated in New Year lottery (one-time participation)';

-- Optional: Create index for faster lookups (if needed for analytics)
CREATE INDEX IF NOT EXISTS idx_users_lottery_participated
ON users(lottery_participated)
WHERE lottery_participated = TRUE;

-- Verify the change
-- SELECT column_name, data_type, column_default, is_nullable
-- FROM information_schema.columns
-- WHERE table_name = 'users' AND column_name = 'lottery_participated';
