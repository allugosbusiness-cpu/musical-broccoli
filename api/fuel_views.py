"""
Fuel Consumption API Views
ViewSets and endpoints for fuel tracking and consumption data
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
import json

from .models import (
    Truck, TruckFuel, FuelConsumption, FuelRefuel, FuelAlert,
    TrackPoint, Route
)
from .serializers import (
    TruckFuelSerializer, FuelConsumptionSerializer, FuelRefuelSerializer,
    FuelAlertSerializer
)
from .fuel_calculator import FuelCalculator


class TruckFuelViewSet(viewsets.ModelViewSet):
    """
    ViewSet for truck fuel information and status.
    
    Actions:
    - list: Get all truck fuel info
    - retrieve: Get fuel info for specific truck
    - update: Update fuel levels
    - calculate_consumption: Calculate fuel consumption
    - log_refuel: Log a refueling event
    - check_fuel_status: Check if fuel level triggers alerts
    """
    queryset = TruckFuel.objects.all()
    serializer_class = TruckFuelSerializer
    lookup_field = 'truck_id'
    
    @action(detail=True, methods=['post'])
    def calculate_consumption(self, request, truck_id=None):
        """
        Calculate fuel consumption for a truck based on recent movement.
        
        Request body:
        {
            "distance_km": float,
            "duration_minutes": int,
            "avg_speed_kmh": float,
            "elevation_gain_m": float,
            "load_percent": float,
            "weather": {
                "rain": bool,
                "wind_speed": float,
                "temperature": float
            }
        }
        """
        try:
            truck_fuel = self.get_object()
            data = request.data
            
            consumption_result = FuelCalculator.calculate_trip_consumption(
                distance_km=float(data.get('distance_km', 0)),
                duration_minutes=float(data.get('duration_minutes', 0)),
                avg_speed_kmh=float(data.get('avg_speed_kmh', 0)),
                total_elevation_gain_m=float(data.get('elevation_gain_m', 0)),
                load_percent=float(data.get('load_percent', 50)),
                vehicle_type=truck_fuel.vehicle_type,
                weather=data.get('weather', {}),
                stops_count=int(data.get('stops_count', 0)),
                stop_duration_minutes=float(data.get('stop_duration_minutes', 10)),
            )
            
            # Update fuel levels
            old_fuel = truck_fuel.current_fuel_liters
            truck_fuel.current_fuel_liters -= consumption_result['total_consumption_liters']
            truck_fuel.current_fuel_liters = max(0, truck_fuel.current_fuel_liters)
            truck_fuel.fuel_efficiency_kmpl = consumption_result['efficiency_kmpl']
            truck_fuel.total_fuel_consumed_liters += consumption_result['total_consumption_liters']
            truck_fuel.total_distance_traveled_km += data.get('distance_km', 0)
            
            # Check fuel status
            fuel_percent = truck_fuel.fuel_percentage()
            truck_fuel.is_low_fuel = fuel_percent <= truck_fuel.warning_level_percent
            truck_fuel.is_critical_fuel = fuel_percent <= truck_fuel.critical_level_percent
            truck_fuel.needs_refuel = truck_fuel.is_critical_fuel
            
            truck_fuel.save()
            
            # Create fuel consumption record
            FuelConsumption.objects.create(
                truck=truck_fuel.truck,
                consumption_type='segment',
                consumption_liters=consumption_result['total_consumption_liters'],
                distance_km=data.get('distance_km', 0),
                duration_minutes=data.get('duration_minutes', 0),
                avg_speed_kmh=data.get('avg_speed_kmh', 0),
                elevation_gain_m=data.get('elevation_gain_m', 0),
                load_percent=data.get('load_percent', 50),
                weather_conditions=data.get('weather', {}),
                efficiency_kmpl=consumption_result['efficiency_kmpl'],
                efficiency_mpg=consumption_result['efficiency_kmpl'] * 2.352,
                fuel_before_liters=old_fuel,
                fuel_after_liters=truck_fuel.current_fuel_liters,
                consumption_factors=consumption_result['breakdown'],
                start_timestamp=timezone.now(),
                end_timestamp=timezone.now() + timedelta(minutes=data.get('duration_minutes', 0)),
                was_predicted=False,
            )
            
            # Check for alerts
            self._check_and_create_fuel_alerts(truck_fuel)
            
            return Response({
                'success': True,
                'consumption': consumption_result,
                'fuel_status': TruckFuelSerializer(truck_fuel).data,
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def log_refuel(self, request, truck_id=None):
        """
        Log a refueling event.
        
        Request body:
        {
            "amount_liters": float,
            "cost_usd": float,
            "location": string,
            "latitude": float,
            "longitude": float,
            "driver_name": string,
            "driver_notes": string
        }
        """
        try:
            truck_fuel = self.get_object()
            data = request.data
            
            amount_liters = float(data.get('amount_liters', 0))
            old_fuel = truck_fuel.current_fuel_liters
            
            # Update fuel levels
            truck_fuel.current_fuel_liters = min(
                truck_fuel.tank_capacity_liters,
                truck_fuel.current_fuel_liters + amount_liters
            )
            truck_fuel.last_refuel_date = timezone.now()
            truck_fuel.last_refuel_amount = amount_liters
            
            # Recalculate fuel status
            fuel_percent = truck_fuel.fuel_percentage()
            truck_fuel.is_low_fuel = fuel_percent <= truck_fuel.warning_level_percent
            truck_fuel.is_critical_fuel = fuel_percent <= truck_fuel.critical_level_percent
            truck_fuel.needs_refuel = False
            
            truck_fuel.save()
            
            # Log refuel event
            refuel = FuelRefuel.objects.create(
                truck=truck_fuel.truck,
                amount_liters=amount_liters,
                cost_usd=float(data.get('cost_usd', 0)),
                location=data.get('location', ''),
                latitude=data.get('latitude'),
                longitude=data.get('longitude'),
                fuel_before_liters=old_fuel,
                fuel_after_liters=truck_fuel.current_fuel_liters,
                fuel_price_per_liter=float(data.get('cost_usd', 0)) / amount_liters if amount_liters > 0 else 0,
                refuel_timestamp=timezone.now(),
                driver_name=data.get('driver_name', ''),
                driver_notes=data.get('driver_notes', ''),
                fuel_efficiency_kmpl_before=truck_fuel.fuel_efficiency_kmpl,
                distance_since_last_refuel_km=truck_fuel.total_distance_traveled_km,
            )
            
            return Response({
                'success': True,
                'refuel': FuelRefuelSerializer(refuel).data,
                'fuel_status': TruckFuelSerializer(truck_fuel).data,
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def check_fuel_status(self, request, truck_id=None):
        """Check current fuel status and get alerts"""
        try:
            truck_fuel = self.get_object()
            self._check_and_create_fuel_alerts(truck_fuel)
            
            alerts = FuelAlert.objects.filter(
                truck=truck_fuel.truck,
                is_resolved=False
            ).order_by('-created_at')
            
            return Response({
                'fuel_info': TruckFuelSerializer(truck_fuel).data,
                'active_alerts': FuelAlertSerializer(alerts, many=True).data,
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def consumption_history(self, request, truck_id=None):
        """Get fuel consumption history for the truck"""
        try:
            truck_fuel = self.get_object()
            days = int(request.query_params.get('days', 7))
            
            since = timezone.now() - timedelta(days=days)
            consumption_records = FuelConsumption.objects.filter(
                truck=truck_fuel.truck,
                start_timestamp__gte=since
            ).order_by('-start_timestamp')
            
            return Response({
                'truck_id': truck_fuel.truck.id,
                'period_days': days,
                'total_records': consumption_records.count(),
                'total_consumption_liters': sum(c.consumption_liters for c in consumption_records),
                'total_distance_km': sum(c.distance_km for c in consumption_records),
                'avg_efficiency_kmpl': (
                    sum(c.efficiency_kmpl * c.distance_km for c in consumption_records) / 
                    sum(c.distance_km for c in consumption_records)
                    if sum(c.distance_km for c in consumption_records) > 0 else 0
                ),
                'records': FuelConsumptionSerializer(consumption_records, many=True).data,
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def refuel_history(self, request, truck_id=None):
        """Get refueling history for the truck"""
        try:
            truck_fuel = self.get_object()
            days = int(request.query_params.get('days', 30))
            
            since = timezone.now() - timedelta(days=days)
            refuel_records = FuelRefuel.objects.filter(
                truck=truck_fuel.truck,
                refuel_timestamp__gte=since
            ).order_by('-refuel_timestamp')
            
            return Response({
                'truck_id': truck_fuel.truck.id,
                'period_days': days,
                'total_refuels': refuel_records.count(),
                'total_refueled_liters': sum(r.amount_liters for r in refuel_records),
                'total_cost_usd': sum(r.cost_usd for r in refuel_records),
                'avg_refuel_amount': (
                    sum(r.amount_liters for r in refuel_records) / refuel_records.count()
                    if refuel_records.count() > 0 else 0
                ),
                'records': FuelRefuelSerializer(refuel_records, many=True).data,
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def _check_and_create_fuel_alerts(self, truck_fuel):
        """Create fuel alerts if needed"""
        fuel_percent = truck_fuel.fuel_percentage()
        truck = truck_fuel.truck
        
        # Clear old resolved alerts
        FuelAlert.objects.filter(
            truck=truck,
            is_resolved=True,
            resolved_at__lt=timezone.now() - timedelta(days=7)
        ).delete()
        
        # Check for existing unresolved critical alert
        existing_critical = FuelAlert.objects.filter(
            truck=truck,
            alert_type='critical_fuel_level',
            is_resolved=False
        ).first()
        
        # Create new alert if critical
        if truck_fuel.is_critical_fuel and not existing_critical:
            FuelAlert.objects.create(
                truck=truck,
                alert_type='critical_fuel_level',
                severity='critical',
                message=f'CRITICAL: Fuel level at {fuel_percent:.1f}%. Refuel immediately!',
                current_fuel_liters=truck_fuel.current_fuel_liters,
                current_fuel_percent=fuel_percent,
                estimated_range_km=truck_fuel.estimated_range_km(),
            )
        
        # Check for existing unresolved low fuel alert
        existing_low = FuelAlert.objects.filter(
            truck=truck,
            alert_type='low_fuel_level',
            is_resolved=False
        ).first()
        
        # Create new alert if low fuel
        if truck_fuel.is_low_fuel and not truck_fuel.is_critical_fuel and not existing_low:
            FuelAlert.objects.create(
                truck=truck,
                alert_type='low_fuel_level',
                severity='warning',
                message=f'Low fuel: {fuel_percent:.1f}% remaining. Consider refueling soon.',
                current_fuel_liters=truck_fuel.current_fuel_liters,
                current_fuel_percent=fuel_percent,
                estimated_range_km=truck_fuel.estimated_range_km(),
            )
        
        # Resolve alerts if fuel is replenished
        if not truck_fuel.is_low_fuel:
            FuelAlert.objects.filter(
                truck=truck,
                alert_type__in=['critical_fuel_level', 'low_fuel_level'],
                is_resolved=False
            ).update(
                is_resolved=True,
                resolved_at=timezone.now(),
                resolution_notes='Fuel level restored'
            )


class FuelConsumptionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing fuel consumption records"""
    queryset = FuelConsumption.objects.all()
    serializer_class = FuelConsumptionSerializer
    
    def get_queryset(self):
        """Filter by truck if truck_id provided"""
        queryset = FuelConsumption.objects.all()
        truck_id = self.request.query_params.get('truck_id')
        if truck_id:
            queryset = queryset.filter(truck__id=truck_id)
        return queryset.order_by('-start_timestamp')


