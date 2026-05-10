# TruckAdmin Component Guide

## Overview
The **TruckAdmin** component provides a complete admin interface for managing trucks in your fleet. It allows admins to:
- **Create** new trucks with full details
- **Edit** existing truck information
- **Delete** trucks with confirmation
- **View** all trucks in a responsive table

## Features

### Add Truck
- Click the "Add Truck" button in the header
- Fill in truck details:
  - Truck ID (unique identifier)
  - License Plate
  - Driver Name
  - Status (moving, delayed, stopped, delivered, maintenance)
  - Location (40+ global locations)
  - Speed (km/h)
  - ETA (Estimated Time of Arrival)
  - Progress (0-100%)
  - Cargo Type
  - Weight

### Edit Truck
- Click the edit icon (pencil) on any truck row
- Modify any field except Truck ID
- Click "Save" to apply changes

### Delete Truck
- Click the delete icon (trash) on any truck row
- Confirm the deletion
- Truck is permanently removed from the fleet

## API Integration

### Backend Endpoints Used
- `GET /api/trucks/` - Fetch all trucks
- `POST /api/trucks/` - Create new truck
- `PATCH /api/trucks/{id}/` - Update truck
- `DELETE /api/trucks/{id}/` - Delete truck

### API Methods in `api.js`
```javascript
getTrucks()              // Fetch all trucks
createTruck(data)        // Create new truck
updateTruck(id, data)    // Update existing truck
deleteTruck(id)          // Delete truck
```

## Usage

### Import in App.jsx
```javascript
import TruckAdmin from "./components/TruckAdmin.jsx";

// Use in your app
<TruckAdmin />
```

### Toggle Between Views
The app now includes a toggle button (bottom-right corner) to switch between:
- **Dashboard** - Main fleet tracking view with maps and charts
- **Admin** - Truck management interface

## Global Locations
The component includes a dropdown with 40+ global cities across:
- **Africa**: Harare, Mutare, Bulawayo, Lusaka, Gaborone, Johannesburg, Nairobi, Dar es Salaam, Lilongwe, Maputo
- **Asia**: Dubai, Abu Dhabi, Singapore, Hong Kong, Shanghai, Bangkok
- **Europe**: London, Amsterdam, Paris, Berlin
- **Americas**: New York, Los Angeles, Toronto, Mexico City
- **Other**: Sydney, Cape Town, Casablanca

## Form Validation
- All required fields must be filled
- Speed must be 0-200 km/h
- Progress must be 0-100%
- Truck ID is immutable after creation
- Location must be selected from predefined list

## Error Handling
- Success messages appear for 3 seconds after successful actions
- Error messages display API response details
- Loading state prevents duplicate submissions
- Form modal can be closed without saving via Cancel button or X button

## Styling
- Glassmorphism design with backdrop blur
- Status-based color coding (blue=moving, amber=delayed, red=stopped, green=delivered)
- Responsive table design for all screen sizes
- Smooth transitions and hover effects

## Future Enhancements
- Bulk import/export CSV functionality
- Advanced filtering and sorting
- Batch status updates
- Driver assignment management
- Maintenance schedule tracking
