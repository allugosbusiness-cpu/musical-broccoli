import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  StatusBar,
} from 'react-native';
import { COLORS } from '../config/theme';

const SplashScreen = ({ navigation }) => {
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const scaleAnim = useRef(new Animated.Value(0.3)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 1000,
        useNativeDriver: true,
      }),
      Animated.spring(scaleAnim, {
        toValue: 1,
        friction: 4,
        tension: 40,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  return (
    <View style={styles.container}>
      <StatusBar backgroundColor={COLORS.primaryDark} barStyle="light-content" />
      <Animated.View
        style={[
          styles.logoContainer,
          {
            opacity: fadeAnim,
            transform: [{ scale: scaleAnim }],
          },
        ]}
      >
        <View style={styles.logoIcon}>
          <Text style={styles.logoEmoji}>🚛</Text>
        </View>
        <Text style={styles.title}>PulseTrack</Text>
        <Text style={styles.subtitle}>Fleet Management</Text>
        <Text style={styles.tagline}>Real-time fleet tracking & monitoring</Text>
      </Animated.View>

      <Animated.Text style={[styles.loadingText, { opacity: fadeAnim }]}>
        Loading...
      </Animated.Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },
  logoContainer: {
    alignItems: 'center',
  },
  logoIcon: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: 'rgba(255,255,255,0.15)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
  },
  logoEmoji: {
    fontSize: 50,
  },
  title: {
    fontSize: 36,
    fontWeight: 'bold',
    color: COLORS.textLight,
    letterSpacing: 2,
  },
  subtitle: {
    fontSize: 18,
    color: COLORS.accentLight,
    fontWeight: '600',
    marginTop: 4,
  },
  tagline: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.7)',
    marginTop: 12,
  },
  loadingText: {
    position: 'absolute',
    bottom: 80,
    color: 'rgba(255,255,255,0.5)',
    fontSize: 14,
  },
});

export default SplashScreen;