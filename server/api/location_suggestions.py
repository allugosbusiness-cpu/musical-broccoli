"""
Location suggestions for mission creation
Includes schools, butcheries, abattoirs, universities and all key locations in Manicaland and Zimbabwe
"""

# Comprehensive Zimbabwe Location Database
MANICALAND_LOCATIONS = [
    # ===== MUTARE CITY =====
    # City Center
    {'name': 'Mutare CBD', 'lat': -18.9704, 'lon': 32.6648, 'type': 'city_center'},
    {'name': 'Mutare Main Post Office', 'lat': -18.9700, 'lon': 32.6650, 'type': 'landmark'},
    {'name': 'Mutare Central Hospital', 'lat': -18.9600, 'lon': 32.6700, 'type': 'hospital'},
    
    # Universities in Manicaland
    {'name': 'Africa University', 'lat': -19.2800, 'lon': 32.4500, 'type': 'university'},
    {'name': 'Manicaland State University of Applied Science (MSUAS)', 'lat': -18.9750, 'lon': 32.6600, 'type': 'university'},
    {'name': 'Harare Institute of Technology - Mutare Campus', 'lat': -18.9650, 'lon': 32.6700, 'type': 'university'},
    {'name': 'Chinhoyi University of Technology - Eastern Campus', 'lat': -19.0500, 'lon': 32.5500, 'type': 'university'},
    
    # Schools in Mutare
    {'name': 'Mutare Boys High School', 'lat': -18.9750, 'lon': 32.6550, 'type': 'school'},
    {'name': 'Mutare Girls High School', 'lat': -18.9680, 'lon': 32.6720, 'type': 'school'},
    {'name': 'Sakubva Primary School', 'lat': -18.9850, 'lon': 32.6500, 'type': 'school'},
    {'name': 'Magwegwe Primary School', 'lat': -18.9550, 'lon': 32.6800, 'type': 'school'},
    {'name': 'St. Johns Catholic High School', 'lat': -18.9500, 'lon': 32.7000, 'type': 'school'},
    {'name': 'Mutare Technical School', 'lat': -18.9900, 'lon': 32.6400, 'type': 'school'},
    {'name': 'Chikanda High School', 'lat': -18.9750, 'lon': 32.6500, 'type': 'school'},
    
    # Butcheries in Mutare
    {'name': 'Sakubva Butchery', 'lat': -18.9860, 'lon': 32.6510, 'type': 'butchery'},
    {'name': 'Central Mutare Butchery', 'lat': -18.9710, 'lon': 32.6650, 'type': 'butchery'},
    {'name': 'Chikanga Butchery', 'lat': -18.9600, 'lon': 32.6450, 'type': 'butchery'},
    {'name': 'Magwegwe Butchery', 'lat': -18.9540, 'lon': 32.6850, 'type': 'butchery'},
    {'name': 'Mbare Butchery', 'lat': -18.9950, 'lon': 32.6350, 'type': 'butchery'},
    
    # Abattoirs in Manicaland
    {'name': 'Mutare Central Abattoir', 'lat': -18.9900, 'lon': 32.6300, 'type': 'abattoir'},
    {'name': 'Sakubva Slaughter House', 'lat': -18.9880, 'lon': 32.6520, 'type': 'abattoir'},
    {'name': 'Manicaland Abattoir - Mutare East', 'lat': -18.9750, 'lon': 32.7050, 'type': 'abattoir'},
    {'name': 'Molus Abattoir', 'lat': -19.1250, 'lon': 32.5850, 'type': 'abattoir'},
    {'name': 'Sakubva Main Abattoir', 'lat': -18.9890, 'lon': 32.6490, 'type': 'abattoir'},
    
    # Markets
    {'name': 'Mutare Central Market', 'lat': -18.9705, 'lon': 32.6655, 'type': 'market'},
    {'name': 'Sakubva Market', 'lat': -18.9850, 'lon': 32.6510, 'type': 'market'},
    {'name': 'Chikanga Market', 'lat': -18.9600, 'lon': 32.6450, 'type': 'market'},
    {'name': 'Magwegwe Market', 'lat': -18.9540, 'lon': 32.6850, 'type': 'market'},
    
    # Supermarkets
    {'name': 'OK Bazaars - Mutare', 'lat': -18.9680, 'lon': 32.6700, 'type': 'supermarket'},
    {'name': 'Pick n Pay - Mutare CBD', 'lat': -18.9700, 'lon': 32.6660, 'type': 'supermarket'},
    {'name': 'TM Supermarket - Mutare', 'lat': -18.9720, 'lon': 32.6640, 'type': 'supermarket'},
    
    # ===== CHIPINGE DISTRICT =====
    {'name': 'Chipinge Town', 'lat': -20.2000, 'lon': 32.6000, 'type': 'town'},
    {'name': 'Chipinge High School', 'lat': -20.2010, 'lon': 32.6020, 'type': 'school'},
    {'name': 'Chipinge Primary School', 'lat': -20.2000, 'lon': 32.6010, 'type': 'school'},
    {'name': 'Chipinge Butchery', 'lat': -20.2000, 'lon': 32.5990, 'type': 'butchery'},
    {'name': 'Chipinge Central Market', 'lat': -20.1995, 'lon': 32.6010, 'type': 'market'},
    {'name': 'Chipinge Abattoir', 'lat': -20.2050, 'lon': 32.5950, 'type': 'abattoir'},
    
    # ===== NYANGA DISTRICT =====
    {'name': 'Nyanga Town', 'lat': -18.3000, 'lon': 32.7500, 'type': 'town'},
    {'name': 'Nyanga High School', 'lat': -18.3020, 'lon': 32.7520, 'type': 'school'},
    {'name': 'Nyanga Primary School', 'lat': -18.3000, 'lon': 32.7480, 'type': 'school'},
    {'name': 'Nyanga Butchery', 'lat': -18.3000, 'lon': 32.7480, 'type': 'butchery'},
    {'name': 'Nyanga Central Market', 'lat': -18.3010, 'lon': 32.7510, 'type': 'market'},
    
    # ===== CHIMANIMANI DISTRICT =====
    {'name': 'Chimanimani Town', 'lat': -19.7500, 'lon': 32.9000, 'type': 'town'},
    {'name': 'Chimanimani High School', 'lat': -19.7520, 'lon': 32.9020, 'type': 'school'},
    {'name': 'Chimanimani Primary School', 'lat': -19.7510, 'lon': 32.9010, 'type': 'school'},
    {'name': 'Chimanimani Butchery', 'lat': -19.7500, 'lon': 32.8990, 'type': 'butchery'},
    {'name': 'Chimanimani Market', 'lat': -19.7505, 'lon': 32.9005, 'type': 'market'},
    
    # ===== MAKONI DISTRICT =====
    {'name': 'Macheke Town', 'lat': -18.5000, 'lon': 31.5000, 'type': 'town'},
    {'name': 'Macheke High School', 'lat': -18.5020, 'lon': 31.5020, 'type': 'school'},
    {'name': 'Macheke Primary School', 'lat': -18.5010, 'lon': 31.5010, 'type': 'school'},
    {'name': 'Macheke Butchery', 'lat': -18.5000, 'lon': 31.4990, 'type': 'butchery'},
    {'name': 'Macheke Market', 'lat': -18.5005, 'lon': 31.5005, 'type': 'market'},
    
    # ===== BUHERA DISTRICT =====
    {'name': 'Hauna Town', 'lat': -18.0000, 'lon': 32.0000, 'type': 'town'},
    {'name': 'Hauna High School', 'lat': -18.0020, 'lon': 32.0020, 'type': 'school'},
    {'name': 'Hauna Butchery', 'lat': -18.0010, 'lon': 32.0010, 'type': 'butchery'},
    {'name': 'Hauna Market', 'lat': -18.0015, 'lon': 32.0015, 'type': 'market'},
    
    # ===== RUSAPE (MANICALAND BORDER) =====
    {'name': 'Rusape Town Center', 'lat': -19.7500, 'lon': 31.8000, 'type': 'town'},
    {'name': 'Rusape High School', 'lat': -19.7520, 'lon': 31.8020, 'type': 'school'},
    {'name': 'Rusape Butchery', 'lat': -19.7500, 'lon': 31.7990, 'type': 'butchery'},
    
    # Industrial/Logistics Hubs
    {'name': 'Mutare Industrial Park', 'lat': -19.0050, 'lon': 32.6200, 'type': 'industrial'},
    {'name': 'Mutare Border Post (Mozambique)', 'lat': -19.0150, 'lon': 32.6100, 'type': 'border'},
]

