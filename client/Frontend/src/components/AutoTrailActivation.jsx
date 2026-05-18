import { useEffect, useState } from 'react';
import { getDashboardTrucks, getDashboardMissions } from '../services/api';

/**
 * AutoTrailActivation Component
 * 
 * Monitors truck and mission status to automatically:
 * 1. Activate tracking when truck/driver become enroute
 * 2. Save tracking data to database
 * 3. Deactivate tracking when mission completes
 * 4. Persist all activities, alerts, and routes for historical reference
 */
export default function AutoTrailActivation({ onTrailStatusChange, onMissionEvent }) {
  const [activeTrails, setActiveTrails] = useState({}); // Tracks per truck ID
  const [missions, setMissions] = useState([]);
  const [trucks, setTrucks] = useState([]);

  /**
   * Check all trucks and missions for status changes
   * Automatically activate/deactivate trails based on mission status
   */
  useEffect(() => {
    const checkAndActivateTrails = async () => {
      try {
        // Get current truck and mission data
        const trucksData = await getDashboardTrucks();
        const missionsData = await getDashboardMissions();

        setTrucks(trucksData || []);
        setMissions(missionsData || []);

        // Check for trucks that should have active trails
        const newActiveTrails = { ...activeTrails };
        let trailChanges = false;

        // For each mission, check if it's enroute
        (missionsData || []).forEach(mission => {
          const wasActive = activeTrails[mission.truck_id];
          const isNowActive = mission.status === 'enroute';

          if (isNowActive && !wasActive) {
            // Trail activation event
            console.log(`🟢 TRAIL ACTIVATION: Mission ${mission.identifier} started`);
            newActiveTrails[mission.truck_id] = {
              missionId: mission.id,
              truckId: mission.truck_id,
              startTime: new Date(),
              startLocation: {
                lat: mission.origin_lat,
                lon: mission.origin_lon,
              },
              endLocation: {
                lat: mission.destination_lat,
                lon: mission.destination_lon,
              },
              status: 'active',
              activities: [
                {
                  type: 'MISSION_START',
                  timestamp: new Date().toISOString(),
                  location: {
                    lat: mission.origin_lat,
                    lon: mission.origin_lon,
                  },
                  details: `Mission ${mission.identifier} started`,
                }
              ],
              alerts: [],
              routePoints: [],
            };

            if (onTrailStatusChange) {
              onTrailStatusChange({
                truckId: mission.truck_id,
                missionId: mission.id,
                action: 'ACTIVATE',
                timestamp: new Date().toISOString(),
              });
            }

            if (onMissionEvent) {
              onMissionEvent({
                type: 'MISSION_START',
                missionId: mission.id,
                truckId: mission.truck_id,
                timestamp: new Date().toISOString(),
              });
            }

            trailChanges = true;
          } else if (!isNowActive && wasActive && mission.status === 'completed') {
            // Trail deactivation event - mission completed
            console.log(`🔴 TRAIL DEACTIVATION: Mission ${mission.identifier} completed`);
            
            // Save completed trail to database before clearing
            const completedTrail = activeTrails[mission.truck_id];
            if (completedTrail) {
              // Add completion event
              completedTrail.activities.push({
                type: 'MISSION_COMPLETE',
                timestamp: new Date().toISOString(),
                location: {
                  lat: mission.destination_lat,
                  lon: mission.destination_lon,
                },
                details: `Mission ${mission.identifier} completed`,
              });
              completedTrail.status = 'completed';
              completedTrail.endTime = new Date();

              // Save to database (fire and forget)
              saveMissionTrackingData(mission.id, completedTrail);

              if (onMissionEvent) {
                onMissionEvent({
                  type: 'MISSION_COMPLETE',
                  missionId: mission.id,
                  truckId: mission.truck_id,
                  trailData: completedTrail,
                  timestamp: new Date().toISOString(),
                });
              }
            }

            delete newActiveTrails[mission.truck_id];
            trailChanges = true;
          }
        });

        // Track speed violations and add to active trails
        trucksData?.forEach(truck => {
          if (activeTrails[truck.id] && truck.speed > 100) {
            // Speed violation alert
            activeTrails[truck.id].alerts.push({
              type: 'SPEED_VIOLATION',
              timestamp: new Date().toISOString(),
              location: {
                lat: truck.latitude,
                lon: truck.longitude,
              },
              speed: truck.speed,
              speedLimit: 100,
            });

            if (onMissionEvent) {
              onMissionEvent({
                type: 'SPEED_VIOLATION',
                truckId: truck.id,
                speed: truck.speed,
                timestamp: new Date().toISOString(),
              });
            }
          }
        });

        if (trailChanges) {
          setActiveTrails(newActiveTrails);
        }
      } catch (error) {
        console.error('❌ Trail activation check error:', error);
      }
    };

    // Run check immediately and then every 10 seconds
    checkAndActivateTrails();
    const interval = setInterval(checkAndActivateTrails, 10000);

    return () => clearInterval(interval);
  }, [activeTrails, onTrailStatusChange, onMissionEvent]);

  /**
   * Add GPS point to active trail
   */
  const addGPSPointToTrail = (truckId, lat, lon, speed = 0) => {
    setActiveTrails(prev => {
      if (!prev[truckId]) return prev;

      const updated = { ...prev };
      updated[truckId].routePoints.push({
        latitude: lat,
        longitude: lon,
        speed: speed,
        timestamp: new Date().toISOString(),
      });

      return updated;
    });
  };

  /**
   * Save completed mission tracking data to database
   */
  const saveMissionTrackingData = async (missionId, trailData) => {
    try {
      const response = await fetch(
        `https://pulsetrack-back.onrender.com/api/v1/api-missions/${missionId}/tracking/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            activities: trailData.activities,
            alerts: trailData.alerts,
            routePoints: trailData.routePoints,
            startTime: trailData.startTime,
            endTime: trailData.endTime,
            totalDistance: calculateDistance(trailData.routePoints),
            totalDuration: calculateDuration(trailData.startTime, trailData.endTime),
          }),
        }
      );

      if (response.ok) {
        console.log(`✅ Tracking data saved for mission ${missionId}`);
      } else {
        console.warn(`⚠️ Failed to save tracking data for mission ${missionId}:`, response.status);
      }
    } catch (error) {
      console.error('❌ Error saving tracking data:', error);
    }
  };

  /**
   * Calculate total distance from route points
   */
  const calculateDistance = (routePoints) => {
    if (!routePoints || routePoints.length < 2) return 0;

    let totalDistance = 0;
    for (let i = 0; i < routePoints.length - 1; i++) {
      const lat1 = routePoints[i].latitude;
      const lon1 = routePoints[i].longitude;
      const lat2 = routePoints[i + 1].latitude;
      const lon2 = routePoints[i + 1].longitude;

      // Haversine formula for distance between two points
      const R = 6371; // Earth's radius in kilometers
      const dLat = (lat2 - lat1) * Math.PI / 180;
      const dLon = (lon2 - lon1) * Math.PI / 180;
      const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
                Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
                Math.sin(dLon / 2) * Math.sin(dLon / 2);
      const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
      totalDistance += R * c;
    }

    return Number.isFinite(totalDistance) ? totalDistance.toFixed(2) : '0.00';
  };

  /**
   * Calculate duration between start and end time
   */
  const calculateDuration = (startTime, endTime) => {
    if (!startTime || !endTime) return 0;
    return Math.round((endTime - startTime) / 60000); // Convert to minutes
  };

  // Component returns null - it's a stateful listener/manager
  return null;
}
