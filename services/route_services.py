import collectors.gpx_collector as gpx_collector
import core.graph_builder as graph_builder
import utils.utils as utils

def process_gpx_route(file_gpx):
    """
    Process the GPX into function, in main or another method
    Here request only file_gpx and return graph ponder
    """

    points = gpx_collector.extract_points_gpx(file_gpx)
    total_dist = sum(
        utils.haversine_distance(p1, p2) 
        for p1, p2 in zip(points[:-1], points[1:])
    )
    lim20per = total_dist * 0.20

    G_segment = graph_builder.points_to_graph(points)
    G_grouped = graph_builder.groupByRelevo(G_segment, max_dist=lim20per)
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

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 6:
        return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
    return (52, 152, 219)

def export_to_gephi(G, filename="grafo_gephi.gexf"):
    """
    Exporta o grafo no formato GEXF oficial com extensão VIZ (visual).
    Ao abrir no Gephi, o arquivo já vem com:
      - Cores das arestas e dos nós pré-configuradas (Vermelho/Rosa = Subida, Verde = Descida, Azul = Plano)
      - Posições (X, Y) calculadas em layout linear ordenado da corrida
      - Rótulos explicativos nas arestas e nós (Largada, Chegada, Subida 800m, etc.)
      - Espessura das arestas ponderada pela inclinação e distância
      - Atributos completos de relevo, distância, subida e descida
    """
    import xml.etree.ElementTree as ET

    # Registra o prefixo 'viz' para o namespace visual do GEXF
    viz_ns = "http://www.gexf.net/1.1draft/viz"
    ET.register_namespace("viz", viz_ns)

    # Nota: Não declarar 'xmlns:viz' manualmente aqui, pois ET.register_namespace já gera automaticamente sem duplicar
    root = ET.Element("gexf", {
        "xmlns": "http://www.gexf.net/1.2draft",
        "version": "1.2"
    })
    
    graph_elem = ET.SubElement(root, "graph", {
        "defaultedgetype": "directed",
        "mode": "static"
    })

    # Atributos de dados das arestas
    edge_attrs = ET.SubElement(graph_elem, "attributes", {"class": "edge", "mode": "static"})
    ET.SubElement(edge_attrs, "attribute", {"id": "0", "title": "relevo", "type": "string"})
    ET.SubElement(edge_attrs, "attribute", {"id": "1", "title": "distancia_m", "type": "float"})
    ET.SubElement(edge_attrs, "attribute", {"id": "2", "title": "inclinacao_pct", "type": "float"})
    ET.SubElement(edge_attrs, "attribute", {"id": "3", "title": "subida_m", "type": "float"})
    ET.SubElement(edge_attrs, "attribute", {"id": "4", "title": "descida_m", "type": "float"})

    nodes_elem = ET.SubElement(graph_elem, "nodes")
    edges_elem = ET.SubElement(graph_elem, "edges")

    # Identificar nós ordenados e mapear posições visuais
    ordered_nodes = []
    edges_list = list(G.edges(data=True))
    if edges_list:
        ordered_nodes.append(edges_list[0][0])
        for _, v, _ in edges_list:
            if v not in ordered_nodes:
                ordered_nodes.append(v)
    else:
        ordered_nodes = list(G.nodes())

    total_nodes = len(ordered_nodes)

    # Detecta se a rota é um circuito (se o último nó fecha no primeiro ou estão próximos)
    is_circuit = False
    if edges_list and len(edges_list) >= 3:
        first_node = ordered_nodes[0]
        last_target = edges_list[-1][1]
        if first_node == last_target:
            is_circuit = True
        else:
            # Checa se as coordenadas geográficas do primeiro e último ponto são muito próximas (< 150m)
            p1 = edges_list[0][2].get('coords', [[]])[0]
            p2 = edges_list[-1][2].get('coords', [[]])[-1]
            if p1 and p2 and len(p1) >= 2 and len(p2) >= 2:
                import utils.utils as u_utils
                d = u_utils.haversine_distance({'lat': p1[0], 'lng': p1[1]}, {'lat': p2[0], 'lng': p2[1]})
                if d <= 250.0:
                    is_circuit = True

    import math

    # Raio do círculo caso seja circuito, ou espaçamento linear caso seja ponto-a-ponto
    radius = max(200.0, total_nodes * 45.0)
    spacing_x = 220.0

    # Cria nós com coordenadas visuais (x, y), tamanho e cor
    for idx, node_id in enumerate(ordered_nodes):
        if idx == 0:
            node_label = f"Largada ({node_id})"
            node_color = (46, 204, 113)  # Verde esmeralda para largada
            node_size = 24.0
        elif idx == total_nodes - 1 and not is_circuit:
            node_label = f"Chegada ({node_id})"
            node_color = (231, 76, 60)   # Vermelho para chegada
            node_size = 24.0
        else:
            node_label = f"Ponto {node_id}"
            node_color = (52, 73, 94)    # Neutro para nós intermediários
            node_size = 15.0

        n_tag = ET.SubElement(nodes_elem, "node", {
            "id": str(node_id),
            "label": node_label
        })
        
        # Se for circuito, organiza em círculo no sentido horário; se for reta, organiza em linha
        if is_circuit:
            # Ângulo começando do topo (-pi/2) e girando no sentido horário
            angle = -math.pi / 2 + (2 * math.pi * idx / total_nodes)
            pos_x = radius * math.cos(angle)
            pos_y = -radius * math.sin(angle)
        else:
            pos_x = idx * spacing_x
            pos_y = 0.0

        ET.SubElement(n_tag, f"{{{viz_ns}}}position", {
            "x": f"{pos_x:.1f}",
            "y": f"{pos_y:.1f}",
            "z": "0.0"
        })
        ET.SubElement(n_tag, f"{{{viz_ns}}}size", {"value": str(node_size)})
        ET.SubElement(n_tag, f"{{{viz_ns}}}color", {
            "r": str(node_color[0]),
            "g": str(node_color[1]),
            "b": str(node_color[2])
        })

    # Adiciona arestas com cores, rótulos formatados e atributos
    for edge_idx, (u, v, data) in enumerate(edges_list):
        relevo = data.get('relevo', '')
        relevo_str = relevo.value if hasattr(relevo, 'value') else str(relevo)
        dist = float(data.get('distance', 0))
        inc = float(data.get('inc', 0))
        up = float(data.get('up', 0))
        down = float(data.get('down', 0))
        hex_color = data.get('color', '#3498DB')

        rgb = hex_to_rgb(hex_color)

        # Rótulo que aparece diretamente sobre a aresta no Gephi
        edge_label = f"{relevo_str} | {dist:.0f}m ({inc:+.1f}%)"
        
        # Espessura visual proporcional ao impacto do trecho
        edge_weight = max(2.0, min(10.0, 2.0 + abs(inc)))

        e_tag = ET.SubElement(edges_elem, "edge", {
            "id": str(edge_idx),
            "source": str(u),
            "target": str(v),
            "label": edge_label,
            "weight": f"{edge_weight:.1f}"
        })

        # Cor visual da aresta (ex: Vermelho para subida, Azul/Verde para plano/descida)
        ET.SubElement(e_tag, f"{{{viz_ns}}}color", {
            "r": str(rgb[0]),
            "g": str(rgb[1]),
            "b": str(rgb[2])
        })

        # Atributos de dados
        attvalues = ET.SubElement(e_tag, "attvalues")
        ET.SubElement(attvalues, "attvalue", {"for": "0", "value": relevo_str})
        ET.SubElement(attvalues, "attvalue", {"for": "1", "value": f"{dist:.1f}"})
        ET.SubElement(attvalues, "attvalue", {"for": "2", "value": f"{inc:.2f}"})
        ET.SubElement(attvalues, "attvalue", {"for": "3", "value": f"{up:.1f}"})
        ET.SubElement(attvalues, "attvalue", {"for": "4", "value": f"{down:.1f}"})

    tree = ET.ElementTree(root)
    tree.write(filename, encoding="utf-8", xml_declaration=True)
    return filename