import streamlit as st
from streamlit_geolocation import streamlit_geolocation
import folium
from streamlit_folium import st_folium
import osmnx as ox
import networkx as nx
import matplotlib.pyplot as plt
from dijkstra import dijkstra
import pacer_recomm as pc
import utils as utils
import parsers 
import renders

ox.settings.elevation_url_template = "https://api.opentopodata.org/v1/aster30m?locations={locations}"

def inicializar_estado():
    """Inicializa todas as variáveis de sessão do Streamlit"""
    variaveis = {
        'pontos': [],
        'rotas': [],
        'distancias': [],
        'elevacoes': [],
        'full_path': None,
        'total_ganhos': 0,
        'total_percas': 0,
        'graphPonder': None,
        'legs_paths': [],
        'G': None,
        'mostrar_calculo': False
    }
    for chave, valor_padrao in variaveis.items():
        if chave not in st.session_state:
            st.session_state[chave] = valor_padrao

inicializar_estado()

pontos     = st.session_state.pontos
rotas      = st.session_state.rotas
distancias = st.session_state.distancias
elevacoes  = st.session_state.elevacoes
legs_paths = st.session_state.legs_paths
G          = st.session_state.G

modo = st.radio("Escolha a forma da rota:", ["Selecionar", "Upload"], horizontal=True)

if modo == "Upload":
    file = st.file_uploader("Faça upload do arquivo .gpx", type=["gpx"])

    if file is not None and st.session_state.G is None:
        with st.spinner("⏳ Processando GPX e baixando malha viária/relevo..."):
            import gpxpy
            gpx = gpxpy.parse(file)
            p0 = gpx.tracks[0].segments[0].points[0]

            G = ox.graph_from_point([p0.latitude, p0.longitude], dist=2500, network_type='walk')
            G = ox.elevation.add_node_elevations_google(G, batch_size=80, pause=1.1)
            st.session_state.G = G

            file.seek(0)
            full_path = parsers.extract_gpx_map(file, G)
            st.session_state.full_path = full_path
            st.session_state.rotas = [parsers.extract_from_dijk(G, full_path)]
            st.session_state.pontos = [{'lat': G.nodes[full_path[0]]['y'], 'lng': G.nodes[full_path[0]]['x']}]
            st.rerun()

