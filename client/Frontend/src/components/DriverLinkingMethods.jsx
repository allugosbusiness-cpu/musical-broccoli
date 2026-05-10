import { useState, useEffect } from 'react';
import { Copy, Check, Send, Shield, Phone, Mail, Users } from 'lucide-react';

export default function DriverLinkingMethods({ truckId = null, truckData = null }) {
  const [activeMethod, setActiveMethod] = useState('pin');
  const [driverPin, setDriverPin] = useState('');
  const [drivers, setDrivers] = useState([]);
  const [selectedDriver, setSelectedDriver] = useState(null);
  const [copied, setCopied] = useState({});
  const [loading, setLoading] = useState(false);

  // Generate unique driver PIN on component mount
  useEffect(() => {
    if (truckId && !driverPin) {
      const pin = Math.random().toString(36).substring(2, 8).toUpperCase();
      setDriverPin(pin);
    }
  }, [truckId]);

  // Fetch available drivers
  useEffect(() => {
    const fetchDrivers = async () => {
      try {
        const response = await fetch(`/api/v1/drivers/`);
        if (response.ok) {
          const data = await response.json();
          setDrivers(Array.isArray(data) ? data : data.results || []);
        }
      } catch (error) {
        console.error('Failed to fetch drivers:', error);
      }
    };

    if (activeMethod === 'direct') {
      fetchDrivers();
    }
  }, [activeMethod]);

  const copyToClipboard = (text, key) => {
    navigator.clipboard.writeText(text);
    setCopied({ ...copied, [key]: true });
    setTimeout(() => setCopied({ ...copied, [key]: false }), 2000);
  };

  const assignDriverDirect = async () => {
    if (!selectedDriver || !truckId) return;
    
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/trucks/${truckId}/assign-driver/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ driver_id: selectedDriver.id }),
      });
      
      if (response.ok) {
        alert(`✅ Driver ${selectedDriver.name} assigned to truck!`);
        setSelectedDriver(null);
      }
    } catch (error) {
      alert('❌ Failed to assign driver: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const sendInvite = async (email, method) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/drivers/send-invite/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          truck_id: truckId,
          email: email,
          method: method,
        }),
      });
      
      if (response.ok) {
        alert(`✅ Invite sent to ${email}!`);
      }
    } catch (error) {
      alert('❌ Failed to send invite: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full bg-slate-800 border border-slate-700 rounded-lg p-6">
      <h2 className="text-2xl font-bold text-slate-100 mb-6">Alternative Linking Methods</h2>
      
      {/* Method Tabs */}
      <div className="grid grid-cols-4 gap-3 mb-6">
        <button
          onClick={() => setActiveMethod('pin')}
          className={`flex items-center gap-2 px-4 py-3 rounded-lg font-medium transition-colors text-sm ${
            activeMethod === 'pin'
              ? 'bg-blue-600 text-white'
              : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
          }`}
        >
          <Shield size={18} />
          Driver PIN
        </button>
        
        <button
          onClick={() => setActiveMethod('phone')}
          className={`flex items-center gap-2 px-4 py-3 rounded-lg font-medium transition-colors text-sm ${
            activeMethod === 'phone'
              ? 'bg-blue-600 text-white'
              : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
          }`}
        >
          <Phone size={18} />
          Phone Link
        </button>
        
        <button
          onClick={() => setActiveMethod('email')}
          className={`flex items-center gap-2 px-4 py-3 rounded-lg font-medium transition-colors text-sm ${
            activeMethod === 'email'
              ? 'bg-blue-600 text-white'
              : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
          }`}
        >
          <Mail size={18} />
          Email Invite
        </button>
        
        <button
          onClick={() => setActiveMethod('direct')}
          className={`flex items-center gap-2 px-4 py-3 rounded-lg font-medium transition-colors text-sm ${
            activeMethod === 'direct'
              ? 'bg-blue-600 text-white'
              : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
          }`}
        >
          <Users size={18} />
          Direct Assign
        </button>
      </div>

      {/* Method Content */}
      <div className="bg-slate-700 rounded-lg p-6">
        
        {/* PIN Method */}
        {activeMethod === 'pin' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-slate-100">Share Driver PIN</h3>
            <p className="text-slate-300 text-sm">
              Driver enters this PIN in the mobile app instead of scanning QR code. Valid for this truck only.
            </p>
            
            <div className="bg-slate-800 rounded-lg p-4 border border-slate-600">
              <p className="text-xs text-slate-400 mb-2">PIN Code</p>
              <div className="flex items-center gap-3">
                <input
                  type="text"
                  value={driverPin}
                  readOnly
                  className="flex-1 bg-slate-900 border border-slate-600 rounded px-4 py-3 text-slate-100 font-mono text-lg font-bold text-center"
                />
                <button
                  onClick={() => copyToClipboard(driverPin, 'pin')}
                  className="flex items-center gap-2 px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                >
                  {copied['pin'] ? <Check size={18} /> : <Copy size={18} />}
                </button>
              </div>
            </div>

            <div className="bg-blue-900 bg-opacity-30 border border-blue-700 rounded-lg p-4 text-sm text-slate-300">
              <p className="font-semibold text-blue-300 mb-2">How to use:</p>
              <ol className="list-decimal list-inside space-y-1 text-xs">
                <li>Share the PIN code with your driver</li>
                <li>Driver opens PulseTrack app</li>
                <li>On registration screen, tap "Enter PIN Code"</li>
                <li>Driver pastes this PIN instead of scanning QR</li>
                <li>System links driver to this truck automatically</li>
              </ol>
            </div>
          </div>
        )}

        {/* Phone Method */}
        {activeMethod === 'phone' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-slate-100">Link by Phone Number</h3>
            <p className="text-slate-300 text-sm">
              Driver provides their phone number - system finds and links them automatically.
            </p>
            
            <input
              type="text"
              placeholder="Enter driver's phone number"
              className="w-full bg-slate-900 border border-slate-600 rounded px-4 py-3 text-slate-100 placeholder-slate-500"
            />

            <button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-lg font-medium transition-colors flex items-center justify-center gap-2">
              <Phone size={18} />
              Send SMS Link
            </button>

            <div className="bg-green-900 bg-opacity-30 border border-green-700 rounded-lg p-4 text-sm text-slate-300">
              <p className="font-semibold text-green-300 mb-2">How it works:</p>
              <ol className="list-decimal list-inside space-y-1 text-xs">
                <li>Driver receives SMS with truck PIN code</li>
                <li>Driver scans QR or enters PIN in app</li>
                <li>Phone number auto-matches existing registration</li>
                <li>Driver is linked to truck and ready to track</li>
              </ol>
            </div>
          </div>
        )}

        {/* Email Method */}
        {activeMethod === 'email' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-slate-100">Send Email Invitation</h3>
            <p className="text-slate-300 text-sm">
              Send a customized email invitation with QR code and setup instructions.
            </p>
            
            <input
              type="email"
              placeholder="Enter driver's email"
              className="w-full bg-slate-900 border border-slate-600 rounded px-4 py-3 text-slate-100 placeholder-slate-500"
            />

            <button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-lg font-medium transition-colors flex items-center justify-center gap-2">
              <Mail size={18} />
              Send Email Invite
            </button>

            <div className="bg-purple-900 bg-opacity-30 border border-purple-700 rounded-lg p-4 text-sm text-slate-300">
              <p className="font-semibold text-purple-300 mb-2">Email includes:</p>
              <ul className="list-disc list-inside space-y-1 text-xs">
                <li>Truck assignment details</li>
                <li>QR code for direct scanning</li>
                <li>Setup instructions</li>
                <li>PIN code as backup option</li>
                <li>Download link for PulseTrack app</li>
              </ul>
            </div>
          </div>
        )}

        {/* Direct Assignment */}
        {activeMethod === 'direct' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-slate-100">Direct Driver Assignment</h3>
            <p className="text-slate-300 text-sm">
              Assign an existing driver directly from your database. No QR scanning needed.
            </p>
            
            <select
              value={selectedDriver?.id || ''}
              onChange={(e) => {
                const driver = drivers.find(d => d.id === e.target.value);
                setSelectedDriver(driver || null);
              }}
              className="w-full bg-slate-900 border border-slate-600 rounded px-4 py-3 text-slate-100"
            >
              <option value="">-- Select a driver --</option>
              {drivers.map(driver => (
                <option key={driver.id} value={driver.id}>
                  {driver.name} ({driver.phone_number || 'No phone'})
                </option>
              ))}
            </select>

            <button
              onClick={assignDriverDirect}
              disabled={!selectedDriver || loading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 text-white py-3 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
            >
              <Users size={18} />
              {loading ? 'Assigning...' : 'Assign Driver to Truck'}
            </button>

            {selectedDriver && (
              <div className="bg-slate-900 rounded-lg p-4 border border-slate-600">
                <p className="text-xs text-slate-400 mb-2">Selected Driver</p>
                <p className="text-slate-100 font-medium">{selectedDriver.name}</p>
                <p className="text-slate-400 text-sm">{selectedDriver.phone_number}</p>
                <p className="text-slate-500 text-xs mt-2">Email: {selectedDriver.email}</p>
              </div>
            )}

            <div className="bg-orange-900 bg-opacity-30 border border-orange-700 rounded-lg p-4 text-sm text-slate-300">
              <p className="font-semibold text-orange-300 mb-2">Note:</p>
              <p className="text-xs">
                This bypasses QR scanning entirely. Driver is immediately linked to truck in the system. They'll receive a notification on next app login.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Quick Reference */}
      <div className="mt-6 grid grid-cols-2 gap-4">
        <div className="bg-slate-700 rounded-lg p-4 border border-slate-600">
          <h4 className="text-slate-100 font-semibold mb-2 text-sm">✅ Quick: PIN Code</h4>
          <p className="text-slate-400 text-xs">Fastest for existing drivers. 6-digit PIN, no scanning needed.</p>
        </div>
        <div className="bg-slate-700 rounded-lg p-4 border border-slate-600">
          <h4 className="text-slate-100 font-semibold mb-2 text-sm">🔗 Standard: QR Code</h4>
          <p className="text-slate-400 text-xs">Traditional method. Print/share QR, driver scans with app.</p>
        </div>
        <div className="bg-slate-700 rounded-lg p-4 border border-slate-600">
          <h4 className="text-slate-100 font-semibold mb-2 text-sm">📧 Remote: Email</h4>
          <p className="text-slate-400 text-xs">Send complete setup package via email with all options.</p>
        </div>
        <div className="bg-slate-700 rounded-lg p-4 border border-slate-600">
          <h4 className="text-slate-100 font-semibold mb-2 text-sm">⚡ Instant: Direct</h4>
          <p className="text-slate-400 text-xs">Admin manually assigns. No waiting for driver action.</p>
        </div>
      </div>
    </div>
  );
}
