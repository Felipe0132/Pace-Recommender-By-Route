import math

def setStart(lat, lon, points):
    if points:
        last = points[-1]
        return [last['lat'], last['lng']]  # Folium espera [lat, lng]
    else:
        return [lat, lon]

def elevation(p1, p2):
    e1 = p1.get('elev', p1.get('elevation', 0))
    e2 = p2.get('elev', p2.get('elevation', 0))

    diff = e2 - e1 
    
    ganho = max(0, diff)
    perda = max(0, -diff)

    return ganho, perda

def haversine_distance(p1, p2):
    """
    Calcule distance between two points in superface real
    """

    R = 6371000  # Raio da Terra em metros
    lat1, lon1 = math.radians(p1['lat']), math.radians(p1['lng'])
    lat2, lon2 = math.radians(p2['lat']), math.radians(p2['lng'])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c