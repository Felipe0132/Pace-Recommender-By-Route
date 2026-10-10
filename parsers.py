import gpxpy
import osmnx as ox
from itertools import groupby

def extract_gpx_map(file_gpx, G):

    if isinstance(file_gpx, str): # If recive string in st.upload
        with open(file_gpx, 'r') as f:
            gpx = gpxpy.parse(f)
    else:
        gpx = gpxpy.parse(file_gpx)

    points = []
    lats = []
    lons = []

    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                lons.append(point.longitude)
                lats.append(point.latitude)

    points = ox.distance.nearest_nodes(G, X=lons, Y=lats)

    points_clean = [node for node, _ in groupby(points)]

    return points_clean

def extract_from_dijk(G, path):
    # Recive path of dijkstra, after select sub_start to sub_end
    # Dijkstra return the esquinas, no ever points

    coords = []
    for u, v in zip(path[:-1], path[1:]): # one to one
        if v in G[u]:
            edge = min(G[u][v].values(), key=lambda d: d.get('length', float('inf')))
            if 'geometry' in edge:
                coords.extend([[lat, lng] for lng, lat in edge['geometry'].coords])
            else:
                coords.append([G.nodes[u]['y'], G.nodes[u]['x']])
                coords.append([G.nodes[v]['y'], G.nodes[v]['x']])
        elif u in G[v]:
            edge = min(G[v][u].values(), key=lambda d: d.get('length', float('inf')))
            if 'geometry' in edge:
                coords.extend([[lat, lng] for lng, lat in reversed(list(edge['geometry'].coords))])
            else:
                coords.append([G.nodes[u]['y'], G.nodes[u]['x']])
                coords.append([G.nodes[v]['y'], G.nodes[v]['x']])
        else:
            coords.append([G.nodes[u]['y'], G.nodes[u]['x']])
            coords.append([G.nodes[v]['y'], G.nodes[v]['x']])
    return coords

def group_by_path(path_select):
    # The path select is one node to another node, here complete full

    full_path = []
    for path in path_select:
        if not full_path:
            full_path.extend(path)
        else:
            # One sub path finish in the start the next, here skip the firts
            full_path.extend(path[1:])
    return full_path