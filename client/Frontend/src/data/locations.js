// Global city/location coordinates (latitude, longitude)
export const GLOBAL_LOCATIONS = {
  // Zimbabwe
  'Harare': { lat: -17.8252, lng: 31.0335, country: 'Zimbabwe', region: 'Southern Africa' },
  'Bulawayo': { lat: -20.1550, lng: 28.5795, country: 'Zimbabwe', region: 'Southern Africa' },
  'Mutare': { lat: -18.9663, lng: 32.6678, country: 'Zimbabwe', region: 'Southern Africa' },
  'Gweru': { lat: -19.4483, lng: 29.8183, country: 'Zimbabwe', region: 'Southern Africa' },
  'Masvingo': { lat: -20.0655, lng: 30.8285, country: 'Zimbabwe', region: 'Southern Africa' },
  'Marondera': { lat: -18.3250, lng: 31.5333, country: 'Zimbabwe', region: 'Southern Africa' },
  'Macheke': { lat: -18.4500, lng: 31.7667, country: 'Zimbabwe', region: 'Southern Africa' },
  'Rusape': { lat: -18.5214, lng: 32.1169, country: 'Zimbabwe', region: 'Southern Africa' },
  'Headlands': { lat: -18.5978, lng: 32.4058, country: 'Zimbabwe', region: 'Southern Africa' },
  'Chegutu': { lat: -18.2919, lng: 29.7769, country: 'Zimbabwe', region: 'Southern Africa' },
  'Kariba': { lat: -16.5319, lng: 28.2453, country: 'Zimbabwe', region: 'Southern Africa' },
  'Chinhoyi': { lat: -17.3653, lng: 30.1990, country: 'Zimbabwe', region: 'Southern Africa' },

  // Zambia
  'Lusaka': { lat: -15.3875, lng: 28.3228, country: 'Zambia', region: 'Southern Africa' },
  'Ndola': { lat: -12.9641, lng: 28.6362, country: 'Zambia', region: 'Southern Africa' },
  'Kitwe': { lat: -12.8381, lng: 28.2596, country: 'Zambia', region: 'Southern Africa' },
  'Livingstone': { lat: -17.8426, lng: 25.8550, country: 'Zambia', region: 'Southern Africa' },

  // Botswana
  'Gaborone': { lat: -24.6282, lng: 25.9145, country: 'Botswana', region: 'Southern Africa' },
  'Francistown': { lat: -21.1625, lng: 27.5000, country: 'Botswana', region: 'Southern Africa' },

  // South Africa
  'Johannesburg': { lat: -26.2023, lng: 28.0436, country: 'South Africa', region: 'Southern Africa' },
  'Pretoria': { lat: -25.7479, lng: 28.2293, country: 'South Africa', region: 'Southern Africa' },
  'Cape Town': { lat: -33.9249, lng: 18.4241, country: 'South Africa', region: 'Southern Africa' },
  'Durban': { lat: -29.8587, lng: 31.0218, country: 'South Africa', region: 'Southern Africa' },

  // Kenya
  'Nairobi': { lat: -1.2864, lng: 36.8172, country: 'Kenya', region: 'East Africa' },
  'Mombasa': { lat: -4.0435, lng: 39.6682, country: 'Kenya', region: 'East Africa' },

  // Tanzania
  'Dar es Salaam': { lat: -6.8000, lng: 39.2833, country: 'Tanzania', region: 'East Africa' },
  'Dodoma': { lat: -6.1639, lng: 35.7465, country: 'Tanzania', region: 'East Africa' },

  // Malawi
  'Lilongwe': { lat: -13.9626, lng: 33.7741, country: 'Malawi', region: 'Southern Africa' },
  'Blantyre': { lat: -15.7942, lng: 35.0058, country: 'Malawi', region: 'Southern Africa' },

  // Mozambique
  'Maputo': { lat: -23.8650, lng: 35.3281, country: 'Mozambique', region: 'Southern Africa' },
  'Beira': { lat: -19.8406, lng: 34.5367, country: 'Mozambique', region: 'Southern Africa' },

  // Chitungwiza (Zimbabwe)
  'Chitungwiza': { lat: -18.0083, lng: 31.0753, country: 'Zimbabwe', region: 'Southern Africa' },

  // Zimbabwe - Universities
  'University of Zimbabwe': { lat: -17.8290, lng: 31.0397, country: 'Zimbabwe', region: 'Southern Africa', type: 'University' },
  'Zimbabwe Open University': { lat: -17.8250, lng: 31.0350, country: 'Zimbabwe', region: 'Southern Africa', type: 'University' },
  'Africa University': { lat: -18.3250, lng: 31.5333, country: 'Zimbabwe', region: 'Southern Africa', type: 'University' },
  'Zimbabwe Academy of Music': { lat: -17.8260, lng: 31.0400, country: 'Zimbabwe', region: 'Southern Africa', type: 'University' },
  'Harare Polytechnic': { lat: -17.8220, lng: 31.0320, country: 'Zimbabwe', region: 'Southern Africa', type: 'University' },
  'Chinhoyi University of Technology': { lat: -17.3653, lng: 30.1990, country: 'Zimbabwe', region: 'Southern Africa', type: 'University' },

  // Zimbabwe - Schools (Harare)
  'Harare International School': { lat: -17.7950, lng: 31.0100, country: 'Zimbabwe', region: 'Southern Africa', type: 'School' },
  'Prince Edward School': { lat: -17.8180, lng: 31.0250, country: 'Zimbabwe', region: 'Southern Africa', type: 'School' },
  'Arundel School': { lat: -17.8350, lng: 31.0450, country: 'Zimbabwe', region: 'Southern Africa', type: 'School' },
  'Eager School': { lat: -17.8100, lng: 31.0200, country: 'Zimbabwe', region: 'Southern Africa', type: 'School' },
  'Westgate School': { lat: -17.8400, lng: 31.0500, country: 'Zimbabwe', region: 'Southern Africa', type: 'School' },
  'Founders School': { lat: -17.8250, lng: 31.0350, country: 'Zimbabwe', region: 'Southern Africa', type: 'School' },

  // Zimbabwe - Schools (Other Cities)
  'Bulawayo High School': { lat: -20.1550, lng: 28.5795, country: 'Zimbabwe', region: 'Southern Africa', type: 'School' },
  'Milton School': { lat: -20.1600, lng: 28.5850, country: 'Zimbabwe', region: 'Southern Africa', type: 'School' },
  'Mutare School': { lat: -18.9663, lng: 32.6678, country: 'Zimbabwe', region: 'Southern Africa', type: 'School' },
  'Gweru High School': { lat: -19.4483, lng: 29.8183, country: 'Zimbabwe', region: 'Southern Africa', type: 'School' },

  // Zimbabwe - Hospitals & Health Institutions
  'Parirenyatwa Hospital': { lat: -17.8220, lng: 31.0300, country: 'Zimbabwe', region: 'Southern Africa', type: 'Hospital' },
  'Sally Mugabe Central Hospital': { lat: -17.8180, lng: 31.0250, country: 'Zimbabwe', region: 'Southern Africa', type: 'Hospital' },
  'Harare Hospital': { lat: -17.8100, lng: 31.0150, country: 'Zimbabwe', region: 'Southern Africa', type: 'Hospital' },
  'United Bulawayo Hospitals': { lat: -20.1550, lng: 28.5795, country: 'Zimbabwe', region: 'Southern Africa', type: 'Hospital' },
  'Mutare General Hospital': { lat: -18.9663, lng: 32.6678, country: 'Zimbabwe', region: 'Southern Africa', type: 'Hospital' },

  // Zimbabwe - Government Buildings & Institutions
  'Parliament of Zimbabwe': { lat: -17.8280, lng: 31.0380, country: 'Zimbabwe', region: 'Southern Africa', type: 'Government' },
  'Reserve Bank of Zimbabwe': { lat: -17.8230, lng: 31.0280, country: 'Zimbabwe', region: 'Southern Africa', type: 'Government' },
  'Constitutional Court': { lat: -17.8150, lng: 31.0200, country: 'Zimbabwe', region: 'Southern Africa', type: 'Government' },
  'State House': { lat: -17.8400, lng: 31.0500, country: 'Zimbabwe', region: 'Southern Africa', type: 'Government' },
  'Ministry of Finance': { lat: -17.8260, lng: 31.0350, country: 'Zimbabwe', region: 'Southern Africa', type: 'Government' },

  // Zimbabwe - Shopping Centers & Markets
  'Westgate Shopping Centre': { lat: -17.8400, lng: 31.0500, country: 'Zimbabwe', region: 'Southern Africa', type: 'Market' },
  'Harare City Centre': { lat: -17.8250, lng: 31.0350, country: 'Zimbabwe', region: 'Southern Africa', type: 'Market' },
  'Kuwadzana Shopping Centre': { lat: -17.8550, lng: 30.9950, country: 'Zimbabwe', region: 'Southern Africa', type: 'Market' },
  'Eastgate Shopping Centre': { lat: -17.8150, lng: 31.0400, country: 'Zimbabwe', region: 'Southern Africa', type: 'Market' },
  'Bulawayo Market': { lat: -20.1550, lng: 28.5795, country: 'Zimbabwe', region: 'Southern Africa', type: 'Market' },

  // Zimbabwe - Industrial & Transport Hubs
  'Harare International Airport': { lat: -17.9319, lng: 31.1089, country: 'Zimbabwe', region: 'Southern Africa', type: 'Transport' },
  'Harare Railway Station': { lat: -17.8270, lng: 31.0370, country: 'Zimbabwe', region: 'Southern Africa', type: 'Transport' },
  'Bulawayo Railway Station': { lat: -20.1550, lng: 28.5795, country: 'Zimbabwe', region: 'Southern Africa', type: 'Transport' },
  'Zimbabwe Industrial Trade Park': { lat: -17.8500, lng: 31.0600, country: 'Zimbabwe', region: 'Southern Africa', type: 'Industrial' },

  // International Major Hubs - Middle East
  'Dubai': { lat: 25.2048, lng: 55.2708, country: 'UAE', region: 'Middle East' },
  'Abu Dhabi': { lat: 24.4539, lng: 54.3773, country: 'UAE', region: 'Middle East' },
  'Doha': { lat: 25.2854, lng: 51.5310, country: 'Qatar', region: 'Middle East' },
  'Riyadh': { lat: 24.7136, lng: 46.6753, country: 'Saudi Arabia', region: 'Middle East' },
  'Jeddah': { lat: 21.5433, lng: 39.1727, country: 'Saudi Arabia', region: 'Middle East' },

  // Asia - East & Southeast
  'Singapore': { lat: 1.3521, lng: 103.8198, country: 'Singapore', region: 'Asia' },
  'Hong Kong': { lat: 22.3193, lng: 114.1694, country: 'Hong Kong', region: 'Asia' },
  'Shanghai': { lat: 31.2304, lng: 121.4737, country: 'China', region: 'Asia' },
  'Beijing': { lat: 39.9042, lng: 116.4074, country: 'China', region: 'Asia' },
  'Tokyo': { lat: 35.6762, lng: 139.6503, country: 'Japan', region: 'Asia' },
  'Bangkok': { lat: 13.7563, lng: 100.5018, country: 'Thailand', region: 'Asia' },
  'Ho Chi Minh City': { lat: 10.8231, lng: 106.6297, country: 'Vietnam', region: 'Asia' },
  'Manila': { lat: 14.5994, lng: 120.9842, country: 'Philippines', region: 'Asia' },
  'Jakarta': { lat: -6.2088, lng: 106.8456, country: 'Indonesia', region: 'Asia' },
  'Kuala Lumpur': { lat: 3.1390, lng: 101.6869, country: 'Malaysia', region: 'Asia' },

  // India
  'Mumbai': { lat: 19.0760, lng: 72.8777, country: 'India', region: 'Asia' },
  'Delhi': { lat: 28.7041, lng: 77.1025, country: 'India', region: 'Asia' },
  'Bangalore': { lat: 12.9716, lng: 77.5946, country: 'India', region: 'Asia' },
  'Chennai': { lat: 13.0827, lng: 80.2707, country: 'India', region: 'Asia' },
  'Kolkata': { lat: 22.5726, lng: 88.3639, country: 'India', region: 'Asia' },

  // Europe - Major Cities
  'London': { lat: 51.5074, lng: -0.1278, country: 'UK', region: 'Europe' },
  'Rotterdam': { lat: 51.9225, lng: 4.4792, country: 'Netherlands', region: 'Europe' },
  'Hamburg': { lat: 53.5511, lng: 9.9937, country: 'Germany', region: 'Europe' },
  'Berlin': { lat: 52.5200, lng: 13.4050, country: 'Germany', region: 'Europe' },
  'Frankfurt': { lat: 50.1109, lng: 8.6821, country: 'Germany', region: 'Europe' },
  'Paris': { lat: 48.8566, lng: 2.3522, country: 'France', region: 'Europe' },
  'Lyon': { lat: 45.7640, lng: 4.8357, country: 'France', region: 'Europe' },
  'Madrid': { lat: 40.4168, lng: -3.7038, country: 'Spain', region: 'Europe' },
  'Barcelona': { lat: 41.3851, lng: 2.1734, country: 'Spain', region: 'Europe' },
  'Milan': { lat: 45.4642, lng: 9.1900, country: 'Italy', region: 'Europe' },
  'Rome': { lat: 41.9028, lng: 12.4964, country: 'Italy', region: 'Europe' },
  'Amsterdam': { lat: 52.3676, lng: 4.9041, country: 'Netherlands', region: 'Europe' },
  'Antwerp': { lat: 51.2211, lng: 4.4204, country: 'Belgium', region: 'Europe' },
  'Warsaw': { lat: 52.2297, lng: 21.0122, country: 'Poland', region: 'Europe' },

  // North America
  'Los Angeles': { lat: 34.0522, lng: -118.2437, country: 'USA', region: 'North America' },
  'New York': { lat: 40.7128, lng: -74.0060, country: 'USA', region: 'North America' },
  'Chicago': { lat: 41.8781, lng: -87.6298, country: 'USA', region: 'North America' },
  'Houston': { lat: 29.7604, lng: -95.3698, country: 'USA', region: 'North America' },
  'Dallas': { lat: 32.7767, lng: -96.7970, country: 'USA', region: 'North America' },
  'Seattle': { lat: 47.6062, lng: -122.3321, country: 'USA', region: 'North America' },
  'San Francisco': { lat: 37.7749, lng: -122.4194, country: 'USA', region: 'North America' },
  'Miami': { lat: 25.7617, lng: -80.1918, country: 'USA', region: 'North America' },
  'Toronto': { lat: 43.6532, lng: -79.3832, country: 'Canada', region: 'North America' },
  'Vancouver': { lat: 49.2827, lng: -123.1207, country: 'Canada', region: 'North America' },
  'Mexico City': { lat: 19.4326, lng: -99.1332, country: 'Mexico', region: 'North America' },

  // South America
  'São Paulo': { lat: -23.5505, lng: -46.6333, country: 'Brazil', region: 'South America' },
  'Rio de Janeiro': { lat: -22.9068, lng: -43.1729, country: 'Brazil', region: 'South America' },
  'Buenos Aires': { lat: -34.6037, lng: -58.3816, country: 'Argentina', region: 'South America' },
  'Santiago': { lat: -33.4489, lng: -70.6693, country: 'Chile', region: 'South America' },
  'Lima': { lat: -12.0464, lng: -77.0428, country: 'Peru', region: 'South America' },
  'Bogotá': { lat: 4.7110, lng: -74.0055, country: 'Colombia', region: 'South America' },

  // Australia
  'Sydney': { lat: -33.8688, lng: 151.2093, country: 'Australia', region: 'Oceania' },
  'Melbourne': { lat: -37.8136, lng: 144.9631, country: 'Australia', region: 'Oceania' },
  'Brisbane': { lat: -27.4698, lng: 153.0251, country: 'Australia', region: 'Oceania' },
  'Perth': { lat: -31.9505, lng: 115.8605, country: 'Australia', region: 'Oceania' },

  // Africa - Other countries
  'Lagos': { lat: 6.5244, lng: 3.3792, country: 'Nigeria', region: 'West Africa' },
  'Cairo': { lat: 30.0444, lng: 31.2357, country: 'Egypt', region: 'North Africa' },
  'Casablanca': { lat: 33.5731, lng: -7.5898, country: 'Morocco', region: 'North Africa' },
  'Johannesburg': { lat: -26.2023, lng: 28.0436, country: 'South Africa', region: 'Southern Africa' },
  'Cape Town': { lat: -33.9249, lng: 18.4241, country: 'South Africa', region: 'Southern Africa' },
};

// Get coordinates for a location, fallback to Harare if not found
export const getCoordinates = (location) => {
  return GLOBAL_LOCATIONS[location] || { lat: -17.8252, lng: 31.0335, country: 'Zimbabwe', region: 'Southern Africa' };
};

// Calculate distance between two coordinates (Haversine formula)
export const calculateDistance = (lat1, lng1, lat2, lng2) => {
  const R = 6371; // Earth's radius in km
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLng = (lng2 - lng1) * Math.PI / 180;
  const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLng / 2) * Math.sin(dLng / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return Math.round(R * c);
};

export default GLOBAL_LOCATIONS;
