import { useState, useEffect } from 'react';
import { QRCodeSVG as QRCode } from 'qrcode.react';
import { Download, RefreshCw, Copy, Check } from 'lucide-react';

export default function QRCodeDisplay({ truckId = null, truckData = null, missionId = null, missionData = null }) {
  const [qrValue, setQrValue] = useState(() => {
    if (missionData && missionId) {
      // Mission QR code with all tracking details - COMPLETE PAYLOAD
      return JSON.stringify({
        type: 'driver_mission_assignment',
        mission_id: missionId,
        mission_number: missionData.mission_number || `MISSION-${missionId.substring(0, 8)}`,
        truck_id: missionData.truck_id || truckId,
        driver_id: missionData.driver_id || '',
        driver_name: missionData.driver_name || 'Unassigned',
        driver_phone: missionData.driver_phone || '',
        destination_latitude: missionData.destination_latitude !== undefined ? missionData.destination_latitude : (missionData.destination?.latitude || 0),
        destination_longitude: missionData.destination_longitude !== undefined ? missionData.destination_longitude : (missionData.destination?.longitude || 0),
        origin_latitude: missionData.origin_latitude !== undefined ? missionData.origin_latitude : (missionData.origin?.latitude || 0),
        origin_longitude: missionData.origin_longitude !== undefined ? missionData.origin_longitude : (missionData.origin?.longitude || 0),
        destination_address: missionData.destination_address || missionData.destination?.address || '',
        origin_address: missionData.origin_address || missionData.origin?.address || '',
        status: missionData.status || 'PENDING',
        eta_minutes: missionData.eta_minutes || 0,
        timestamp: new Date().toISOString(),
      });
    } else if (truckData && truckId) {
      // Truck registration QR code - COMPLETE PAYLOAD with backend URL
      return JSON.stringify({
        type: 'truck_registration',
        truck_id: truckId,
        truck_name: truckData.truck_identifier || 'Unknown',
        truck_identifier: truckData.truck_identifier || 'Unknown',
        plate: truckData.plate || 'Unknown',
        phone: truckData.phone || '', // Add phone to QR for validation
        backend_url: window.location.origin,
        timestamp: new Date().toISOString(),
        version: '2.0',
      });
    }
    // ✅ FIXED: Return null instead of generic code - will show helpful message
    return null;
  });

  const [copied, setCopied] = useState(false);

  // ✅ FIXED: Show helpful message when no data available
  if (!qrValue) {
    return (
      <div style={{
        padding: '20px',
        textAlign: 'center',
        border: '2px dashed #ccc',
        borderRadius: '8px',
        backgroundColor: '#f9f9f9',
      }}>
        <h3 style={{ color: '#666', marginBottom: '10px' }}>📱 QR Code</h3>
        <p style={{ color: '#999', marginBottom: '10px' }}>
          ✅ Select a mission or truck to generate a scannable QR code
        </p>
        <p style={{ color: '#bbb', fontSize: '12px' }}>
          • Click a mission row to generate mission QR<br/>
          • Click a truck row to generate truck QR<br/>
          • QR code will appear here automatically
        </p>
      </div>
    );
  }

  const downloadQRCode = () => {
    const qrCodeCanvas = document.getElementById('qr-code-canvas');
    if (qrCodeCanvas) {
      const image = qrCodeCanvas.toDataURL('image/png');
      const link = document.createElement('a');
      const filename = missionId 
        ? `PulseTrack-Mission-${missionData?.mission_number || missionId.substring(0, 8)}.png`
        : `PulseTrack-Truck-${truckId || 'General'}.png`;
      link.download = filename;
      link.href = image;
      link.click();
    }
  };

  const regenerateQR = () => {
    let newValue;
    if (missionData && missionId) {
      newValue = JSON.stringify({
        type: 'driver_mission_assignment',
        mission_id: missionId,
        mission_number: missionData.mission_number || `MISSION-${missionId.substring(0, 8)}`,
        truck_id: missionData.truck_id || truckId,
        driver_id: missionData.driver_id || '',
        driver_name: missionData.driver_name || 'Unassigned',
        driver_phone: missionData.driver_phone || '',
        destination_latitude: missionData.destination_latitude !== undefined ? missionData.destination_latitude : (missionData.destination?.latitude || 0),
        destination_longitude: missionData.destination_longitude !== undefined ? missionData.destination_longitude : (missionData.destination?.longitude || 0),
        origin_latitude: missionData.origin_latitude !== undefined ? missionData.origin_latitude : (missionData.origin?.latitude || 0),
        origin_longitude: missionData.origin_longitude !== undefined ? missionData.origin_longitude : (missionData.origin?.longitude || 0),
        destination_address: missionData.destination_address || missionData.destination?.address || '',
        origin_address: missionData.origin_address || missionData.origin?.address || '',
        status: missionData.status || 'PENDING',
        eta_minutes: missionData.eta_minutes || 0,
        timestamp: new Date().toISOString(),
      });
    } else if (truckData && truckId) {
      newValue = JSON.stringify({
        type: 'truck_registration',
        truck_id: truckId,
        truck_name: truckData.truck_identifier || 'Unknown',
        truck_identifier: truckData.truck_identifier || 'Unknown',
        plate: truckData.plate || 'Unknown',
        phone: truckData.phone || '',
        backend_url: window.location.origin,
        timestamp: new Date().toISOString(),
        version: '2.0',
      });
    }
    // ✅ FIXED: Always update, even if null
    setQrValue(newValue || null);
  };

  const copyToClipboard = () => {
    if (qrValue) {
      navigator.clipboard.writeText(qrValue);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="flex flex-col items-center gap-4 p-6 bg-slate-800 border border-slate-700 rounded-lg">
      <div>
        <h3 className="text-lg font-semibold text-slate-100 mb-2">
          {missionId 
            ? `📋 Mission QR: ${missionData?.mission_number || missionId.substring(0, 8)}`
            : truckId 
              ? `🚗 Truck QR: ${truckData?.truck_identifier || truckId}`
              : '🔗 Fleet Registration QR'
          }
        </h3>
        <p className="text-sm text-slate-400 mb-4">
          {missionId 
            ? 'Scan to assign mission and start tracking'
            : 'Scan with PulseTrack mobile app to link driver'
          }
        </p>
      </div>

      {/* QR Code Container */}
      <div className="bg-white p-4 rounded-lg shadow-lg">
        <QRCode
          id="qr-code-canvas"
          value={qrValue}
          size={256}
          level="H"
          includeMargin={true}
          renderAs="canvas"
        />
      </div>

      {/* Actions */}
      <div className="flex gap-3 mt-4 flex-wrap justify-center">
        <button
          onClick={downloadQRCode}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
        >
          <Download size={16} />
          Download
        </button>

        <button
          onClick={copyToClipboard}
          className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors text-sm font-medium"
        >
          {copied ? <Check size={16} /> : <Copy size={16} />}
          {copied ? 'Copied!' : 'Copy Data'}
        </button>

        <button
          onClick={regenerateQR}
          className="flex items-center gap-2 px-4 py-2 bg-slate-700 text-slate-100 rounded-lg hover:bg-slate-600 transition-colors text-sm font-medium"
        >
          <RefreshCw size={16} />
          Refresh
        </button>
      </div>

      {/* Data Preview */}
      <div className="mt-4 p-3 bg-slate-700 rounded-lg text-xs text-slate-300 w-full max-h-32 overflow-y-auto font-mono">
        <p className="font-semibold mb-1 text-slate-200">QR Code Data:</p>
        <pre className="text-xs whitespace-pre-wrap break-words">
          {JSON.stringify(JSON.parse(qrValue), null, 2)}
        </pre>
      </div>

      {/* Info Box */}
      <div className="mt-4 p-3 bg-slate-700 rounded-lg text-xs text-slate-300 w-full">
        <p className="font-semibold mb-1 text-slate-200">Setup Instructions:</p>
        <ol className="list-decimal list-inside space-y-1">
          <li>{missionId ? 'Share mission QR with assigned driver' : 'Share this QR code with the driver'}</li>
          <li>Driver scans code with PulseTrack mobile app</li>
          {!missionId && <li>Driver enters phone number to register</li>}
          {!missionId && <li>System automatically links driver to truck</li>}
          {missionId && <li>Tracking automatically starts for mission</li>}
          <li>Monitor progress in main dashboard</li>
        </ol>
      </div>
    </div>
  );
}
