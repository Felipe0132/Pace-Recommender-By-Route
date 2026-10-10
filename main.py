import streamlit as st
import services.route_services as sv
import views.chart_view as chvi
from streamlit_folium import st_folium
import pandas as pd
import Enums.enum as enums

m = None

st.title("Recomendador de Pace referente a parametros de relevancia antes nao calculados")

mode = st.radio("Passagem da Rota:", ['Manual', "GPX"], horizontal=True)

if mode == "GPX":
    file_gpx = st.file_uploader("Faca Upload de um arquivo .GPX", type=["gpx"])

    if file_gpx:
        G_segment, G_grouped, segments, dist, up, down = sv.process_gpx_route(file_gpx)

        st.success(f"Rota processada com sucesso! Segmentos: {G_segment.number_of_edges()} | Blocos de relevo: {G_grouped.number_of_edges()}")

        m = chvi.plot_map_grouped(G_grouped)

        col1, col2, col3 = st.columns(3)
        col1.metric("Distância total", f"{dist:.0f} m")
        col2.metric("↑ Subida total", f"{up:.0f} m")
        col3.metric("↓ Descida total", f"{down:.0f} m")


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