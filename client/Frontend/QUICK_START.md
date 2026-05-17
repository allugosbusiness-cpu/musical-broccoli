# ⚡ Quick Start Guide - Smart Routing System

## 30-Second Setup

```bash
cd "c:\Users\Admin\Desktop\Fleet Management\client\Frontend"
npm run dev
# Open http://localhost:5173
# Click green "🚀 Smart Routes" button → Done!
```

## What You Get

✅ **Multi-Waypoint Route Planning** - Add up to 20+ delivery stops  
✅ **4 Optimization Profiles** - Balanced, Fastest, Fuel Optimal, Safest  
✅ **Vehicle Profiling** - Support for different truck types  
✅ **Real-Time Analytics** - Distance, time, fuel, cost calculations  
✅ **Export & Share** - Download as JSON or share via clipboard  

## How to Use

| Step | Action | Where |
|------|--------|-------|
| 1 | Click "🚀 Smart Routes" button | Bottom-right corner |
| 2 | Select START location | Dropdown (default: Harare) |
| 3 | Select END location | Dropdown (default: Mutare) |
| 4 | (Optional) Add stops | Click "Add Stop" button |
| 5 | Choose route profile | Radio buttons (Balanced/Fastest/Fuel/Safest) |
| 6 | Select vehicle | Dropdown (TRUCK-001, TRUCK-002, VAN-001) |
| 7 | Click "Optimize Order" | Reorders waypoints optimally |
| 8 | Export or Share | Download JSON or copy to clipboard |

## Available Cities (21)

**Zimbabwe**: Harare, Bulawayo, Mutare, Gweru, Masvingo, Marondera, Macheke, Rusape, Headlands, Chegutu, Kariba, Chinhoyi

**Zambia**: Lusaka, Ndola, Kitwe, Livingstone

**South Africa**: Johannesburg, Pretoria

**Botswana**: Gaborone, Francistown

## Route Profiles Explained

| Profile | Best For | Characteristic |
|---------|----------|-----------------|
| **Balanced** | General use | 50% speed, 50% fuel efficiency |
| **Fastest** | Urgent delivery | Prioritizes shortest time |
| **Fuel Optimal** | Cost-sensitive | Minimizes fuel consumption |
| **Safest** | Hazardous routes | Avoids dangerous areas |

## Features Overview

### 🎯 Waypoint Management
- Click "Add Stop" to add intermediate delivery points
- Click trash icon to remove waypoints
- Click "Reverse Route" to invert direction
- Select locations from dropdown

### 📈 Optimization
- "Optimize Order" button reorders waypoints for optimal route
- Changes route profile to apply different optimization strategies
- Real-time calculation of distance, time, fuel, cost

### 🚗 Vehicle Selection
- TRUCK-001 (Volvo FH16) - Heavy cargo
- TRUCK-002 (Scania R450) - Medium cargo  
- VAN-001 (Sprinter Van) - Light cargo
- Each vehicle has different fuel consumption rates

### 📊 Metrics Displayed
- **Distance**: Total kilometers
- **Duration**: Total time in minutes
- **Fuel Needed**: Liters required
- **Cost**: Estimated expense
- **Confidence**: Route reliability score (0-1)

### 💾 Export & Share
- **Export**: Downloads route as JSON file for import/archiving
- **Share**: Copies route data to clipboard for sharing

## What's Coming Soon (Backend)

The system is waiting for backend implementation of:
- Real route optimization calculations
- Live traffic prediction
- Fuel consumption forecasting
- Hazard and weather detection
- Alternative route suggestions

See `BACKEND_IMPLEMENTATION_GUIDE.md` for technical details.

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Esc | Close current view |
| Tab | Navigate between fields |
| Enter | Submit/Confirm |
| ← | Return to Dashboard |

## Common Tasks

### Plan a Route from Harare to Bulawayo
1. Click Smart Routes button
2. START = Harare (default)
3. END = Bulawayo (select from dropdown)
4. Click Optimize Order
5. Done!

### Add Multiple Stops
1. Click Smart Routes button
2. Set START and END locations
3. Click "Add Stop" button
4. Select intermediate city
5. Repeat for each stop
6. Click "Optimize Order" for best order

### Compare Route Profiles
1. Plan a route (Harare → Mutare)
2. Try each profile (Balanced, Fastest, Fuel Optimal, Safest)
3. Compare metrics shown (time, fuel, cost)
4. Choose best option

### Export Route for Later
1. Plan and optimize route
2. Click "Export" button
3. Save JSON file
4. Share with team or import later

## Supported Vehicles

```json
{
  "TRUCK-001": {
    "name": "Volvo FH16",
    "capacity": "20 tons",
    "fuelType": "diesel",
    "consumption": "6.5 L/100km",
    "fuelCapacity": "250L"
  },
  "TRUCK-002": {
    "name": "Scania R450",
    "capacity": "18 tons",
    "fuelType": "diesel",
    "consumption": "7.2 L/100km",
    "fuelCapacity": "200L"
  },
  "VAN-001": {
    "name": "Sprinter Van",
    "capacity": "3.5 tons",
    "fuelType": "diesel",
    "consumption": "8.5 L/100km",
    "fuelCapacity": "80L"
  }
}
```

## Tips & Tricks

1. **Fastest Route**: Select "Fastest" profile for time-sensitive deliveries
2. **Fuel Savings**: Use "Fuel Optimal" profile for long-distance routes
3. **Safe Routes**: Choose "Safest" profile for hazardous areas
4. **Balanced Default**: "Balanced" profile is recommended for most routes
5. **Optimize Order**: Always click "Optimize Order" for 3+ waypoints
6. **Vehicle Match**: Select vehicle based on cargo weight and type

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Button not visible | Hard refresh: Ctrl+Shift+R |
| Routes not calculating | Backend not yet implemented |
| Cities not showing | Refresh page and try again |
| Performance slow | Close other tabs/applications |
| Export not working | Check browser console for errors |

## System Status

✅ **Frontend**: Fully implemented and tested  
⏳ **Backend**: Awaiting implementation (see guide)  
✅ **UI**: Responsive and modern  
✅ **Performance**: Optimized for speed  

## Need Help?

1. **Read**: `README_SMART_ROUTING.md` (full documentation)
2. **Code**: `ADVANCED_ROUTING_GUIDE.md` (technical details)
3. **Examples**: `USAGE_EXAMPLES.md` (code snippets)
4. **Backend**: `BACKEND_IMPLEMENTATION_GUIDE.md` (API specs)

## Quick Links

- Main App: http://localhost:5173
- Component: `src/components/EnhancedRoutePlanner.jsx`
- Services: `src/services/routeOptimizer.js`
- Locations: `src/data/locations.js`
- API: `src/services/api.js`

---

**Status**: ✅ Ready to Use (Frontend Complete)  
**Version**: 1.0  
**Last Updated**: April 29, 2024