else:
    localizacao = streamlit_geolocation()

    if localizacao and localizacao.get('latitude') and localizacao.get('longitude'):
        lat = localizacao['latitude']
        lon = localizacao['longitude']

        start = utils.setStart(lat, lon, pontos)

        if len(pontos) == 0:
            st.info("📍 **Passo 1:** Clique no mapa para marcar o **ponto de partida** do seu percurso.")
        elif len(pontos) == 1:
            st.success("🏁 Ponto de partida definido! Clique no próximo ponto para traçar a rota.")

        m = renders.render_map_main(start, pontos, rotas)

        if distancias:
            col1, col2, col3 = st.columns(3)
            col1.metric("Distância total", f"{sum(distancias):.0f} m")
            col2.metric("↑ Subida total", f"{st.session_state.total_ganhos:.0f} m")
            col3.metric("↓ Descida total", f"{st.session_state.total_percas:.0f} m")

            if st.button("↩ Desfazer último ponto"):
                st.session_state.mostrar_calculo = False
                if pontos:
                    pontos.pop()
                    if rotas: rotas.pop()
                    if distancias: distancias.pop()
                    if elevacoes: elevacoes.pop()
                
                    if legs_paths:
                        legs_paths.pop()
                        full_path = parsers.group_by_path(legs_paths)
                        st.session_state.full_path = full_path if legs_paths else None
                    
                        if full_path and st.session_state.G is not None:
                            st.session_state.graphPonder = pc.defineSegmentsWithElevation(st.session_state.G, full_path) # Only to refresh won and less
                            g_total, p_total = pc.elevationTotalsFromGraph(st.session_state.graphPonder)
                            st.session_state.total_ganhos = g_total
                            st.session_state.total_percas = p_total
                        else:
                            st.session_state.total_ganhos = 0
                            st.session_state.total_percas = 0
                    else:
                        st.session_state.total_ganhos = 0
                        st.session_state.total_percas = 0

                    if len(pontos) == 0:
                        st.session_state.G = None

                    st.rerun()

        col_btn2, col_btn3 = st.columns(2)

        with col_btn2:
            if len(pontos) > 0 and st.button("🗑️ Reiniciar percurso"):
                st.session_state.pontos = []
                st.session_state.rotas = []
                st.session_state.distancias = []
                st.session_state.elevacoes = []
                st.session_state.legs_paths = []
                st.session_state.full_path = None
                st.session_state.total_ganhos = 0
                st.session_state.total_percas = 0
                st.session_state.G = None
                st.session_state.mostrar_calculo = False
                st.rerun()

        output = st_folium(m, width=700, height=500, key="mapa_principal")

        if output and output.get('last_clicked'):
            clicked_point = output['last_clicked']

            if not pontos or pontos[-1] != clicked_point:
                pontos.append(clicked_point)
                st.session_state.mostrar_calculo = False

                if len(pontos) == 1: # Firts click
                    with st.spinner("⏳ Baixando malha viária e altimetria (raio de 2000m da largada)..."):
                        st.session_state.G = ox.graph_from_point(
                            [clicked_point['lat'], clicked_point['lng']], 
                            dist=2000, 
                            network_type='walk'
                        )
                        st.session_state.G = ox.elevation.add_node_elevations_google(
                            st.session_state.G,
                            batch_size=80,
                            pause=1.1
                        )
                    st.rerun()

                elif len(pontos) > 1 and st.session_state.G is not None:
                    G_atual = st.session_state.G
                    point_near_first = ox.distance.nearest_nodes(G_atual, X=pontos[-2]['lng'], Y=pontos[-2]['lat'])
                    point_near_last  = ox.distance.nearest_nodes(G_atual, X=pontos[-1]['lng'], Y=pontos[-1]['lat'])

                    path, distancia = dijkstra(G_atual, point_near_first, point_near_last)

                    if path and len(path) > 1:
                        coords = parsers.extract_from_dijk(G_atual, path)

                        if coords:
                            rotas.append(coords)         
                            distancias.append(distancia)  
                            legs_paths.append(path)

                            full_path = parsers.group_by_path(legs_paths)
                            st.session_state.full_path = full_path
                    else:
                        pontos.pop()
                        st.warning("⚠️ Não foi possível encontrar uma rota a pé até esse ponto. Tente clicar mais próximo de uma via conectada.")

                    st.rerun()
    else:
        st.info("Aguardando a obtenção da geolocalização pelo navegador...")


if st.session_state.full_path is not None and len(st.session_state.full_path) > 1:
    if st.button("Calcular"):
        st.session_state.graphPonder = pc.defineSegmentsWithElevation(st.session_state.G, st.session_state.full_path)

        g_total, p_total = pc.elevationTotalsFromGraph(st.session_state.graphPonder)
        st.session_state.total_ganhos = g_total
        st.session_state.total_percas = p_total
        
        st.session_state.mostrar_calculo = True
        st.rerun()

    if st.session_state.mostrar_calculo and st.session_state.graphPonder is not None:
        # Agrupa pelo relevo e mostra o 2º mapa
        G_agrupado = pc.groupByRelevo(st.session_state.graphPonder)

        if G_agrupado is not None:
            st.divider()
            st.subheader("Mapa Consolidado (groupByRelevo)")

            no_inicial = st.session_state.full_path[0]
            start_coord = [
                st.session_state.G.nodes[no_inicial]['y'], 
                st.session_state.G.nodes[no_inicial]['x']
            ]

            m_calc = renders.render_map_groupBy(start_coord, G_agrupado, st.session_state.G)

            st_folium(m_calc, width=700, height=450, key="mapa_agrupado")
