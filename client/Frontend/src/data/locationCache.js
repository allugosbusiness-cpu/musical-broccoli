/**
 * Client-side location cache for OSM Nominatim autocomplete.
 * Reduces API calls to backend proxy, improving performance and privacy.
 * Uses LRU-like eviction: keeps last 100 unique queries.
 */

const CACHE_KEY = 'pulsetrack_location_cache_v2';
const MAX_ENTRIES = 100;
const CACHE_TTL_MS = 3600000; // 1 hour

// Clear legacy cache (pre-v2) to remove stale hardcoded data
try {
  const oldCache = localStorage.getItem('pulsetrack_location_cache');
  if (oldCache) {
    localStorage.removeItem('pulsetrack_location_cache');
    console.log('📍 [LocationCache] Cleared legacy cache (v1 → v2)');
  }
} catch (e) {
  // ignore
}

/**
 * Get all cached entries
 */
function getCache() {
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    if (!raw) return {};
    const cache = JSON.parse(raw);
    
    // Remove expired entries
    const now = Date.now();
    const valid = {};
    for (const [key, value] of Object.entries(cache)) {
      if (now - value.cachedAt < CACHE_TTL_MS) {
        valid[key] = value;
      }
    }
    
    // Update storage with cleaned cache
    localStorage.setItem(CACHE_KEY, JSON.stringify(valid));
    return valid;
  } catch {
    return {};
  }
}

/**
 * Get cached result for a query
 */
export function getCachedResults(query) {
  const cache = getCache();
  const key = query.toLowerCase().trim();
  if (cache[key]) {
    console.log(`📍 [LocationCache] HIT for: "${query}"`);
    return cache[key].results;
  }
  console.log(`📍 [LocationCache] MISS for: "${query}"`);
  return null;
}

/**
 * Store results in cache
 */
export function setCachedResults(query, results) {
  try {
    const cache = getCache();
    const key = query.toLowerCase().trim();
    
    // Add new entry
    cache[key] = {
      results,
      cachedAt: Date.now(),
    };
    
    // Evict oldest if over limit
    const entries = Object.entries(cache);
    if (entries.length > MAX_ENTRIES) {
      entries.sort((a, b) => a[1].cachedAt - b[1].cachedAt);
      const toRemove = entries.slice(0, entries.length - MAX_ENTRIES);
      for (const [key] of toRemove) {
        delete cache[key];
      }
    }
    
    localStorage.setItem(CACHE_KEY, JSON.stringify(cache));
    console.log(`📍 [LocationCache] Stored ${results.length} results for: "${query}"`);
  } catch (e) {
    console.warn('[LocationCache] Failed to cache:', e.message);
  }
}

/**
 * Clear the entire cache
 */
export function clearCache() {
  localStorage.removeItem(CACHE_KEY);
  console.log('📍 [LocationCache] Cleared');
}