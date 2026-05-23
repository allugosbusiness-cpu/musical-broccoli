import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { COLORS } from '../config/theme';

import LoginScreen from '../screens/LoginScreen';
import QRScannerScreen from '../screens/QRScannerScreen';
import HomeScreen from '../screens/HomeScreen';
import MissionsScreen from '../screens/MissionsScreen';
import TrackingScreen from '../screens/TrackingScreen';
import AlertsScreen from '../screens/AlertsScreen';
import ProfileScreen from '../screens/ProfileScreen';

const Stack = createNativeStackNavigator();

const AppNavigator = () => {
  return (
    <Stack.Navigator
      initialRouteName="Login"
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: COLORS.background },
        animation: 'slide_from_right',
      }}
    >
      <Stack.Screen name="Login" component={LoginScreen} />
      <Stack.Screen
        name="QRScanner"
        component={QRScannerScreen}
        options={{
          animation: 'slide_from_bottom',
          headerShown: false,
        }}
      />
      <Stack.Screen name="MainTabs" component={HomeScreen} />
      <Stack.Screen
        name="Home"
        component={HomeScreen}
        options={{
          headerShown: false,
        }}
      />
      <Stack.Screen
        name="Missions"
        component={MissionsScreen}
        options={{
          headerShown: false,
        }}
      />
      <Stack.Screen
        name="Tracking"
        component={TrackingScreen}
        options={{
          headerShown: false,
          animation: 'fade',
        }}
      />
      <Stack.Screen
        name="Alerts"
        component={AlertsScreen}
        options={{
          headerShown: false,
        }}
      />
      <Stack.Screen
        name="Profile"
        component={ProfileScreen}
        options={{
          headerShown: false,
        }}
      />
    </Stack.Navigator>
  );
};

export default AppNavigator;