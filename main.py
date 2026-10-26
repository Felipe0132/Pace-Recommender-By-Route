import streamlit as st
import services.route_services as sv
import views.chart_view as chvi
from streamlit_folium import st_folium
import pandas as pd
import Enums.enum as enums
import json
from networkx.readwrite import json_graph
import utils.utils as utils
from datetime import time
import models.pace_reccom as pr

m = None
segments = None

st.title("Recomendador de Pace referente a parametros de relevancia antes nao calculados")

st.markdown(
    """
    <div style="background: rgba(255, 255, 255, 0.05); padding: 14px 18px; border-radius: 10px; border: 1px solid rgba(255, 255, 255, 0.12); margin-bottom: 15px;">
        <span style="font-size: 15px; font-weight: 600;">⏱️ Pace Base de Referência (no Plano):</span>
        <span style="color: #4CAF50; font-size: 18px; font-weight: 700; margin-left: 8px;">min / km</span>
        <div style="font-size: 12px; color: #888; margin-top: 2px;">Defina os minutos e segundos do seu ritmo alvo em terreno plano</div>
    </div>
    """,
    unsafe_allow_html=True
)

col_min, col_seg = st.columns(2)
with col_min:
    minutos = st.number_input("Minutos (min)", min_value=2, max_value=15, value=5, step=1)
with col_seg:
    segundos = st.number_input("Segundos (seg)", min_value=0, max_value=59, value=30, step=1)

total_segundos = minutos * 60 + segundos
st.caption(f"🏁 Ritmo Selecionado: **{minutos:02d}:{segundos:02d} min/km** ({total_segundos}s)")

st.info(
    """
    ℹ️ **Como funciona o cálculo de ritmo?**
    * **Pace de Referência:** O valor definido acima é o seu ritmo alvo para **terreno plano (0% de inclinação)**.
    * **Esforço Fisiológico Constante (Minetti et al., 2002 / GAP):** O algoritmo calcula o custo metabólico real de cada inclinação para que seu esforço cardiovascular permaneça constante ao longo de toda a rota.
    * **🔺 Subidas:** O ritmo é dosado proporcionalmente à inclinação para poupar energia e evitar a fadiga por acúmulo de lactato.
    * **🔻 Descidas:** O ritmo acelera com controle biomecânico (trava de segurança em declives acentuados) para amortecimento e proteção articular contra impacto excessivo.
    * **➖ Trechos Planos:** Aplica aquecimento gradual no primeiro trecho (+5%) e aceleração progressiva tática ao longo da prova.
    """
)

mode = st.radio("Passagem da Rota:", ['Manual', "GPX"], horizontal=True)

if mode == "GPX":
    file_gpx = st.file_uploader("Faca Upload de um arquivo .GPX", type=["gpx"])

    if not file_gpx:
        # Se o usuário remover o arquivo, limpa o estado
        st.session_state.pop("calculado", None)
        st.info("📂 Envie um arquivo .GPX acima para habilitar o cálculo.")
        st.stop()

    # Botões de Ação lado a lado com visual moderno
    col_btn1, col_btn2 = st.columns([2, 1])
    with col_btn1:
        if st.button("🚀 Confirmar Pace e Calcular", type="primary", use_container_width=True):
            st.session_state["calculado"] = True
    with col_btn2:
        if st.session_state.get("calculado", False):
            if st.button("🔄 Recalcular", use_container_width=True):
                st.session_state["calculado"] = True
                st.rerun()

    if not st.session_state.get("calculado", False):
        st.warning("⚠️ Rota carregada! Ajuste o seu ritmo desejado no seletor acima e clique em **'Confirmar Pace e Calcular'**.")
        st.stop()

    G_segment, G_grouped, segments, dist, up, down = sv.process_gpx_route(file_gpx)

    st.success(f"Rota processada com sucesso! Segmentos: {G_segment.number_of_edges()} | Blocos de relevo: {G_grouped.number_of_edges()}")

    m = chvi.plot_map_grouped(G_grouped)

    col1, col2, col3 = st.columns(3)
    col1.metric("Distância total", f"{dist:.0f} m")
    col2.metric("↑ Subida total", f"{up:.0f} m")
    col3.metric("↓ Descida total", f"{down:.0f} m")

if segments:
    paces_by_segment = pr.define_paces_by_segment(segments, total_segundos)

    df_paces, tempo_total_str, pace_medio_str = utils.paces_to_dataframe(segments, paces_by_segment, total_segundos)
    st.subheader("Ritmo Recomendado por Segmento")
    col_t1, col_t2 = st.columns(2)
    col_t1.metric("Tempo Total Previsto", tempo_total_str)
    col_t2.metric("Pace Médio Geral", pace_medio_str)
    st.dataframe(df_paces, use_container_width=True, hide_index=True)

if m:
    st_folium(m, width=800, height=500)

    if segments:
        st.subheader("Detalhe por segmento")

        table_sheet = []
        for i, seg in enumerate(segments, start=1):
            relevo = seg.get('relevo')

            if relevo == enums.TipoRelevo.SUBIDA:
                icone = "🔺 Subida"
            elif relevo == enums.TipoRelevo.DESCIDA:
                icone = "🔻 Descida"
            else:
                icone = "➖ Plano"

            table_sheet.append({
                "Trecho": f"Segmento #{i}",
                "Relevo": icone,
                "Distância": f"{seg.get('dist', 0):.0f} m",
                "Inclinação Média": f"{seg.get('inc', 0):+.1f}%"
            })

        df = pd.DataFrame(table_sheet)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Plota o grafo topológico diretamente no frontend com nós, pesos e cores
        st.subheader("Topologia do Grafo Ponderado")
        fig_grafo = chvi.plot_graph_topology(G_grouped)
        if fig_grafo:
            st.pyplot(fig_grafo)

        # Exporta o grafo formatado com propriedades visuais para o Gephi (.gexf)
        gephi_path = sv.export_to_gephi(G_grouped, "grafo_gephi.gexf")
        with open(gephi_path, "r", encoding="utf-8") as f:
            st.download_button(
                label="📥 Baixar Grafo Pré-Configurado para o Gephi (.gexf)",
                data=f.read(),
                file_name="grafo_gephi.gexf",
                mime="application/xml"
            )
