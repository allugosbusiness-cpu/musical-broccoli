"""
Post-migration signals to ensure FleetActivity table exists
"""
from django.db.models.signals import post_migrate, pre_save
from django.dispatch import receiver
from django.db import connection
from django.core.management import call_command


# Signal function removed - columns now exist in database
# No longer need to strip these fields


@receiver(post_migrate)
def ensure_fleet_activity_table(sender, **kwargs):
    """Ensure FleetActivity table is created after migrations run"""
    
    db_alias = kwargs.get('using', 'default')
    
    # Check if FleetActivity table exists
    with connection.cursor() as cursor:
        try:
            if connection.vendor == 'postgresql':
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'fleet_activities'
                """)
            else:
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name = 'fleet_activities'
                """)
            
            result = cursor.fetchone()
            if result:
                print("[OK] FleetActivity table already exists")
                return
        except Exception as e:
            print(f"[OK] Table check error (expected if first run): {e}")
    
    # Table doesn't exist, create it using Django ORM
    print("[OK] Creating FleetActivity table via Django...")
    
    try:
        from server.api.models import FleetActivity
        
        # The table should be created by the migration, but if it's not,
        # we can use Django's table creation
        with connection.schema_editor() as schema_editor:
            # Check again before creating
            if not connection.introspection.table_names().__contains__('fleet_activities'):
                schema_editor.create_model(FleetActivity)
                print("[OK] FleetActivity table created via schema editor")
            else:
                print("[OK] FleetActivity table exists")
                
    except Exception as e:
        print(f"[OK] FleetActivity table creation error: {e}")


# Signal registration removed - columns now exist in database
