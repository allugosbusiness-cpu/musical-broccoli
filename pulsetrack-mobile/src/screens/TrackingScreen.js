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
  const [missionStatus, setMissionStatus] = useState('');

  useEffect(() => {
    initTracking();
    const speedInterval = setInterval(() => {
      setCurrentSpeed(locationService.getCurrentSpeed());
      setTrackingActive(locationService.isTrackingActive());
    }, 2000);

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
        const origin = currentMission.origin || {};
        const destination = currentMission.destination || {};
        const originLat = parseFloat(origin.lat || origin.latitude || 0);
        const originLng = parseFloat(origin.lon || origin.lng || origin.longitude || 0);
        const destLat = parseFloat(destination.lat || destination.latitude || 0);
        const destLng = parseFloat(destination.lon || destination.lng || destination.longitude || 0);

        if (originLat && originLng && destLat && destLng) {
          setRouteCoords([
            { latitude: originLat, longitude: originLng },
            { latitude: destLat, longitude: destLng },
          ]);
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

  const handleStartStopTracking = async () => {
    if (!driverSession) return;

    if (trackingActive) {
      await locationService.stopTracking();
      setTrackingActive(false);
    } else {
      const granted = await locationService.requestPermissions();
      if (granted.granted) {
        await locationService.startTracking(driverSession.driver_id);
        setTrackingActive(true);
      }
    }
  };

  const handleCompleteMission = () => {
    if (!mission) return;
    
    Alert.alert(
      'Complete Mission',
      `Are you sure you want to complete ${mission.mission_number}?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Complete',
          style: 'destructive',
          onPress: async () => {
            try {
              const result = await apiService.completeMission(mission.id);
              if (result && result.success) {
                await locationService.stopTracking();
                await storage.clearCurrentMission();
                Alert.alert('Success', 'Mission completed!', [
                  { text: 'OK', onPress: () => navigation.navigate('Home') },
                ]);
              }
            } catch (error) {
              Alert.alert('Error', error.message);
            }
          },
        },
      ]
    );
  };

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

        {/* Route polyline */}
        {routeCoords.length >= 2 && (
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
              </Text>
            </>
          )}
        </View>

        <View style={styles.gpsIndicator}>
          <View style={[styles.gpsDot, trackingActive ? styles.gpsActive : styles.gpsInactive]} />
          <Text style={styles.gpsText}>{trackingActive ? 'GPS ON' : 'GPS OFF'}</Text>
        </View>
      </View>

      {/* Action Buttons */}
      <View style={styles.actionPanel}>
        <TouchableOpacity
          style={[styles.mainButton, trackingActive ? styles.stopButton : styles.startButton]}
          onPress={handleStartStopTracking}
        >
          <Text style={styles.mainButtonText}>
            {trackingActive ? '■ Stop Tracking' : '▶ Start Tracking'}
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.mainButton, styles.completeMissionButton]}
          onPress={handleCompleteMission}
        >
          <Text style={styles.mainButtonText}>✓ Complete Mission</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
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
  completeMissionButton: {
    backgroundColor: COLORS.primary,
  },
  mainButtonText: {
    color: COLORS.textLight,
    fontSize: 14,
    fontWeight: 'bold',
  },
});

export default TrackingScreen;