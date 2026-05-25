import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  StatusBar,
  Dimensions,
} from 'react-native';
import MapView, { Marker, Polyline, PROVIDER_GOOGLE, Circle } from 'react-native-maps';
import { COLORS, SPACING, SHADOWS, BORDER_RADIUS } from '../config/theme';
import storage from '../utils/storage';
import apiService from '../services/apiService';
import locationService from '../services/locationService';
import API_CONFIG from '../config/api';

const { width, height } = Dimensions.get('window');

const TrackingScreen = ({ navigation, route }) => {
  const mapRef = useRef(null);
  const [currentLocation, setCurrentLocation] = useState(null);
  const [currentSpeed, setCurrentSpeed] = useState(0);
  const [trackingActive, setTrackingActive] = useState(false);
  const [mission, setMission] = useState(route.params?.mission || null);
  const [driverSession, setDriverSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [routeCoords, setRouteCoords] = useState([]);
  const [osrmRouteCoords, setOsrmRouteCoords] = useState([]);
  const [missionStatus, setMissionStatus] = useState('');
  const [autoCompleted, setAutoCompleted] = useState(false);

  useEffect(() => {
    initTracking();
    
    // Update speed more frequently (every 500ms instead of 2s) for responsive UI
    const speedInterval = setInterval(async () => {
      // Get fresh location with latest GPS speed
      const locWithSpeed = await locationService.getCurrentLocationWithSpeed();
      if (locWithSpeed) {
        setCurrentSpeed(locWithSpeed.speed);
        // Also update current location if GPS provided a new fix
        if (locWithSpeed.latitude && locWithSpeed.longitude) {
          setCurrentLocation(locWithSpeed);
        }
      } else {
        // Fallback to cached speed if fresh fetch fails
        setCurrentSpeed(locationService.getCurrentSpeed());
      }
      setTrackingActive(locationService.isTrackingActive());
    }, 500);

    return () => {
      clearInterval(speedInterval);
    };
  }, []);

  const initTracking = async () => {
    try {
      const session = await storage.getDriverSession();
      setDriverSession(session);

      // Load mission from storage if not passed as param
      let currentMission = mission;
      if (!currentMission) {
        currentMission = await storage.getCurrentMission();
        setMission(currentMission);
      }

      // Get current GPS position
      const position = await locationService.getCurrentPosition();
      if (position) {
        setCurrentLocation(position);
      }

      // Build route coordinates if we have origin/destination
      if (currentMission) {
        setMissionStatus(currentMission.status);
        
        // Check if mission is already auto-completed
        if (currentMission.status === 'completed' || currentMission.status === 'delivered') {
          setAutoCompleted(true);
        }
        
        const origin = currentMission.origin || {};
        const destination = currentMission.destination || {};
        const originLat = parseFloat(origin.lat || origin.latitude || 0);
        const originLng = parseFloat(origin.lon || origin.lng || origin.longitude || 0);
        const destLat = parseFloat(destination.lat || destination.latitude || 0);
        const destLng = parseFloat(destination.lon || destination.lng || destination.longitude || 0);

        if (originLat && originLng && destLat && destLng) {
          // Basic straight-line route as fallback
          setRouteCoords([
            { latitude: originLat, longitude: originLng },
            { latitude: destLat, longitude: destLng },
          ]);
          
          // Fetch OSRM-based route from backend for road-following trail
          fetchOsrmRoute(currentMission.id, originLat, originLng, destLat, destLng);
        }
      }

      setLoading(false);

      // Fit map to show both markers
      if (position && currentMission) {
        setTimeout(() => {
          mapRef.current?.fitToSuppliedMarkers(['driver', 'origin', 'destination'], {
            edgePadding: { top: 100, right: 100, bottom: 100, left: 100 },
            animated: true,
          });
        }, 500);
      }
    } catch (error) {
      console.error('Error initializing tracking:', error);
      setLoading(false);
    }
  };

  /**
   * Fetch OSRM road-following route from backend
   * This provides turn-by-turn trail following roads (like Google Maps directions)
   */
  const fetchOsrmRoute = async (missionId, originLat, originLng, destLat, destLng) => {
    try {
      // First try to get route geometry from mission endpoint
      const response = await fetch(
        `${API_CONFIG.baseUrl}/dashboard/missions/${missionId}/route-geometry/`,
        { method: 'GET' }
      );
      
      if (response.ok) {
        const data = await response.json();
        if (data.geometry && data.geometry.coordinates) {
          // GeoJSON uses [lon, lat] format - convert to [lat, lon] for react-native-maps
          const osrmCoords = data.geometry.coordinates.map(coord => ({
            latitude: coord[1],
            longitude: coord[0],
          }));
          setOsrmRouteCoords(osrmCoords);
          console.log(`✅ OSRM route loaded: ${osrmCoords.length} road-following points`);
          return;
        }
      }
      
      // Fallback: compute OSRM route directly  
      console.log('Falling back to direct OSRM route computation');
      const osrmUrl = `https://router.project-osrm.org/route/v1/driving/${originLng},${originLat};${destLng},${destLat}?overview=full&geometries=geojson`;
      const osrmResponse = await fetch(osrmUrl);
      if (osrmResponse.ok) {
        const osrmData = await osrmResponse.json();
        if (osrmData.routes && osrmData.routes[0] && osrmData.routes[0].geometry) {
          const coords = osrmData.routes[0].geometry.coordinates.map(c => ({
            latitude: c[1],
            longitude: c[0],
          }));
          setOsrmRouteCoords(coords);
          console.log(`✅ Direct OSRM route loaded: ${coords.length} road-following points`);
        }
      }
    } catch (error) {
      console.warn('⚠️ Could not fetch OSRM route, using straight-line:', error.message);
    }
  };

  const handleStartStopTracking = async () => {
    if (!driverSession) return;

    if (trackingActive) {
      await locationService.stopTracking();
      locationService.stopNetworkMonitoring();
      setTrackingActive(false);
    } else {
      const granted = await locationService.requestPermissions();
      if (granted.granted) {
        await locationService.startTracking(driverSession.driver_id);
        // Start network monitoring to process offline queue when connectivity restored
        locationService.startNetworkMonitoring();
        setTrackingActive(true);
      }
    }
  };

  // Auto-complete mission button REMOVED - system detects arrival via geofence
  // The backend mobile_location_update endpoint now checks geofence and auto-completes

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
        <Text style={styles.loadingText}>Loading map...</Text>
      </View>
    );
  }

  const originData = mission?.origin || {};
  const destinationData = mission?.destination || {};
  const originLat = parseFloat(originData.lat || originData.latitude || 0);
  const originLng = parseFloat(originData.lon || originData.lng || originData.longitude || 0);
  const destLat = parseFloat(destinationData.lat || destinationData.latitude || 0);
  const destLng = parseFloat(destinationData.lon || destinationData.lng || destinationData.longitude || 0);

  return (
    <View style={styles.container}>
      <StatusBar barStyle="dark-content" />
      
      {/* Auto-completed banner */}
      {autoCompleted && (
        <View style={styles.completedBanner}>
          <Text style={styles.completedBannerText}>✅ Delivered - Mission Complete</Text>
        </View>
      )}
      
      {/* Map View */}
      <MapView
        ref={mapRef}
        style={styles.map}
        provider={PROVIDER_GOOGLE}
        initialRegion={{
          latitude: currentLocation?.latitude || originLat || 0,
          longitude: currentLocation?.longitude || originLng || 0,
          latitudeDelta: 0.05,
          longitudeDelta: 0.05,
        }}
        showsUserLocation={false}
        showsCompass={true}
        showsScale={true}
        rotateEnabled={true}
      >
        {/* Driver's current location */}
        {currentLocation && (
          <>
            <Marker
              identifier="driver"
              coordinate={{
                latitude: currentLocation.latitude,
                longitude: currentLocation.longitude,
              }}
              title="Your Location"
              description={`Speed: ${Math.round(currentSpeed)} km/h`}
            >
              <View style={styles.driverMarker}>
                <Text style={styles.driverMarkerText}>🚛</Text>
              </View>
            </Marker>
            <Circle
              center={{
                latitude: currentLocation.latitude,
                longitude: currentLocation.longitude,
              }}
              radius={currentLocation.accuracy || 50}
              strokeColor="rgba(26, 35, 126, 0.3)"
              fillColor="rgba(26, 35, 126, 0.1)"
            />
          </>
        )}

        {/* Origin marker */}
        {originLat !== 0 && (
          <Marker
            identifier="origin"
            coordinate={{
              latitude: originLat,
              longitude: originLng,
            }}
            title="Origin"
            description="Mission start point"
          >
            <View style={[styles.marker, styles.originMarker]}>
              <Text style={styles.markerText}>🟢</Text>
            </View>
          </Marker>
        )}

        {/* Destination marker */}
        {destLat !== 0 && (
          <Marker
            identifier="destination"
            coordinate={{
              latitude: destLat,
              longitude: destLng,
            }}
            title="Destination"
            description="Mission end point"
          >
            <View style={[styles.marker, styles.destinationMarker]}>
              <Text style={styles.markerText}>🔴</Text>
            </View>
          </Marker>
        )}

        {/* OSRM road-following route (preferred - follows roads like Google Maps) */}
        {osrmRouteCoords.length >= 2 && (
          <Polyline
            coordinates={osrmRouteCoords}
            strokeColor="#0066cc"
            strokeWidth={4}
            lineDashPattern={[]}
          />
        )}

        {/* Fallback straight-line route (only shown when OSRM route unavailable) */}
        {osrmRouteCoords.length < 2 && routeCoords.length >= 2 && (
          <Polyline
            coordinates={routeCoords}
            strokeColor={COLORS.primary}
            strokeWidth={3}
            lineDashPattern={[10, 5]}
          />
        )}
      </MapView>

      {/* Overlay Info Panel */}
      <View style={styles.infoPanel}>
        <View style={styles.speedSection}>
          <Text style={styles.speedValue}>{Math.round(currentSpeed)}</Text>
          <Text style={styles.speedLabel}>km/h</Text>
        </View>
        
        <View style={styles.missionInfo}>
          {mission && (
            <>
              <Text style={styles.missionNumber}>{mission.mission_number}</Text>
              <Text style={styles.missionStatus}>
                Status: {missionStatus?.charAt(0).toUpperCase() + missionStatus?.slice(1) || 'N/A'}
                {autoCompleted ? ' ✅ Delivered' : ''}
              </Text>
            </>
          )}
        </View>

        <View style={styles.gpsIndicator}>
          <View style={[styles.gpsDot, trackingActive ? styles.gpsActive : styles.gpsInactive]} />
          <Text style={styles.gpsText}>{trackingActive ? 'GPS ON' : 'GPS OFF'}</Text>
        </View>
      </View>

      {/* Action Buttons - Complete Mission REMOVED (auto-detected on arrival) */}
      <View style={styles.actionPanel}>
        <TouchableOpacity
          style={[styles.mainButton, trackingActive ? styles.stopButton : styles.startButton]}
          onPress={handleStartStopTracking}
        >
          <Text style={styles.mainButtonText}>
            {trackingActive ? '■ Stop Tracking' : '▶ Start Tracking'}
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  completedBanner: {
    position: 'absolute',
    top: 10,
    left: 20,
    right: 20,
    backgroundColor: '#4CAF50',
    padding: 12,
    borderRadius: 8,
    zIndex: 100,
    alignItems: 'center',
  },
  completedBannerText: {
    color: 'white',
    fontWeight: 'bold',
    fontSize: 16,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: COLORS.background,
  },
  loadingText: {
    marginTop: SPACING.md,
    color: COLORS.textSecondary,
    fontSize: 16,
  },
  map: {
    ...StyleSheet.absoluteFillObject,
  },
  driverMarker: {
    backgroundColor: COLORS.primary,
    borderRadius: 20,
    padding: 6,
    borderWidth: 3,
    borderColor: COLORS.white,
    ...SHADOWS.large,
  },
  driverMarkerText: {
    fontSize: 20,
  },
  marker: {
    borderRadius: 16,
    padding: 4,
    borderWidth: 2,
    borderColor: COLORS.white,
  },
  originMarker: {
    backgroundColor: 'rgba(76, 175, 80, 0.8)',
  },
  destinationMarker: {
    backgroundColor: 'rgba(244, 67, 54, 0.8)',
  },
  markerText: {
    fontSize: 20,
  },
  infoPanel: {
    position: 'absolute',
    top: 50,
    left: SPACING.md,
    right: SPACING.md,
    flexDirection: 'row',
    backgroundColor: 'rgba(255,255,255,0.95)',
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.sm,
    ...SHADOWS.large,
  },
  speedSection: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: SPACING.md,
    borderRightWidth: 1,
    borderRightColor: COLORS.border,
  },
  speedValue: {
    fontSize: 28,
    fontWeight: 'bold',
    color: COLORS.primary,
  },
  speedLabel: {
    fontSize: 11,
    color: COLORS.textSecondary,
  },
  missionInfo: {
    flex: 1,
    paddingHorizontal: SPACING.md,
    justifyContent: 'center',
  },
  missionNumber: {
    fontSize: 14,
    fontWeight: 'bold',
    color: COLORS.textPrimary,
  },
  missionStatus: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginTop: 2,
  },
  gpsIndicator: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: SPACING.md,
    borderLeftWidth: 1,
    borderLeftColor: COLORS.border,
  },
  gpsDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    marginBottom: 4,
  },
  gpsActive: {
    backgroundColor: COLORS.success,
  },
  gpsInactive: {
    backgroundColor: COLORS.danger,
  },
  gpsText: {
    fontSize: 9,
    fontWeight: 'bold',
    color: COLORS.textSecondary,
  },
  actionPanel: {
    position: 'absolute',
    bottom: 40,
    left: SPACING.md,
    right: SPACING.md,
    flexDirection: 'row',
    gap: 8,
  },
  mainButton: {
    flex: 1,
    paddingVertical: 16,
    borderRadius: BORDER_RADIUS.lg,
    alignItems: 'center',
    ...SHADOWS.large,
  },
  startButton: {
    backgroundColor: COLORS.success,
  },
  stopButton: {
    backgroundColor: COLORS.danger,
  },
  mainButtonText: {
    color: COLORS.textLight,
    fontSize: 14,
    fontWeight: 'bold',
  },
});

export default TrackingScreen;