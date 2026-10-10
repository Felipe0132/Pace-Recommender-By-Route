import collectors.gpx_collector as gpx_collector
import core.graph_builder as graph_builder

def process_gpx_route(file_gpx):
    """
    Process the GPX into function, in main or another method
    Here request only file_gpx and return graph ponder
    """

    points = gpx_collector.extract_points_gpx(file_gpx)
    G_segment = graph_builder.points_to_graph(points)
    G_grouped = graph_builder.groupByRelevo(G_segment)
    segments, dist, up, down = extract_infs(G_grouped)

    return G_segment, G_grouped, segments, dist, up, down

def extract_infs(G_grouped):
    segments = []
    dist_acum = 0
    up = 0
    down = 0

    for u, v, data in G_grouped.edges(data=True):
        coords = data.get('coords', [])
        relevo = data.get('relevo')           
        dist = data.get('distance', 0)         
        inc = data.get('inc', 0)      

        dist_acum += dist

        up += data.get('up', 0)
        down += data.get('down', 0)

        segments.append({
            "start":coords[0],
            "end":coords[-1:],
            "relevo":relevo,
            "dist":dist,
            "inc":inc
        })

    return segments, dist_acum, up, down