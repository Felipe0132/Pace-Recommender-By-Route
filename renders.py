import folium
import networkx as nx
import matplotlib.pyplot as plt

def render_map_main(start_coords, points, path):
    # Interative map

    m = folium.Map(location=start_coords, zoom_start=15)

    if len(points) > 0:
        start_point = [points[0]['lat'], points[0]['lng']]
        folium.Circle(
            location=start_point,
            radius=2000,
            color='#1E90FF',
            weight=1.5,
            fill=True,
            fill_color='#1E90FF',
            fill_opacity=0.07,
            dash_array='6, 6',
            tooltip='Área de Cobertura (2000m)'
        ).add_to(m)

        cursor_css = "<style>.leaflet-container { cursor: crosshair !important; }</style>"
        m.get_root().html.add_child(folium.Element(cursor_css))
        folium.plugins.LocateControl().add_to(m)

    for idx, point in enumerate(points):
        cor = 'green' if idx == 0 else 'blue'
        folium.CircleMarker(
            location=[point['lat'], point['lng']],
            radius=8,
            color=cor,
            weight=3,
            fill=True,
            fill_color='white',
            fill_opacity=1.0,
            interactive=False,
            tooltip="Partida" if idx == 0 else f"Ponto {idx+1}"
        ).add_to(m)

    for coords in path:
        if coords:
            folium.PolyLine(coords, color="blue", weight=4, interactive=False).add_to(m)

    return m

def render_map_groupBy(start_coords, G_groupBy, G_base):
    # Render map of a gruped of relevo

    m = folium.Map(location=start_coords, zoom_start=15)

    for u, v, data in G_groupBy.edges(data=True):
        dist = data.get('distance', 0)
        relevo = data.get('relevo', 0)
        inclinacao = data.get('inclinacao', 0)
        coords = data.get('coords', [])

        if u in G_base.nodes:
            u_coord = [G_base.nodes[u]['y'], G_base.nodes[u]['x']]
            folium.CircleMarker(
                location=u_coord,
                radius=6,
                color="#333333",
                tooltip=f"Nó de Início: {u}"
            ).add_to(m)

        if coords:
            folium.PolyLine(
                coords,
                color="blue",
                weight=5,
                tooltip=f"{relevo}: {dist:.0f}m ({inclinacao:+.1f}%)"
            ).add_to(m)
    return m

def plot_graph(G, atributo_label='relevo', node_color='lightblue'):
    # Draw the graph

    num_nodes = G.number_of_nodes()
    try:
        nodes_ordered = list(nx.topological_sort(G))
        pos = {node: (i, 0) for i, node in enumerate(nodes_ordered)}
    except nx.NetworkUnfeasible:
        pos = nx.circular_layout(G)

    fig, ax = plt.subplots(figsize=(max(6, num_nodes * 1.5), 2.5))
    nx.draw(G, pos, with_labels=True, node_color=node_color, node_size=600, font_size=7, ax=ax, arrows=True)
    labels = nx.get_edge_attributes(G, atributo_label)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=labels, font_size=7, ax=ax)

    return fig