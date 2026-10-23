import folium
import networkx as nx
import matplotlib.pyplot as plt
import Enums.enum as enum

def plot_map_grouped(G_grouped):
    if G_grouped is None or G_grouped.number_of_edges() == 0:
        return None

    first_edge = list(G_grouped.edges(data=True))[0][2] # 0 is first edge, 2 is data of edge 
    start_coords = first_edge['coords'][0] # Get coords of data and 0 indxof

    m = folium.Map(location=start_coords, zoom_start=15)

    for u, v, data in G_grouped.edges(data=True):
        coords = data.get('coords', [])
        relevo = data.get('relevo')           
        dist = data.get('distance', 0)         
        inc = data.get('inc', 0)        
        color = data.get('color') or enum.ColorByRelevo[relevo.name].value

        folium.PolyLine(
            locations=coords,                                   
            color=color,                                         
            weight=5,                                           
            opacity=0.85,                                      
            tooltip=f"{relevo}: {dist:.0f}m ({inc:+.1f}%)"      
        ).add_to(m)

    folium.CircleMarker(
        location=start_coords,
        radius=7,
        color="green",
        fill=True,
        fill_color="white",
        fill_opacity=1.0,
        tooltip="Largada"
    ).add_to(m)

    return m

def plot_graph_topology(G_grouped):
    """
    Plota no frontend o grafo direcionado com os pesos (distância, inclinação),
    cores por relevo (Subida = Vermelho, Descida = Verde, Plano = Azul)
    e nós destacados de Largada/Chegada.
    Se for circuito fechado, desenha em anel circular; se for reta, alinha horizontalmente.
    """
    import math

    if G_grouped is None or G_grouped.number_of_edges() == 0:
        return None

    edges_list = list(G_grouped.edges(data=True))
    ordered_nodes = []
    if edges_list:
        ordered_nodes.append(edges_list[0][0])
        for _, v, _ in edges_list:
            if v not in ordered_nodes:
                ordered_nodes.append(v)
    else:
        ordered_nodes = list(G_grouped.nodes())

    total_nodes = len(ordered_nodes)

    # Detecta se é circuito fechado (largada próxima da chegada)
    is_circuit = False
    if edges_list and len(edges_list) >= 3:
        p1 = edges_list[0][2].get('coords', [[]])[0]
        p2 = edges_list[-1][2].get('coords', [[]])[-1]
        if p1 and p2 and len(p1) >= 2 and len(p2) >= 2:
            import utils.utils as u_utils
            d = u_utils.haversine_distance({'lat': p1[0], 'lng': p1[1]}, {'lat': p2[0], 'lng': p2[1]})
            if d <= 250.0:
                is_circuit = True

    # Posições (Layout circular para circuito ou linear para reta)
    pos = {}
    if is_circuit:
        radius = 1.0
        for idx, node in enumerate(ordered_nodes):
            angle = -math.pi / 2 + (2 * math.pi * idx / total_nodes)
            pos[node] = (radius * math.cos(angle), -radius * math.sin(angle))
        figsize = (8, 7)
    else:
        for idx, node in enumerate(ordered_nodes):
            pos[node] = (idx * 1.5, 0.0)
        figsize = (max(9, total_nodes * 1.8), 3.2)

    fig, ax = plt.subplots(figsize=figsize)

    # Cores dos nós
    node_colors = []
    node_sizes = []
    for idx, node in enumerate(ordered_nodes):
        if idx == 0:
            node_colors.append('#2ECC71')  # Verde (Largada)
            node_sizes.append(1000)
        elif idx == total_nodes - 1 and not is_circuit:
            node_colors.append('#E74C3C')  # Vermelho (Chegada)
            node_sizes.append(1000)
        else:
            node_colors.append('#34495E')  # Cinza escuro azulado
            node_sizes.append(750)

    # Desenha os nós
    nx.draw_networkx_nodes(
        G_grouped, pos,
        nodelist=ordered_nodes,
        node_color=node_colors,
        node_size=node_sizes,
        edgecolors='#2C3E50',
        linewidths=1.5,
        ax=ax
    )

    # Rótulos dos nós (com destaque para Largada)
    labels_dict = {}
    for idx, node in enumerate(ordered_nodes):
        if idx == 0:
            labels_dict[node] = f"{node}\n(Largada)"
        elif idx == total_nodes - 1 and not is_circuit:
            labels_dict[node] = f"{node}\n(Chegada)"
        else:
            labels_dict[node] = str(node)

    nx.draw_networkx_labels(
        G_grouped, pos,
        labels=labels_dict,
        font_size=8,
        font_color='white',
        font_weight='bold',
        ax=ax
    )

    # Cores e pesos das arestas
    edge_colors = []
    edge_widths = []
    edge_labels = {}

    for u, v, data in edges_list:
        cor = data.get('color', '#3498DB')
        inc = float(data.get('inc', 0))
        dist = float(data.get('distance', 0))
        relevo = data.get('relevo', '')
        relevo_str = relevo.value if hasattr(relevo, 'value') else str(relevo)

        edge_colors.append(cor)
        # Espessura proporcional ao impacto da inclinação
        edge_widths.append(max(2.5, min(6.0, 2.5 + abs(inc) * 0.4)))

        # Rótulo em cima de cada aresta com o tipo de relevo, metragem e inclinação
        edge_labels[(u, v)] = f"{relevo_str}\n{dist:.0f}m ({inc:+.1f}%)"

    # Desenha arestas direcionadas com curvatura harmônica
    rad = 0.15 if is_circuit else 0.1
    nx.draw_networkx_edges(
        G_grouped, pos,
        edgelist=[(u, v) for u, v, _ in edges_list],
        edge_color=edge_colors,
        width=edge_widths,
        arrows=True,
        arrowsize=18,
        arrowstyle='-|>',
        connectionstyle=f"arc3,rad={rad}",
        node_size=900,
        ax=ax
    )

    # Desenha os rótulos de cada aresta
    nx.draw_networkx_edge_labels(
        G_grouped, pos,
        edge_labels=edge_labels,
        font_size=7.5,
        font_weight='bold',
        bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='#BDC3C7', alpha=0.85),
        connectionstyle=f"arc3,rad={rad}",
        ax=ax
    )

    title_desc = "Circuito Fechado (Ciclo)" if is_circuit else "Percurso Ponto a Ponto"
    ax.set_title(f"Topologia do Grafo Ponderado - {title_desc}", fontsize=11, fontweight='bold', pad=12)
    ax.axis('off')
    plt.tight_layout()

    return fig