# Zimbabwe National Locations (Major Cities)
ZIMBABWE_LOCATIONS = [
    # ===== HARARE (CAPITAL) =====
    {'name': 'Harare CBD', 'lat': -17.8252, 'lon': 31.0335, 'type': 'city_center'},
    {'name': 'Harare International Airport', 'lat': -17.9255, 'lon': 31.0924, 'type': 'airport'},
    {'name': 'University of Zimbabwe', 'lat': -17.8857, 'lon': 31.0096, 'type': 'university'},
    {'name': 'Zimbabwe Open University - Harare', 'lat': -17.8500, 'lon': 31.0500, 'type': 'university'},
    {'name': 'Harare Central Hospital', 'lat': -17.8300, 'lon': 31.0500, 'type': 'hospital'},
    {'name': 'Avondale Market', 'lat': -17.8650, 'lon': 31.0200, 'type': 'market'},
    {'name': 'Mbare Musika (Main Market)', 'lat': -17.8500, 'lon': 31.0700, 'type': 'market'},
    {'name': 'Harare Abattoir', 'lat': -17.8800, 'lon': 31.0100, 'type': 'abattoir'},
    
    # ===== BULAWAYO =====
    {'name': 'Bulawayo CBD', 'lat': -20.1500, 'lon': 28.5800, 'type': 'city_center'},
    {'name': 'Bulawayo International Airport', 'lat': -20.0176, 'lon': 28.6119, 'type': 'airport'},
    {'name': 'National University of Science and Technology (NUST)', 'lat': -20.1300, 'lon': 28.5900, 'type': 'university'},
    {'name': 'Bulawayo Central Hospital', 'lat': -20.1550, 'lon': 28.5850, 'type': 'hospital'},
    {'name': 'Ascot Market', 'lat': -20.1450, 'lon': 28.5900, 'type': 'market'},
    {'name': 'Bulawayo Abattoir', 'lat': -20.1600, 'lon': 28.5750, 'type': 'abattoir'},
    
    # ===== MASVINGO =====
    {'name': 'Masvingo Town Center', 'lat': -20.0631, 'lon': 30.8276, 'type': 'city_center'},
    {'name': 'Zimbabwe Open University - Masvingo', 'lat': -20.0650, 'lon': 30.8300, 'type': 'university'},
    {'name': 'Great Zimbabwe University', 'lat': -20.2500, 'lon': 30.9000, 'type': 'university'},
    {'name': 'Masvingo Central Hospital', 'lat': -20.0650, 'lon': 30.8300, 'type': 'hospital'},
    {'name': 'Masvingo Central Market', 'lat': -20.0640, 'lon': 30.8280, 'type': 'market'},
    {'name': 'Great Zimbabwe Monuments', 'lat': -20.2650, 'lon': 30.9250, 'type': 'landmark'},
    
    # ===== GWERU =====
    {'name': 'Gweru Town Center', 'lat': -19.4500, 'lon': 29.8200, 'type': 'city_center'},
    {'name': 'Midlands State University', 'lat': -19.4550, 'lon': 29.8250, 'type': 'university'},
    {'name': 'Gweru Central Hospital', 'lat': -19.4520, 'lon': 29.8220, 'type': 'hospital'},
    {'name': 'Gweru Market', 'lat': -19.4510, 'lon': 29.8210, 'type': 'market'},
    
    # ===== KADOMA =====
    {'name': 'Kadoma Town Center', 'lat': -18.3250, 'lon': 29.9150, 'type': 'city_center'},
    {'name': 'Kadoma Hospital', 'lat': -18.3260, 'lon': 29.9160, 'type': 'hospital'},
    {'name': 'Kadoma Market', 'lat': -18.3245, 'lon': 29.9140, 'type': 'market'},
    
    # ===== CHINHOYI =====
    {'name': 'Chinhoyi Town Center', 'lat': -17.3700, 'lon': 30.2100, 'type': 'city_center'},
    {'name': 'Chinhoyi University of Technology', 'lat': -17.3750, 'lon': 30.2150, 'type': 'university'},
    {'name': 'Chinhoyi Hospital', 'lat': -17.3710, 'lon': 30.2110, 'type': 'hospital'},
    {'name': 'Chinhoyi Caves', 'lat': -17.3600, 'lon': 30.2050, 'type': 'landmark'},
    
    # ===== VICTORIA FALLS =====
    {'name': 'Victoria Falls Town', 'lat': -17.9244, 'lon': 25.8274, 'type': 'city_center'},
    {'name': 'Victoria Falls Airport', 'lat': -17.9247, 'lon': 25.8160, 'type': 'airport'},
    {'name': 'Victoria Falls National Park', 'lat': -17.9244, 'lon': 25.8250, 'type': 'landmark'},
    {'name': 'Victoria Falls Hospital', 'lat': -17.9250, 'lon': 25.8280, 'type': 'hospital'},
    
    # ===== LIVINGSTONE (BORDER) =====
    {'name': 'Kazungula Border Post (Botswana)', 'lat': -17.7844, 'lon': 25.2553, 'type': 'border'},
    
    # ===== KARIBA =====
    {'name': 'Kariba Town', 'lat': -16.5146, 'lon': 28.2804, 'type': 'town'},
    {'name': 'Kariba Dam', 'lat': -16.5165, 'lon': 28.2850, 'type': 'landmark'},
    
    # ===== ZVISHAVANE =====
    {'name': 'Zvishavane Town', 'lat': -20.3250, 'lon': 30.0150, 'type': 'town'},
    {'name': 'Zvishavane High School', 'lat': -20.3260, 'lon': 30.0160, 'type': 'school'},
    
    # ===== BEITBRIDGE =====
    {'name': 'Beitbridge Border Post (South Africa)', 'lat': -22.2167, 'lon': 30.0167, 'type': 'border'},
    {'name': 'Beitbridge Town', 'lat': -22.2150, 'lon': 30.0150, 'type': 'town'},
]

