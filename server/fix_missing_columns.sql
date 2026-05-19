-- ======================================================
-- Migration: Add missing optional columns to fleet_missions table
-- Run this on Render PostgreSQL database
-- ======================================================

-- Add max_speed column if it doesn't exist
ALTER TABLE fleet_missions ADD COLUMN IF NOT EXISTS max_speed numeric(6,2) NOT NULL DEFAULT 0;

-- Add avg_speed column if it doesn't exist
ALTER TABLE fleet_missions ADD COLUMN IF NOT EXISTS avg_speed numeric(6,2) NOT NULL DEFAULT 0;

-- Add compressed_trail column if it doesn't exist
ALTER TABLE fleet_missions ADD COLUMN IF NOT EXISTS compressed_trail jsonb NOT NULL DEFAULT '[]'::jsonb;

-- ======================================================
-- Verify the columns were added
-- ======================================================
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'fleet_missions'
  AND column_name IN ('max_speed', 'avg_speed', 'compressed_trail');

-- ======================================================
-- ROLLBACK (if needed):
-- ALTER TABLE fleet_missions DROP COLUMN IF EXISTS max_speed;
-- ALTER TABLE fleet_missions DROP COLUMN IF EXISTS avg_speed;
-- ALTER TABLE fleet_missions DROP COLUMN IF EXISTS compressed_trail;
-- ======================================================
