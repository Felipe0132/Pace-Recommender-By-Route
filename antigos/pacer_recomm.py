import osmnx as ox
import utils as utils
import networkx as nx

def defineSegmentsWithElevation(G, path):
    """
    Segmenta a rota em blocos de ~300m salvando na aresta a distância,
    a inclinação, a subida real e a descida real do trecho consolidado.
    """

    if not path or len(path) < 2:
        return None
    
    firstNode = path[0]
    G_segment = nx.DiGraph()
    dist_acumulada = 0
    coords_trecho = []
    subida = 0
    descida = 0

    for u, v in zip(path[:-1], path[1:]):
        if v not in G[u]:
            continue

        edge = min(G[u][v].values(), key=lambda d: d.get('length', float('inf')))
        dist_acumulada += edge.get('length', 0)

        if 'geometry' in edge:
            coords_trecho.extend([[lat, lng] for lng, lat in edge['geometry'].coords])
        else:
            coords_trecho.append([G.nodes[u]['y'], G.nodes[u]['x']])
            coords_trecho.append([G.nodes[v]['y'], G.nodes[v]['x']])

        # Acumula a elevação de nó em nó do par atual (u, v)
        subidaAux, descidaAux = utils.elevation(G.nodes[u], G.nodes[v])
        subida += subidaAux
        descida += descidaAux
            
        if dist_acumulada >= 300:
            first = G.nodes[firstNode] 
            vNode = G.nodes[v]

            # Diferença líquida entre o início e o fim do bloco para definir a inclinação
            subidaRelevante, descidaRelevante = utils.elevation(first, vNode)
            inclinacao = (subidaRelevante - descidaRelevante) / dist_acumulada * 100

            if inclinacao > 3.9:
                tipo = "Subida"
            elif inclinacao < -3.9:
                tipo = "Descida"
            else:
                tipo = "Plano"

            G_segment.add_edge(
                firstNode,
                v,
                distance=dist_acumulada,
                coords=coords_trecho,
                subida=subida,
                descida=descida,
                inclinacao=inclinacao,
                relevo=tipo
            )

            # Reseta para o próximo bloco de 300m
            firstNode = v
            dist_acumulada = 0
            coords_trecho = []
            subida = 0
            descida = 0

    # Sobra final da rota (< 300m)
    if firstNode != path[-1] and dist_acumulada > 0:
        first = G.nodes[firstNode]
        vNode = G.nodes[path[-1]]
        subidaRelevante, descidaRelevante = utils.elevation(first, vNode)
        inclinacao = (subidaRelevante - descidaRelevante) / dist_acumulada * 100
        tipo = "Subida" if inclinacao > 3.9 else ("Descida" if inclinacao < -3.9 else "Plano")
        
        G_segment.add_edge(
            firstNode,
            path[-1],
            distance=dist_acumulada,
            coords=coords_trecho,
            subida=subida,
            descida=descida,
            inclinacao=inclinacao,
            relevo=tipo
        )

    return G_segment

def groupByRelevo(G, path=None):
    """
    Agrupa arestas consecutivas de mesmo relevo usando a lógica RLE,
    acumulando as distâncias, as coordenadas e capturando o maior grau de inclinação.
    """
    if G is None or G.number_of_edges() == 0:
        return None

    G_groupByRelevo = nx.DiGraph()

    first_node = path[0] if path and len(path) > 0 else list(G.edges())[0][0]

    relevo_atual = None
    dist_acumulado = 0
    coords_acumuladas = []
    inclinacoes_bloco = []

    for u, v, data in G.edges(data=True):
        relevo = data.get('relevo')
        dist = data.get('distance', 0)
        coords = data.get('coords', [])
        inc = data.get('inclinacao', 0)

        if relevo == relevo_atual:
            dist_acumulado += dist
            coords_acumuladas.extend(coords)
            inclinacoes_bloco.append(inc)

        else:
            if relevo_atual is not None:
                maior_inc = max(inclinacoes_bloco, key=abs) if inclinacoes_bloco else 0
                G_groupByRelevo.add_edge(
                    first_node,
                    u, 
                    distance=dist_acumulado, 
                    coords=coords_acumuladas,
                    relevo=relevo_atual,
                    inclinacao=maior_inc
                )
            first_node = u
            relevo_atual = relevo
            dist_acumulado = dist
            coords_acumuladas = list(coords)
            inclinacoes_bloco = [inc]

    if relevo_atual is not None:
        maior_inc = max(inclinacoes_bloco, key=abs) if inclinacoes_bloco else 0
        G_groupByRelevo.add_edge(
            first_node,
            v, 
            distance=dist_acumulado, 
            coords=coords_acumuladas,
            relevo=relevo_atual,
            inclinacao=maior_inc
        )

    return G_groupByRelevo      


def elevationTotalsFromGraph(G_segment):
    """
    Calcula a subida total e a descida total acumuladas a partir dos
    trechos consolidados do grafo, eliminando ruídos de micro-nós.
    """
    if G_segment is None or G_segment.number_of_edges() == 0:
        return 0, 0

    total_ganho = sum(data.get('subida', 0) for _, _, data in G_segment.edges(data=True))
    total_perda = sum(data.get('descida', 0) for _, _, data in G_segment.edges(data=True))

    return total_ganho, total_perda