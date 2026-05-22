#!/usr/bin/env python
"""
Simple fix to apply the SQL statements directly
"""
print("=== Applying Database Fix ===")

# SQL statements to add missing columns
sql_statements = [
    "ALTER TABLE fleet_missions ADD COLUMN IF NOT EXISTS max_speed numeric(6,2) NOT NULL DEFAULT 0;",
    "ALTER TABLE fleet_missions ADD COLUMN IF NOT EXISTS avg_speed numeric(6,2) NOT NULL DEFAULT 0;",
    "ALTER TABLE fleet_missions ADD COLUMN IF NOT EXISTS compressed_trail jsonb NOT NULL DEFAULT '[]'::jsonb;"
]

print("SQL statements to execute:")
for i, stmt in enumerate(sql_statements, 1):
    print(f"{i}. {stmt}")

print("\n=== Manual Instructions ===")
print("Since we cannot execute the SQL directly, please run these commands manually:")
print("1. Open your database client (pgAdmin, DBeaver, etc.)")
print("2. Connect to your database")
print("3. Execute these SQL statements in order:")
for i, stmt in enumerate(sql_statements, 1):
    print(f"   {i}. {stmt}")
print("4. Verify the columns were added by running:")
print("   SELECT column_name, data_type, is_nullable, column_default")
print("   FROM information_schema.columns")
print("   WHERE table_name = 'fleet_missions'")
print("   AND column_name IN ('max_speed', 'avg_speed', 'compressed_trail');")

print("\n=== Alternative Django Migration ===")
print("If you have Django migrations enabled, you can also:")
print("1. Create a new migration file:")
print("   python manage.py makemissions add_missing_speed_fields")
print("2. Apply the migration:")
print("   python manage.py migrate")

print("\n=== After Fix Verification ===")
print("After applying the fix, test mission creation:")
print("1. Try adding a mission through the web app")
print("2. Check if the error 'column fleet_missions.max_speed does not exist' is resolved")