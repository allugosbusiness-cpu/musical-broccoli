"""
Production Hardening - Database Indexes & Performance Optimizations
Applied to trail endpoints and location tracking for scale.
"""
import logging
from django.db import connection, transaction
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta
import json

logger = logging.getLogger(__name__)


@require_http_methods(["POST"])
@csrf_exempt
def apply_production_indexes(request):
    """
    POST /api/v1/production/apply-indexes/
    
    Creates database indexes for production-scale performance.
    Safe to run multiple times - uses IF NOT EXISTS / CREATE INDEX CONCURRENTLY
    
    Indexes created:
    1. fleet_truck_locations (truck_id, timestamp) - for trail queries
    2. fleet_truck_locations (timestamp) - for time-range queries
    3. fleet_activities (truck_id, activity_type, timestamp) - for audit trail
    4. fleet_missions (truck_id, status) - for mission lookups
    5. fleet_missions (driver_id, status) - for driver mission lookups
    """
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                indexes = [
                    # Trail queries: get all locations for a truck in date range
                    """
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS 
                        idx_truck_locations_truck_ts 
                    ON fleet_truck_locations (truck_id, timestamp DESC)
                    """,
                    
                    # Time-range queries: cleanup old data
                    """
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS 
                        idx_truck_locations_ts 
                    ON fleet_truck_locations (timestamp DESC)
                    """,
                    
                    # Audit trail queries
                    """
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS 
                        idx_activities_truck_type_ts 
                    ON fleet_activities (truck_id, activity_type, timestamp DESC)
                    """,
                    
                    # Mission lookups by truck
                    """
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS 
                        idx_missions_truck_status 
                    ON fleet_missions (truck_id, status)
                    """,
                    
                    # Mission lookups by driver
                    """
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS 
                        idx_missions_driver_status 
                    ON fleet_missions (driver_id, status)
                    """,
                    
                    # Activity category queries
                    """
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS 
                        idx_activities_category_ts 
                    ON fleet_activities (activity_category, timestamp DESC)
                    """,
                ]
                
                results = []
                for sql in indexes:
                    try:
                        cursor.execute(sql)
                        results.append({"sql": sql[:80] + "...", "status": "created"})
                    except Exception as e:
                        # PostgreSQL CONCURRENTLY requires outside transaction
                        # Fall back to non-concurrent
                        try:
                            non_current = sql.replace("CONCURRENTLY ", "")
                            cursor.execute(non_current)
                            results.append({"sql": sql[:80] + "...", "status": "created (fallback)"})
                        except Exception as e2:
                            results.append({"sql": sql[:80] + "...", "status": f"failed: {str(e2)[:50]}"})
                
                # Also add composite index for the main trail query
                try:
                    cursor.execute("""
                        CREATE INDEX CONCURRENTLY IF NOT EXISTS 
                            idx_truck_locations_lookup 
                        ON fleet_truck_locations (truck_id, timestamp DESC, latitude, longitude, speed)
                    """)
                    results.append({"sql": "idx_truck_locations_lookup", "status": "created"})
                except Exception:
                    try:
                        cursor.execute("""
                            CREATE INDEX IF NOT EXISTS 
                                idx_truck_locations_lookup 
                            ON fleet_truck_locations (truck_id, timestamp DESC, latitude, longitude, speed)
                        """)
                        results.append({"sql": "idx_truck_locations_lookup", "status": "created (fallback)"})
                    except Exception as e:
                        err_msg = str(e)[:50] if e else "unknown error"
                        results.append({"sql": "idx_truck_locations_lookup", "status": f"skipped: {err_msg}"})
        
        return JsonResponse({
            'status': 'success',
            'message': 'Production indexes applied',
            'results': results
        }, status=200)
        
    except Exception as e:
        logger.error(f"Index creation error: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def cleanup_old_locations(request):
    """
    POST /api/v1/production/cleanup-locations/
    
    Deletes old TruckLocation records older than N days to save storage.
    Only keeps the most recent 1000 points per truck to maintain trail quality.
    
    Request body: { "days": 90, "max_points_per_truck": 1000 }
    """
    try:
        data = json.loads(request.body) if request.body else {}
        days = int(data.get('days', 90))
        max_points = int(data.get('max_points_per_truck', 1000))
        
        cutoff = timezone.now() - timedelta(days=days)
        
        # Get count before deletion
        from .models import TruckLocation, FleetTruck
        
        total_before = TruckLocation.objects.count()
        
        # Delete old records beyond retention period
        deleted_batch, _ = TruckLocation.objects.filter(
            timestamp__lt=cutoff
        ).delete()
        
        # For trucks with too many points, trim to max_points
        trucks = FleetTruck.objects.all()
        trimmed_count = 0
        for truck in trucks:
            # Get IDs of points to keep (most recent max_points)
            keep_ids = TruckLocation.objects.filter(
                truck=truck
            ).order_by('-timestamp').values_list('id', flat=True)[:max_points]
            
            # Delete points not in keep list
            deleted, _ = TruckLocation.objects.filter(
                truck=truck
            ).exclude(id__in=list(keep_ids)).delete()
            trimmed_count += deleted
        
        after = TruckLocation.objects.count()
        
        from .models import FleetActivity
        audit_deleted, _ = FleetActivity.objects.filter(
            timestamp__lt=cutoff,
            activity_category='trail'
        ).delete()
        
        return JsonResponse({
            'status': 'success',
            'records_before': total_before,
            'records_after': after,
            'old_records_deleted': int(deleted_batch or 0),
            'trimmed_records': int(trimmed_count),
            'audit_entries_deleted': int(audit_deleted or 0),
            'retention_days': days,
            'max_points_per_truck': max_points,
        }, status=200)
        
    except Exception as e:
        logger.error(f"Cleanup error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)