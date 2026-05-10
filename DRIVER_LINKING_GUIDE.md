# Driver Linking Methods: Complete Guide

## Overview

PulseTrack supports **5 different methods** to link drivers with trucks and missions in the mobile app. Each method has unique advantages for different scenarios.

---

## 1. QR Code Scanning (Default)

### How It Works
- Dashboard generates unique QR code per truck/mission
- QR code contains truck ID, name, and coordinates
- Driver scans with phone camera in PulseTrack app
- System auto-links driver to truck

### Advantages
✅ No manual data entry  
✅ Visual confirmation on truck  
✅ Offline-capable  
✅ Multiple ways to share (print, email, display)

### Implementation
```javascript
// Frontend - Generate QR
<QRCodeDisplay 
  truckId={truck.id}
  truckData={truck}
/>

// Mobile app
const qrData = JSON.parse(scannedQRCode);
const { truck_id } = qrData;
// Register driver with truck
```

### When to Use
- Physical trucks with permanent QR codes
- In-person driver handoff
- High-volume driver onboarding

---

## 2. Driver PIN Code

### How It Works
- Dashboard generates 6-digit random PIN per truck
- PIN is unique, time-limited (optional)
- Driver enters PIN in mobile app instead of scanning
- System validates PIN and links driver

### Advantages
✅ No equipment needed (no camera/printer)  
✅ Works over phone/text  
✅ Faster for tech-comfortable drivers  
✅ Good fallback option

### Implementation
```javascript
// Frontend - Generate PIN
function generateDriverPin() {
  return Math.random().toString(36).substring(2, 8).toUpperCase();
}

// Mobile app
const PIN_PATTERN = /^[A-Z0-9]{6}$/;
if (PIN_PATTERN.test(enteredPin)) {
  // Call backend to validate PIN
  apiClient.validatePin(truckId, pin);
}
```

### Backend Endpoint
```python
# server/api/mobile_endpoints.py
@api_view(['POST'])
def validate_driver_pin(request, truck_id):
    """Validate PIN and register driver to truck"""
    pin = request.data.get('pin', '')
    phone_number = request.data.get('phone_number', '')
    
    # Check if PIN matches truck
    # Proceed with registration
```

### When to Use
- Remote driver assignment
- Phone/SMS based registration
- Backup method when QR fails
- Pre-shift driver briefing

---

## 3. Phone Number Linking

### How It Works
- Driver provides phone number during registration
- System searches for existing driver record by phone
- Automatically links to their assigned truck
- SMS confirmation sent with PIN/tracking link

### Advantages
✅ Works with any phone number  
✅ Self-service for drivers  
✅ SMS confirmation available  
✅ No QR/PIN needed

### Implementation
```javascript
// Mobile app - Phone entry
const phoneNumber = '5551234567';

// Backend lookup
apiClient.post('/api/v1/mobile/phone-lookup/', {
  phone_number: phoneNumber,
  verify_code: '123456' // Optional SMS code
});

// Returns truck assignment + driver details
```

### Backend Logic
```python
@api_view(['POST'])
def phone_number_lookup(request):
    """Link driver by phone number"""
    phone = request.data.get('phone_number')
    
    try:
        driver = FleetDriver.objects.get(phone_number=phone)
        truck = driver.truck
        
        # Auto-link and return truck info
        return Response({
            'driver_id': driver.id,
            'truck_id': truck.id,
            'truck_name': truck.truck_name,
            'status': 'linked'
        })
    except FleetDriver.DoesNotExist:
        return Response({'status': 'new_driver'})
```

### When to Use
- Returning drivers
- System-of-record integration
- Minimal friction registration
- Multi-vehicle drivers

---

## 4. Email Invitation System

### How It Works
- Admin sends customized email to driver
- Email contains:
  - QR code attachment/link
  - PIN code
  - Setup instructions
  - App download link
- Driver clicks link or scans QR

### Advantages
✅ Complete setup in one email  
✅ Branded communication  
✅ Multiple options provided  
✅ Audit trail of invitations

