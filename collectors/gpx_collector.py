import osmnx as ox
from itertools import groupby
import gpxpy
import networkx as nx

def extract_points_gpx(file_gpx):
    # Extract point to point in gpx file

    if isinstance(file_gpx, str): # If recive string in st.upload
        with open(file_gpx, 'r') as f:
            gpx = gpxpy.parse(f)
    else:
        gpx = gpxpy.parse(file_gpx)

    points = []
    points_aux = []

    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                ponto_aux = {
                            'lng':point.longitude,
                            'lat':point.latitude,
                            'elev':point.elevation
                        }
                if not points or ponto_aux != points[-1]:  
                    points.append(ponto_aux)
                    points_aux.append(ponto_aux)

    return points