def search_locations(query, limit=10):
    """
    Search for locations matching the query string
    Returns list of matching locations with name, lat, lon, and type
    """
    all_locations = MANICALAND_LOCATIONS + ZIMBABWE_LOCATIONS
    
    if not query:
        return all_locations[:limit]
    
    query_lower = query.lower()
    matches = []
    
    for location in all_locations:
        name_lower = location['name'].lower()
        if query_lower in name_lower or name_lower.startswith(query_lower):
            matches.append(location)
    
    # Sort by relevance (exact prefix match first, then contains)
    exact_prefix = [loc for loc in matches if loc['name'].lower().startswith(query_lower)]
    others = [loc for loc in matches if loc not in exact_prefix]
    
    return (exact_prefix + others)[:limit]

def get_locations_by_type(location_type, limit=50):
    """
    Get all locations of a specific type
    Types: school, butchery, abattoir, market, supermarket, hospital, industrial, town, university, etc.
    """
    all_locations = MANICALAND_LOCATIONS + ZIMBABWE_LOCATIONS
    matches = [loc for loc in all_locations if loc['type'] == location_type]
    return matches[:limit]

def get_all_location_types():
    """Get list of all unique location types"""
    all_locations = MANICALAND_LOCATIONS + ZIMBABWE_LOCATIONS
    types = set(loc['type'] for loc in all_locations)
    return sorted(list(types))
