import streamlit as st
import os
import services.route_services as sv
import views.chart_view as chvi
import views.download_view as dwv
from streamlit_folium import st_folium
import pandas as pd
import Enums.enum as enums
import json
from networkx.readwrite import json_graph
import utils.utils as utils
from datetime import time, timedelta
import models.pace_reccom as pr

m = None
segments = None


def _clamp_pace_time():
    """Keep the editable mm:ss pace selector within supported bounds."""
    selected = st.session_state.get("pace_input")
    if selected is None:
        return

    total_seconds = selected.hour * 3600 + selected.minute * 60 + selected.second
    total_seconds = max(120, min(959, total_seconds))
    st.session_state["pace_input"] = time(0, total_seconds // 60, total_seconds % 60)


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "in")
OUTPUT_DIR = os.path.join(BASE_DIR, "out")
IMAGE_OUTPUT_DIR = os.path.join(OUTPUT_DIR, "imagens")
os.makedirs(IMAGE_OUTPUT_DIR, exist_ok=True)

st.set_page_config(page_title="Recomendador de Pace", page_icon="🏃", layout="wide")
st.markdown(
    """
    <style>
        .block-container { max-width: 1280px; padding-top: 1.6rem; padding-bottom: 2.5rem; }
        div[data-testid="stExpander"] { border: 1px solid #DCE5E0; border-radius: 12px; background: #FFFFFF; }
        div[data-testid="stVerticalBlockBorderWrapper"] { border: 1px solid #EDF1EE; border-radius: 12px; background: #FFFFFF; padding: 0.45rem !important; }
        [data-testid="stMetric"] { height: 114px; box-sizing: border-box; background: #FFFFFF; border: 1px solid #E3EAE6; padding: 0.8rem 1rem; border-radius: 12px; }
        .pace-metric { height: 114px; box-sizing: border-box; display: flex; flex-direction: column; justify-content: center; padding: 0.8rem 1rem; border: 1px solid #E3EAE6; border-radius: 12px; background: #FFFFFF; }
        .pace-metric-label { color: #68756E; font-size: 0.875rem; margin-bottom: 0.35rem; }
        .pace-metric-value { color: #24312B; font-size: 1.25rem; font-weight: 600; line-height: 1.2; white-space: nowrap; }
        .feedback-link { display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.7rem 1rem; color: #FFFFFF !important; background: #0B704F; border: 1px solid #0B704F; border-radius: 10px; font-weight: 650; text-decoration: none !important; box-shadow: 0 2px 7px rgba(11, 112, 79, 0.20); transition: background 120ms ease, border-color 120ms ease; }
        .feedback-link:hover { color: #FFFFFF !important; background: #095C41; border-color: #095C41; }
        [data-testid="stDownloadButton"] button[kind="primary"], .st-key-download_results button { background: #175CD3 !important; border-color: #175CD3 !important; color: #FFFFFF !important; font-weight: 650 !important; box-shadow: 0 2px 7px rgba(23, 92, 211, 0.22); }
        [data-testid="stDownloadButton"] button[kind="primary"]:hover, .st-key-download_results button:hover { background: #1849A9 !important; border-color: #1849A9 !important; }
        .pace-preview { min-height: 74px; box-sizing: border-box; display: flex; flex-direction: column; justify-content: center; padding: 0.65rem 0.85rem; border: 1px solid #D7E8DE; border-radius: 10px; background: #F2F8F4; }
        .pace-preview-label { color: #68756E; font-size: 0.78rem; }
        .pace-preview-value { color: #0B704F; font-size: 1.2rem; font-weight: 700; white-space: nowrap; }
        h1, h2, h3 { letter-spacing: -0.02em; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🏃 Recomendador de Pace")
st.caption("Seu plano de ritmo, ajustado ao relevo da rota.")

with st.expander("🔎 Sobre o recomendador e como o cálculo funciona", expanded=False):
    st.markdown(
        """
        O ritmo informado abaixo representa seu alvo em terreno plano. O cálculo ajusta o pace por trecho para manter um esforço fisiológico mais constante ao longo da rota.

        - **Subidas:** o ritmo diminui conforme a inclinação; morros mais longos ou íngremes podem exigir uma redução maior para manter o esforço confortável.
        - **Descidas:** o ritmo pode aumentar, com controle em declives acentuados para reduzir o impacto.
        - **Trechos planos:** o primeiro usa o ritmo base; os seguintes podem acelerar progressivamente, com limite de 5%.

        O modelo considera o custo energético da inclinação (Minetti et al., 2002 / GAP).
        """
    )

st.markdown(
    '<a class="feedback-link" href="https://forms.gle/PtV5PbgrqhwXLBzz9" target="_blank" rel="noopener noreferrer">📝 Avalie o recomendador <span aria-hidden="true">↗</span></a>',
    unsafe_allow_html=True,
)

with st.container(border=True):
    st.markdown("### ⏱️ Pace base no plano")
    st.caption("Use um pace um pouco mais lento que sua média alvo. Nas subidas, o ajuste varia conforme a inclinação; nos planos, o ritmo pode progredir gradualmente.")
    col_input, col_preview = st.columns([1.4, 1])
    with col_input:
        pace_selecionado = st.time_input(
            "Pace base (00:mm:ss)",
            value=time(0, 5, 30),
            step=timedelta(seconds=1),
            key="pace_input",
            on_change=_clamp_pace_time,
            help="Use 00 para horas e ajuste os campos de minutos e segundos juntos. Ao passar de 00 ou 59 segundos, os minutos acompanham automaticamente.",
        )
    minutos = pace_selecionado.hour * 60 + pace_selecionado.minute
    segundos = pace_selecionado.second
    with col_preview:
        st.markdown(
            f'<div class="pace-preview"><span class="pace-preview-label">Pace selecionado</span>'
            f'<span class="pace-preview-value">{minutos:02d}:{segundos:02d} min/km</span></div>',
            unsafe_allow_html=True,
        )

total_segundos = minutos * 60 + segundos

#mode = st.radio("Passagem da Rota:", ['Manual', "GPX"], horizontal=True)
mode = "GPX"

if mode == "GPX":
    origem = st.radio(
        "Origem da rota:",
        ["Enviar meu arquivo .GPX", "Testar com trajeto de exemplo (Viveza)"],
        horizontal=True
    )

    # Ao trocar de origem, limpa o cálculo anterior
    if st.session_state.get("origem_rota") != origem:
        st.session_state["origem_rota"] = origem
        st.session_state.pop("calculado", None)

    if origem == "Testar com trajeto de exemplo (Viveza)":
        file_gpx = os.path.join(INPUT_DIR, "Corrida_Viveza.gpx")
        st.caption("Trajeto de exemplo: circuito de aproximadamente 5 km no bairro Viveza.")
    else:
        file_gpx = st.file_uploader("Faça upload de um arquivo .GPX", type=["gpx"])

    if not file_gpx:
        # Se o usuário remover o arquivo, limpa o estado
        st.session_state.pop("calculado", None)
        st.info("📂 Envie um arquivo .GPX acima para habilitar o cálculo.")
        st.stop()

    # Botões de Ação lado a lado com visual moderno
    col_btn1, col_btn2 = st.columns([2, 1])
    with col_btn1:
        if st.button("Confirmar pace e calcular", type="primary", use_container_width=True):
            st.session_state["calculado"] = True
    with col_btn2:
        if st.session_state.get("calculado", False):
            if st.button("🔄 Recalcular", use_container_width=True):
                st.session_state["calculado"] = True
                st.rerun()

    if not st.session_state.get("calculado", False):
        st.warning("⚠️ Rota carregada! Ajuste o seu ritmo desejado no seletor acima e clique em **'Confirmar Pace e Calcular'**.")
        st.stop()

    G_segment, G_grouped, segments, dist, up, down, points = sv.process_gpx_route(file_gpx)

    st.success("Rota pronta. Confira o resumo e as visualizações abaixo.")

    m = chvi.plot_map_grouped(G_grouped)

if segments:
    paces_by_segment = pr.define_paces_by_segment(segments, total_segundos)

    df_paces, tempo_total_str, pace_medio_str = utils.paces_to_dataframe(segments, paces_by_segment, total_segundos)
    st.subheader("Resumo da rota")
    col_dist, col_up, col_down, col_time, col_pace = st.columns(5)
    col_dist.metric("Distância", f"{dist:.0f} m")
    col_up.metric("Subida", f"↑ {up:.0f} m")
    col_down.metric("Descida", f"↓ {down:.0f} m")
    col_time.metric("Tempo previsto", tempo_total_str)
    with col_pace:
        st.markdown(
            f'<div class="pace-metric"><div class="pace-metric-label">Pace médio</div>'
            f'<div class="pace-metric-value">{pace_medio_str}</div></div>',
            unsafe_allow_html=True,
        )
    st.subheader("📋 Ritmos recomendados por trecho")
    with st.container(border=True):
        st.dataframe(df_paces, use_container_width=True, hide_index=True)

if m:
    col_map, col_charts = st.columns([1, 1], gap="medium")
    with col_map:
        with st.container(border=True):
            st.subheader("🗺️ Percurso")
            st_folium(m, width=500, height=410)

    with col_charts:
        with st.container(border=True):
            tab_pace, tab_topologia, tab_segmentos = st.tabs(
                ["📈 Pace e altimetria", "🕸️ Grafo", "📋 Segmentos"]
            )
            with tab_pace:
                st.caption("Passe o mouse nos trechos para consultar os detalhes.")
                chart_interativo = chvi.plot_esforco_relevo_interativo(points, segments, dist)
                if chart_interativo is not None:
                    st.altair_chart(chart_interativo, use_container_width=False)
            with tab_topologia:
                st.caption("Rede de segmentos e conexões do percurso.")
                fig_grafo = chvi.plot_graph_topology(G_grouped, segments)
                if fig_grafo:
                    st.pyplot(fig_grafo, use_container_width=True)
            with tab_segmentos:
                st.caption("Distância, inclinação e ajuste de ritmo em cada trecho.")
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
                        "Inclinação Média": f"{seg.get('inc', 0):+.1f}%",
                        "Ajuste / Esforço": f"{seg.get('esforco_extra_pct', 0.0):+.1f}%"
                    })

                df_segmentos = pd.DataFrame(table_sheet)
                st.dataframe(df_segmentos, use_container_width=True, hide_index=True)

    if segments:
        # Botão único: baixa a pasta output/ (gráfico, tabela CSV, grafo .gexf e output.dat)
        dwv.botao_download_output(
            df_paces, G_grouped, segments, points, dist, up, down,
            f"{minutos:02d}:{segundos:02d} min/km", tempo_total_str, pace_medio_str
        )
