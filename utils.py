def setStart(lat, lon, points):
    if points:
        last = points[-1]
        return [last['lat'], last['lng']]  # Folium espera [lat, lng]
    else:
        return [lat, lon]

def elevation(p1, p2):
    diff = p2.get('elevation', 0) - p1.get('elevation', 0)  # positivo = subida

    ganho = max(0, diff)   # subida: nunca negativo
    perda = max(0, -diff)  # descida: nunca negativo

    return ganho, perda