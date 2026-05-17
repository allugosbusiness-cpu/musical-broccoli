import { useEffect, useRef } from 'react';

/**
 * Driver Event Alerts Component
 * Sends native browser notifications for critical events
 */
export default function DriverEventAlerts({ tracker }) {
  const notifiedRef = useRef(new Set());
  const permissionRequestedRef = useRef(false);

  // Request notification permission immediately on mount
  useEffect(() => {
    if (!permissionRequestedRef.current) {
      permissionRequestedRef.current = true;
      
      if ('Notification' in window) {
        console.log('🔔 Notification API available');
        console.log('🔔 Current permission:', Notification.permission);
        
        if (Notification.permission === 'default') {
          console.log('🔔 Requesting notification permission...');
          Notification.requestPermission().then(permission => {
            console.log('🔔 Permission result:', permission);
          });
        } else if (Notification.permission === 'granted') {
          console.log('🔔 Notifications already permitted');
        } else {
          console.log('⚠️ Notifications denied');
        }
      } else {
        console.warn('⚠️ Notification API not supported');
      }
    }
  }, []);

  useEffect(() => {
    if (!tracker) return;

    const sendNotification = (title, options = {}) => {
      if (!('Notification' in window)) {
        console.warn('⚠️ Notification API not supported');
        return;
      }

      if (Notification.permission !== 'granted') {
        console.warn('⚠️ Notification permission not granted. Current:', Notification.permission);
        return;
      }

      try {
        const notif = new Notification(title, {
          icon: '/truck-icon.png',
          badge: '/truck-icon.png',
          tag: 'fleet-alerts',
          requireInteraction: true,
          ...options
        });
        
        console.log('✅ Notification sent:', title);
        
        notif.onclick = () => {
          window.focus();
          notif.close();
        };
      } catch (error) {
        console.error('❌ Notification error:', error);
      }
    };

    const handleEvent = (eventType, data) => {
      const truckId = data?.truckId || 'unknown';
      const notifyKey = `${truckId}-${eventType}`;

      // Skip if we've already notified recently (5 min cooldown)
      if (notifiedRef.current.has(notifyKey)) {
        console.log(`⏭️ Skipping duplicate notification: ${notifyKey}`);
        return;
      }

      console.log(`📢 Processing event: ${eventType} for ${truckId}`);

      notifiedRef.current.add(notifyKey);
      setTimeout(() => {
        notifiedRef.current.delete(notifyKey);
        console.log(`🔄 Cleared cooldown for: ${notifyKey}`);
      }, 300000); // Clear after 5 min

      switch (eventType) {
        case 'off-route-detected':
          sendNotification('🚨 Off-Route Alert', {
            body: `Truck ${truckId} is off-route by ${data?.distance || 'unknown'} meters`,
            tag: `off-route-${truckId}`
          });
          break;

        case 'truck-delayed':
          sendNotification('⏰ Truck Delayed', {
            body: `Truck ${truckId} has been delayed`,
            tag: `delayed-${truckId}`
          });
          break;

        case 'speed-drop':
          sendNotification('📉 Speed Drop', {
            body: `Truck ${truckId} speed dropped significantly`,
            tag: `speed-drop-${truckId}`
          });
          break;

        case 'driver-stopped':
          sendNotification('🛑 Driver Stopped', {
            body: `Driver on Truck ${truckId} has stopped`,
            tag: `stopped-${truckId}`
          });
          break;

        case 'back-on-route':
          sendNotification('✅ Back on Route', {
            body: `Truck ${truckId} is back on its designated route`,
            tag: `back-on-route-${truckId}`
          });
          break;

        default:
          console.log(`ℹ️ Unhandled event type: ${eventType}`);
          break;
      }
    };

    // Register event listeners
    const events = [
      'off-route-detected',
      'back-on-route',
      'truck-delayed',
      'speed-drop',
      'driver-stopped'
    ];

    events.forEach(evt => {
      tracker.on(evt, (data) => {
        console.log(`📨 Event received: ${evt}`, data);
        handleEvent(evt, data);
      });
    });

    console.log('✅ Event listeners registered for:', events.join(', '));

    return () => {
      notifiedRef.current.clear();
      console.log('🧹 Cleaned up event listeners');
    };
  }, [tracker]);

  // This component doesn't render anything - it only sends notifications
  return null;
}
