/**
 * API Configuration for PulseTrack
 * 
 * This configuration supports multiple network scenarios:
 * - Local development (localhost:8000)
 * - Same LAN network (192.168.x.x)
 * - Different networks (via public IP or domain)
 * - Emulator/Simulator (special IPs like 10.0.2.2)
 * 
 * CONFIGURATION GUIDE:
 * 1. Development: Use localhost or your machine IP
 * 2. Testing on Physical Devices: Use your computer's LAN IP
 * 3. Production: Use domain name or public IP with HTTPS
 */

// Environment detection
const isDevelopment = import.meta.env.MODE === 'development';
const isProduction = import.meta.env.MODE === 'production';

// Get API base URL - prioritize environment variable, then fallback to defaults
const getApiBaseUrl = () => {
  // Check for explicit environment variable
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }

  // Development defaults
  if (isDevelopment) {
    // Try to detect if we're behind a proxy or on a specific IP
    // For local development, use localhost
    return 'http://localhost:8000/api';
  }

  // Production - use Railway backend
  if (isProduction) {
    return 'https://web-production-691ff.up.railway.app/api/v1';
  }

  return 'https://web-production-691ff.up.railway.app/api/v1';
};

// Retry configuration for network resilience
export const RETRY_CONFIG = {
  maxRetries: 3,
  retryDelay: 1000, // ms
  backoffMultiplier: 2,
  timeoutMs: 15000,
  retryableStatusCodes: [408, 429, 500, 502, 503, 504], // Timeout, TooManyRequests, ServerErrors
};

// API configuration  
export const API_CONFIG = {
  baseUrl: getApiBaseUrl(),
  timeout: RETRY_CONFIG.timeoutMs,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
};

/**
 * Create API URL with proper error handling
 * Validates that the URL is configured correctly
 */
export const getValidatedApiUrl = () => {
  const url = API_CONFIG.baseUrl;
  
  if (!url) {
    throw new Error(
      'API_BASE_URL is not configured. ' +
      'Set VITE_API_BASE_URL environment variable or check your .env file'
    );
  }

  // Warn if using localhost in production
  if (isProduction && url.includes('localhost')) {
    console.warn(
      '⚠️ WARNING: Using localhost API in production. ' +
      'This will not work for real devices. ' +
      'Set VITE_API_BASE_URL to your server IP or domain.'
    );
  }

  return url;
};

/**
 * Helper to check if API is reachable
 */
export const checkApiHealth = async () => {
  try {
    const response = await fetch(`${API_CONFIG.baseUrl}/health/`, {
      method: 'GET',
    });
    return response.ok;
  } catch (error) {
    console.error('API health check failed:', error);
    return false;
  }
};

export default API_CONFIG;
