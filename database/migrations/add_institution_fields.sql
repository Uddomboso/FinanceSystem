-- Migration: Add institution fields to accounts table for multi-institution support
-- This allows tracking which bank/institution each account belongs to

-- Add institution_id and institution_name columns if they don't exist
-- Note: SQLite doesn't support IF NOT EXISTS for ALTER TABLE ADD COLUMN directly
-- We'll use a safer approach with a try-catch pattern in Python, but for SQL-only migration:

-- Check if columns exist (SQLite doesn't have IF NOT EXISTS for ALTER TABLE)
-- So we'll add them with a default value and handle errors gracefully
ALTER TABLE accounts ADD COLUMN institution_id TEXT;
ALTER TABLE accounts ADD COLUMN institution_name TEXT;

-- Update existing accounts to have default institution name from bank_name if null
UPDATE accounts 
SET institution_name = bank_name 
WHERE institution_name IS NULL AND bank_name IS NOT NULL;




