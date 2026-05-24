import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Alert,
  ActivityIndicator,
  TouchableOpacity,
  StatusBar,
} from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { useNavigation } from '@react-navigation/native';
import { COLORS, SPACING, SHADOWS, BORDER_RADIUS } from '../config/theme';
import apiService from '../services/apiService';
import storage from '../utils/storage';
import locationService from '../services/locationService';

const QRScannerScreen = ({ navigation: navProp, route }) => {
  // Use hook as primary source - more reliable than prop in async callbacks
  const navigation = useNavigation();
  const [permission, requestPermission] = useCameraPermissions();
  const [scanning, setScanning] = useState(true);
  const [loading, setLoading] = useState(false);
  const [flashMode, setFlashMode] = useState(false);
  const phoneNumber = route.params?.phoneNumber || '';
  const driverName = route.params?.driverName || 'Mobile Driver';

  useEffect(() => {
    try {
      console.log('[QRScanner] mounted - navigation available:', !!navigation);
      console.log('[QRScanner] navigation keys:', navigation ? Object.keys(navigation) : null);
      console.log('[QRScanner] route:', route);
    } catch (e) {
      // ignore
    }
  }, []);

  useEffect(() => {
    console.log('[QRScanner] permission state changed:', {
      permission: permission ? { granted: permission.granted, expires: permission.expires } : null,
    });
  }, [permission]);

  useEffect(() => {
    getCameraPermission();
  }, []);

  const getCameraPermission = async () => {
    if (permission?.granted) {
      console.log('[QRScanner] camera permission already granted');
      return;
    }

    console.log('[QRScanner] requesting camera permission...');
    try {
      const result = await requestPermission();
      console.log('[QRScanner] requestPermission result:', result);
      
      if (!result?.granted) {
        console.log('[QRScanner] camera permission denied - navigation:', !!navigation);
        Alert.alert(
          'Camera Permission Required',
          'Camera access is needed to scan QR codes for truck registration.',
          [
            {
              text: 'Go Back',
              onPress: () => {
                console.log('[QRScanner] Alert Go Back pressed - navigation:', !!navigation);
                navigation?.goBack?.();
              },
            },
            { text: 'Retry', onPress: getCameraPermission },
          ]
        );
      } else {
        console.log('[QRScanner] camera permission granted successfully');
      }
    } catch (err) {
      console.log('[QRScanner] error requesting permission:', err.message);
    }
  };

  const handleBarCodeScanned = async ({ type, data }) => {
    console.log('[QRScanner] ===== BARCODE DETECTED =====');
    console.log('[QRScanner] barcode type:', type);
    console.log('[QRScanner] barcode data:', data);
    console.log('[QRScanner] current scanning state:', scanning);
    console.log('[QRScanner] current loading state:', loading);

    if (!scanning || loading) {
      console.log('[QRScanner] ignoring barcode - scanning:', scanning, 'loading:', loading);
      return;
    }

    console.log('[QRScanner] processing barcode...');
    setScanning(false);
    setLoading(true);

    try {
      // Try to get current location for audit trail
      let location = null;
      try {
        location = await locationService.getCurrentPosition();
      } catch (e) {
        console.log('[QRScanner] location not available:', e.message);
      }

      console.log('[QRScanner] calling registerDriverByQR with:', { data, phoneNumber, driverName });
      const result = await apiService.registerDriverByQR(data, phoneNumber, driverName);
      console.log('[QRScanner] registerDriverByQR result:', result);

      if (result && result.success) {
        console.log('[QRScanner] registration success, saving session...');
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

        console.log('[QRScanner] registration success - navigation before replace:', !!navigation);
        Alert.alert(
          'Registration Successful',
          `Welcome ${result.driver_name}!\nLinked to truck: ${result.truck_name}`,
          [
            {
              text: 'View Missions',
              onPress: () => {
                console.log('[QRScanner] Alert View Missions pressed - navigation:', !!navigation);
                navigation?.replace?.('MainTabs');
              },
            },
          ]
        );
      } else {
        console.log('[QRScanner] registration failed:', result);
        Alert.alert('Registration Failed', result?.error || 'Invalid QR code');
        setScanning(true);
      }
    } catch (error) {
      console.log('[QRScanner] error during registration:', error.message, error);
      Alert.alert('Error', error.message);
      setScanning(true);
    } finally {
      setLoading(false);
    }
  };

  if (permission === null) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color={COLORS.primary} />
        <Text style={styles.loadingText}>Requesting camera permission...</Text>
      </View>
    );
  }

  if (!permission?.granted) {
    return (
      <View style={styles.container}>
        <Text style={styles.errorText}>Camera permission denied</Text>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigation?.goBack?.()}
        >
          <Text style={styles.backButtonText}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" />
      
      <CameraView
        style={styles.camera}
        facing="back"
        enableTorch={flashMode}
        onBarcodeScanned={handleBarCodeScanned}
        barcodeScannerSettings={{
          barcodeTypes: ['qr'],
        }}
      />
      
      {/* Overlay - positioned absolutely, not as children */}
      <View style={styles.overlay}>
        <View style={styles.overlayTop}>
          <TouchableOpacity
            style={styles.closeButton}
            onPress={() => navigation?.goBack?.()}
          >
            <Text style={styles.closeButtonText}>✕</Text>
          </TouchableOpacity>
          <Text style={styles.overlayTitle}>Scan Truck QR Code</Text>
        </View>

        {/* Scanner Frame */}
        <View style={styles.scannerFrameContainer}>
          <View style={styles.scannerFrame}>
            <View style={[styles.corner, styles.cornerTopLeft]} />
            <View style={[styles.corner, styles.cornerTopRight]} />
            <View style={[styles.corner, styles.cornerBottomLeft]} />
            <View style={[styles.corner, styles.cornerBottomRight]} />
            {loading && (
              <ActivityIndicator
                size="large"
                color={COLORS.accent}
                style={styles.scannerLoader}
              />
            )}
          </View>
          <Text style={styles.scannerInstruction}>
            Point camera at the QR code on the truck
          </Text>
        </View>

        {/* Flash toggle */}
        <View style={styles.overlayBottom}>
          <TouchableOpacity
            style={[styles.flashButton, flashMode && styles.flashButtonActive]}
            onPress={() => setFlashMode(!flashMode)}
          >
            <Text style={styles.flashIcon}>{flashMode ? '🔦' : '💡'}</Text>
            <Text style={styles.flashText}>
              {flashMode ? 'Flash On' : 'Flash Off'}
            </Text>
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.black,
  },
  camera: {
    flex: 1,
  },
  overlay: {
    ...StyleSheet.absoluteFillObject,
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.3)',
    justifyContent: 'space-between',
    pointerEvents: 'box-none',
  },
  overlayTop: {
    paddingTop: 60,
    paddingHorizontal: SPACING.lg,
    flexDirection: 'row',
    alignItems: 'center',
  },
  closeButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: SPACING.md,
  },
  closeButtonText: {
    color: COLORS.white,
    fontSize: 20,
    fontWeight: 'bold',
  },
  overlayTitle: {
    color: COLORS.white,
    fontSize: 18,
    fontWeight: 'bold',
  },
  scannerFrameContainer: {
    alignItems: 'center',
  },
  scannerFrame: {
    width: 250,
    height: 250,
    justifyContent: 'center',
    alignItems: 'center',
  },
  corner: {
    position: 'absolute',
    width: 40,
    height: 40,
    borderColor: COLORS.accent,
  },
  cornerTopLeft: {
    top: 0,
    left: 0,
    borderTopWidth: 4,
    borderLeftWidth: 4,
  },
  cornerTopRight: {
    top: 0,
    right: 0,
    borderTopWidth: 4,
    borderRightWidth: 4,
  },
  cornerBottomLeft: {
    bottom: 0,
    left: 0,
    borderBottomWidth: 4,
    borderLeftWidth: 4,
  },
  cornerBottomRight: {
    bottom: 0,
    right: 0,
    borderBottomWidth: 4,
    borderRightWidth: 4,
  },
  scannerLoader: {
    position: 'absolute',
  },
  scannerInstruction: {
    color: COLORS.white,
    fontSize: 14,
    marginTop: SPACING.lg,
    textAlign: 'center',
  },
  overlayBottom: {
    paddingBottom: 80,
    alignItems: 'center',
  },
  flashButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.md,
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: BORDER_RADIUS.md,
  },
  flashButtonActive: {
    backgroundColor: 'rgba(255,255,0,0.3)',
  },
  flashIcon: {
    fontSize: 20,
    marginRight: SPACING.sm,
  },
  flashText: {
    color: COLORS.white,
    fontSize: 14,
  },
  loadingText: {
    color: COLORS.white,
    fontSize: 16,
    marginTop: SPACING.lg,
    textAlign: 'center',
  },
  errorText: {
    color: COLORS.red,
    fontSize: 16,
    textAlign: 'center',
    marginBottom: SPACING.lg,
  },
  backButton: {
    paddingHorizontal: SPACING.lg,
    paddingVertical: SPACING.md,
    backgroundColor: COLORS.primary,
    borderRadius: BORDER_RADIUS.md,
  },
  backButtonText: {
    color: COLORS.white,
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default QRScannerScreen;