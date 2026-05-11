"""
Location suggestions for mission creation
Includes schools, butcheries, abattoirs and other key locations in Manicaland
"""

# Manicaland Region Locations (Zimbabwe)
MANICALAND_LOCATIONS = [
    # Mutare City Center
    {'name': 'Mutare CBD', 'lat': -18.9704, 'lon': 32.6648, 'type': 'city_center'},
    {'name': 'Mutare Main Post Office', 'lat': -18.9700, 'lon': 32.6650, 'type': 'landmark'},
    {'name': 'Mutare Central Hospital', 'lat': -18.9600, 'lon': 32.6700, 'type': 'hospital'},
    
    # Schools in Mutare
    {'name': 'Mutare Boys High School', 'lat': -18.9750, 'lon': 32.6550, 'type': 'school'},
    {'name': 'Mutare Girls High School', 'lat': -18.9680, 'lon': 32.6720, 'type': 'school'},
    {'name': 'Sakubva Primary School', 'lat': -18.9850, 'lon': 32.6500, 'type': 'school'},
    {'name': 'Magwegwe Primary School', 'lat': -18.9550, 'lon': 32.6800, 'type': 'school'},
    {'name': 'St. Johns Catholic High School', 'lat': -18.9500, 'lon': 32.7000, 'type': 'school'},
    {'name': 'Mutare Technical School', 'lat': -18.9900, 'lon': 32.6400, 'type': 'school'},
    
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
    
    # Markets
    {'name': 'Mutare Central Market', 'lat': -18.9705, 'lon': 32.6655, 'type': 'market'},
    {'name': 'Sakubva Market', 'lat': -18.9850, 'lon': 32.6510, 'type': 'market'},
    {'name': 'Chikanga Market', 'lat': -18.9600, 'lon': 32.6450, 'type': 'market'},
    
    # Supermarkets
    {'name': 'OK Bazaars - Mutare', 'lat': -18.9680, 'lon': 32.6700, 'type': 'supermarket'},
    {'name': 'Pick n Pay - Mutare CBD', 'lat': -18.9700, 'lon': 32.6660, 'type': 'supermarket'},
    {'name': 'TM Supermarket - Mutare', 'lat': -18.9720, 'lon': 32.6640, 'type': 'supermarket'},
    
    # Industrial/Logistics Hubs
    {'name': 'Mutare Industrial Park', 'lat': -19.0050, 'lon': 32.6200, 'type': 'industrial'},
    {'name': 'Mutare Border Post', 'lat': -19.0150, 'lon': 32.6100, 'type': 'border'},
    
    # Outlying Towns
    {'name': 'Rusape Town Center', 'lat': -19.7500, 'lon': 31.8000, 'type': 'town'},
    {'name': 'Masvingo - Rusape Road', 'lat': -19.7450, 'lon': 31.8050, 'type': 'route'},
    
    # Chipinge District
    {'name': 'Chipinge Town', 'lat': -20.2000, 'lon': 32.6000, 'type': 'town'},
    {'name': 'Chipinge High School', 'lat': -20.2010, 'lon': 32.6020, 'type': 'school'},
    {'name': 'Chipinge Butchery', 'lat': -20.2000, 'lon': 32.5990, 'type': 'butchery'},
    {'name': 'Chipinge Central Market', 'lat': -20.1995, 'lon': 32.6010, 'type': 'market'},
    
    # Nyanga District
    {'name': 'Nyanga Town', 'lat': -18.3000, 'lon': 32.7500, 'type': 'town'},
    {'name': 'Nyanga High School', 'lat': -18.3020, 'lon': 32.7520, 'type': 'school'},
    {'name': 'Nyanga Butchery', 'lat': -18.3000, 'lon': 32.7480, 'type': 'butchery'},
    
    # Chimanimani District
    {'name': 'Chimanimani Town', 'lat': -19.7500, 'lon': 32.9000, 'type': 'town'},
    {'name': 'Chimanimani High School', 'lat': -19.7520, 'lon': 32.9020, 'type': 'school'},
    
    # Makoni District
    {'name': 'Macheke Town', 'lat': -18.5000, 'lon': 31.5000, 'type': 'town'},
    {'name': 'Macheke High School', 'lat': -18.5020, 'lon': 31.5020, 'type': 'school'},
    
    # Buhera District
    {'name': 'Hauna Town', 'lat': -18.0000, 'lon': 32.0000, 'type': 'town'},
    {'name': 'Hauna Butchery', 'lat': -18.0010, 'lon': 32.0010, 'type': 'butchery'},
]

def search_locations(query, limit=10):
    """
    Search for locations matching the query string
    Returns list of matching locations with name, lat, lon, and type
    """
    if not query:
        return MANICALAND_LOCATIONS[:limit]
    
    query_lower = query.lower()
    matches = []
    
    for location in MANICALAND_LOCATIONS:
        name_lower = location['name'].lower()
        if query_lower in name_lower or name_lower.startswith(query_lower):
            matches.append(location)
    
    # Sort by relevance (exact prefix match first, then contains)
    exact_prefix = [loc for loc in matches if loc['name'].lower().startswith(query_lower)]
    others = [loc for loc in matches if loc not in exact_prefix]
    
    return (exact_prefix + others)[:limit]

def get_locations_by_type(location_type, limit=20):
    """
    Get all locations of a specific type
    Types: school, butchery, abattoir, market, supermarket, hospital, industrial, town, etc.
    """
    matches = [loc for loc in MANICALAND_LOCATIONS if loc['type'] == location_type]
    return matches[:limit]

def get_all_location_types():
    """Get list of all unique location types"""
    types = set(loc['type'] for loc in MANICALAND_LOCATIONS)
    return sorted(list(types))
