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

def process_gpx_segments(file_gpx, target_segment_dist=300):
    """
    Lê o arquivo GPX diretamente e calcula distâncias e elevações reais gravadas pelo GPS,
    retornando o graphPonder já particionado em segmentos de ~300m instantaneamente.
    """
    if isinstance(file_gpx, str):
        with open(file_gpx, 'r') as f:
            gpx = gpxpy.parse(f)
    else:
        gpx = gpxpy.parse(file_gpx)

    all_points = []
    for track in gpx.tracks:
        for segment in track.segments:
            all_points.extend(segment.points)

    if not all_points:
        return nx.DiGraph(), [], []

    G_segment = nx.DiGraph()
    all_coords = [[p.latitude, p.longitude] for p in all_points]

    node_idx = 0
    dist_acumulada = 0
    subida = 0
    descida = 0
    coords_trecho = []

    for i in range(len(all_points) - 1):
        p1 = all_points[i]
        p2 = all_points[i + 1]

        d = p1.distance_2d(p2)
        if d is None or d == 0:
            continue

        dist_acumulada += d
        coords_trecho.append([p1.latitude, p1.longitude])

        ele1 = p1.elevation if p1.elevation is not None else 0
        ele2 = p2.elevation if p2.elevation is not None else 0
        diff = ele2 - ele1
        if diff > 0:
            subida += diff
        else:
            descida += abs(diff)

        if dist_acumulada >= target_segment_dist:
            coords_trecho.append([p2.latitude, p2.longitude])
            inclinacao = (subida - descida) / dist_acumulada * 100 if dist_acumulada > 0 else 0
            tipo = "Subida" if inclinacao > 3.9 else ("Descida" if inclinacao < -3.9 else "Plano")

            u = f"gpx_{node_idx}"
            v = f"gpx_{node_idx + 1}"

            G_segment.add_node(u, y=coords_trecho[0][0], x=coords_trecho[0][1])
            G_segment.add_node(v, y=coords_trecho[-1][0], x=coords_trecho[-1][1])

            G_segment.add_edge(
                u,
                v,
                distance=dist_acumulada,
                coords=coords_trecho,
                subida=subida,
                descida=descida,
                inclinacao=inclinacao,
                relevo=tipo
            )

            node_idx += 1
            dist_acumulada = 0
            subida = 0
            descida = 0
            coords_trecho = []

    if dist_acumulada > 0 and coords_trecho:
        coords_trecho.append([all_points[-1].latitude, all_points[-1].longitude])
        inclinacao = (subida - descida) / dist_acumulada * 100 if dist_acumulada > 0 else 0
        tipo = "Subida" if inclinacao > 3.9 else ("Descida" if inclinacao < -3.9 else "Plano")

        u = f"gpx_{node_idx}"
        v = f"gpx_{node_idx + 1}"

        G_segment.add_node(u, y=coords_trecho[0][0], x=coords_trecho[0][1])
        G_segment.add_node(v, y=coords_trecho[-1][0], x=coords_trecho[-1][1])

        G_segment.add_edge(
            u,
            v,
            distance=dist_acumulada,
            coords=coords_trecho,
            subida=subida,
            descida=descida,
            inclinacao=inclinacao,
            relevo=tipo
        )

    return G_segment, all_coords, all_points


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