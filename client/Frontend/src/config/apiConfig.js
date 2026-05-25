/**
 * API Configuration for PulseTrack
 * 
 * All environments align to use /api/v1/ prefix consistently.
 */
const isDevelopment = import.meta.env.MODE === 'development';
const isProduction = import.meta.env.MODE === 'production';

const getApiBaseUrl = () => {
  if (import.meta.env.VITE_API_BASE_URL) {
    let url = import.meta.env.VITE_API_BASE_URL;
    // Ensure /api/v1 suffix
    if (!url.endsWith('/api/v1') && !url.endsWith('/api/v1/')) {
      url = url.replace(/\/+$/, '') + '/api/v1';
    }
    return url;
  }
  if (isDevelopment) {
    return 'http://localhost:8000/api/v1';
  }
  // Production
  const backendUrl = import.meta.env.VITE_BACKEND_URL;
  if (backendUrl) return `${backendUrl}/api/v1`;
  return 'https://pulsetrack-back.onrender.com/api/v1';
};

export const RETRY_CONFIG = {
  maxRetries: 3,
  retryDelay: 1000,
  backoffMultiplier: 2,
  timeoutMs: 15000,
  retryableStatusCodes: [408, 429, 500, 502, 503, 504],
};

export const API_CONFIG = {
  baseUrl: getApiBaseUrl(),
  timeout: RETRY_CONFIG.timeoutMs,
  headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
};

export const getValidatedApiUrl = () => {
  const url = API_CONFIG.baseUrl;
  if (!url) throw new Error('API_BASE_URL is not configured');
  if (isProduction && url.includes('localhost')) {
    console.warn('⚠️ Using localhost API in production - will not work for real devices.');
  }
  return url;
};

export const checkApiHealth = async () => {
  try {
    const response = await fetch(`${API_CONFIG.baseUrl}/health/`, { method: 'GET' });
    return response.ok;
  } catch { return false; }
};

export default API_CONFIG;