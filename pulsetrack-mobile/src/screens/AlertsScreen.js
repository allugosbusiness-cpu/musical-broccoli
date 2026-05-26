/**
 * AlertsScreen - Driver Alert System
 * - View active notifications from fleet manager
 * - Send custom alerts back to the fleet manager
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  ActivityIndicator,
  RefreshControl,
  StatusBar,
} from 'react-native';
import { COLORS, SPACING, SHADOWS, BORDER_RADIUS } from '../config/theme';
import storage from '../utils/storage';
import apiService from '../services/apiService';
import locationService from '../services/locationService';
import API_CONFIG from '../config/api';

const ALERT_CATEGORIES = [
  { id: 'mechanical', label: '🔧 Mechanical Issue', icon: '🔧' },
  { id: 'accident', label: '💥 Accident', icon: '💥' },
  { id: 'traffic', label: '🚦 Heavy Traffic', icon: '🚦' },
  { id: 'weather', label: '🌧️ Bad Weather', icon: '🌧️' },
  { id: 'road_closed', label: '🚧 Road Closed', icon: '🚧' },
  { id: 'need_rest', label: '😴 Need Rest Break', icon: '😴' },
  { id: 'other', label: '📢 Other', icon: '📢' },
];

export default function AlertsScreen({ navigation }) {
  const [driverSession, setDriverSession] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showSendAlert, setShowSendAlert] = useState(false);
  const [alertMessage, setAlertMessage] = useState('');
  const [alertCategory, setAlertCategory] = useState('other');
  const [sending, setSending] = useState(false);

  useEffect(() => {
    loadAlerts();
  }, []);

  const loadAlerts = async () => {
    try {
      const session = await storage.getDriverSession();
      setDriverSession(session);
      
      if (session && session.driver_id) {
        // Fetch active alerts from backend
        const alerts = await apiService.getDriverAlerts(session.driver_id);
        if (alerts && alerts.alerts) {
          setNotifications(alerts.alerts);
        }
      }
    } catch (error) {
      console.log('[AlertsScreen] Load error:', error.message);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await loadAlerts();
    setRefreshing(false);
  }, []);

  const handleSendAlert = async () => {
    if (!alertMessage.trim() || alertMessage.trim().length < 5) {
      Alert.alert('Error', 'Please enter a message (min 5 characters)');
      return;
    }

    setSending(true);
    try {
      const position = await locationService.getCurrentPosition();
      const result = await apiService.sendDriverAlert(
        driverSession.driver_id,
        driverSession.truck_id,
        alertMessage.trim(),
        alertCategory,
        position?.latitude || 0,
        position?.longitude || 0
      );

      if (result && result.success) {
        Alert.alert('✅ Alert Sent', 'Your message has been sent to the fleet manager.');
        setShowSendAlert(false);
        setAlertMessage('');
        setAlertCategory('other');
      } else {
        Alert.alert('Error', result?.error || 'Failed to send alert');
      }
    } catch (error) {
      Alert.alert('Error', error.message || 'Failed to send alert');
    } finally {
      setSending(false);
    }
  };

  const formatTime = (ts) => {
    if (!ts) return '';
    try {
      const d = new Date(ts);
      const now = new Date();
      const diff = Math.floor((now - d) / 1000);
      if (diff < 60) return 'Just now';
      if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
      if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
      return d.toLocaleDateString();
    } catch { return ''; }
  };

  const getAlertColor = (type, severity) => {
    if (severity === 'critical' || severity === 'high') return COLORS.danger;
    if (type === 'overspeed') return '#f59e0b';
    if (type === 'delayed') return '#f97316';
    if (type === 'driver_alert') return '#8b5cf6';
    return COLORS.primary;
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
        <Text style={styles.headerTitle}>🔔 Notifications & Alerts</Text>
        <Text style={styles.headerSubtitle}>
          {notifications.length > 0 ? `${notifications.length} active` : 'No active alerts'}
        </Text>
      </View>

      {/* Send Alert Button */}
      <TouchableOpacity
        style={styles.sendAlertButton}
        onPress={() => setShowSendAlert(!showSendAlert)}
      >
        <Text style={styles.sendAlertButtonText}>
          {showSendAlert ? '✕ Cancel' : '📢 Send Alert to Fleet Manager'}
        </Text>
      </TouchableOpacity>

      {/* Send Alert Form */}
      {showSendAlert && (
        <View style={styles.sendAlertForm}>
          <Text style={styles.formTitle}>What would you like to report?</Text>
          
          {/* Category Picker */}
          <Text style={styles.label}>Category</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.categoryScroll}>
            {ALERT_CATEGORIES.map(cat => (
              <TouchableOpacity
                key={cat.id}
                style={[
                  styles.categoryChip,
                  alertCategory === cat.id && styles.categoryChipActive
                ]}
                onPress={() => setAlertCategory(cat.id)}
              >
                <Text style={styles.categoryChipText}>{cat.label}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>

          {/* Message Input */}
          <Text style={styles.label}>Your Message</Text>
          <TextInput
            style={styles.messageInput}
            placeholder="Describe the issue (min 5 chars)..."
            placeholderTextColor={COLORS.textSecondary}
            multiline
            numberOfLines={3}
            value={alertMessage}
            onChangeText={setAlertMessage}
            maxLength={500}
          />
          <Text style={styles.charCount}>{alertMessage.length}/500</Text>

          {/* Send Button */}
          <TouchableOpacity
            style={[styles.submitButton, sending && styles.submitButtonDisabled]}
            onPress={handleSendAlert}
            disabled={sending}
          >
            {sending ? (
              <ActivityIndicator size="small" color="white" />
            ) : (
              <Text style={styles.submitButtonText}>📤 Send Alert</Text>
            )}
          </TouchableOpacity>
        </View>
      )}

      {/* Notifications List */}
      {notifications.length === 0 ? (
        <View style={styles.emptyState}>
          <Text style={styles.emptyEmoji}>🔔</Text>
          <Text style={styles.emptyTitle}>No Notifications</Text>
          <Text style={styles.emptySubtitle}>
            All clear! Use the button above to send an alert if needed.
          </Text>
        </View>
      ) : (
        notifications.map((alert, index) => (
          <View
            key={alert.id || index}
            style={[
              styles.alertCard,
              { borderLeftColor: getAlertColor(alert.type, alert.severity) }
            ]}
          >
            <View style={styles.alertHeader}>
              <View style={styles.alertTypeRow}>
                <View style={[styles.alertDot, { backgroundColor: getAlertColor(alert.type, alert.severity) }]} />
                <Text style={styles.alertType}>
                  {alert.type?.replace(/_/g, ' ').toUpperCase() || 'ALERT'}
                </Text>
                {alert.severity && (
                  <View style={[styles.severityBadge, {
                    backgroundColor: alert.severity === 'critical' ? '#dc2626' :
                                    alert.severity === 'high' ? '#f59e0b' : '#3b82f6'
                  }]}>
                    <Text style={styles.severityText}>{alert.severity.toUpperCase()}</Text>
                  </View>
                )}
              </View>
              <Text style={styles.alertTime}>{formatTime(alert.created_at)}</Text>
            </View>
            <Text style={styles.alertMessage}>{alert.message}</Text>
            {alert.speed_kmh != null && (
              <Text style={styles.alertSpeed}>Speed: {alert.speed_kmh.toFixed(1)} km/h</Text>
            )}
          </View>
        ))
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.background },
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: COLORS.background },
  header: {
    backgroundColor: COLORS.primary,
    paddingTop: 50,
    paddingBottom: 20,
    paddingHorizontal: SPACING.lg,
    borderBottomLeftRadius: BORDER_RADIUS.xl,
    borderBottomRightRadius: BORDER_RADIUS.xl,
  },
  headerTitle: { color: COLORS.textLight, fontSize: 24, fontWeight: 'bold' },
  headerSubtitle: { color: COLORS.accentLight, fontSize: 14, marginTop: 4 },
  sendAlertButton: {
    margin: SPACING.md,
    padding: 16,
    backgroundColor: '#8b5cf6',
    borderRadius: BORDER_RADIUS.lg,
    alignItems: 'center',
    ...SHADOWS.medium,
  },
  sendAlertButtonText: { color: 'white', fontWeight: 'bold', fontSize: 15 },
  sendAlertForm: {
    margin: SPACING.md,
    marginTop: 0,
    padding: SPACING.md,
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    ...SHADOWS.medium,
  },
  formTitle: { fontSize: 16, fontWeight: 'bold', color: COLORS.textPrimary, marginBottom: SPACING.sm },
  label: { fontSize: 13, fontWeight: '600', color: COLORS.textSecondary, marginBottom: 6, marginTop: 8 },
  categoryScroll: { marginBottom: 4 },
  categoryChip: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: COLORS.gray100,
    marginRight: 8,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  categoryChipActive: { backgroundColor: '#8b5cf6', borderColor: '#8b5cf6' },
  categoryChipText: { fontSize: 13, color: COLORS.textPrimary },
  messageInput: {
    backgroundColor: COLORS.gray50,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: BORDER_RADIUS.md,
    padding: SPACING.sm,
    fontSize: 14,
    color: COLORS.textPrimary,
    minHeight: 80,
    textAlignVertical: 'top',
  },
  charCount: { textAlign: 'right', fontSize: 11, color: COLORS.textSecondary, marginTop: 2 },
  submitButton: {
    marginTop: SPACING.sm,
    padding: 14,
    backgroundColor: '#8b5cf6',
    borderRadius: BORDER_RADIUS.md,
    alignItems: 'center',
  },
  submitButtonDisabled: { opacity: 0.5 },
  submitButtonText: { color: 'white', fontWeight: 'bold', fontSize: 15 },
  emptyState: { alignItems: 'center', marginTop: 60, paddingHorizontal: SPACING.xl },
  emptyEmoji: { fontSize: 60, marginBottom: SPACING.md },
  emptyTitle: { fontSize: 20, fontWeight: 'bold', color: COLORS.textPrimary, marginBottom: 8 },
  emptySubtitle: { fontSize: 14, color: COLORS.textSecondary, textAlign: 'center', lineHeight: 22 },
  alertCard: {
    margin: SPACING.md,
    marginBottom: 0,
    padding: SPACING.md,
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    borderLeftWidth: 4,
    ...SHADOWS.medium,
  },
  alertHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 },
  alertTypeRow: { flexDirection: 'row', alignItems: 'center' },
  alertDot: { width: 10, height: 10, borderRadius: 5, marginRight: 8 },
  alertType: { fontSize: 12, fontWeight: 'bold', color: COLORS.textPrimary, letterSpacing: 1 },
  severityBadge: { marginLeft: 8, paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4 },
  severityText: { fontSize: 9, fontWeight: 'bold', color: 'white' },
  alertTime: { fontSize: 11, color: COLORS.textSecondary },
  alertMessage: { fontSize: 13, color: COLORS.textPrimary, lineHeight: 20 },
  alertSpeed: { fontSize: 11, color: COLORS.textSecondary, marginTop: 4 },
});