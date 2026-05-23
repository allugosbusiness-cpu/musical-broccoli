import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Alert,
  StatusBar,
  Switch,
} from 'react-native';
import { COLORS, SPACING, SHADOWS, BORDER_RADIUS } from '../config/theme';
import storage from '../utils/storage';
import apiService from '../services/apiService';
import locationService from '../services/locationService';

const ProfileScreen = ({ navigation }) => {
  const [driverSession, setDriverSession] = useState(null);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [gpsEnabled, setGpsEnabled] = useState(true);
  const [trackingActive, setTrackingActive] = useState(false);

  useEffect(() => {
    loadProfile();
    const interval = setInterval(() => {
      setTrackingActive(locationService.isTrackingActive());
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const loadProfile = async () => {
    try {
      const session = await storage.getDriverSession();
      setDriverSession(session);

      if (session && session.driver_id) {
        try {
          const profileData = await apiService.getDriverProfile(session.driver_id);
          setProfile(profileData);
          await storage.saveDriverProfile(profileData);
        } catch (e) {
          // Use cached profile
          const cached = await storage.getDriverProfile();
          setProfile(cached);
        }
      }
    } catch (error) {
      console.error('Error loading profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    Alert.alert(
      'Logout',
      'Are you sure you want to logout? GPS tracking will be stopped.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Logout',
          style: 'destructive',
          onPress: async () => {
            await locationService.stopTracking();
            await storage.clearAll();
            navigation.replace('Login');
          },
        },
      ]
    );
  };

  const toggleGpsTracking = async (value) => {
    setGpsEnabled(value);
    if (value && driverSession?.driver_id) {
      const granted = await locationService.requestPermissions();
      if (granted.granted) {
        await locationService.startTracking(driverSession.driver_id);
      }
    } else {
      await locationService.stopTracking();
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <StatusBar backgroundColor={COLORS.primaryDark} barStyle="light-content" />

      {/* Profile Header */}
      <View style={styles.header}>
        <View style={styles.avatarContainer}>
          <Text style={styles.avatarEmoji}>👤</Text>
        </View>
        <Text style={styles.driverName}>
          {profile?.name || driverSession?.driver_name || 'Driver'}
        </Text>
        <Text style={styles.phoneNumber}>
          {profile?.phone || driverSession?.phone_number || 'No phone'}
        </Text>
        <Text style={styles.truckAssignment}>
          🚛 {profile?.truck_name || driverSession?.truck_name || 'Not assigned'}
        </Text>
      </View>

      {/* Stats Card */}
      <View style={styles.statsCard}>
        <View style={styles.statItem}>
          <Text style={styles.statValue}>{profile?.performance_points || 0}</Text>
          <Text style={styles.statLabel}>Performance Points</Text>
        </View>
        <View style={styles.statDivider} />
        <View style={styles.statItem}>
          <Text style={styles.statValue}>{trackingActive ? '🟢' : '🔴'}</Text>
          <Text style={styles.statLabel}>GPS Status</Text>
        </View>
      </View>

      {/* Settings Card */}
      <View style={styles.sectionCard}>
        <Text style={styles.sectionTitle}>Settings</Text>
        
        <View style={styles.settingRow}>
          <View style={styles.settingInfo}>
            <Text style={styles.settingLabel}>GPS Tracking</Text>
            <Text style={styles.settingDescription}>
              Send location and speed to fleet manager
            </Text>
          </View>
          <Switch
            value={gpsEnabled}
            onValueChange={toggleGpsTracking}
            trackColor={{ false: COLORS.gray300, true: COLORS.primaryLight }}
            thumbColor={gpsEnabled ? COLORS.primary : COLORS.gray500}
          />
        </View>

        <View style={styles.settingRow}>
          <View style={styles.settingInfo}>
            <Text style={styles.settingLabel}>Speed Alert Threshold</Text>
            <Text style={styles.settingDescription}>
              {Math.round(locationService.getSpeedAlertThreshold())} km/h
            </Text>
          </View>
        </View>
      </View>

      {/* Driver Info Card */}
      <View style={styles.sectionCard}>
        <Text style={styles.sectionTitle}>Driver Information</Text>
        
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>Driver ID</Text>
          <Text style={styles.infoValue} numberOfLines={1}>
            {driverSession?.driver_id || 'N/A'}
          </Text>
        </View>
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>Truck ID</Text>
          <Text style={styles.infoValue} numberOfLines={1}>
            {driverSession?.truck_id || 'N/A'}
          </Text>
        </View>
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>Tracking ID</Text>
          <Text style={styles.infoValue} numberOfLines={1}>
            {driverSession?.tracking_id || 'N/A'}
          </Text>
        </View>
      </View>

      {/* Actions */}
      <View style={styles.actionsSection}>
        <TouchableOpacity
          style={styles.actionButton}
          onPress={() => navigation.navigate('Missions')}
        >
          <Text style={styles.actionIcon}>📋</Text>
          <Text style={styles.actionText}>View Missions</Text>
          <Text style={styles.actionArrow}>›</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.actionButton}
          onPress={() => navigation.navigate('Tracking')}
        >
          <Text style={styles.actionIcon}>🗺️</Text>
          <Text style={styles.actionText}>Open Map</Text>
          <Text style={styles.actionArrow}>›</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={styles.actionButton}
          onPress={() => navigation.navigate('Alerts')}
        >
          <Text style={styles.actionIcon}>🔔</Text>
          <Text style={styles.actionText}>Send Alert</Text>
          <Text style={styles.actionArrow}>›</Text>
        </TouchableOpacity>
      </View>

      {/* Logout */}
      <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
        <Text style={styles.logoutText}>🚪 Logout</Text>
      </TouchableOpacity>

      <View style={styles.footer}>
        <Text style={styles.footerText}>PulseTrack Fleet v2.0</Text>
        <Text style={styles.footerText}>Powered by PulseTrack</Text>
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
  header: {
    backgroundColor: COLORS.primary,
    paddingTop: 50,
    paddingBottom: 30,
    alignItems: 'center',
    borderBottomLeftRadius: BORDER_RADIUS.xl,
    borderBottomRightRadius: BORDER_RADIUS.xl,
  },
  avatarContainer: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: 'rgba(255,255,255,0.15)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  avatarEmoji: {
    fontSize: 40,
  },
  driverName: {
    color: COLORS.textLight,
    fontSize: 24,
    fontWeight: 'bold',
  },
  phoneNumber: {
    color: COLORS.accentLight,
    fontSize: 14,
    marginTop: 4,
  },
  truckAssignment: {
    color: 'rgba(255,255,255,0.7)',
    fontSize: 14,
    marginTop: 8,
  },
  statsCard: {
    flexDirection: 'row',
    margin: SPACING.md,
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    ...SHADOWS.medium,
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: COLORS.primary,
  },
  statLabel: {
    fontSize: 11,
    color: COLORS.textSecondary,
    marginTop: 4,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  statDivider: {
    width: 1,
    backgroundColor: COLORS.border,
    marginVertical: 8,
  },
  sectionCard: {
    margin: SPACING.md,
    marginTop: 0,
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    ...SHADOWS.small,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: COLORS.textSecondary,
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: SPACING.md,
  },
  settingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: SPACING.sm,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.divider,
  },
  settingInfo: {
    flex: 1,
    marginRight: SPACING.md,
  },
  settingLabel: {
    fontSize: 15,
    fontWeight: '500',
    color: COLORS.textPrimary,
  },
  settingDescription: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginTop: 2,
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.divider,
  },
  infoLabel: {
    fontSize: 13,
    color: COLORS.textSecondary,
  },
  infoValue: {
    fontSize: 13,
    color: COLORS.textPrimary,
    fontWeight: '500',
    maxWidth: '60%',
  },
  actionsSection: {
    margin: SPACING.md,
    marginTop: 0,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    marginBottom: 6,
    ...SHADOWS.small,
  },
  actionIcon: {
    fontSize: 20,
    marginRight: SPACING.md,
  },
  actionText: {
    flex: 1,
    fontSize: 15,
    fontWeight: '500',
    color: COLORS.textPrimary,
  },
  actionArrow: {
    fontSize: 24,
    color: COLORS.gray400,
  },
  logoutButton: {
    margin: SPACING.md,
    backgroundColor: COLORS.danger,
    borderRadius: BORDER_RADIUS.lg,
    paddingVertical: 16,
    alignItems: 'center',
    ...SHADOWS.medium,
  },
  logoutText: {
    color: COLORS.textLight,
    fontSize: 16,
    fontWeight: 'bold',
  },
  footer: {
    alignItems: 'center',
    paddingVertical: SPACING.lg,
  },
  footerText: {
    fontSize: 12,
    color: COLORS.textMuted,
    marginBottom: 2,
  },
});

export default ProfileScreen;