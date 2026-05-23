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
} from 'react-native';
import { COLORS, SPACING, SHADOWS, BORDER_RADIUS } from '../config/theme';
import storage from '../utils/storage';
import apiService from '../services/apiService';
import locationService from '../services/locationService';

const AlertsScreen = ({ navigation }) => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadAlerts();
  }, []);

  const loadAlerts = async () => {
    try {
      // For now, the alerts are managed on the web side
      // Mobile can send alerts but reading alerts is done via the driver's current context
      // We'll maintain a local alerts list for display
      const session = await storage.getDriverSession();
      setLoading(false);
    } catch (error) {
      console.error('Error loading alerts:', error);
      setLoading(false);
    }
  };

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadAlerts();
    setRefreshing(false);
  }, []);

  const handleSendAlert = async (type) => {
    const session = await storage.getDriverSession();
    if (!session || !session.driver_id) {
      alert('Driver session not found');
      return;
    }

    try {
      const location = await locationService.getCurrentPosition();
      const speed = locationService.getCurrentSpeed();

      const alertMessages = {
        mechanical: '⚠️ Mechanical issue reported',
        route: '🛣️ Route deviation detected',
        traffic: '🚦 Heavy traffic ahead',
        emergency: '🚨 Emergency situation!',
        fuel: '⛽ Low fuel warning',
        other: '📝 General report',
      };

      const result = await apiService.sendAlert(
        session.driver_id,
        type,
        alertMessages[type] || 'Alert reported',
        location || { latitude: 0, longitude: 0 },
        speed
      );

      if (result && result.success) {
        // Add to local alerts list
        const newAlert = {
          id: result.alert_id || Date.now().toString(),
          type: type,
          message: alertMessages[type] || 'Alert sent',
          timestamp: new Date().toISOString(),
          severity: type === 'emergency' ? 'critical' : 'medium',
        };
        setAlerts(prev => [newAlert, ...prev]);
        alert('Alert sent to fleet manager');
      }
    } catch (error) {
      alert('Failed to send alert: ' + error.message);
    }
  };

  const getAlertColor = (type) => {
    const colors = {
      speed: COLORS.alertSpeed,
      overspeeding: COLORS.alertSpeed,
      route_deviation: COLORS.alertRoute,
      route: COLORS.alertRoute,
      location: COLORS.alertLocation,
      maintenance: COLORS.alertMaintenance,
      mechanical: COLORS.alertMaintenance,
      delivery: COLORS.alertDelivery,
      emergency: COLORS.danger,
      traffic: COLORS.warning,
      fuel: COLORS.warning,
      other: COLORS.info,
    };
    return colors[type] || COLORS.info;
  };

  const getAlertIcon = (type) => {
    const icons = {
      speed: '⚡',
      overspeeding: '⚡',
      route_deviation: '🔄',
      route: '🔄',
      location: '📍',
      maintenance: '🔧',
      mechanical: '🔧',
      delivery: '📦',
      emergency: '🚨',
      traffic: '🚦',
      fuel: '⛽',
      other: '📝',
    };
    return icons[type] || '🔔';
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
        <Text style={styles.headerTitle}>Alerts & Reports</Text>
        <Text style={styles.headerSubtitle}>Send alerts to fleet manager</Text>
      </View>

      {/* Quick Alert Buttons */}
      <Text style={styles.sectionTitle}>Quick Report</Text>
      <View style={styles.alertGrid}>
        {[
          { type: 'mechanical', label: 'Mechanical', icon: '🔧' },
          { type: 'route', label: 'Route Issue', icon: '🔄' },
          { type: 'traffic', label: 'Traffic', icon: '🚦' },
          { type: 'emergency', label: 'Emergency', icon: '🚨' },
          { type: 'fuel', label: 'Fuel Issue', icon: '⛽' },
          { type: 'other', label: 'Other', icon: '📝' },
        ].map((item) => (
          <TouchableOpacity
            key={item.type}
            style={styles.alertButton}
            onPress={() => handleSendAlert(item.type)}
          >
            <Text style={styles.alertButtonIcon}>{item.icon}</Text>
            <Text style={styles.alertButtonLabel}>{item.label}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Speed Alert Info */}
      <View style={styles.speedAlertInfo}>
        <Text style={styles.speedAlertTitle}>⚡ Speed Alert</Text>
        <Text style={styles.speedAlertText}>
          If you exceed {Math.round(locationService.getSpeedAlertThreshold())} km/h, an automatic
          speeding alert will be sent to the fleet manager.
        </Text>
      </View>

      {/* Alert History */}
      <Text style={styles.sectionTitle}>Alert History</Text>
      {alerts.length === 0 ? (
        <View style={styles.emptyState}>
          <Text style={styles.emptyEmoji}>🔔</Text>
          <Text style={styles.emptyText}>No alerts sent yet</Text>
          <Text style={styles.emptySubtext}>
            Use the buttons above to report issues to your fleet manager
          </Text>
        </View>
      ) : (
        alerts.map((alert, index) => (
          <View key={alert.id || index} style={styles.alertItem}>
            <View style={[styles.alertIcon, { backgroundColor: getAlertColor(alert.type) }]}>
              <Text style={styles.alertIconText}>
                {getAlertIcon(alert.type)}
              </Text>
            </View>
            <View style={styles.alertInfo}>
              <Text style={styles.alertMessage}>{alert.message}</Text>
              <Text style={styles.alertTime}>
                {new Date(alert.timestamp).toLocaleTimeString()}
              </Text>
            </View>
          </View>
        ))
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
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: COLORS.textPrimary,
    margin: SPACING.md,
    marginBottom: SPACING.sm,
  },
  alertGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: SPACING.md,
    marginBottom: SPACING.md,
  },
  alertButton: {
    width: '30%',
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    alignItems: 'center',
    marginRight: '3.33%',
    marginBottom: SPACING.sm,
    ...SHADOWS.small,
  },
  alertButtonIcon: {
    fontSize: 32,
    marginBottom: 6,
  },
  alertButtonLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: COLORS.textSecondary,
    textAlign: 'center',
  },
  speedAlertInfo: {
    marginHorizontal: SPACING.md,
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.md,
    marginBottom: SPACING.md,
    borderLeftWidth: 4,
    borderLeftColor: COLORS.warning,
    ...SHADOWS.small,
  },
  speedAlertTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: COLORS.textPrimary,
    marginBottom: 4,
  },
  speedAlertText: {
    fontSize: 12,
    color: COLORS.textSecondary,
    lineHeight: 18,
  },
  emptyState: {
    alignItems: 'center',
    marginTop: 20,
    paddingHorizontal: SPACING.xl,
  },
  emptyEmoji: {
    fontSize: 48,
    marginBottom: SPACING.md,
  },
  emptyText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.textSecondary,
    marginBottom: 4,
  },
  emptySubtext: {
    fontSize: 13,
    color: COLORS.textMuted,
    textAlign: 'center',
    lineHeight: 20,
  },
  alertItem: {
    flexDirection: 'row',
    backgroundColor: COLORS.card,
    marginHorizontal: SPACING.md,
    marginBottom: 6,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.md,
    ...SHADOWS.small,
  },
  alertIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: SPACING.md,
  },
  alertIconText: {
    fontSize: 20,
  },
  alertInfo: {
    flex: 1,
    justifyContent: 'center',
  },
  alertMessage: {
    fontSize: 14,
    color: COLORS.textPrimary,
    fontWeight: '500',
  },
  alertTime: {
    fontSize: 11,
    color: COLORS.textMuted,
    marginTop: 2,
  },
});

export default AlertsScreen;