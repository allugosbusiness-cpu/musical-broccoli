import { useEffect, useState } from "react";
import { BarChart3, Settings, QrCode } from "lucide-react";

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
    <div className="h-16 flex items-center justify-between px-8 border-b border-slate-700 bg-slate-900 sticky top-0 z-50 shadow-dark">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-3 font-bold text-lg">
          <img src="/ass.png" alt="PulseTrack" className="w-8 h-8" />
          <span className="text-slate-100">PulseTrack</span>
        </div>
        {currentView === 'dashboard' && (selectedTruck || selectedDriver) && (
          <div className="flex items-center gap-2 ml-4 px-3 py-1 bg-slate-800 border border-slate-700 rounded-lg text-sm">
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

      <div className="flex items-center gap-3">
        {/* Navigation Buttons */}
        <button
          onClick={() => onViewChange('dashboard')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all text-sm font-medium ${
            currentView === 'dashboard'
              ? 'bg-primary text-white shadow-dark'
              : 'text-slate-300 hover:bg-slate-800 border border-slate-700'
          }`}
        >
          <BarChart3 size={18} />
          Dashboard
        </button>

        <button
          onClick={() => onViewChange('admin')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all text-sm font-medium ${
            currentView === 'admin'
              ? 'bg-primary text-white shadow-dark'
              : 'text-slate-300 hover:bg-slate-800 border border-slate-700'
          }`}
        >
          <Settings size={18} />
          Admin
        </button>

        <button
          onClick={() => onViewChange('qr')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all text-sm font-medium ${
            currentView === 'qr'
              ? 'bg-primary text-white shadow-dark'
              : 'text-slate-300 hover:bg-slate-800 border border-slate-700'
          }`}
        >
          <QrCode size={18} />
          QR Code
        </button>
      </div>

      <div className="flex items-center gap-4 text-sm">
        <span className="flex items-center gap-2 text-success font-semibold">
          <div className="w-2 h-2 bg-success rounded-full animate-pulse"></div>
          LIVE
        </span>

        <span className="font-mono text-slate-300 px-3 py-1 bg-slate-800 rounded-md border border-slate-700">
          {time}
        </span>
      </div>
    </div>
  );
}
