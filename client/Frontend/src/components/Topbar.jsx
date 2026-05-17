import { useEffect, useState } from "react";
import { BarChart3, Settings, QrCode, BarChart4 } from "lucide-react";

export default function Topbar({ currentView = 'dashboard', onViewChange = () => {}, selectedTruck = null, selectedDriver = null }) {
  const [time, setTime] = useState("");

  useEffect(() => {
    const update = () => {
      const now = new Date();
      setTime(now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
    };
    update();
    const i = setInterval(update, 1000);
    return () => clearInterval(i);
  }, []);

  return (
    <div className="h-16 flex items-center justify-between px-6 bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 border-b border-slate-700/50 sticky top-0 z-50 shadow-xl backdrop-blur-md">
      <div className="flex items-center gap-6">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-primary to-blue-600 flex items-center justify-center">
            <img src="/ass.png" alt="PulseTrack" className="w-6 h-6" />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-lg font-bold bg-gradient-to-r from-slate-100 to-slate-300 bg-clip-text text-transparent">PulseTrack</span>
            <span className="px-2 py-1 text-xs font-bold bg-gradient-to-r from-blue-600 to-cyan-600 text-white rounded-md">V2</span>
          </div>
        </div>
        {currentView === 'dashboard' && (selectedTruck || selectedDriver) && (
          <div className="flex items-center gap-2 ml-2 px-4 py-2 bg-slate-800/50 border border-slate-700/50 rounded-lg text-sm backdrop-blur-sm hover:bg-slate-800/70 transition-colors">
            {selectedTruck && (
              <>
                <span className="text-slate-400">📍</span>
                <span className="font-semibold text-slate-100">{selectedTruck.truck_identifier || selectedTruck.plate}</span>
              </>
            )}
            {selectedDriver && (
              <>
                <span className="text-slate-400">👤</span>
                <span className="font-semibold text-slate-100">{selectedDriver.first_name} {selectedDriver.last_name}</span>
              </>
            )}
          </div>
        )}
      </div>

      <div className="flex items-center gap-2">
        {/* Navigation Buttons */}
        <button
          onClick={() => onViewChange('dashboard')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all text-sm font-medium ${
            currentView === 'dashboard'
              ? 'bg-gradient-to-r from-primary to-blue-600 text-white shadow-lg'
              : 'text-slate-300 hover:bg-slate-800/50 border border-slate-700/50 backdrop-blur-sm'
          }`}
        >
          <BarChart3 size={18} />
          Dashboard
        </button>

        <button
          onClick={() => onViewChange('admin')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all text-sm font-medium ${
            currentView === 'admin'
              ? 'bg-gradient-to-r from-primary to-blue-600 text-white shadow-lg'
              : 'text-slate-300 hover:bg-slate-800/50 border border-slate-700/50 backdrop-blur-sm'
          }`}
        >
          <Settings size={18} />
          Admin
        </button>

        <button
          onClick={() => onViewChange('qr')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all text-sm font-medium ${
            currentView === 'qr'
              ? 'bg-gradient-to-r from-primary to-blue-600 text-white shadow-lg'
              : 'text-slate-300 hover:bg-slate-800/50 border border-slate-700/50 backdrop-blur-sm'
          }`}
        >
          <QrCode size={18} />
          QR Code
        </button>

        <button
          onClick={() => onViewChange('activity')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all text-sm font-medium ${
            currentView === 'activity'
              ? 'bg-gradient-to-r from-primary to-blue-600 text-white shadow-lg'
              : 'text-slate-300 hover:bg-slate-800/50 border border-slate-700/50 backdrop-blur-sm'
          }`}
        >
          <BarChart4 size={18} />
          Activities
        </button>
      </div>

      <div className="flex items-center gap-4 text-sm">
        <span className="flex items-center gap-2 text-emerald-400 font-semibold">
          <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse"></div>
          LIVE
        </span>

        <span className="font-mono text-slate-300 px-3 py-1 bg-slate-800/50 rounded-lg border border-slate-700/50 backdrop-blur-sm">
          {time}
        </span>
      </div>
    </div>
  );
}
