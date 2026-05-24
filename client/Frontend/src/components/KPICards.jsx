import { useState, useEffect } from "react";
import { TrendingUp, CheckCircle2, Gauge, Package, AlertTriangle, Zap } from "lucide-react";
import axios from "axios";
import { 
  getDashboardSummary, 
  getDashboardTrucks, 
  getDashboardDrivers,
  getTrucks, 
  getAlerts 
} from '../services/api';

const getApiBase = () => {
  if (import.meta.env.MODE === 'development') return 'http://localhost:8000/api';
  return 'https://pulsetrack-back.onrender.com/api';
};

export default function KPICards({ selectedTruck = null, selectedDriver = null, refreshTrigger = 0 }) {
  const [kpis, setKpis] = useState({
    activeTrucks: 0,
    onTimeRate: 0,
    avgSpeed: 0,
    totalDeliveries: 0,
    criticalAlerts: 0,
    speedViolations: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const calculateKPIs = async () => {
      try {
        // If a specific truck is selected, fetch its metrics from dashboard
        if (selectedTruck) {
          try {
            const trucksData = await getDashboardTrucks();
            const truck = Array.isArray(trucksData) ? trucksData.find(t => t.truck_identifier === selectedTruck.truck_identifier || t.id === selectedTruck.id) : null;
            
            if (truck) {
              setKpis({
                activeTrucks: truck.status === 'enroute' ? 1 : 0,
                onTimeRate: 0,  // Individual truck on-time rate would need more data
                avgSpeed: truck.speed || 0,
                totalDeliveries: 1,  // Placeholder
                criticalAlerts: 0,
                speedViolations: 0,
              });
              setLoading(false);
              return;
            }
          } catch (err) {
            console.log('Could not fetch specific truck metrics');
          }
        }

        // If a specific driver is selected, fetch their metrics
        if (selectedDriver) {
          try {
            const driversData = await getDashboardDrivers();
            const driver = Array.isArray(driversData) ? driversData.find(d => d.id === selectedDriver.id || d.name === selectedDriver.name) : null;
            
            if (driver) {
              setKpis({
                activeTrucks: 0,
                onTimeRate: driver.performance_points || 0,
                avgSpeed: 0,
                totalDeliveries: driver.deliveries_count || 0,
                criticalAlerts: 0,
                speedViolations: 0,
              });
              setLoading(false);
              return;
            }
          } catch (err) {
            console.log('Could not fetch specific driver metrics');
          }
        }
        
        // Fetch real-time truck locations
        try {
          const locResponse = await axios.get(`${getApiBase()}/v1/truck-tracking/all-locations/`);
          const trucks = locResponse.data.trucks || [];
          
          // Calculate metrics from real-time location data
          const activeTrucks = trucks.filter(t => t.status === 'enroute').length;
          const speeds = trucks.map(t => t.speed || 0).filter(s => s > 0);
          const avgSpeed = speeds.length > 0 ? Math.round(speeds.reduce((a, b) => a + b, 0) / speeds.length * 100) / 100 : 0;
          
          setKpis({
            activeTrucks,
            onTimeRate: 0,
            avgSpeed,
            totalDeliveries: 0,
            criticalAlerts: 0,
            speedViolations: speeds.filter(s => s > 100).length,
          });
          setLoading(false);
          return;
        } catch (err) {
          console.log('Could not fetch real-time locations');
        }
        
        // Fallback to manual calculation if endpoint fails
        const [trucksData, driversData] = await Promise.all([
          getDashboardTrucks(),
          getDashboardDrivers(),
        ]);

        console.log('📊 KPICards: Received trucks:', trucksData);
        console.log('📊 KPICards: Received drivers:', driversData);

        const trucks = Array.isArray(trucksData) ? trucksData : [];
        const drivers = Array.isArray(driversData) ? driversData : [];

        // Calculate metrics from v2 data
        const activeTrucks = trucks.filter(t => t.status === 'enroute' || t.status === 'moving').length;
        const totalDeliveries = drivers.reduce((sum, d) => sum + (d.deliveries_count || 0), 0);
        
        // Calculate average on-time rate from drivers
        const avgPerformance = drivers.length > 0 ? 
          Math.round(drivers.reduce((sum, d) => sum + (d.performance_points || 0), 0) / drivers.length) : 0;
        
        console.log('📊 KPICards: Active trucks:', activeTrucks, 'Total trucks:', trucks.length);
        
        setKpis({
          activeTrucks,
          onTimeRate: Math.min(100, avgPerformance),
          avgSpeed: 0,
          totalDeliveries,
          criticalAlerts: 0,
          speedViolations: 0,
        });
      } catch (error) {
        console.error('Error calculating KPIs:', error);
      } finally {
        setLoading(false);
      }
    };

    calculateKPIs();
    const interval = setInterval(calculateKPIs, 5000); // Update every 5 seconds for real-time
    return () => clearInterval(interval);
  }, [selectedTruck, selectedDriver, refreshTrigger]);

  const cards = [
    {
      label: "Active Trucks",
      value: kpis.activeTrucks,
      Icon: TrendingUp,
      iconColor: "text-green",
      sub: "Currently moving",
      color: "text-green",
    },
    {
      label: "On-Time Rate",
      value: `${kpis.onTimeRate}%`,
      Icon: CheckCircle2,
      iconColor: kpis.onTimeRate >= 80 ? "text-green" : "text-amber",
      sub: kpis.onTimeRate >= 80 ? "Good performance" : "Needs improvement",
      color: kpis.onTimeRate >= 80 ? "text-green" : "text-amber",
    },
    {
      label: "Avg Speed",
      value: kpis.avgSpeed,
      unit: "km/h",
      Icon: Gauge,
      iconColor: kpis.avgSpeed > 100 ? "text-amber" : "text-blue",
      sub: kpis.avgSpeed > 100 ? "High average" : "Within limits",
      color: kpis.avgSpeed > 100 ? "text-amber" : "text-blue",
    },
    {
      label: "Deliveries",
      value: kpis.totalDeliveries,
      Icon: Package,
      iconColor: "text-purple",
      sub: "Completed",
      color: "text-purple",
    },
    {
      label: "Speed Violations",
      value: kpis.speedViolations,
      Icon: Zap,
      iconColor: kpis.speedViolations > 0 ? "text-red" : "text-green",
      sub: kpis.speedViolations > 0 ? "Attention needed" : "All safe",
      color: kpis.speedViolations > 0 ? "text-red" : "text-green",
    },
    {
      label: "Critical Alerts",
      value: kpis.criticalAlerts,
      Icon: AlertTriangle,
      iconColor: kpis.criticalAlerts > 0 ? "text-red" : "text-green",
      sub: kpis.criticalAlerts > 0 ? "Unresolved" : "All clear",
      color: kpis.criticalAlerts > 0 ? "text-red" : "text-green",
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-3 mb-6">
      {cards.map((c, i) => {
        const colorMap = {
          "text-red": { 
            bg: "from-red-900/10 to-red-800/5", 
            border: "border-red-700/30", 
            text: "text-red-400", 
            icon: "text-red-500",
            label: "text-red-300/70"
          },
          "text-amber": { 
            bg: "from-amber-900/10 to-amber-800/5", 
            border: "border-amber-700/30", 
            text: "text-amber-400", 
            icon: "text-amber-500",
            label: "text-amber-300/70"
          },
          "text-green": { 
            bg: "from-green-900/10 to-green-800/5", 
            border: "border-green-700/30", 
            text: "text-green-400", 
            icon: "text-green-500",
            label: "text-green-300/70"
          },
          "text-blue": { 
            bg: "from-blue-900/10 to-blue-800/5", 
            border: "border-blue-700/30", 
            text: "text-blue-400", 
            icon: "text-blue-500",
            label: "text-blue-300/70"
          },
          "text-purple": { 
            bg: "from-purple-900/10 to-purple-800/5", 
            border: "border-purple-700/30", 
            text: "text-purple-400", 
            icon: "text-purple-500",
            label: "text-purple-300/70"
          },
        };
        const styles = colorMap[c.color] || { 
          bg: "from-slate-800/50 to-slate-900/20", 
          border: "border-slate-700/30", 
          text: "text-slate-100", 
          icon: "text-slate-400",
          label: "text-slate-400/70"
        };
        
        return (
          <div
            key={i}
            className={`bg-gradient-to-br ${styles.bg} border ${styles.border} rounded-xl p-4 hover:border-slate-600/50 transition-all duration-300 shadow-lg hover:shadow-xl backdrop-blur-sm`}
          >
            <div className="flex items-start justify-between mb-3">
              <p className={`text-xs uppercase font-semibold tracking-widest ${styles.label}`}>{c.label}</p>
              <div className={`p-2 rounded-lg bg-slate-900/40 ${styles.icon}`}>
                <c.Icon size={16} />
              </div>
            </div>
            <div className="space-y-1">
              <h2 className={`text-3xl font-bold ${styles.text}`}>
                {c.value}{c.unit ? ` ${c.unit}` : ''}
              </h2>
              <p className="text-xs text-slate-400">{c.sub}</p>
            </div>
          </div>
        );
      })}
    </div>
  );

}
