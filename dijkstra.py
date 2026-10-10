import heapq

def dijkstra(G, origin, destination):
    """
    Finds the shortest path between two nodes in an OSMnx graph using Dijkstra's algorithm.

    Args:
        G: OSMnx graph (MultiDiGraph)
        origin: ID of the origin node
        destination: ID of the destination node

    Returns:
        path: ordered list of node IDs from origin to destination
        distance: total distance in meters
    """
    if origin not in G or destination not in G:
        return [], 0

    if origin == destination:
        return [origin], 0

    distances = {origin: 0}
    previous = {}
    pq = [(0, origin)]
    visited = set()

    while pq:
        dist_u, u = heapq.heappop(pq)

        if u in visited:
            continue
        visited.add(u)

        if u == destination:
            break

        if u not in G:
            continue

        for v, edge_data in G[u].items():
            edge_length = min(d.get('length', float('inf')) for d in edge_data.values())
            alt = dist_u + edge_length
            if alt < distances.get(v, float('inf')):
                distances[v] = alt
                previous[v] = u
                heapq.heappush(pq, (alt, v))

    if destination not in previous and origin != destination:
        return [], 0

    path = []
    curr = destination
    while curr is not None:
        path.append(curr)
        curr = previous.get(curr)

    path.reverse()

    if not path or path[0] != origin:
        return [], 0

    return path, distances.get(destination, 0)