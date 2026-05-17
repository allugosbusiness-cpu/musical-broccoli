/**
 * Alert Manager Service
 * Handles alert deduplication and lifecycle to prevent memory issues
 */

class AlertManager {
  constructor() {
    // Track active alerts: { truckId: { alertType: alertData } }
    this.activeAlerts = new Map();
    
    // Track when alerts were last emitted to prevent duplicates
    this.lastEmittedTime = new Map();
    
    // Emit callbacks
    this.listeners = new Map();
    
    // Min time between duplicate alerts (5 seconds)
    this.MIN_EMIT_INTERVAL = 5000;
  }

  /**
   * Register event listener
   */
  on(eventType, callback) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, []);
    }
    this.listeners.get(eventType).push(callback);
  }

  /**
   * Emit event only if not recently emitted (deduplicated)
   */
  emitIfNew(truckId, alertType, data) {
    const key = `${truckId}:${alertType}`;
    const now = Date.now();
    const lastEmit = this.lastEmittedTime.get(key) || 0;

    // If recently emitted, skip
    if (now - lastEmit < this.MIN_EMIT_INTERVAL) {
      return false;
    }

    this.lastEmittedTime.set(key, now);
    this.emit(alertType, data);
    return true;
  }

  /**
   * Emit event to all listeners
   */
  emit(eventType, data) {
    const callbacks = this.listeners.get(eventType) || [];
    callbacks.forEach((cb) => {
      try {
        cb(data);
      } catch (e) {
        console.error(`Error in ${eventType} listener:`, e);
      }
    });
  }

  /**
   * Set active alert for a truck
   */
  setActive(truckId, alertType, data) {
    if (!this.activeAlerts.has(truckId)) {
      this.activeAlerts.set(truckId, {});
    }
    const truckAlerts = this.activeAlerts.get(truckId);
    truckAlerts[alertType] = { ...data, timestamp: Date.now() };
  }

  /**
   * Clear alert for a truck
   */
  clearAlert(truckId, alertType) {
    if (this.activeAlerts.has(truckId)) {
      delete this.activeAlerts.get(truckId)[alertType];
    }
  }

  /**
   * Get all active alerts
   */
  getActiveAlerts() {
    const alerts = [];
    this.activeAlerts.forEach((truckAlerts, truckId) => {
      Object.entries(truckAlerts).forEach(([alertType, data]) => {
        alerts.push({
          truckId,
          alertType,
          ...data,
        });
      });
    });
    return alerts;
  }

  /**
   * Get alerts for specific truck
   */
  getTruckAlerts(truckId) {
    return this.activeAlerts.get(truckId) || {};
  }

  /**
   * Clear all alerts for truck (e.g., when on-route again)
   */
  clearTruckAlerts(truckId) {
    this.activeAlerts.delete(truckId);
  }

  /**
   * Clean up old alerts (max 100 trucks to prevent memory bloat)
   */
  cleanup() {
    if (this.activeAlerts.size > 100) {
      const entriesToDelete = this.activeAlerts.size - 50; // Keep 50
      let deleted = 0;
      for (const [truckId] of this.activeAlerts) {
        if (deleted >= entriesToDelete) break;
        this.activeAlerts.delete(truckId);
        deleted++;
      }
    }

    // Also cleanup lastEmittedTime (keep last 1000 entries)
    if (this.lastEmittedTime.size > 1000) {
      const entries = Array.from(this.lastEmittedTime.entries());
      const oldestEntries = entries.slice(0, entries.length - 500);
      oldestEntries.forEach(([key]) => this.lastEmittedTime.delete(key));
    }
  }
}

export const alertManager = new AlertManager();
