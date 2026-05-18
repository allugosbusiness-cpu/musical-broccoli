import React, { useState, useEffect } from 'react';
import { Clock, CheckCircle, AlertCircle, Zap, TrendingDown } from 'lucide-react';

const API_BASE = 'http://localhost:8000/api/v2';

export function SLAMonitor({ vehicleId = 'TRUCK-001' }) {
  const [slaData, setSLAData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchSLAStatus = async () => {
      try {
        const response = await fetch(`${API_BASE}/vehicles/${vehicleId}/sla-status`);
        if (!response.ok) throw new Error('Failed to fetch SLA data');
        const data = await response.json();
        setSLAData(data);
        setError(null);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchSLAStatus();
    // Poll every 30 seconds
    const interval = setInterval(fetchSLAStatus, 30000);
    return () => clearInterval(interval);
  }, [vehicleId]);

  if (loading) {
    return (
      <div className="bg-slate-800 rounded-xl p-8 border border-slate-700 text-center">
        <div className="text-slate-400">Loading SLA data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-600 rounded-xl p-4 text-red-300">
        Error: {error}
      </div>
    );
  }

  const onTrack = slaData?.milestones?.every((m) => m.status === 'on_track');
  const totalPenalty = slaData?.total_potential_penalty || 0;

  return (
    <div className="space-y-4">
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Status */}
        <div
          className={`rounded-xl p-6 border ${
            onTrack
              ? 'bg-green-900/20 border-green-600'
              : 'bg-yellow-900/20 border-yellow-600'
          }`}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-slate-400 mb-1">SLA Status</p>
              <p className={`text-2xl font-bold ${onTrack ? 'text-green-400' : 'text-yellow-400'}`}>
                {onTrack ? 'On Track' : 'At Risk'}
              </p>
            </div>
            {onTrack ? (
              <CheckCircle size={32} className="text-green-400" />
            ) : (
              <AlertCircle size={32} className="text-yellow-400" />
            )}
          </div>
        </div>

        {/* Breaches */}
        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-slate-400 mb-1">Potential Breaches</p>
              <p className="text-2xl font-bold text-red-400">{slaData?.breach_count || 0}</p>
            </div>
            <AlertCircle size={32} className="text-red-400" />
          </div>
        </div>

        {/* Penalty */}
        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-slate-400 mb-1">Potential Penalty</p>
              <p className="text-2xl font-bold text-orange-400">
                ${Number.isFinite(totalPenalty) ? Number(totalPenalty).toFixed(2) : '0.00'}
              </p>
            </div>
            <TrendingDown size={32} className="text-orange-400" />
          </div>
        </div>
      </div>

      {/* Milestones */}
      <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
        <h3 className="text-lg font-bold text-white mb-4">Delivery Milestones</h3>

        {!slaData?.milestones || slaData.milestones.length === 0 ? (
          <p className="text-slate-400 text-center py-8">No active milestones</p>
        ) : (
          <div className="space-y-3">
            {slaData.milestones.map((milestone, idx) => (
              <MilestoneCard key={idx} milestone={milestone} />
            ))}
          </div>
        )}
      </div>

      {/* Recommendations */}
      {slaData?.milestones?.some((m) => m.status === 'at_risk') && (
        <div className="bg-yellow-900/20 border border-yellow-600 rounded-xl p-4">
          <h4 className="font-semibold text-yellow-300 mb-3 flex items-center gap-2">
            <Zap size={18} />
            Recommended Actions
          </h4>
          <ul className="space-y-2">
            {slaData.milestones
              .filter((m) => m.status === 'at_risk')
              .map((m, idx) => (
                <li key={idx} className="text-sm text-yellow-200">
                  • {m.recommended_action || 'Increase speed or take alternative route'}
                </li>
              ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function MilestoneCard({ milestone }) {
  const getStatusColor = (status) => {
    switch (status) {
      case 'on_track':
        return 'bg-green-900/20 border-green-600 text-green-300';
      case 'at_risk':
        return 'bg-yellow-900/20 border-yellow-600 text-yellow-300';
      case 'breached':
        return 'bg-red-900/20 border-red-600 text-red-300';
      default:
        return 'bg-slate-900/40 border-slate-600 text-slate-300';
    }
  };

  const formatTime = (seconds) => {
    const sign = seconds < 0 ? '-' : '';
    const absSeconds = Math.abs(seconds);
    const minutes = Math.floor(absSeconds / 60);
    return `${sign}${minutes}m`;
  };

  return (
    <div
      className={`rounded-lg p-4 border ${getStatusColor(milestone.status)} transition-all`}
    >
      <div className="flex items-center justify-between mb-2">
        <div>
          <h4 className="font-semibold text-white">{milestone.geofence_name}</h4>
          <p className="text-xs text-slate-400 mt-1">
            Target: {new Date(milestone.target_arrival).toLocaleTimeString()}
          </p>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold">
            {milestone.status === 'on_track'
              ? '✓'
              : milestone.status === 'at_risk'
              ? '⚠'
              : '✕'}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3 mt-3">
        <div>
          <p className="text-xs text-slate-400">ETA</p>
          <p className="font-semibold text-white">
            {new Date(milestone.estimated_arrival).toLocaleTimeString()}
          </p>
        </div>
        <div>
          <p className="text-xs text-slate-400">Variance</p>
          <p
            className={`font-semibold ${
              milestone.eta_seconds < 0
                ? 'text-green-400'
                : milestone.eta_seconds === 0
                ? 'text-white'
                : 'text-yellow-400'
            }`}
          >
            {formatTime(milestone.eta_seconds)}
          </p>
        </div>
        <div>
          <p className="text-xs text-slate-400">Penalty</p>
          <p className="font-semibold text-orange-400">
            ${Number.isFinite(milestone?.penalty_usd) ? Number(milestone.penalty_usd).toFixed(2) : '0.00'}
          </p>
        </div>
      </div>

      {milestone.recommended_action && (
        <div className="mt-3 pt-3 border-t border-slate-600">
          <p className="text-xs font-semibold text-blue-300 mb-1">💡 Action:</p>
          <p className="text-xs text-slate-300">{milestone.recommended_action}</p>
        </div>
      )}
    </div>
  );
}

export default SLAMonitor;