### Implementation
```javascript
// Frontend - Send email
async function sendDriverInvitation(driverId, truckId) {
  const response = await fetch('/api/v1/drivers/send-invite/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      truck_id: truckId,
      driver_id: driverId,
      email: driverEmail
    })
  });
}

// Email template
const emailTemplate = `
Hello ${driverName},

You have been assigned to ${truckName} for delivery tracking.

Setup Options:

1. SCAN QR CODE (Recommended)
[Display QR Image]

2. ENTER PIN CODE
PIN: ${pinCode}

3. DOWNLOAD APP
[App Store Link]

Visit: ${appDownloadUrl}

Questions? Contact support@pulsetrack.com
`;
```

### Backend
```python
from django.core.mail import send_mail
from django.template.loader import render_to_string

def send_driver_invitation(driver, truck, email):
    """Send invitation with QR and PIN"""
    context = {
        'driver_name': driver.name,
        'truck_name': truck.truck_name,
        'pin_code': generate_pin(),
        'qr_image': generate_qr_code(truck),
    }
    
    html_message = render_to_string('driver_invitation.html', context)
    send_mail(
        'PulseTrack: Truck Assignment',
        'Please set up PulseTrack tracking',
        'noreply@pulsetrack.com',
        [email],
        html_message=html_message
    )
```

### When to Use
- New driver onboarding
- Remote assignments
- Professional communication
- Contractual requirements

---

## 5. Direct Admin Assignment

### How It Works
- Admin selects driver from dropdown
- Clicks "Assign to Truck"
- System immediately links driver
- Driver notified on next login

### Advantages
✅ Instant linking  
✅ No driver action needed  
✅ Perfect for manager overrides  
✅ Works for existing drivers only

### Implementation
```javascript
// Frontend
async function assignDriverToTruck(driverId, truckId) {
  const response = await fetch(
    `/api/v1/trucks/${truckId}/assign-driver/`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ driver_id: driverId })
    }
  );
  
  return response.json();
}

// Backend
@api_view(['POST'])
def assign_driver_to_truck(request, truck_id):
    """Admin directly assigns driver to truck"""
    driver_id = request.data.get('driver_id')
    
    driver = FleetDriver.objects.get(id=driver_id)
    truck = FleetTruck.objects.get(id=truck_id)
    
    driver.truck = truck
    driver.save()
    
    # Create notification
    Notification.objects.create(
        driver=driver,
        message=f"You have been assigned to {truck.truck_name}",
        type='assignment'
    )
    
    return Response({'status': 'assigned'})
```

### When to Use
- Fleet management decisions
- Interim/backup drivers
- Emergency reassignments
- Internal fleet transfers

---

## Mission-Specific Linking

### Mission QR Codes
After driver is linked to a truck, they scan **mission-specific** QR codes to start tracking.

```json
{
  "type": "driver_mission_assignment",
  "mission_id": "mission-uuid",
  "mission_number": "DELIVERY-001",
  "truck_id": "truck-uuid",
  "driver_id": "driver-uuid",
  "destination_latitude": 40.7589,
  "destination_longitude": -73.9851,
  "timestamp": "2026-05-08T12:00:00Z"
}
```

### Generate Mission QR
```python
# Backend endpoint
@api_view(['GET'])
def generate_mission_qr(request, mission_id):
    mission = FleetMission.objects.get(id=mission_id)
    
    qr_data = {
        'type': 'driver_mission_assignment',
        'mission_id': str(mission.id),
        'mission_number': mission.mission_number,
        'truck_id': str(mission.truck_id),
        'driver_id': str(mission.driver_id),
        'destination_latitude': mission.destination_latitude,
        'destination_longitude': mission.destination_longitude,
    }
    
    # Generate QR and return
    return Response({
        'qr_data': json.dumps(qr_data),
        'qr_image': base64_qr_image
    })
```

---

## Recommended Workflow

