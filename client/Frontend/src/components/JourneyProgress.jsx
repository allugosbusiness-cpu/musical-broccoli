import { Road, Navigation, Zap, AlertTriangle } from 'lucide-react';
import { useState, useEffect } from 'react';
import { getTrucks } from '../services/api';

export default function JourneyProgress() {
  const [trucks, setTrucks] = useState([]);
  const [loading, setLoading] = useState(true);

  // Fetch trucks with distance data
  useEffect(() => {
    const fetchTrucks = async () => {
      try {
        const data = await getTrucks();
        setTrucks(Array.isArray(data) ? data : []);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching trucks:', error);
        setLoading(false);
      }
    };

    fetchTrucks();
    const interval = setInterval(fetchTrucks, 5000); // Update every 5 seconds
    return () => clearInterval(interval);
  }, []);

  if (loading && trucks.length === 0) {
    return (
      <div className="bg-bg2/80 backdrop-blur-sm border border-border rounded-xl overflow-hidden glass">
        <div className="px-5 py-4 border-b border-border flex items-center gap-2">
          <Road className="w-5 h-5 text-cyan" />
          <span className="text-sm font-semibold font-heading text-text2 uppercase tracking-wider">Journey Progress</span>
        </div>
        <div className="p-5 text-center text-text3">Loading...</div>
      </div>
    );
  }

  return (
    <div className="bg-bg2/80 backdrop-blur-sm border border-border rounded-xl overflow-hidden glass">
      <div className="px-5 py-4 border-b border-border flex items-center gap-2">
        <Road className="w-5 h-5 text-cyan" />
        <div>
          <span className="text-sm font-semibold font-heading text-text2 uppercase tracking-wider">Journey Progress</span>
          <p className="text-xs text-text3">Distance travelled vs total journey</p>
        </div>
      </div>
      <div className="p-5">
        <div className="space-y-5 max-h-96 overflow-y-auto">
          {trucks.filter(t => t.status !== 'delivered' && t.status !== 'maintenance').map(truck => {
            const totalDistance = truck.total_distance || 1000;
            const travelled = truck.distance_travelled || 0;
            const remaining = totalDistance - travelled;
            const progressPct = Math.round((travelled / totalDistance) * 100);
            
            // Status icon and color
            let statusColor = 'text-blue';
            let StatusIcon = Navigation;
            
            if (truck.status === 'stopped') {
              statusColor = 'text-red';
              StatusIcon = AlertTriangle;
            } else if (truck.status === 'delayed') {
              statusColor = 'text-amber';
              StatusIcon = Zap;
            }

            return (
              <div key={truck.id} className="space-y-2 p-3 rounded-lg bg-bg3/30 border border-border/20">
                {/* Header with truck info */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <StatusIcon className={`w-4 h-4 ${statusColor}`} />
                    <span className="font-semibold text-sm text-text1">{truck.plate}</span>
                    <span className="text-xs text-text3">({truck.driver})</span>
                  </div>
                  <span className={`text-xs font-mono font-bold ${statusColor}`}>{progressPct}%</span>
                </div>

                {/* Progress bar */}
                <div className="w-full h-2 bg-bg2 rounded-full overflow-hidden border border-border/30">
                  <div
                    className={`h-full transition-all duration-1000 ${
                      truck.status === 'stopped' ? 'bg-red' : 
                      truck.status === 'delayed' ? 'bg-amber' : 
                      'bg-cyan'
                    }`}
                    style={{ width: `${progressPct}%` }}
                  ></div>
                </div>

                {/* Distance info */}
                <div className="flex items-center justify-between text-xs text-text3 font-mono">
                  <span>Travelled: {Number.isFinite(travelled) ? Number(travelled).toFixed(1) : '0.0'} km</span>
                  <span>Remaining: {Number.isFinite(remaining) ? Number(Math.max(0, remaining)).toFixed(1) : '0.0'} km</span>
                  <span>Total: {Number.isFinite(totalDistance) ? Number(totalDistance).toFixed(1) : '0.0'} km</span>
                </div>
              </div>
            );
          })}
          {trucks.filter(t => t.status !== 'delivered' && t.status !== 'maintenance').length === 0 && (
            <p className="text-center text-text3 py-8">No active journeys</p>
          )}
        </div>
      </div>
    </div>
  );
}
