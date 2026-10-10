import utils as utils
import networkx as nx
import utils.utils as utils
import Enums.enum as enum

TRHESHOLD_INC = 3
TRHESHOLD_DIST = 432

def points_to_graph(points):
    """
    Transform list of points in graphs
    300m to 300m of segments, or edge
    """

    if not points or len(points) < 2:
        return None

    firstNode = points[0]
    G = nx.DiGraph()
    dist_acum = 0
    coords_seg = []
    up = 0
    down = 0
    node_idx = 0

    for u, v in zip(points[:-1], points[1:]):

        dist_acum += utils.haversine_distance(u, v)

        coords_seg.append([u['lat'], u['lng']])

        upAux, downAux = utils.elevation(u, v)

        up += upAux
        down += downAux

        if dist_acum >= TRHESHOLD_DIST:
            coords_seg.append([v['lat'], v['lng']])

            first = firstNode
            vNode = v

            upCon, downCon = utils.elevation(first, vNode)

            inc = (upCon - downCon) / dist_acum * 100

            if inc >= TRHESHOLD_INC:
                tipo = enum.TipoRelevo.SUBIDA
            elif inc < -TRHESHOLD_INC:
                tipo = enum.TipoRelevo.DESCIDA
            else:
                tipo = enum.TipoRelevo.PLANO

            # Don't accept dict
            u_id = f"p_{node_idx}"
            v_id = f"p_{node_idx + 1}"

            G.add_edge(
                u_id,
                v_id,
                distance=dist_acum,
                coords=coords_seg,
                up=up,
                down=down,
                inc=inc,
                relevo=tipo
            )

            firstNode = v
            node_idx += 1
            dist_acum = 0
            coords_seg = []
            up = 0
            down = 0

    if dist_acum > 0 and coords_seg:
        coords_seg.append([points[-1]['lat'], points[-1]['lng']])

        upCon, downCon = utils.elevation(firstNode, points[-1])

        inc = (upCon - downCon) / dist_acum * 100 if dist_acum > 0 else 0

        tipo = enum.TipoRelevo.SUBIDA if inc >= TRHESHOLD_INC else (enum.TipoRelevo.DESCIDA if inc < -TRHESHOLD_INC else enum.TipoRelevo.PLANO)

        u_id = f"p_{node_idx}"
        v_id = f"p_{node_idx + 1}"

        G.add_edge(
            u_id,
            v_id,
            distance=dist_acum,
            coords=coords_seg,
            up=up,
            down=down,
            inc=inc,
            relevo=tipo
        )

    return G

def groupByRelevo(G):
    # Group egdes to same relevo in sequence, do a super edge
    # That Node is extremes of conjunt relevos equals

    if G is None or G.number_of_edges() == 0:
        return None

    G_grouped = nx.DiGraph()

    firstNode = None
    relevo_atual = None
    dist_acum = 0
    coords_seg = []
    up_acum = 0
    down_acum = 0
    inc_seg = []

    for u, v, data in G.edges(data=True):
        relevo = data.get('relevo')
        dist = data.get('distance', 0)
        coords = data.get('coords', [])
        up = data.get('up', 0)
        down = data.get('down', 0)
        inc = data.get('inc', 0)

        if firstNode is None:
            firstNode = u
            relevo_atual = relevo

        if relevo == relevo_atual:
            dist_acum += dist
            coords_seg.extend(coords)
            up_acum += up
            down_acum += down
            inc_seg.append(inc)
        else:
            heigthest = max(inc_seg, key=abs) if inc_seg else 0

            G_grouped.add_edge(
                firstNode,
                u,
                distance=dist_acum,
                coords=coords_seg,
                relevo=relevo_atual,
                up=up_acum,
                down=down_acum,
                inc=heigthest,
                color=enum.ColorByRelevo[relevo_atual.name].value
            )
            firstNode = u
            relevo_atual = relevo
            dist_acum = dist
            coords_seg = list(coords)
            up_acum = up
            down_acum = down
            inc_seg = [inc]

    if relevo_atual is not None and firstNode is not None:
        heigthest = max(inc_seg, key=abs) if inc_seg else 0

        G_grouped.add_edge(
            firstNode,
            v, 
            distance=dist_acum, 
            coords=coords_seg,
            relevo=relevo_atual,
            up=up_acum,
            down=down_acum,
            inc=heigthest,
            color=enum.ColorByRelevo[relevo_atual.name].value
        )

    return G_grouped