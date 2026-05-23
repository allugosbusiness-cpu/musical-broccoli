/**
 * PulseTrack Mobile App
 * Fleet Management Driver Application
 * 
 * Handles driver registration via QR/PIN, mission management,
 * GPS location tracking, speed monitoring, and alerting.
 * Communicates with PulseTrack backend at:
 * https://pulsetrack-back.onrender.com/api/v1
 */

import React, { useEffect, useState, useRef } from 'react';
import { StatusBar, LogBox } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import AppNavigator from './src/navigation/AppNavigator';
import SplashScreen from './src/screens/SplashScreen';
import storage from './src/utils/storage';

// Suppress known warnings
LogBox.ignoreLogs([
  'Non-serializable values were found in the navigation state',
  'VirtualizedLists should never be nested',
]);

export default function App() {
  const [isLoading, setIsLoading] = useState(true);
  const navRef = useRef(null);

  useEffect(() => {
    // Perform app initialization
    initApp();
  }, []);

  const initApp = async () => {
    try {
      // Check for existing session
      const session = await storage.getDriverSession();
      
      // Load app settings
      const settings = await storage.getAppSettings();

      // Show splash for a brief moment
      await new Promise(resolve => setTimeout(resolve, 2000));
    } catch (error) {
      console.error('App initialization error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return <SplashScreen />;
  }

  return (
    <NavigationContainer ref={navRef}>
      <StatusBar
        barStyle="light-content"
        backgroundColor="#0d1259"
        translucent={false}
      />
      <AppNavigator />
    </NavigationContainer>
  );
}