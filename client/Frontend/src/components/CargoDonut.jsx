import { useState, useEffect } from 'react';
import { Package, Box, Leaf, Pill, Zap } from "lucide-react";
import { getTrucks } from '../services/api';

const CARGO_TYPES = {
  'Electronics': { color: '#3b82f6', Icon: Package },
  'FMCG': { color: '#f59e0b', Icon: Box },
  'Agriculture': { color: '#ef4444', Icon: Leaf },
  'Agri': { color: '#ef4444', Icon: Leaf },
  'Pharma': { color: '#10b981', Icon: Pill },
  'Fuel Tanks': { color: '#8b5cf6', Icon: Zap },
};

export default function CargoDonut() {
  const [cargoData, setCargoData] = useState([]);
  const [loading, setLoading] = useState(true);

  // Fetch and aggregate cargo from all trucks
  useEffect(() => {
    const fetchCargo = async () => {
      try {
        const trucks = await getTrucks();
        const trucksList = Array.isArray(trucks) ? trucks : [];

        // Aggregate cargo by type
        const cargoMap = {};
        trucksList.forEach(truck => {
          const cargoType = truck.cargo || 'Other';
          const weight = truck.weight ? truck.weight / 1000 : 0; // Convert kg to tons

          if (!cargoMap[cargoType]) {
            cargoMap[cargoType] = 0;
          }
          cargoMap[cargoType] += weight;
        });

        // Convert to array format
        const cargo = Object.entries(cargoMap).map(([type, weight]) => {
          const config = CARGO_TYPES[type] || {
            color: '#64748b',
            Icon: Package,
          };
          return {
            type,
            weight: parseFloat(weight.toFixed(2)),
            color: config.color,
            Icon: config.Icon,
          };
        });

        setCargoData(cargo);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching cargo data:', error);
        setLoading(false);
      }
    };

    fetchCargo();
    const interval = setInterval(fetchCargo, 10000); // Update every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const total = cargoData.reduce((sum, item) => sum + item.weight, 0);
  let cumulative = 0;

  const segments = cargoData.map(item => {
    const startAngle = total > 0 ? (cumulative / total) * 360 : 0;
    cumulative += item.weight;
    const endAngle = total > 0 ? (cumulative / total) * 360 : 0;
    return { ...item, startAngle, endAngle };
  });

  const createPath = (startAngle, endAngle) => {
    const centerX = 80;
    const centerY = 80;
    const radius = 60;
    const innerRadius = 30;

    const startAngleRad = (startAngle * Math.PI) / 180;
    const endAngleRad = (endAngle * Math.PI) / 180;

    const x1 = centerX + radius * Math.cos(startAngleRad);
    const y1 = centerY + radius * Math.sin(startAngleRad);
    const x2 = centerX + radius * Math.cos(endAngleRad);
    const y2 = centerY + radius * Math.sin(endAngleRad);

    const x3 = centerX + innerRadius * Math.cos(endAngleRad);
    const y3 = centerY + innerRadius * Math.sin(endAngleRad);
    const x4 = centerX + innerRadius * Math.cos(startAngleRad);
    const y4 = centerY + innerRadius * Math.sin(startAngleRad);

    const largeArcFlag = endAngle - startAngle > 180 ? 1 : 0;

    return `M ${x1} ${y1} A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2} L ${x3} ${y3} A ${innerRadius} ${innerRadius} 0 ${largeArcFlag} 0 ${x4} ${y4} Z`;
  };

  return (
    <div className="bg-bg2/80 backdrop-blur-sm border border-border rounded-xl overflow-hidden">
      <div className="px-5 py-4 border-b border-border">
        <span className="text-sm font-semibold font-heading text-text2 uppercase tracking-wider">Cargo Breakdown</span>
      </div>
      <div className="p-5">
        {loading ? (
          <div className="text-center text-text3 py-8">Loading cargo data...</div>
        ) : cargoData.length > 0 ? (
          <div className="flex items-center gap-6">
            <div className="relative">
              <svg width="160" height="160" viewBox="0 0 160 160">
                {segments.map((segment, i) => (
                  <path
                    key={i}
                    d={createPath(segment.startAngle, segment.endAngle)}
                    fill={segment.color}
                    className="transition-all duration-500 hover:opacity-80 cursor-pointer"
                  />
                ))}
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <div className="text-lg font-bold text-text1 font-mono">{total.toFixed(1)}t</div>
                  <div className="text-xs text-text2 font-mono">Total</div>
                </div>
              </div>
            </div>

            <div className="flex-1 space-y-3">
              {cargoData.map(item => {
                const IconComponent = item.Icon;
                const percentage = total > 0 ? ((item.weight / total) * 100).toFixed(0) : 0;
                return (
                  <div key={item.type} className="flex items-center gap-3 p-2 rounded-lg hover:bg-bg3/30 transition-colors">
                    <IconComponent size={20} className="flex-shrink-0" style={{ color: item.color }} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-text1 font-medium truncate">{item.type}</span>
                        <span className="text-xs font-mono text-text3 px-2 py-0.5 rounded bg-bg3/50 flex-shrink-0" style={{ borderLeft: `2px solid ${item.color}` }}>
                          {percentage}%
                        </span>
                      </div>
                      <div className="text-xs text-text2 font-mono">{item.weight}t</div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ) : (
          <div className="text-center text-text3 py-8">No cargo data available</div>
        )}
      </div>
    </div>
  );
}
