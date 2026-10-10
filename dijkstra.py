def dijkstra(G, origin, destination):
    """
    Finds the shortest path between two nodes in an OSMnx graph using Dijkstra's algorithm.

    Args:
        G: OSMnx graph (MultiDiGraph)
        origin: ID of the origin node
        destination: ID of the destination node

    Returns:
        path: ordered list of node IDs from origin to destination
    """
    nodes = list(G.nodes)
    distances = {node: float('inf') for node in nodes}
    distances[origin] = 0
    visited = set()
    previous = {node: None for node in nodes}

    while True:
        # Pick unvisited node with smallest distance
        u = None
        for node in nodes:
            if node not in visited:
                if u is None or distances[node] < distances[u]:
                    u = node    

        if u is None or distances[u] == float('inf'):
            break  # All remaining nodes are unreachable

        if u == destination:
            break  # Reached destination

        visited.add(u)

        # Explore neighbors
        for v, edge_data in G[u].items():
            # OSMnx MultiDiGraph: edge_data is a dict of {edge_key: attributes}
            edge_length = min(d.get('length', float('inf')) for d in edge_data.values())
            alt = distances[u] + edge_length
            if alt < distances[v]:
                distances[v] = alt
                previous[v] = u

    # Reconstruct path from destination back to origin
    path = []
    current = destination
    while current is not None:
        path.append(current)
        current = previous[current]

    path.reverse()

    if path[0] != origin:
        return [], 0  # No path found

    return path, distances[destination]