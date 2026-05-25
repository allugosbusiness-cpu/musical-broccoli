import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  RefreshControl,
  ActivityIndicator,
  Alert,
  StatusBar,
} from 'react-native';
import { COLORS, SPACING, SHADOWS, BORDER_RADIUS, getMissionStatusColor } from '../config/theme';
import storage from '../utils/storage';
import apiService from '../services/apiService';
import locationService from '../services/locationService';

const MissionsScreen = ({ navigation }) => {
  const [missions, setMissions] = useState([]);
  const [driverSession, setDriverSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedMission, setSelectedMission] = useState(null);
  const [startingMission, setStartingMission] = useState(false);

  useEffect(() => {
    loadMissions();
  }, []);

  const loadMissions = async () => {
    try {
      const session = await storage.getDriverSession();
      console.log('[MissionsScreen] driver session:', session);
      setDriverSession(session);

      if (session && session.driver_id) {
        console.log('[MissionsScreen] fetching available missions for driver:', session.driver_id);
        const result = await apiService.getAvailableMissions(session.driver_id);
        console.log('[MissionsScreen] available missions result:', result);
        
        if (result && result.missions) {
          console.log('[MissionsScreen] setting missions:', result.missions);
          setMissions(result.missions);
        } else {
          console.log('[MissionsScreen] no missions in result');
          setMissions([]);
        }
      } else {
        console.log('[MissionsScreen] no driver session or driver_id');
        setMissions([]);
      }
    } catch (error) {
      console.error('[MissionsScreen] error loading missions:', error.message, error);
      setMissions([]);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadMissions();
    setRefreshing(false);
  }, []);

  const handleStartMission = async (mission) => {
    if (!driverSession) {
      Alert.alert('Error', 'Driver session not found. Please re-register.');
      return;
    }

    setStartingMission(true);
    setSelectedMission(mission.id);

    try {
      // Get current location for audit trail
      let location = null;
      try {
        location = await locationService.getCurrentPosition();
      } catch (e) {
        // proceed without location
      }

      const result = await apiService.startMissionTracking(
        driverSession.driver_id,
        mission.id,
        location
      );

      if (result && result.success) {
        // Start GPS tracking if not already started
        if (!locationService.isTrackingActive()) {
          const granted = await locationService.requestPermissions();
          if (granted.granted) {
            await locationService.startTracking(driverSession.driver_id);
          }
        }

        await storage.saveCurrentMission(result);
        Alert.alert(
          'Mission Started',
          `Tracking mission ${mission.mission_number}`,
          [
            {
              text: 'View Tracking',
              onPress: () => navigation.navigate('Tracking', { mission: result }),
            },
          ]
        );
        // Reload missions list
        loadMissions();
      } else {
        Alert.alert('Error', result.error || 'Failed to start mission');
      }
    } catch (error) {
      Alert.alert('Error', error.message || 'Failed to start mission');
    } finally {
      setStartingMission(false);
      setSelectedMission(null);
    }
  };

  // Complete Mission button REMOVED - System auto-detects arrival via geofence
  // When the driver reaches within 100m of destination, the backend auto-completes

  const formatStatus = (status) => {
    return status ? status.charAt(0).toUpperCase() + status.slice(1) : 'Unknown';
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[COLORS.primary]} />
      }
    >
      <StatusBar backgroundColor={COLORS.primaryDark} barStyle="light-content" />
      
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>
          Missions ({missions.length})
        </Text>
        <Text style={styles.headerSubtitle}>
          {driverSession?.driver_name || 'Driver'}
        </Text>
      </View>

      {missions.length === 0 ? (
        <View style={styles.emptyState}>
          <Text style={styles.emptyEmoji}>📋</Text>
          <Text style={styles.emptyTitle}>No Missions Available</Text>
          <Text style={styles.emptySubtitle}>
            Check with your fleet manager for new assignments
          </Text>
        </View>
      ) : (
        missions.map((mission, index) => {
          const isStarting = startingMission && selectedMission === mission.id;
          const statusColor = getMissionStatusColor(mission.status);
          const origin = mission.origin || {};
          const destination = mission.destination || {};
          const originLat = origin.lat || origin.latitude || 'N/A';
          const originLng = origin.lon || origin.lng || origin.longitude || 'N/A';
          const destLat = destination.lat || destination.latitude || 'N/A';
          const destLng = destination.lon || destination.lng || destination.longitude || 'N/A';

          return (
            <View key={mission.id || index} style={styles.missionCard}>
              {/* Status bar */}
              <View style={[styles.statusBar, { backgroundColor: statusColor }]}>
                <Text style={styles.statusBarText}>
                  {formatStatus(mission.status)}
                </Text>
              </View>

              <View style={styles.missionContent}>
                {/* Header */}
                <View style={styles.missionHeader}>
                  <Text style={styles.missionNumber}>{mission.mission_number}</Text>
                  <Text style={styles.missionDistance}>
                    {(mission.distance_total_m / 1000).toFixed(1)} km
                  </Text>
                </View>

                {/* Route */}
                <View style={styles.routeContainer}>
                  <View style={styles.routePoint}>
                    <View style={[styles.routeDot, { backgroundColor: COLORS.success }]} />
                    <Text style={styles.routeLabel}>From:</Text>
                    <Text style={styles.routeCoords}>
                      {typeof originLat === 'number' ? originLat.toFixed(4) : originLat},{' '}
                      {typeof originLng === 'number' ? originLng.toFixed(4) : originLng}
                    </Text>
                  </View>
                  <View style={styles.routeLine} />
                  <View style={styles.routePoint}>
                    <View style={[styles.routeDot, { backgroundColor: COLORS.danger }]} />
                    <Text style={styles.routeLabel}>To:</Text>
                    <Text style={styles.routeCoords}>
                      {typeof destLat === 'number' ? destLat.toFixed(4) : destLat},{' '}
                      {typeof destLng === 'number' ? destLng.toFixed(4) : destLng}
                    </Text>
                  </View>
                </View>

                {/* Cargo info */}
                {mission.cargo && Object.keys(mission.cargo).length > 0 && (
                  <View style={styles.cargoInfo}>
                    <Text style={styles.cargoLabel}>Cargo:</Text>
                    <Text style={styles.cargoText}>
                      {mission.cargo.item || mission.cargo.description || JSON.stringify(mission.cargo)}
                    </Text>
                  </View>
                )}

                {/* Action Buttons */}
                <View style={styles.actionButtons}>
                  {mission.status === 'planned' || mission.status === 'assigned' ? (
                    <TouchableOpacity
                      style={[styles.actionButton, styles.startButton]}
                      onPress={() => handleStartMission(mission)}
                      disabled={isStarting}
                    >
                      {isStarting ? (
                        <ActivityIndicator size="small" color={COLORS.textLight} />
                      ) : (
                        <Text style={styles.actionButtonText}>Start Mission</Text>
                      )}
                    </TouchableOpacity>
                  ) : mission.status === 'enroute' ? (
                    <>
                      <TouchableOpacity
                        style={[styles.actionButton, styles.mapButton]}
                        onPress={() => navigation.navigate('Tracking', { mission })}
                      >
                        <Text style={styles.actionButtonText}>View Map</Text>
                      </TouchableOpacity>
                      {/* Complete button REMOVED - auto-detected on arrival via geofence */}
                    </>
                  ) : null}
                </View>
              </View>
            </View>
          );
        })
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: COLORS.background,
  },
  header: {
    backgroundColor: COLORS.primary,
    paddingTop: 50,
    paddingBottom: 20,
    paddingHorizontal: SPACING.lg,
    borderBottomLeftRadius: BORDER_RADIUS.xl,
    borderBottomRightRadius: BORDER_RADIUS.xl,
  },
  headerTitle: {
    color: COLORS.textLight,
    fontSize: 24,
    fontWeight: 'bold',
  },
  headerSubtitle: {
    color: COLORS.accentLight,
    fontSize: 14,
    marginTop: 4,
  },
  emptyState: {
    flex: 1,
    alignItems: 'center',
    marginTop: 80,
    paddingHorizontal: SPACING.xl,
  },
  emptyEmoji: {
    fontSize: 60,
    marginBottom: SPACING.md,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: COLORS.textPrimary,
    marginBottom: 8,
  },
  emptySubtitle: {
    fontSize: 14,
    color: COLORS.textSecondary,
    textAlign: 'center',
    lineHeight: 22,
  },
  missionCard: {
    margin: SPACING.md,
    marginBottom: 0,
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    overflow: 'hidden',
    ...SHADOWS.medium,
  },
  statusBar: {
    paddingHorizontal: SPACING.md,
    paddingVertical: 6,
  },
  statusBarText: {
    color: COLORS.textLight,
    fontSize: 12,
    fontWeight: 'bold',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  missionContent: {
    padding: SPACING.md,
  },
  missionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SPACING.sm,
  },
  missionNumber: {
    fontSize: 18,
    fontWeight: 'bold',
    color: COLORS.textPrimary,
  },
  missionDistance: {
    fontSize: 14,
    color: COLORS.textSecondary,
    fontWeight: '600',
  },
  routeContainer: {
    marginBottom: SPACING.sm,
  },
  routePoint: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 4,
  },
  routeDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 10,
  },
  routeLine: {
    width: 2,
    height: 16,
    backgroundColor: COLORS.gray300,
    marginLeft: 5,
    marginVertical: 2,
  },
  routeLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.textSecondary,
    marginRight: 6,
    width: 40,
  },
  routeCoords: {
    fontSize: 13,
    color: COLORS.textPrimary,
    flex: 1,
  },
  cargoInfo: {
    flexDirection: 'row',
    backgroundColor: COLORS.gray50,
    padding: SPACING.sm,
    borderRadius: BORDER_RADIUS.sm,
    marginBottom: SPACING.sm,
  },
  cargoLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.textSecondary,
    marginRight: 8,
  },
  cargoText: {
    fontSize: 12,
    color: COLORS.textPrimary,
    flex: 1,
  },
  actionButtons: {
    flexDirection: 'row',
    marginTop: SPACING.sm,
  },
  actionButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: BORDER_RADIUS.md,
    alignItems: 'center',
  },
  startButton: {
    backgroundColor: COLORS.success,
  },
  mapButton: {
    backgroundColor: COLORS.primary,
    marginRight: 8,
  },
  completeButton: {
    backgroundColor: COLORS.warning,
    marginLeft: 8,
  },
  actionButtonText: {
    color: COLORS.textLight,
    fontWeight: 'bold',
    fontSize: 14,
  },
});

export default MissionsScreen;