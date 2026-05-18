import React, { useState, useEffect } from 'react';
import {
  TrendingUp, BarChart3, PieChart, LineChart, Activity, Zap,
  AlertTriangle, Check, Clock, Fuel, DollarSign, MapPin,
  Download, Filter, Calendar, GripHorizontal
} from 'lucide-react';

/**
 * Advanced Route Analytics Dashboard
 * Real-time insights, historical analysis, predictive metrics
 */
export default function RouteAnalyticsDashboard({ route, historicalData = [] }) {
  const [timeRange, setTimeRange] = useState('7days'); // 24h, 7days, 30days, 90days
  const [selectedMetric, setSelectedMetric] = useState('efficiency');
  const [analytics, setAnalytics] = useState(null);

  useEffect(() => {
    if (route) {
      calculateAnalytics();
    }
  }, [route, timeRange]);

  const calculateAnalytics = () => {
    const data = {
      efficiency: {
        overall: calculateEfficiency(route),
        bySegment: calculateSegmentEfficiency(route),
        trend: calculateTrend('efficiency', historicalData, timeRange),
      },
      fuel: {
        consumption: route.summary?.estimatedFuel || 0,
        cost: route.summary?.estimatedCost || 0,
        savings: calculateFuelSavings(route),
        trend: calculateTrend('fuel', historicalData, timeRange),
      },
      time: {
        eta: calculateETA(route),
        delays: calculateDelays(route),
        savings: calculateTimeSavings(route),
        trend: calculateTrend('time', historicalData, timeRange),
      },
      safety: {
        score: calculateSafetyScore(route),
        hazards: route.hazards?.length || 0,
        risks: analyzeRisks(route),
      },
      emissions: {
        co2: (route.summary?.estimatedFuel || 0) * 2.31, // kg
        reduction: calculateEmissionReduction(route),
        equivalent: calculateEmissionEquivalent(route),
      },
    };

    setAnalytics(data);
  };

  // Utility Functions
  const calculateEfficiency = (route) => {
    const idealTime = route.distance / 90; // 90 km/h ideal
    const actualTime = route.summary?.duration / 60 || 1; // convert to hours
    return Math.round((idealTime / actualTime) * 100);
  };

  const calculateSegmentEfficiency = (route) => {
    return route.segments?.map(seg => ({
      name: seg.name,
      efficiency: Math.round((seg.distance / (seg.speed || 80)) / ((seg.duration || 60) / 60) * 100),
    })) || [];
  };

  const calculateTrend = (metric, data, range) => {
    const values = data
      .filter(d => isWithinRange(d.date, range))
      .map(d => d[metric] || 0);

    return values.length > 1
      ? ((values[values.length - 1] - values[0]) / values[0] * 100)
      : 0;
  };

  const calculateFuelSavings = (route) => {
    // Compare with default consumption
    const defaultConsumption = route.distance / 8; // 8 km/L default
    const actualConsumption = route.summary?.estimatedFuel || 0;
    return Math.round((defaultConsumption - actualConsumption) * 1.5); // fuel price assumption
  };

  const calculateTimeSavings = (route) => {
    // Compare with average route time
    const averageTime = route.distance / 80; // 80 km/h average with stops
    const actualTime = route.summary?.duration / 60;
    return Math.round((averageTime - actualTime) * 60); // return in minutes
  };

  const calculateETA = (route) => {
    const hours = Math.floor(route.summary?.duration / 60);
    const minutes = (route.summary?.duration || 0) % 60;
    return `${hours}h ${minutes}m`;
  };

  const calculateDelays = (route) => {
    const baseTime = route.distance / 100; // 100 km/h baseline
    const actualTime = route.summary?.duration / 60;
    return Math.round((actualTime - baseTime) * 60);
  };

  const calculateSafetyScore = (route) => {
    let score = 100;
    if (route.hazards?.length > 5) score -= 20;
    else if (route.hazards?.length > 0) score -= 10;
    if (route.roadCondition === 'poor') score -= 15;
    if (route.metrics?.difficulty > 75) score -= 10;
    return Math.max(0, score);
  };

  const analyzeRisks = (route) => {
    const risks = [];
    if (route.congestionIndex > 0.7) risks.push('High congestion risk');
    if (route.elevationGain > 1000) risks.push('Steep terrain');
    if (route.weather?.warning) risks.push('Weather warning active');
    return risks;
  };

  const calculateEmissionReduction = (route) => {
    const defaultCo2 = route.distance / 8 * 2.31; // Default consumption * CO2
    const actualCo2 = (route.summary?.estimatedFuel || 0) * 2.31;
    return Math.round((defaultCo2 - actualCo2));
  };

  const calculateEmissionEquivalent = (route) => {
    const co2 = (route.summary?.estimatedFuel || 0) * 2.31;
    return {
      cars: Math.round(co2 / 4.6 * 10) / 10, // Average car CO2
      trees: Math.round(co2 / 20), // Trees needed to offset
    };
  };

  const isWithinRange = (date, range) => {
    const now = new Date();
    const days = {
      '24h': 1,
      '7days': 7,
      '30days': 30,
      '90days': 90,
    }[range] || 7;

    return new Date(date) > new Date(now.setDate(now.getDate() - days));
  };

  if (!analytics) {
    return <div className="text-white p-4">Loading analytics...</div>;
  }

  return (
    <div className="route-analytics-dashboard bg-gradient-to-br from-slate-900 to-slate-800 rounded-lg p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <BarChart3 className="text-blue-400" size={28} />
          Route Analytics
        </h2>
        <div className="flex gap-2">
          {['24h', '7days', '30days', '90days'].map(range => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`px-3 py-1 text-sm rounded transition ${
                timeRange === range
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              {range}
            </button>
          ))}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Efficiency */}
        <KPICard
          title="Route Efficiency"
          value={`${analytics.efficiency.overall}%`}
          icon={<Activity className="text-green-400" />}
          trend={`${analytics.efficiency.trend > 0 ? '+' : ''}${Number.isFinite(analytics.efficiency.trend) ? Number(analytics.efficiency.trend).toFixed(1) : '0.0'}%`}
          trendPositive={analytics.efficiency.trend > 0}
          color="green"
        />

        {/* Fuel */}
        <KPICard
          title="Fuel Consumption"
          value={`${analytics.fuel.consumption} L`}
          icon={<Fuel className="text-yellow-400" />}
          subtitle={`$${Number.isFinite(analytics.fuel.cost) ? Number(analytics.fuel.cost).toFixed(2) : '0.00'} cost`}
          trend={`Save $${analytics.fuel.savings}`}
          trendPositive={true}
          color="yellow"
        />

        {/* Time */}
        <KPICard
          title="Estimated Time"
          value={analytics.time.eta}
          icon={<Clock className="text-blue-400" />}
          subtitle={`${analytics.time.delays > 0 ? '+' : ''}${analytics.time.delays}m delay`}
          trend={`Save ${analytics.time.savings}min`}
          trendPositive={analytics.time.savings > 0}
          color="blue"
        />

        {/* Safety */}
        <KPICard
          title="Safety Score"
          value={`${analytics.safety.score}/100`}
          icon={<Check className="text-green-400" />}
          subtitle={`${analytics.safety.hazards} hazards detected`}
          color="green"
        />

        {/* Emissions */}
        <KPICard
          title="CO₂ Emissions"
          value={`${Number.isFinite(analytics.emissions.co2) ? Number(analytics.emissions.co2).toFixed(1) : '0.0'} kg`}
          icon={<Zap className="text-purple-400" />}
          subtitle={`≈ ${analytics.emissions.equivalent.trees} trees`}
          trend={`Reduce ${analytics.emissions.reduction}kg`}
          trendPositive={true}
          color="purple"
        />
      </div>

      {/* Detailed Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Segment Efficiency */}
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
          <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
            <TrendingUp size={18} /> Segment Performance
          </h3>
          <div className="space-y-3">
            {analytics.efficiency.bySegment.slice(0, 5).map((seg, idx) => (
              <div key={idx} className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="text-sm text-slate-300 mb-1">{seg.name}</div>
                  <div className="w-full bg-slate-700 rounded-full h-2">
                    <div
                      className="bg-gradient-to-r from-green-400 to-blue-500 h-2 rounded-full"
                      style={{ width: `${Math.min(seg.efficiency, 100)}%` }}
                    />
                  </div>
                </div>
                <div className="text-sm font-semibold text-white ml-4">{seg.efficiency}%</div>
              </div>
            ))}
          </div>
        </div>

        {/* Safety Risks */}
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
          <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
            <AlertTriangle size={18} /> Risk Assessment
          </h3>
          {analytics.safety.risks.length > 0 ? (
            <div className="space-y-2">
              {analytics.safety.risks.map((risk, idx) => (
                <div key={idx} className="flex items-center gap-3 p-2 bg-red-900/20 border border-red-600/30 rounded">
                  <AlertTriangle size={16} className="text-red-400 flex-shrink-0" />
                  <span className="text-sm text-red-300">{risk}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex items-center gap-3 p-2 bg-green-900/20 border border-green-600/30 rounded">
              <Check size={16} className="text-green-400" />
              <span className="text-sm text-green-300">No major risks detected</span>
            </div>
          )}
        </div>

        {/* Cost Breakdown */}
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
          <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
            <DollarSign size={18} /> Cost Analysis
          </h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center p-2 bg-slate-700/50 rounded">
              <span className="text-slate-300">Fuel Cost</span>
              <span className="font-semibold text-green-400">${Number.isFinite(analytics.fuel.cost) ? Number(analytics.fuel.cost).toFixed(2) : '0.00'}</span>
            </div>
            <div className="flex justify-between items-center p-2 bg-slate-700/50 rounded">
              <span className="text-slate-300">Maintenance Est.</span>
              <span className="font-semibold text-yellow-400">${Number.isFinite(route?.distance) ? (Number(route.distance) * 0.05).toFixed(2) : '0.00'}</span>
            </div>
            <div className="flex justify-between items-center p-2 bg-slate-700/50 rounded">
              <span className="text-slate-300">Driver Hours</span>
              <span className="font-semibold text-blue-400">${Number.isFinite(route?.summary?.duration) ? (Number(route.summary.duration) / 60 * 20).toFixed(2) : '0.00'}</span>
            </div>
            <div className="flex justify-between items-center p-2 bg-slate-800 border border-slate-600 rounded">
              <span className="text-white font-semibold">Total Cost</span>
              <span className="font-bold text-lg text-yellow-400">
                ${Number.isFinite(analytics.fuel.cost) && Number.isFinite(route?.distance) && Number.isFinite(route?.summary?.duration) ? (Number(analytics.fuel.cost) + (Number(route.distance) * 0.05) + ((Number(route.summary.duration) || 0) / 60 * 20)).toFixed(2) : '0.00'}
              </span>
            </div>
          </div>
        </div>

        {/* Environmental Impact */}
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
          <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
            <Zap size={18} /> Environmental Impact
          </h3>
          <div className="space-y-4">
            <div className="p-3 bg-green-900/20 border border-green-600/30 rounded">
              <div className="text-sm text-slate-300 mb-1">CO₂ Emissions</div>
              <div className="text-2xl font-bold text-green-400">{Number.isFinite(analytics.emissions.co2) ? Number(analytics.emissions.co2).toFixed(1) : '0.0'} kg</div>
              <div className="text-xs text-slate-400 mt-2">
                Equivalent to {analytics.emissions.equivalent.cars} cars driving 1km
              </div>
            </div>
            <div className="p-3 bg-blue-900/20 border border-blue-600/30 rounded">
              <div className="text-sm text-slate-300 mb-1">Trees Needed to Offset</div>
              <div className="text-2xl font-bold text-blue-400">{analytics.emissions.equivalent.trees}</div>
              <div className="text-xs text-slate-400 mt-2">
                Reduction: {Number.isFinite(analytics.emissions.reduction) ? Number(analytics.emissions.reduction).toFixed(1) : '0.0'} kg CO₂
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Recommendations */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
        <h3 className="text-white font-semibold mb-4">💡 AI Recommendations</h3>
        <div className="space-y-2">
          {[
            `Depart ${timeRange === '24h' ? 'in early morning' : 'during off-peak hours'} to save ${Number.isFinite(analytics.time.savings) ? (Number(analytics.time.savings) * 0.3).toFixed(0) : '0'} minutes`,
            `Switch to Eco mode to reduce fuel consumption by 15-20%`,
            `Take recommended fuel stop at ${Number.isFinite(route?.distance) ? (Number(route.distance) / 2).toFixed(0) : '0'}km mark`,
            `Avoid ${analytics.safety.risks.length > 0 ? analytics.safety.risks[0] : 'peak traffic hours'}`,
          ].map((rec, idx) => (
            <div key={idx} className="flex items-start gap-3 p-2 bg-blue-900/20 border border-blue-600/30 rounded">
              <span className="text-blue-400 flex-shrink-0">✓</span>
              <span className="text-sm text-blue-200">{rec}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/**
 * KPI Card Component
 */
function KPICard({ title, value, icon, subtitle, trend, trendPositive, color = 'blue' }) {
  const colorClasses = {
    green: 'from-green-500/10 to-green-600/5 border-green-500/20',
    blue: 'from-blue-500/10 to-blue-600/5 border-blue-500/20',
    yellow: 'from-yellow-500/10 to-yellow-600/5 border-yellow-500/20',
    purple: 'from-purple-500/10 to-purple-600/5 border-purple-500/20',
  };

  return (
    <div className={`bg-gradient-to-br ${colorClasses[color]} border rounded-lg p-4`}>
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-sm font-semibold text-slate-300">{title}</h4>
        {icon}
      </div>
      <div className="text-2xl font-bold text-white mb-2">{value}</div>
      {subtitle && <div className="text-xs text-slate-400 mb-2">{subtitle}</div>}
      {trend && (
        <div className={`text-xs font-semibold ${trendPositive ? 'text-green-400' : 'text-red-400'}`}>
          {trendPositive ? '↑' : '↓'} {trend}
        </div>
      )}
    </div>
  );
}
