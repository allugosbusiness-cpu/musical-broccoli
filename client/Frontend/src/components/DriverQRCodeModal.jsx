import { useState } from 'react';
import { QRCodeSVG as QRCode } from 'qrcode.react';
import { Download, X } from 'lucide-react';

export default function DriverQRCodeModal({ 
  driver = null, 
  truck = null, 
  mission = null, 
  onClose = () => {} 
}) {
  const [qrValue, setQrValue] = useState(() => {
    if (driver) {
      return JSON.stringify({
        type: 'driver_mission_assignment',
        driver_id: driver.id,
        driver_phone: driver.phone_number,
        driver_name: `${driver.first_name} ${driver.last_name}`,
        truck_id: truck?.id || null,
        truck_identifier: truck?.truck_identifier || null,
        truck_plate: truck?.plate || null,
        mission_id: mission?.id || null,
        mission_type: mission?.type || 'general_tracking',
        timestamp: new Date().toISOString(),
        action: 'start_tracking',
      });
    }
    return '';
  });

  const downloadQRCode = () => {
    const qrCodeCanvas = document.getElementById('driver-qr-code-canvas');
    if (qrCodeCanvas) {
      const image = qrCodeCanvas.toDataURL('image/png');
      const link = document.createElement('a');
      link.download = `PulseTrack-Driver-${driver?.id || 'QR'}.png`;
      link.href = image;
      link.click();
    }
  };

  if (!driver) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-lg p-6 max-w-md w-full shadow-2xl">
        {/* Header */}
        <div className="flex justify-between items-start mb-4">
          <div>
            <h2 className="text-2xl font-bold text-slate-100">
              {driver.first_name} {driver.last_name}
            </h2>
            <p className="text-sm text-slate-400 mt-1">Driver QR Code Registration</p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 transition-colors"
          >
            <X size={24} />
          </button>
        </div>

        {/* Driver Info */}
        <div className="bg-slate-800 rounded-lg p-3 mb-4 text-sm space-y-1">
          <div className="text-slate-300">
            <span className="text-slate-400">Phone:</span> {driver.phone_number}
          </div>
          {truck && (
            <div className="text-slate-300">
              <span className="text-slate-400">Truck:</span> {truck.truck_identifier} ({truck.plate})
            </div>
          )}
          {mission && (
            <div className="text-slate-300">
              <span className="text-slate-400">Mission:</span> {mission.type}
            </div>
          )}
        </div>

        {/* QR Code */}
        <div className="bg-white p-4 rounded-lg flex justify-center mb-4">
          <QRCode
            id="driver-qr-code-canvas"
            value={qrValue}
            size={220}
            level="H"
            includeMargin={true}
            renderAs="canvas"
          />
        </div>

        {/* Instructions */}
        <div className="bg-slate-800 rounded-lg p-3 mb-4 text-xs text-slate-300">
          <p className="font-semibold text-slate-100 mb-2">✓ Driver Setup:</p>
          <ol className="list-decimal list-inside space-y-1">
            <li>Have driver open PulseTrack app</li>
            <li>Driver scans this QR code</li>
            <li>Real-time tracking starts automatically</li>
            <li>Location & speed recorded every 5 seconds</li>
          </ol>
        </div>

        {/* Actions */}
        <div className="flex gap-2">
          <button
            onClick={downloadQRCode}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
          >
            <Download size={16} />
            Download
          </button>
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 bg-slate-700 text-slate-100 rounded-lg hover:bg-slate-600 transition-colors font-medium"
          >
            Close
          </button>
        </div>

        {/* Share Instructions */}
        <div className="mt-4 p-3 bg-slate-700 rounded-lg text-xs text-slate-200 border border-slate-600">
          <p className="font-semibold mb-1">💡 Display Options:</p>
          <ul className="space-y-1">
            <li>• Print and place on dashboard</li>
            <li>• Share via phone screen to driver</li>
            <li>• Download and email to driver</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
