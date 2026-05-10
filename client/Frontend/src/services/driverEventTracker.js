/**
 * Driver Event Tracker
 * Monitors truck events: stops, speed drops, maintenance, off-route, etc.
 */

class DriverEventTracker {
  constructor() {
    this.truckStates = {}; // Per-truck state tracking
    this.events = {}; // Queue of events per truck
    this.eventCallbacks = {}; // Callback functions
  }

  /**
   * Register event callback
   */
  on(eventType, callback) {
    this.eventCallbacks[eventType] = callback;
  }

  /**
   * Emit event with data
   */
  emitEvent(eventType, data) {
    if (this.eventCallbacks[eventType]) {
      this.eventCallbacks[eventType](data);
    }
    console.log(`📢 Event: ${eventType}`, data);
  }

  /**
   * Track truck GPS update and detect events
   */
  trackTruck(truck, previousTruck = null) {
    const truckId = truck.id;

    // Initialize state if needed
    if (!this.truckStates[truckId]) {
      this.truckStates[truckId] = {
        speed: truck.speed || 0,
        location: truck.location,
        status: truck.status,
        stoppedAt: null,
        stoppedSince: null,
        speedDropDetected: false,
        lastSpeedDropTime: null,
        coordinates: truck.coordinates,
      };
    }

    const prevState = this.truckStates[truckId];
    const currentSpeed = truck.speed || 0;
    const wasMoving = prevState.speed > 5;
    const isNowStopped = currentSpeed <= 5;

    // EVENT 1: TRUCK STOPPED
    if (wasMoving && isNowStopped && !prevState.stoppedAt) {
      prevState.stoppedAt = truck.location;
      prevState.stoppedSince = new Date();

      this.emitEvent('driver-stopped', {
        truckId,
        truck,
        location: truck.location,
        coordinates: truck.coordinates,
        timestamp: prevState.stoppedSince,
        speed: currentSpeed,
      });
    }

    // EVENT 2: TRUCK RESUMED
    if (!wasMoving && currentSpeed > 5 && prevState.stoppedAt) {
      const stoppedDuration = (new Date() - prevState.stoppedSince) / 1000; // seconds
      const stoppedMinutes = Math.round(stoppedDuration / 60);

      this.emitEvent('driver-resumed', {
        truckId,
        truck,
        stoppedAt: prevState.stoppedAt,
        stoppedDuration: stoppedDuration,
        stoppedMinutes: stoppedMinutes,
        timestamp: new Date(),
      });

      prevState.stoppedAt = null;
      prevState.stoppedSince = null;
    }

    // EVENT 3: SPEED DROP (sudden deceleration)
    if (previousTruck && previousTruck.speed > 0) {
      const speedDrop = previousTruck.speed - currentSpeed;
      const isDropSignificant = speedDrop > 20; // >20 km/h drop

      if (isDropSignificant && !prevState.speedDropDetected) {
        prevState.speedDropDetected = true;
        prevState.lastSpeedDropTime = new Date();

        this.emitEvent('speed-drop', {
          truckId,
          truck,
          previousSpeed: previousTruck.speed,
          currentSpeed: currentSpeed,
          speedDrop: speedDrop,
          location: truck.location,
          coordinates: truck.coordinates,
          timestamp: prevState.lastSpeedDropTime,
        });

        // Reset after 30 seconds
        setTimeout(() => {
          prevState.speedDropDetected = false;
        }, 30000);
      }
    }

    // EVENT 4: MAINTENANCE MODE
    if (previousTruck && previousTruck.status !== 'maintenance' && truck.status === 'maintenance') {
      this.emitEvent('maintenance-started', {
        truckId,
        truck,
        location: truck.location,
        coordinates: truck.coordinates,
        timestamp: new Date(),
      });
    }

    // EVENT 5: MAINTENANCE COMPLETED
    if (previousTruck && previousTruck.status === 'maintenance' && truck.status !== 'maintenance') {
      this.emitEvent('maintenance-completed', {
        truckId,
        truck,
        location: truck.location,
        timestamp: new Date(),
      });
    }

    // EVENT 6: DELAYED STATUS
    if (previousTruck && previousTruck.status !== 'delayed' && truck.status === 'delayed') {
      this.emitEvent('truck-delayed', {
        truckId,
        truck,
        location: truck.location,
        coordinates: truck.coordinates,
        timestamp: new Date(),
      });
    }

    // EVENT 7: DELIVERED
    if (previousTruck && previousTruck.status !== 'delivered' && truck.status === 'delivered') {
      this.emitEvent('delivery-completed', {
        truckId,
        truck,
        location: truck.location,
        coordinates: truck.coordinates,
        timestamp: new Date(),
      });
    }

    // EVENT 8: OFF-ROUTE (if off-route flag detected)
    if (truck.off_route && !prevState.offRouteDetected) {
      prevState.offRouteDetected = true;

      this.emitEvent('off-route-detected', {
        truckId,
        truck,
        location: truck.location,
        coordinates: truck.coordinates,
        timestamp: new Date(),
        detectedAt: truck.coordinates,
      });
    }

    // Clear off-route flag when back on route
    if (!truck.off_route && prevState.offRouteDetected) {
      prevState.offRouteDetected = false;

      this.emitEvent('back-on-route', {
        truckId,
        truck,
        location: truck.location,
        coordinates: truck.coordinates,
        timestamp: new Date(),
      });
    }

    // Update state
    prevState.speed = currentSpeed;
    prevState.location = truck.location;
    prevState.status = truck.status;
    prevState.coordinates = truck.coordinates;
  }

  /**
   * Get current state of a truck
   */
  getState(truckId) {
    return this.truckStates[truckId] || null;
  }

  /**
   * Get all active events
   */
  getActiveEvents() {
    return this.events;
  }

  /**
   * Clear state for a truck (e.g., when deleted)
   */
  clearTruck(truckId) {
    delete this.truckStates[truckId];
    delete this.events[truckId];
  }
}

// Singleton instance
export const driverEventTracker = new DriverEventTracker();
