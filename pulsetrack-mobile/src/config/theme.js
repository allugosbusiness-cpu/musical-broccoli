/**
 * PulseTrack Mobile Theme
 * Corporate fleet management app styling
 */

export const COLORS = {
  // Primary brand colors
  primary: '#1a237e',
  primaryDark: '#0d1259',
  primaryLight: '#534bae',
  
  // Accent colors
  accent: '#00bcd4',
  accentLight: '#62efff',
  accentDark: '#008ba3',
  
  // Status colors
  success: '#4caf50',
  warning: '#ff9800',
  danger: '#f44336',
  info: '#2196f3',
  
  // Mission status colors
  statusPlanned: '#9e9e9e',
  statusAssigned: '#2196f3',
  statusEnroute: '#ff9800',
  statusPaused: '#ffeb3b',
  statusCompleted: '#4caf50',
  statusCancelled: '#f44336',
  
  // Neutral colors
  white: '#ffffff',
  black: '#000000',
  gray50: '#fafafa',
  gray100: '#f5f5f5',
  gray200: '#eeeeee',
  gray300: '#e0e0e0',
  gray400: '#bdbdbd',
  gray500: '#9e9e9e',
  gray600: '#757575',
  gray700: '#616161',
  gray800: '#424242',
  gray900: '#212121',
  
  // Background
  background: '#f5f5f5',
  card: '#ffffff',
  surface: '#ffffff',
  
  // Text
  textPrimary: '#212121',
  textSecondary: '#757575',
  textLight: '#ffffff',
  textMuted: '#9e9e9e',
  
  // Alerts
  alertSpeed: '#f44336',
  alertRoute: '#ff9800',
  alertLocation: '#2196f3',
  alertMaintenance: '#9c27b0',
  alertDelivery: '#4caf50',
  
  // Specific UI
  border: '#e0e0e0',
  divider: '#eeeeee',
  overlay: 'rgba(0, 0, 0, 0.5)',
  transparent: 'transparent',
};

export const FONTS = {
  regular: {
    fontSize: 14,
    color: COLORS.textPrimary,
  },
  medium: {
    fontSize: 16,
    fontWeight: '500',
    color: COLORS.textPrimary,
  },
  bold: {
    fontSize: 16,
    fontWeight: 'bold',
    color: COLORS.textPrimary,
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: COLORS.textPrimary,
  },
  heading: {
    fontSize: 24,
    fontWeight: 'bold',
    color: COLORS.textPrimary,
  },
  small: {
    fontSize: 12,
    color: COLORS.textSecondary,
  },
  caption: {
    fontSize: 10,
    color: COLORS.textMuted,
  },
};

export const SPACING = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};

export const SHADOWS = {
  small: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  medium: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 4,
  },
  large: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 8,
    elevation: 8,
  },
};

export const BORDER_RADIUS = {
  sm: 4,
  md: 8,
  lg: 12,
  xl: 16,
  round: 50,
};

export const getMissionStatusColor = (status) => {
  const statusColors = {
    'planned': COLORS.statusPlanned,
    'assigned': COLORS.statusAssigned,
    'enroute': COLORS.statusEnroute,
    'paused': COLORS.statusPaused,
    'completed': COLORS.statusCompleted,
    'cancelled': COLORS.statusCancelled,
  };
  return statusColors[status] || COLORS.gray500;
};

export default {
  COLORS,
  FONTS,
  SPACING,
  SHADOWS,
  BORDER_RADIUS,
  getMissionStatusColor,
};