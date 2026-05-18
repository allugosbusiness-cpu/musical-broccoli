import { useState, useEffect } from "react";
import { Navigation, AlertTriangle, CheckCircle, Zap, MapPin, Users, Package } from "lucide-react";
import { getTruck, getCheckpoints, getTrucks } from '../services/api';
import { getCoordinates } from '../data/locations';

const statusConfig = {
  moving: { color: 'text-blue', Icon: Navigation, bg: 'bg-blue/10', border: 'border-blue/30' },
  delayed: { color: 'text-amber', Icon: Zap, bg: 'bg-amber/10', border: 'border-amber/30' },
  stopped: { color: 'text-red', Icon: AlertTriangle, bg: 'bg-red/10', border: 'border-red/30' },
  delivered: { color: 'text-purple', Icon: CheckCircle, bg: 'bg-purple/10', border: 'border-purple/30' },
};

export default function TruckDetail({ truckId: propTruckId, onClose }) {
  const [selectedTruck, setSelectedTruck] = useState(propTruckId || null);
  const [truck, setTruck] = useState(null);
  const [trucks, setTrucks] = useState([]);
  const [checkpoints, setCheckpoints] = useState([]);
  const [coords, setCoords] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchAllTrucks = async () => {
      try {
        const data = await getTrucks();
        setTrucks(Array.isArray(data) ? data : []);
      } catch (error) {
        console.error('Error fetching trucks:', error);
      }
    };
    fetchAllTrucks();
  }, []);

  useEffect(() => {
    const fetchTruckData = async () => {
      if (!selectedTruck) return;
      setLoading(true);
      try {
        const truckData = await getTruck(selectedTruck);
        if (truckData) {
          setTruck(truckData);
          const locationCoords = getCoordinates(truckData.location);
          setCoords(locationCoords);
          const checkpointsData = await getCheckpoints(selectedTruck);
          setCheckpoints(Array.isArray(checkpointsData) ? checkpointsData : []);
        }
      } catch (error) {
        console.error('Error fetching truck details:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchTruckData();
  }, [selectedTruck]);

  if (!selectedTruck || !truck || loading) {
    return (
      <div className="bg-bg2/80 backdrop-blur-sm border border-border rounded-xl overflow-hidden glass">
        <div className="px-5 py-4 border-b border-border flex items-center justify-between">
          <span className="text-sm font-semibold font-heading text-text2 uppercase tracking-wider">Truck Detail</span>
          {onClose && <button onClick={onClose} className="text-text3 hover:text-text2">✕</button>}
        </div>
        <div className="p-5 text-center text-text3">
          {!selectedTruck ? 'Select a truck to view details' : loading ? 'Loading...' : 'No truck found'}
        </div>
      </div>
    );
  }

  const t = truck;
  const config = statusConfig[t.status] || statusConfig.moving;
  const StatusIcon = config.Icon;

  return (
    <div className="bg-bg2/80 backdrop-blur-sm border border-border rounded-xl overflow-hidden glass">
      <div className="px-5 py-4 border-b border-border flex items-center justify-between">
        <div>
          <span className="text-sm font-semibold font-heading text-text2 uppercase tracking-wider">Truck Detail</span>
          <p className="text-xs text-text3 mt-1">{t.plate}</p>
        </div>
        {onClose && <button onClick={onClose} className="text-text3 hover:text-text2">✕</button>}
      </div>

      <div className="p-5 space-y-6">
        <div className="flex gap-2 flex-wrap overflow-x-auto pb-2">
          {trucks.map(truck => (
            <button
              key={truck.id}
              onClick={() => setSelectedTruck(truck.id)}
              className={`px-3 py-2 text-xs font-mono rounded-lg border transition-all duration-300 whitespace-nowrap ${
                truck.id === selectedTruck
                  ? 'bg-blue/20 border-blue/40 text-blue glow-blue'
                  : 'border-border text-text2 hover:bg-bg3 hover:border-border2'
              }`}
            >
              {truck.id}
            </button>
          ))}
        </div>

        <div className={`${config.bg} border ${config.border} rounded-lg p-4`}>
          <div className="flex items-start justify-between mb-4">
            <div>
              <h3 className="text-lg font-heading font-bold text-text1">{t.id}</h3>
              <p className={`${config.color} text-sm font-mono uppercase tracking-wider`}>{t.status}</p>
            </div>
            <StatusIcon className={`${config.color} w-6 h-6`} />
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <span className="text-text3 font-mono text-xs">Driver</span>
              <p className="text-text1 font-semibold">{t.driver}</p>
            </div>
            <div>
              <span className="text-text3 font-mono text-xs">Speed</span>
              <p className="text-text1 font-semibold">{t.speed} km/h</p>
            </div>
          </div>
        </div>

        {coords && (
          <div className="bg-bg3 border border-border2 rounded-lg p-4 space-y-3">
            <div className="flex items-center gap-2 text-text2">
              <MapPin className="w-4 h-4 text-cyan" />
              <span className="font-mono text-sm font-semibold">Location</span>
            </div>
            <div className="space-y-2 text-sm">
              <p className="text-text1">{t.location}</p>
              <p className="text-text3 font-mono text-xs">
                Coordinates: {Number.isFinite(coords.lat) ? Number(coords.lat).toFixed(4) : 'N/A'}, {Number.isFinite(coords.lng) ? Number(coords.lng).toFixed(4) : 'N/A'}
              </p>
              <p className="text-text3 font-mono text-xs">
                {coords.country} · {coords.region}
              </p>
            </div>
          </div>
        )}

        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-sm font-mono text-text3">Progress</span>
            <span className="font-mono font-bold text-text2">{t.progress}%</span>
          </div>
          <div className="w-full h-2 bg-bg3 rounded-full overflow-hidden border border-border2">
            <div
              className="h-full bg-gradient-to-r from-cyan to-blue transition-all duration-500 glow-cyan"
              style={{width: `${t.progress}%`}}
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="bg-bg3 border border-border2 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-2">
              <Package className="w-4 h-4 text-text3" />
              <span className="text-xs font-mono text-text3">Cargo</span>
            </div>
            <p className="text-sm font-semibold text-text1">{t.cargo}</p>
            <p className="text-xs text-text3 mt-1">{t.weight}</p>
          </div>
          <div className="bg-bg3 border border-border2 rounded-lg p-3">
            <span className="text-xs font-mono text-text3">ETA</span>
            <p className="text-sm font-semibold text-text1 mt-2">{t.eta}</p>
          </div>
        </div>

        {checkpoints.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-text2">
              <Users className="w-4 h-4 text-text3" />
              <span className="font-mono text-sm font-semibold">Checkpoints</span>
            </div>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {checkpoints.map((cp, idx) => (
                <div key={cp.id || idx} className="flex gap-3 text-sm">
                  <div className="flex flex-col items-center">
                    {cp.status === 'done' ? (
                      <div className="w-4 h-4 rounded-full bg-green border border-green/50" />
                    ) : cp.status === 'active' ? (
                      <div className="w-4 h-4 rounded-full bg-blue border border-blue/50 animate-pulse" />
                    ) : (
                      <div className="w-4 h-4 rounded-full border border-border2" />
                    )}
                    {idx < checkpoints.length - 1 && (
                      <div className="w-0.5 h-8 bg-border2 mt-1" />
                    )}
                  </div>
                  <div className="py-1 flex-1">
                    <p className={`font-semibold ${
                      cp.status === 'done' ? 'text-green' :
                      cp.status === 'active' ? 'text-blue' :
                      'text-text3'
                    }`}>
                      {cp.name}
                    </p>
                    <p className="text-xs text-text3">{cp.detail}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}