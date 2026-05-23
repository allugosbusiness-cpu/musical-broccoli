import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  RefreshControl,
  ActivityIndicator,
  StatusBar,
  Dimensions,
} from 'react-native';
import { COLORS, SPACING, SHADOWS, BORDER_RADIUS, getMissionStatusColor } from '../config/theme';
import storage from '../utils/storage';
import apiService from '../services/apiService';
import locationService from '../services/locationService';

const { width } = Dimensions.get('window');

const HomeScreen = ({ navigation }) => {
  const [driverSession, setDriverSession] = useState(null);
  const [driverProfile, setDriverProfile] = useState(null);
  const [currentMission, setCurrentMission] = useState(null);
  const [availableMissions, setAvailableMissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [trackingActive, setTrackingActive] = useState(false);
  const [currentSpeed, setCurrentSpeed] = useState(0);

  useEffect(() => {
    loadData();
    const interval = setInterval(updateSpeed, 2000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const session = await storage.getDriverSession();
      setDriverSession(session);

      if (session && session.driver_id) {
        // Get current mission
        try {
          const mission = await apiService.getCurrentMission(session.driver_id);
          if (mission && mission.id) {
            setCurrentMission(mission);
            await storage.saveCurrentMission(mission);
          }
        } catch (e) {
          // No current mission
          console.log('No current mission:', e.message);
        }

        // Get available missions
        try {
          const missions = await apiService.getAvailableMissions(session.driver_id);
          if (missions && missions.missions) {
            setAvailableMissions(missions.missions);
          }
        } catch (e) {
          console.log('Failed to load missions:', e.message);
        }

        // Check if tracking is active
        setTrackingActive(locationService.isTrackingActive());
      }
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  }, []);

  const updateSpeed = () => {
    setCurrentSpeed(locationService.getCurrentSpeed());
  };

  const handleStartTracking = async () => {
    if (driverSession && driverSession.driver_id) {
      const granted = await locationService.requestPermissions();
      if (granted.granted) {
        await locationService.startTracking(driverSession.driver_id);
        setTrackingActive(true);
      }
    }
  };

  const handleStopTracking = async () => {
    await locationService.stopTracking();
    setTrackingActive(false);
  };

  const formatMissionStatus = (status) => {
    return status ? status.charAt(0).toUpperCase() + status.slice(1) : 'Unknown';
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
        <Text style={styles.loadingText}>Loading dashboard...</Text>
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

      {/* Header Section */}
      <View style={styles.header}>
        <View style={styles.headerContent}>
          <Text style={styles.greeting}>
            Welcome, {driverSession?.driver_name || 'Driver'}
          </Text>
          <Text style={styles.truckName}>
            🚛 {driverSession?.truck_name || 'Not Assigned'}
          </Text>
        </View>
        <TouchableOpacity
          style={styles.profileButton}
          onPress={() => navigation.navigate('Profile')}
        >
          <Text style={styles.profileIcon}>👤</Text>
        </TouchableOpacity>
      </View>

      {/* Speed & GPS Card */}
      <View style={styles.speedCard}>
        <View style={styles.speedContainer}>
          <Text style={styles.speedValue}>{Math.round(currentSpeed)}</Text>
          <Text style={styles.speedUnit}>km/h</Text>
        </View>
        <View style={styles.gpsInfo}>
          <Text style={styles.gpsStatus}>
            {trackingActive ? '🟢 GPS Active' : '🔴 GPS Off'}
          </Text>
          <TouchableOpacity
            style={[
              styles.trackingToggle,
              trackingActive ? styles.trackingStop : styles.trackingStart,
            ]}
            onPress={trackingActive ? handleStopTracking : handleStartTracking}
          >
            <Text style={styles.trackingToggleText}>
              {trackingActive ? 'Stop' : 'Start'} Tracking
            </Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Current Mission Card */}
      {currentMission ? (
        <TouchableOpacity
          style={styles.missionCard}
          onPress={() => navigation.navigate('Tracking', { mission: currentMission })}
        >
          <View style={styles.missionHeader}>
            <Text style={styles.missionTitle}>Current Mission</Text>
            <View style={[styles.statusBadge, { backgroundColor: getMissionStatusColor(currentMission.status) }]}>
              <Text style={styles.statusText}>
                {formatMissionStatus(currentMission.status)}
              </Text>
            </View>
          </View>
          <Text style={styles.missionNumber}>{currentMission.mission_number}</Text>
          <View style={styles.progressBar}>
            <View
              style={[
                styles.progressFill,
                { width: `${currentMission.progress_pct || 0}%` },
              ]}
            />
          </View>
          <Text style={styles.progressText}>
            Progress: {Math.round(currentMission.progress_pct || 0)}%
          </Text>
          <Text style={styles.missionDistance}>
            Distance: {Math.round((currentMission.distance_total_m || 0) / 1000)} km
          </Text>
        </TouchableOpacity>
      ) : (
        <View style={styles.noMissionCard}>
          <Text style={styles.noMissionText}>No active mission</Text>
          <Text style={styles.noMissionSubtext}>
            Tap "Missions" below to view available assignments
          </Text>
        </View>
      )}

      {/* Available Missions Summary */}
      <View style={styles.missionsSummary}>
        <Text style={styles.sectionTitle}>Available Missions</Text>
        {availableMissions.length > 0 ? (
          availableMissions.slice(0, 3).map((mission, index) => (
            <TouchableOpacity
              key={mission.id || index}
              style={styles.missionRow}
              onPress={() => navigation.navigate('Missions')}
            >
              <View style={styles.missionRowLeft}>
                <Text style={styles.missionRowNumber}>{mission.mission_number}</Text>
                <Text style={styles.missionRowStatus}>
                  {formatMissionStatus(mission.status)}
                </Text>
              </View>
              <View style={styles.missionRowRight}>
                <Text style={styles.missionRowDistance}>
                  {(mission.distance_total_m / 1000).toFixed(0)} km
                </Text>
                <Text style={styles.missionRowArrow}>›</Text>
              </View>
            </TouchableOpacity>
          ))
        ) : (
          <Text style={styles.noMissionsText}>No missions available</Text>
        )}
        {availableMissions.length > 3 && (
          <TouchableOpacity
            style={styles.viewAllButton}
            onPress={() => navigation.navigate('Missions')}
          >
            <Text style={styles.viewAllText}>
              View All ({availableMissions.length} missions)
            </Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Quick Actions */}
      <View style={styles.quickActions}>
        <Text style={styles.sectionTitle}>Quick Actions</Text>
        <View style={styles.actionsRow}>
          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => navigation.navigate('Missions')}
          >
            <Text style={styles.actionIcon}>📋</Text>
            <Text style={styles.actionLabel}>Missions</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => navigation.navigate('Tracking', { mission: currentMission })}
          >
            <Text style={styles.actionIcon}>🗺️</Text>
            <Text style={styles.actionLabel}>Map View</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => navigation.navigate('Alerts')}
          >
            <Text style={styles.actionIcon}>🔔</Text>
            <Text style={styles.actionLabel}>Alerts</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => navigation.navigate('Profile')}
          >
            <Text style={styles.actionIcon}>👤</Text>
            <Text style={styles.actionLabel}>Profile</Text>
          </TouchableOpacity>
        </View>
      </View>
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
  loadingText: {
    marginTop: SPACING.md,
    color: COLORS.textSecondary,
    fontSize: 16,
  },
  header: {
    backgroundColor: COLORS.primary,
    paddingTop: 50,
    paddingBottom: 30,
    paddingHorizontal: SPACING.lg,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    borderBottomLeftRadius: BORDER_RADIUS.xl,
    borderBottomRightRadius: BORDER_RADIUS.xl,
  },
  headerContent: {
    flex: 1,
  },
  greeting: {
    color: COLORS.textLight,
    fontSize: 22,
    fontWeight: 'bold',
  },
  truckName: {
    color: COLORS.accentLight,
    fontSize: 16,
    marginTop: 4,
  },
  profileButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(255,255,255,0.15)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  profileIcon: {
    fontSize: 24,
  },
  speedCard: {
    flexDirection: 'row',
    margin: SPACING.md,
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    ...SHADOWS.medium,
  },
  speedContainer: {
    flexDirection: 'row',
    alignItems: 'baseline',
    flex: 1,
  },
  speedValue: {
    fontSize: 48,
    fontWeight: 'bold',
    color: COLORS.primary,
  },
  speedUnit: {
    fontSize: 16,
    color: COLORS.textSecondary,
    marginLeft: 4,
  },
  gpsInfo: {
    alignItems: 'flex-end',
    justifyContent: 'center',
  },
  gpsStatus: {
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 8,
  },
  trackingToggle: {
    paddingHorizontal: SPACING.md,
    paddingVertical: 8,
    borderRadius: BORDER_RADIUS.round,
  },
  trackingStart: {
    backgroundColor: COLORS.success,
  },
  trackingStop: {
    backgroundColor: COLORS.danger,
  },
  trackingToggleText: {
    color: COLORS.textLight,
    fontSize: 12,
    fontWeight: 'bold',
  },
  missionCard: {
    margin: SPACING.md,
    marginTop: 0,
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    ...SHADOWS.medium,
    borderLeftWidth: 4,
    borderLeftColor: COLORS.accent,
  },
  missionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  missionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.textSecondary,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  statusBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: BORDER_RADIUS.round,
  },
  statusText: {
    color: COLORS.textLight,
    fontSize: 11,
    fontWeight: 'bold',
    textTransform: 'uppercase',
  },
  missionNumber: {
    fontSize: 18,
    fontWeight: 'bold',
    color: COLORS.textPrimary,
    marginBottom: 8,
  },
  progressBar: {
    height: 6,
    backgroundColor: COLORS.gray200,
    borderRadius: 3,
    marginBottom: 4,
  },
  progressFill: {
    height: '100%',
    backgroundColor: COLORS.accent,
    borderRadius: 3,
  },
  progressText: {
    fontSize: 12,
    color: COLORS.textSecondary,
  },
  missionDistance: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginTop: 2,
  },
  noMissionCard: {
    margin: SPACING.md,
    marginTop: 0,
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.lg,
    alignItems: 'center',
    ...SHADOWS.medium,
  },
  noMissionText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: COLORS.textSecondary,
  },
  noMissionSubtext: {
    fontSize: 13,
    color: COLORS.textMuted,
    marginTop: 4,
    textAlign: 'center',
  },
  missionsSummary: {
    margin: SPACING.md,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: COLORS.textPrimary,
    marginBottom: SPACING.sm,
  },
  missionRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    marginBottom: 6,
    ...SHADOWS.small,
  },
  missionRowLeft: {},
  missionRowNumber: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.textPrimary,
  },
  missionRowStatus: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginTop: 2,
  },
  missionRowRight: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  missionRowDistance: {
    fontSize: 14,
    color: COLORS.textSecondary,
    marginRight: 8,
  },
  missionRowArrow: {
    fontSize: 24,
    color: COLORS.gray400,
  },
  noMissionsText: {
    fontSize: 14,
    color: COLORS.textMuted,
    textAlign: 'center',
    padding: SPACING.lg,
  },
  viewAllButton: {
    alignItems: 'center',
    padding: SPACING.sm,
  },
  viewAllText: {
    color: COLORS.primary,
    fontWeight: '600',
    fontSize: 14,
  },
  quickActions: {
    margin: SPACING.md,
    marginBottom: SPACING.xl,
  },
  actionsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  actionButton: {
    flex: 1,
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    alignItems: 'center',
    marginHorizontal: 4,
    ...SHADOWS.small,
  },
  actionIcon: {
    fontSize: 28,
    marginBottom: 4,
  },
  actionLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.textSecondary,
  },
});

export default HomeScreen;