### For New Drivers
```
1. Admin sends EMAIL with all options
   ↓
2. Driver chooses:
   - QR Code (scan)
   - PIN Code (enter)
   - Phone (auto-link)
   ↓
3. Driver selects truck from dashboard
   ↓
4. Driver scans MISSION QR to start tracking
```

### For Existing Drivers
```
1. Admin selects driver from dropdown
   ↓
2. Click "Assign to Truck"
   ↓
3. Driver notified on next login
   ↓
4. Driver views assigned truck in app
   ↓
5. Driver scans MISSION QR to track
```

### For Remote Teams
```
1. Admin generates PIN code
   ↓
2. Send via SMS/WhatsApp/Slack
   ↓
3. Driver enters PIN in app
   ↓
4. Auto-linked to truck
   ↓
5. Ready to track missions
```

---

## Security Considerations

### QR Code
- Tokens are time-bound (optional)
- No sensitive data in QR
- Can be displayed publicly

### PIN Code
- 6-digit alphanumeric
- One-time use (optional)
- Rate-limited on mobile
- Server-side validation

### Phone Number
- Matched against existing records
- SMS verification (optional)
- Encrypted in transit

### Email
- Secure token in link
- Expiring verification codes
- No credentials in email

### Direct Assignment
- Admin-only action
- Logged in audit trail
- Requires authentication

---

## API Reference

### Generate QR Code
```
GET /api/v1/mobile/truck/{truck_id}/generate-qr/
GET /api/v1/mobile/mission/{mission_id}/generate-qr/

Response:
{
  "qr_code_data": "{"truck_id": "...", ...}",
  "qr_code_image": "data:image/png;base64,..."
}
```

### Validate PIN
```
POST /api/v1/mobile/validate-pin/

Body:
{
  "truck_id": "...",
  "pin": "ABC123"
}

Response:
{
  "valid": true,
  "driver_id": "...",
  "truck_id": "..."
}
```

### Phone Lookup
```
POST /api/v1/mobile/phone-lookup/

Body:
{
  "phone_number": "5551234567"
}

Response:
{
  "status": "linked",
  "driver_id": "...",
  "truck_id": "..."
}
```

### Send Invitation
```
POST /api/v1/drivers/send-invite/

Body:
{
  "driver_id": "...",
  "truck_id": "...",
  "method": "email" | "sms" | "both"
}
```

### Assign Driver
```
POST /api/v1/trucks/{truck_id}/assign-driver/

Body:
{
  "driver_id": "..."
}
```

---

## Testing Each Method

### 1. QR Code
```bash
# Generate QR for truck
curl http://localhost:8000/api/v1/mobile/truck/{TRUCK_ID}/generate-qr/

# Scan in app and verify linking
```

### 2. PIN Code
```bash
# Use QR debug tool
# Or manually test in mobile app
PIN: A1B2C3
```

### 3. Phone Lookup
```bash
curl -X POST http://localhost:8000/api/v1/mobile/phone-lookup/ \
  -d '{"phone_number": "5551234567"}'
```

### 4. Email Invitation
```bash
curl -X POST http://localhost:8000/api/v1/drivers/send-invite/ \
  -d '{
    "driver_id": "...",
    "truck_id": "...",
    "method": "email"
  }'
```

### 5. Direct Assignment
```bash
curl -X POST http://localhost:8000/api/v1/trucks/{TRUCK_ID}/assign-driver/ \
  -d '{"driver_id": "..."}'
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| QR not scanning | Use PIN code as fallback |
| PIN invalid | Regenerate and resend |
| Phone not found | Create new driver record |
| Email not received | Check spam folder, resend |
| Direct assign fails | Verify driver exists |

---

## Summary Table

| Method | Setup Time | Driver Tech | Offline | Fallback |
|--------|-----------|-----------|---------|----------|
| QR Code | Instant | Low | Yes | PIN |
| PIN Code | 30 sec | Low | Yes | QR |
| Phone Lookup | Instant | Medium | No | Email |
| Email | 1-2 min | Medium | No | PIN |
| Direct Assign | Instant | N/A | Yes | QR |

Choose the method that best fits your operational needs and driver population!
