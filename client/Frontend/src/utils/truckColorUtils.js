/**
 * Truck Color Utilities
 * HSL hash-based color assignment with persistent storage
 */

/**
 * Generate deterministic HSL color from truck ID
 * Uses MD5-style hashing for consistent color assignment
 */
export function generateColorFromTruckId(truckId) {
  // Simple hash function
  let hash = 0;
  for (let i = 0; i < truckId.length; i++) {
    const char = truckId.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32bit integer
  }

  // Convert hash to hue (0-359)
  const hue = Math.abs(hash) % 360;

  // Fixed saturation and lightness for professional look
  const saturation = 75; // 75% saturation - vivid but not oversaturated
  const lightness = 50; // 50% lightness - good contrast

  return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}

/**
 * Convert HSL to RGB hex
 */
export function hslToRgb(hslString) {
  // Parse hsl(h, s%, l%)
  const match = hslString.match(/hsl\((\d+),\s*(\d+)%,\s*(\d+)%\)/);
  if (!match) return '#0066cc'; // Fallback

  const h = parseInt(match[1]) / 360;
  const s = parseInt(match[2]) / 100;
  const l = parseInt(match[3]) / 100;

  let r, g, b;

  if (s === 0) {
    r = g = b = l;
  } else {
    const hue2rgb = (p, q, t) => {
      if (t < 0) t += 1;
      if (t > 1) t -= 1;
      if (t < 1 / 6) return p + (q - p) * 6 * t;
      if (t < 1 / 2) return q;
      if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6;
      return p;
    };

    const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
    const p = 2 * l - q;
    r = hue2rgb(p, q, h + 1 / 3);
    g = hue2rgb(p, q, h);
    b = hue2rgb(p, q, h - 1 / 3);
  }

  const toHex = (x) => {
    const hex = Math.round(x * 255).toString(16);
    return hex.length === 1 ? '0' + hex : hex;
  };

  return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

/**
 * Get complementary color for overlap visualization
 */
export function getComplementaryColor(hslString) {
  const match = hslString.match(/hsl\((\d+),\s*(\d+)%,\s*(\d+)%\)/);
  if (!match) return '#ff6600';

  const hue = (parseInt(match[1]) + 180) % 360;
  const saturation = match[2];
  const lightness = Math.min(parseInt(match[3]) + 10, 90); // Slightly lighter

  return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}

/**
 * Get high-contrast color for colorblind accessibility
 */
export function getColorblindColor(truckId, colorblindMode = 'deuteranopia') {
  // Colorblind palette recommendations
  const colorblindPalettes = {
    protanopia: [
      '#1f77b4', // Blue
      '#ff7f0e', // Orange
      '#2ca02c', // Green
      '#d62728', // Red
      '#9467bd', // Purple
      '#8c564b', // Brown
    ],
    deuteranopia: [
      '#1f77b4', // Blue
      '#ff7f0e', // Orange
      '#2ca02c', // Green
      '#e377c2', // Pink
      '#7f7f7f', // Gray
      '#bcbd22', // Olive
    ],
    tritanopia: [
      '#e41a1c', // Red
      '#377eb8', // Blue
      '#4daf4a', // Green
      '#984ea3', // Purple
      '#ff7f00', // Orange
      '#a65628', // Brown
    ],
  };

  const palette = colorblindPalettes[colorblindMode] || colorblindPalettes.deuteranopia;
  const hash = truckId.charCodeAt(0) % palette.length;
  return palette[hash];
}

/**
 * Truck color storage (localStorage or database)
 */
class TruckColorStore {
  constructor() {
    this.colors = new Map();
    this.loadFromStorage();
  }

  loadFromStorage() {
    try {
      const stored = localStorage.getItem('truckColors');
      if (stored) {
        const data = JSON.parse(stored);
        this.colors = new Map(Object.entries(data));
      }
    } catch (error) {
      console.warn('Failed to load truck colors from storage:', error);
    }
  }

  saveToStorage() {
    try {
      const data = Object.fromEntries(this.colors);
      localStorage.setItem('truckColors', JSON.stringify(data));
    } catch (error) {
      console.warn('Failed to save truck colors to storage:', error);
    }
  }

  assignColor(truckId, color = null) {
    if (this.colors.has(truckId)) {
      return this.colors.get(truckId);
    }

    const assignedColor = color || generateColorFromTruckId(truckId);
    this.colors.set(truckId, assignedColor);
    this.saveToStorage();
    return assignedColor;
  }

  getColor(truckId) {
    return this.colors.get(truckId) || this.assignColor(truckId);
  }

  getAllColors() {
    return Object.fromEntries(this.colors);
  }

  clearAll() {
    this.colors.clear();
    localStorage.removeItem('truckColors');
  }
}

export const colorStore = new TruckColorStore();

/**
 * Generate trail style options
 */
export function getTrailStyle(truckId, options = {}) {
  const {
    color = colorStore.getColor(truckId),
    isActive = true,
    isOverlapping = false,
    colorblindMode = null,
    width = isActive ? 4 : 2,
  } = options;

  const finalColor = colorblindMode ? getColorblindColor(truckId, colorblindMode) : color;

  return {
    color: finalColor,
    weight: width,
    opacity: isOverlapping ? 0.6 : 0.85,
    lineCap: 'round',
    lineJoin: 'round',
    dashArray: isOverlapping ? '5, 5' : null,
    // Glow/shadow effect (via CSS or L.CircleMarker)
    className: `trail-${truckId}${isOverlapping ? ' trail-overlapping' : ''}`,
  };
}

export default {
  generateColorFromTruckId,
  hslToRgb,
  getComplementaryColor,
  getColorblindColor,
  colorStore,
  getTrailStyle,
};
