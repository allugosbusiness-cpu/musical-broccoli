# Database Schema Fix for Mission Creation Error

## Problem
When trying to add a new mission from the web app, you get this error:
```
column fleet_missions.max_speed does not exist
```

## Root Cause
The `fleet_missions` table is missing three columns:
- `max_speed` (numeric)
- `avg_speed` (numeric) 
- `compressed_trail` (jsonb)

These columns are defined in the Django models but don't exist in the production database.

## Solution

### Option 1: Direct SQL Execution (Recommended)
Execute these SQL statements directly in your database:

```sql
-- Add max_speed column if it doesn't exist
ALTER TABLE fleet_missions ADD COLUMN IF NOT EXISTS max_speed numeric(6,2) NOT NULL DEFAULT 0;

-- Add avg_speed column if it doesn't exist  
ALTER TABLE fleet_missions ADD COLUMN IF NOT EXISTS avg_speed numeric(6,2) NOT NULL DEFAULT 0;

-- Add compressed_trail column if it doesn't exist
ALTER TABLE fleet_missions ADD COLUMN IF NOT EXISTS compressed_trail jsonb NOT NULL DEFAULT '[]'::jsonb;
```

### Option 2: Django Migration
If you have Django migrations set up:

1. Create migration:
```bash
python manage.py makemissions add_missing_speed_fields
```

2. Apply migration:
```bash
python manage.py migrate
```

### Option 3: Use Existing SQL File
The SQL fix is already prepared in `server/fix_missing_columns.sql`. You can execute this file directly.

## Verification
After applying the fix, verify the columns exist:

```sql
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'fleet_missions'
  AND column_name IN ('max_speed', 'avg_speed', 'compressed_trail');
```

## Testing
After applying the fix, test mission creation through the web app. The error should be resolved.

## Why This Happened
The codebase has been updated to include these new fields in the models, but the database schema hasn't been updated to match. This is a common issue when deploying model changes to production databases.

## Files Involved
- `server/api/models.py` - Defines the model with these fields
- `server/fix_missing_columns.sql` - Contains the SQL fix
- `server/api/views.py` - Contains workaround code for missing columns
- `server/api/mission_endpoints.py` - API endpoints for mission management