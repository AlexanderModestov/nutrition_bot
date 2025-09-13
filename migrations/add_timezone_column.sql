-- Migration: Add timezone column to users table
-- Date: 2025-09-06
-- Description: Add timezone support for personalized notifications

-- Add timezone column with default UTC
ALTER TABLE users ADD COLUMN IF NOT EXISTS timezone VARCHAR(10) DEFAULT 'UTC';

-- Add comment for documentation
COMMENT ON COLUMN users.timezone IS 'User timezone in format UTC, UTC+1, UTC-5, etc.';

-- Verify the column was added
SELECT column_name, data_type, column_default 
FROM information_schema.columns 
WHERE table_name = 'users' AND column_name = 'timezone';