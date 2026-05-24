import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  StatusBar,
} from 'react-native';
import { COLORS, SPACING, SHADOWS, BORDER_RADIUS } from '../config/theme';
import apiService from '../services/apiService';
import storage from '../utils/storage';
import locationService from '../services/locationService';

const LoginScreen = ({ navigation, route }) => {
  const [phoneNumber, setPhoneNumber] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [pinCode, setPinCode] = useState('');
  const [isRegistering, setIsRegistering] = useState(false);
  const [loading, setLoading] = useState(false);
  const [method, setMethod] = useState('pin'); // 'pin' or 'qr'

  useEffect(() => {
    checkSavedSession();
  }, []);

  const checkSavedSession = async () => {
    const session = await storage.getDriverSession();
    if (session && session.driver_id) {
      navigation.replace('MainTabs');
    }
  };

  const handleRegisterByPin = async () => {
    if (!phoneNumber || !pinCode) {
      Alert.alert('Validation Error', 'Please enter phone number and PIN code');
      return;
    }
    if (pinCode.length !== 6) {
      Alert.alert('Validation Error', 'PIN code must be 6 characters');
      return;
    }

    setLoading(true);
    try {
      let location = null;
      try {
        location = await locationService.getCurrentPosition();
      } catch (e) {
        // Location not essential for registration
      }

      const result = await apiService.validatePin(
        pinCode,
        phoneNumber,
        firstName,
        lastName,
        location
      );

      if (result && result.success) {
        await storage.saveDriverSession({
          driver_id: result.driver_id,
          truck_id: result.truck_id,
          tracking_id: result.tracking_id,
          token: result.token,
          driver_name: result.driver_name,
          truck_name: result.truck_name,
          phone_number: result.phone_number,
          gps_tracking_enabled: result.gps_tracking_enabled,
        });

        await storage.saveDriverProfile({
          driver_id: result.driver_id,
          driver_name: result.driver_name,
          truck_name: result.truck_name,
          phone_number: result.phone_number,
        });

        Alert.alert('Registration Successful', `Welcome ${result.driver_name}!`, [
          { text: 'OK', onPress: () => navigation.replace('MainTabs') },
        ]);
      } else {
        Alert.alert('Registration Failed', result.error || 'Invalid PIN or phone number');
      }
    } catch (error) {
      Alert.alert('Error', error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRegisterByQR = () => {
    if (!phoneNumber) {
      Alert.alert('Validation Error', 'Please enter your phone number first');
      return;
    }
    if (!firstName && !lastName) {
      Alert.alert('Validation Error', 'Please enter your name (first name at minimum)');
      return;
    }
    const driverName = `${firstName} ${lastName}`.trim();
    navigation.navigate('QRScanner', {
      phoneNumber: phoneNumber,
      driverName: driverName,
    });
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <StatusBar backgroundColor={COLORS.primaryDark} barStyle="light-content" />
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
      >
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.logoContainer}>
            <Text style={styles.logoEmoji}>🚛</Text>
          </View>
          <Text style={styles.title}>PulseTrack</Text>
          <Text style={styles.subtitle}>Driver Registration</Text>
        </View>

        {/* Registration Method Toggle */}
        <View style={styles.methodToggle}>
          <TouchableOpacity
            style={[styles.methodButton, method === 'pin' && styles.methodButtonActive]}
            onPress={() => setMethod('pin')}
          >
            <Text style={[styles.methodText, method === 'pin' && styles.methodTextActive]}>
              PIN Code
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.methodButton, method === 'qr' && styles.methodButtonActive]}
            onPress={() => setMethod('qr')}
          >
            <Text style={[styles.methodText, method === 'qr' && styles.methodTextActive]}>
              QR Code
            </Text>
          </TouchableOpacity>
        </View>

        {/* Form */}
        <View style={styles.formContainer}>
          <Text style={styles.formTitle}>
            {method === 'pin' ? 'Enter PIN from Manager' : 'Scan QR on Truck'}
          </Text>

          {/* Name Fields */}
          <View style={styles.nameRow}>
            <View style={[styles.inputHalf, styles.inputContainer]}>
              <Text style={styles.inputLabel}>First Name</Text>
              <TextInput
                style={styles.input}
                placeholder="John"
                placeholderTextColor={COLORS.gray400}
                value={firstName}
                onChangeText={setFirstName}
                autoCapitalize="words"
              />
            </View>
            <View style={[styles.inputHalf, styles.inputContainer]}>
              <Text style={styles.inputLabel}>Last Name</Text>
              <TextInput
                style={styles.input}
                placeholder="Doe"
                placeholderTextColor={COLORS.gray400}
                value={lastName}
                onChangeText={setLastName}
                autoCapitalize="words"
              />
            </View>
          </View>

          {/* Phone Number */}
          <View style={styles.inputContainer}>
            <Text style={styles.inputLabel}>Phone Number</Text>
            <TextInput
              style={styles.input}
              placeholder="+256 700 000 000"
              placeholderTextColor={COLORS.gray400}
              value={phoneNumber}
              onChangeText={setPhoneNumber}
              keyboardType="phone-pad"
              autoCapitalize="none"
            />
          </View>

          {/* PIN Code (only if pin method) */}
          {method === 'pin' && (
            <View style={styles.inputContainer}>
              <Text style={styles.inputLabel}>PIN Code</Text>
              <TextInput
                style={[styles.input, styles.pinInput]}
                placeholder="6-digit PIN"
                placeholderTextColor={COLORS.gray400}
                value={pinCode}
                onChangeText={setPinCode}
                keyboardType="number-pad"
                maxLength={6}
                secureTextEntry
              />
            </View>
          )}

          {/* Submit Button */}
          {loading ? (
            <ActivityIndicator size="large" color={COLORS.primary} style={styles.loader} />
          ) : (
            <TouchableOpacity
              style={styles.submitButton}
              onPress={method === 'pin' ? handleRegisterByPin : handleRegisterByQR}
            >
              <Text style={styles.submitButtonText}>
                {method === 'pin' ? 'Register with PIN' : 'Scan QR Code'}
              </Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Instructions */}
        <View style={styles.instructionsContainer}>
          <Text style={styles.instructionsTitle}>How it works:</Text>
          <Text style={styles.instructionItem}>
            1. Enter your name and phone number
          </Text>
          <Text style={styles.instructionItem}>
            2. {' '}
            {method === 'pin'
              ? 'Enter the 6-digit PIN from your fleet manager'
              : 'Scan the QR code on your assigned truck'}
          </Text>
          <Text style={styles.instructionItem}>
            3. View available missions and start tracking
          </Text>
          <Text style={styles.instructionItem}>
            4. Your GPS location and speed will be sent to the fleet manager
          </Text>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  scrollContent: {
    flexGrow: 1,
    paddingBottom: 40,
  },
  header: {
    backgroundColor: COLORS.primary,
    paddingTop: 60,
    paddingBottom: 40,
    alignItems: 'center',
    borderBottomLeftRadius: BORDER_RADIUS.xl,
    borderBottomRightRadius: BORDER_RADIUS.xl,
  },
  logoContainer: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: 'rgba(255,255,255,0.15)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  logoEmoji: {
    fontSize: 40,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: COLORS.textLight,
  },
  subtitle: {
    fontSize: 16,
    color: COLORS.accentLight,
    marginTop: 4,
  },
  methodToggle: {
    flexDirection: 'row',
    marginHorizontal: SPACING.lg,
    marginTop: -20,
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: 4,
    ...SHADOWS.medium,
  },
  methodButton: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    borderRadius: BORDER_RADIUS.md,
  },
  methodButtonActive: {
    backgroundColor: COLORS.primary,
  },
  methodText: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.textSecondary,
  },
  methodTextActive: {
    color: COLORS.textLight,
  },
  formContainer: {
    margin: SPACING.lg,
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    padding: SPACING.lg,
    ...SHADOWS.small,
  },
  formTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: COLORS.textPrimary,
    marginBottom: SPACING.md,
    textAlign: 'center',
  },
  nameRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  inputHalf: {
    width: '48%',
  },
  inputContainer: {
    marginBottom: SPACING.md,
  },
  inputLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.textSecondary,
    marginBottom: 6,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  input: {
    backgroundColor: COLORS.gray50,
    borderWidth: 1,
    borderColor: COLORS.border,
    borderRadius: BORDER_RADIUS.md,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 16,
    color: COLORS.textPrimary,
  },
  pinInput: {
    fontSize: 24,
    letterSpacing: 8,
    textAlign: 'center',
    fontWeight: 'bold',
  },
  submitButton: {
    backgroundColor: COLORS.primary,
    borderRadius: BORDER_RADIUS.md,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: SPACING.sm,
    ...SHADOWS.medium,
  },
  submitButtonText: {
    color: COLORS.textLight,
    fontSize: 16,
    fontWeight: 'bold',
  },
  loader: {
    marginVertical: SPACING.lg,
  },
  instructionsContainer: {
    marginHorizontal: SPACING.lg,
    padding: SPACING.md,
    backgroundColor: COLORS.card,
    borderRadius: BORDER_RADIUS.lg,
    borderLeftWidth: 4,
    borderLeftColor: COLORS.accent,
    marginTop: SPACING.sm,
  },
  instructionsTitle: {
    fontSize: 14,
    fontWeight: 'bold',
    color: COLORS.textPrimary,
    marginBottom: 8,
  },
  instructionItem: {
    fontSize: 13,
    color: COLORS.textSecondary,
    marginBottom: 4,
    lineHeight: 20,
  },
});

export default LoginScreen;