class FuelAlertViewSet(viewsets.ModelViewSet):
    """ViewSet for fuel alerts"""
    queryset = FuelAlert.objects.all()
    serializer_class = FuelAlertSerializer
    
    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Acknowledge a fuel alert"""
        alert = self.get_object()
        alert.is_acknowledged = True
        alert.save()
        return Response(FuelAlertSerializer(alert).data)
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve a fuel alert"""
        alert = self.get_object()
        alert.is_resolved = True
        alert.resolved_at = timezone.now()
        alert.resolution_notes = request.data.get('notes', '')
        alert.save()
        return Response(FuelAlertSerializer(alert).data)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active (unresolved) fuel alerts"""
        truck_id = request.query_params.get('truck_id')
        queryset = FuelAlert.objects.filter(is_resolved=False)
        
        if truck_id:
            queryset = queryset.filter(truck__id=truck_id)
        
        return Response(FuelAlertSerializer(queryset, many=True).data)


class FuelReportViewSet(viewsets.ViewSet):
    """
    Provides fuel consumption reports and analytics.
    
    Actions:
    - daily_summary: Daily fuel consumption summary
    - monthly_summary: Monthly fuel consumption summary
    - fleet_efficiency: Fleet-wide fuel efficiency metrics
    """
    
    @action(detail=False, methods=['get'])
    def daily_summary(self, request):
        """Get daily fuel consumption summary for all trucks"""
        try:
            today = timezone.now().date()
            trucks = Truck.objects.all()
            
            summary = []
            for truck in trucks:
                consumption = FuelConsumption.objects.filter(
                    truck=truck,
                    start_timestamp__date=today
                )
                
                if consumption.exists():
                    total_consumption = sum(c.consumption_liters for c in consumption)
                    total_distance = sum(c.distance_km for c in consumption)
                    avg_efficiency = (
                        sum(c.efficiency_kmpl * c.distance_km for c in consumption) / total_distance
                        if total_distance > 0 else 0
                    )
                    
                    summary.append({
                        'truck_id': truck.id,
                        'truck_plate': truck.plate,
                        'total_consumption_liters': round(total_consumption, 2),
                        'total_distance_km': round(total_distance, 2),
                        'avg_efficiency_kmpl': round(avg_efficiency, 2),
                        'trips_count': consumption.count(),
                    })
            
            return Response({
                'date': today,
                'total_trucks': len(summary),
                'total_consumption_liters': sum(s['total_consumption_liters'] for s in summary),
                'summary': summary
            })
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def monthly_summary(self, request):
        """Get monthly fuel consumption summary"""
        try:
            month_back = timezone.now() - timedelta(days=30)
            trucks = Truck.objects.all()
            
            summary = []
            for truck in trucks:
                consumption = FuelConsumption.objects.filter(
                    truck=truck,
                    start_timestamp__gte=month_back
                )
                
                refuels = FuelRefuel.objects.filter(
                    truck=truck,
                    refuel_timestamp__gte=month_back
                )
                
                if consumption.exists():
                    total_consumption = sum(c.consumption_liters for c in consumption)
                    total_distance = sum(c.distance_km for c in consumption)
                    avg_efficiency = (
                        sum(c.efficiency_kmpl * c.distance_km for c in consumption) / total_distance
                        if total_distance > 0 else 0
                    )
                    
                    summary.append({
                        'truck_id': truck.id,
                        'truck_plate': truck.plate,
                        'total_consumption_liters': round(total_consumption, 2),
                        'total_distance_km': round(total_distance, 2),
                        'avg_efficiency_kmpl': round(avg_efficiency, 2),
                        'total_refuels': refuels.count(),
                        'total_refuel_cost_usd': round(sum(r.cost_usd for r in refuels), 2),
                    })
            
            return Response({
                'period': 'Last 30 days',
                'total_trucks': len(summary),
                'total_consumption_liters': sum(s['total_consumption_liters'] for s in summary),
                'summary': summary
            })
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def fleet_efficiency(self, request):
        """Get fleet-wide fuel efficiency metrics"""
        try:
            month_back = timezone.now() - timedelta(days=30)
            
            consumption_records = FuelConsumption.objects.filter(
                start_timestamp__gte=month_back,
                consumption_type__in=['segment', 'trip']
            )
            
            if not consumption_records.exists():
                return Response({
                    'error': 'No consumption data available'
                }, status=status.HTTP_204_NO_CONTENT)
            
            total_consumption = sum(c.consumption_liters for c in consumption_records)
            total_distance = sum(c.distance_km for c in consumption_records)
            avg_efficiency = (
                sum(c.efficiency_kmpl * c.distance_km for c in consumption_records) / total_distance
                if total_distance > 0 else 0
            )
            
            return Response({
                'period': 'Last 30 days',
                'total_consumption_liters': round(total_consumption, 2),
                'total_distance_km': round(total_distance, 2),
                'average_efficiency_kmpl': round(avg_efficiency, 2),
                'average_efficiency_mpg': round(avg_efficiency * 2.352, 2),
                'records_count': consumption_records.count(),
            })
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
