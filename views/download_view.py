import streamlit as st
import services.route_services as sv


def botao_download_output(df_paces, G_grouped, segments, points, dist, up, down,
                          pace_base_str, tempo_total_str, pace_medio_str):
    """
    Renderiza um único botão que baixa a pasta output/ (.zip) com:
    imagem do gráfico, tabela CSV, grafo .gexf e o relatório output.dat.
    Nada é salvo no disco; o .zip é montado em memória.
    """
    resumo = {
        "Pace base (plano)": pace_base_str,
        "Distância total": f"{dist:.0f} m",
        "Subida total": f"{up:.0f} m",
        "Descida total": f"{down:.0f} m",
        "Blocos de relevo": G_grouped.number_of_edges(),
        "Tempo total previsto": tempo_total_str,
        "Pace médio geral": pace_medio_str,
    }

    zip_bytes = sv.build_output_zip(df_paces, G_grouped, segments, points, resumo)

    st.download_button(
        label="⬇️ Baixar resultados (gráfico, tabela, grafo e relatório)",
        data=zip_bytes,
        file_name="output.zip",
        mime="application/zip",
        type="primary",
        use_container_width=True,
        key="download_results",
    )
