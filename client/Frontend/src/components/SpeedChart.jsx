import { useState, useEffect } from 'react';
import { Navigation, Zap, AlertTriangle, CheckCircle, TrendingUp } from "lucide-react";
import { getTrucks } from '../services/api';

export default function SpeedChart() {
  const [trucks, setTrucks] = useState([]);
  const limit = 120;

  // Fetch live truck data from backend
  useEffect(() => {
    const fetchTrucks = async () => {
      try {
        const data = await getTrucks();
        setTrucks(Array.isArray(data) ? data : []);
      } catch (error) {
        console.error('Error fetching trucks:', error);
      }
    };

    fetchTrucks();
    const interval = setInterval(fetchTrucks, 3000); // Update every 3 seconds for real-time
    return () => clearInterval(interval);
  }, []);

  const getColorConfig = (truck) => {
    let color = '#3b82f6';      // blue - moving
    let bgColor = '#3b82f6';
    let Icon = Navigation;
    let textColor = 'text-blue-400';
    
    const speed = truck.speed || 0;

    if (speed > 90) {
      // Speed violation
      color = '#ef4444';
      bgColor = '#ef4444';
      Icon = AlertTriangle;
      textColor = 'text-red-400';
    } else if (speed === 0) {
      // Stopped
      color = '#ef4444';
      bgColor = '#ef4444';
      Icon = AlertTriangle;
      textColor = 'text-red-400';
    } else if (truck.status === 'delayed') {
      color = '#f59e0b';
      bgColor = '#f59e0b';
      Icon = Zap;
      textColor = 'text-amber-400';
    } else if (truck.status === 'delivered') {
      color = '#8b5cf6';
      bgColor = '#8b5cf6';
      Icon = CheckCircle;
      textColor = 'text-purple-400';
    } else if (speed >= 60) {
      color = '#10b981';
      bgColor = '#10b981';
      Icon = TrendingUp;
      textColor = 'text-green-400';
    }

    return { color, bgColor, Icon, textColor };
  };

  return (
    <div className="bg-bg2/80 backdrop-blur-sm border border-border rounded-xl overflow-hidden">
      <div className="px-5 py-4 border-b border-border">
        <span className="text-sm font-semibold font-heading text-text2 uppercase tracking-wider">Live Speed Monitor</span>
      </div>
      <div className="p-5">
        <div className="space-y-4">
          {trucks.length > 0 ? trucks.map(truck => {
            const config = getColorConfig(truck);
            const pct = Math.round((truck.speed / limit) * 100);

            return (
              <div key={truck.id} className="flex items-center gap-3 p-2 rounded-lg hover:bg-bg3/30 transition-colors">
                <span className={`text-sm font-mono font-bold ${config.textColor}`}>{truck.id}</span>
                <span className="text-sm text-text2 w-20 truncate">{truck.driver}</span>
                <div className="flex-1 h-4 bg-bg3 rounded-full overflow-hidden border border-border/30">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{ width: `${pct}%`, backgroundColor: config.bgColor }}
                  ></div>
                </div>
                <span className={`text-sm font-mono font-semibold ${config.textColor} flex items-center gap-1 w-20 text-right justify-end`}>
                  <config.Icon size={16} />
                  {truck.speed > 0 ? `${truck.speed}` : 'STOP'}
                </span>
              </div>
            );
          }) : (
            <div className="text-center text-text3 py-4">Loading trucks...</div>
          )}
        </div>
      </div>
    </div>
  );
}
