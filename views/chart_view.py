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

def plot_graph_topology(G_grouped, segments=None):
    """
    Plota no frontend o grafo direcionado com os pesos (distância, inclinação, esforço),
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
        figsize = (6.5, 5.5)
    else:
        for idx, node in enumerate(ordered_nodes):
            pos[node] = (idx * 1.5, 0.0)
        figsize = (min(12, max(7, total_nodes * 1.05)), 2.8)

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

    for idx_aresta, (u, v, data) in enumerate(edges_list):
        cor = data.get('color', '#3498DB')
        inc = float(data.get('inc', 0))
        dist = float(data.get('distance', 0))
        relevo = data.get('relevo', '')
        relevo_str = relevo.value if hasattr(relevo, 'value') else str(relevo)

        edge_colors.append(cor)
        # Espessura proporcional ao impacto da inclinação
        edge_widths.append(max(2.5, min(6.0, 2.5 + abs(inc) * 0.4)))

        # Rótulo em cima de cada aresta com relevo, inclinação, distância e esforço
        # (as arestas e os segments estão na mesma ordem)
        rotulo = f"{relevo_str}  |  {inc:+.1f}%  |  {dist:.0f}m"
        if segments and idx_aresta < len(segments):
            esforco = segments[idx_aresta].get('esforco_extra_pct')
            if esforco is not None:
                rotulo += f"  |  Esforço {esforco:+.1f}%"
        edge_labels[(u, v)] = rotulo

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
        font_size=6.5,
        font_weight='bold',
        bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='#BDC3C7', alpha=0.85),
        connectionstyle=f"arc3,rad={rad}",
        ax=ax
    )

    title_desc = "Circuito Fechado (Ciclo)" if is_circuit else "Percurso Ponto a Ponto"

    # Resumo do percurso inteiro: distância total e ganhos de elevação
    total_dist = sum(float(d.get('distance', 0)) for _, _, d in edges_list)
    total_up = sum(float(d.get('up', 0)) for _, _, d in edges_list)
    total_down = sum(float(d.get('down', 0)) for _, _, d in edges_list)
    resumo = (
        f"Distância total: {total_dist / 1000:.2f} km  |  "
        f"Ganho de elevação: +{total_up:.0f} m  |  "
        f"Perda de elevação: -{total_down:.0f} m"
    )

    ax.set_title(f"Topologia do Grafo Ponderado - {title_desc}", fontsize=11, fontweight='bold', pad=30)
    ax.text(
        0.5, 1.02, resumo,
        transform=ax.transAxes,
        ha='center', va='bottom',
        fontsize=8.5,
        bbox=dict(boxstyle='round,pad=0.35', facecolor='#F4F6F7', edgecolor='#BDC3C7')
    )
    ax.axis('off')
    plt.tight_layout()

    return fig

def plot_esforco_relevo_interativo(points, segments, total_dist):
    """
    Versão interativa (Altair, nativo do Streamlit) da curva de pace x relevo/altimetria.
    - Painel superior: % do pace base por segmento, colorido pelo relevo, com tooltip.
    - Painel inferior: perfil altimétrico com faixas coloridas pelo relevo.
    Ambos aceitam zoom/arrastar no eixo X (scroll do mouse e duplo clique para resetar).
    """
    import altair as alt
    import pandas as pd
    import utils.utils as utils

    if not points or not segments:
        return None

    nomes = {
        enum.TipoRelevo.SUBIDA: 'Subida',
        enum.TipoRelevo.DESCIDA: 'Descida',
        enum.TipoRelevo.PLANO: 'Plano'
    }
    escala_cor = alt.Scale(
        domain=['Subida', 'Descida', 'Plano'],
        range=['#E74C3C', '#27AE60', '#2980B9']
    )

    # Dados dos segmentos
    linhas_seg = []
    curr_d = 0.0
    for idx, seg in enumerate(segments, start=1):
        d_seg = seg.get('dist', 0)
        fator = seg.get('fator', 1.0 + seg.get('esforco_extra_pct', 0.0) / 100.0)
        pct = fator * 100.0
        linhas_seg.append({
            'Trecho': f"Segmento #{idx}",
            'Relevo': nomes.get(seg.get('relevo'), 'Plano'),
            'inicio_km': curr_d / 1000.0,
            'fim_km': (curr_d + d_seg) / 1000.0,
            'meio_km': (curr_d + d_seg / 2.0) / 1000.0,
            'Distância (m)': round(d_seg, 0),
            'Inclinação (%)': round(seg.get('inc', 0), 1),
            'Pace (% do base)': round(pct, 1),
            'Variação (%)': round(pct - 100.0, 1),
            'base': 100.0
        })
        curr_d += d_seg
    df_seg = pd.DataFrame(linhas_seg)

    # Dados da altimetria (amostrados para não estourar o limite de linhas do Altair)
    dists_cum = [0.0]
    elevs = [points[0].get('elev', 0) or 0]
    for p1, p2 in zip(points[:-1], points[1:]):
        dists_cum.append(dists_cum[-1] + utils.haversine_distance(p1, p2))
        elevs.append(p2.get('elev', 0) or 0)
    passo = max(1, len(dists_cum) // 1500)
    df_elev = pd.DataFrame({
        'km': [d / 1000.0 for d in dists_cum[::passo]],
        'Altitude (m)': [round(e, 1) for e in elevs[::passo]]
    })

    eixo_x = alt.X('inicio_km:Q', title='Distância da Prova (km)', scale=alt.Scale(domain=[0, total_dist / 1000.0]))
    tooltip_seg = ['Trecho', 'Relevo', 'Distância (m)', 'Inclinação (%)', 'Pace (% do base)', 'Variação (%)']

    pct_min = min(df_seg['Pace (% do base)'].min(), 100.0) - 5
    pct_max = max(df_seg['Pace (% do base)'].max(), 100.0) + 5
    eixo_y_pct = alt.Y('Pace (% do base):Q', title='Pace recomendado (% do base)', scale=alt.Scale(domain=[pct_min, pct_max]))

    base_seg = alt.Chart(df_seg)

    # Faixas de fundo por relevo
    fundo_top = base_seg.mark_rect(opacity=0.10).encode(
        x=eixo_x, x2='fim_km:Q',
        color=alt.Color('Relevo:N', scale=escala_cor, legend=alt.Legend(title='Relevo', orient='top'))
    )
    # Área entre 100% e o pace do trecho
    area_var = base_seg.mark_rect(opacity=0.25).encode(
        x=eixo_x, x2='fim_km:Q',
        y=alt.Y('base:Q', scale=alt.Scale(domain=[pct_min, pct_max])), y2='Pace (% do base):Q',
        color=alt.Color('Relevo:N', scale=escala_cor, legend=None),
        tooltip=tooltip_seg
    )
    # Degrau do pace por segmento
    degraus = base_seg.mark_rule(strokeWidth=4).encode(
        x=eixo_x, x2='fim_km:Q', y=eixo_y_pct,
        color=alt.Color('Relevo:N', scale=escala_cor, legend=None),
        tooltip=tooltip_seg
    )
    pontos = base_seg.mark_circle(size=90, opacity=1, stroke='white', strokeWidth=1.5).encode(
        x='meio_km:Q', y=eixo_y_pct,
        color=alt.Color('Relevo:N', scale=escala_cor, legend=None),
        tooltip=tooltip_seg
    )
    rotulos = base_seg.mark_text(dy=-12, fontSize=11, fontWeight='bold', color='#1C2833').encode(
        x='meio_km:Q', y=eixo_y_pct,
        text=alt.Text('Pace (% do base):Q', format='.1f')
    )
    linha_100 = alt.Chart(pd.DataFrame({'y': [100.0]})).mark_rule(
        strokeDash=[6, 4], color='#34495E', strokeWidth=1.5
    ).encode(y='y:Q')

    grafico_pace = alt.layer(
        fundo_top, area_var, linha_100, degraus, pontos, rotulos
    ).properties(
        width=400,
        height=240,
        title='Pace recomendado (% do pace base) por trecho'
    ).interactive(bind_y=False)

    # Painel inferior: altimetria
    elev_min = df_elev['Altitude (m)'].min()
    elev_max = df_elev['Altitude (m)'].max()
    pad = max((elev_max - elev_min) * 0.15, 5)
    escala_elev = alt.Scale(domain=[elev_min - pad, elev_max + pad])

    fundo_bottom = base_seg.mark_rect(opacity=0.15).encode(
        x=eixo_x, x2='fim_km:Q',
        color=alt.Color('Relevo:N', scale=escala_cor, legend=None),
        tooltip=tooltip_seg
    )
    area_elev = alt.Chart(df_elev).mark_area(
        opacity=0.35, color='#5DADE2', line={'color': '#1A5276', 'strokeWidth': 2}
    ).encode(
        x=alt.X('km:Q', title='Distância da Prova (km)', scale=alt.Scale(domain=[0, total_dist / 1000.0])),
        y=alt.Y('Altitude (m):Q', scale=escala_elev),
        tooltip=[alt.Tooltip('km:Q', format='.2f', title='Km'), 'Altitude (m)']
    )

    grafico_elev = alt.layer(fundo_bottom, area_elev).properties(
        width=400,
        height=150,
        title='Perfil altimétrico'
    ).interactive(bind_y=False)

    return alt.vconcat(grafico_pace, grafico_elev).resolve_scale(color='shared')

def plot_esforco_relevo_km(points, segments, total_dist):
    """
    Gera layout visual profissional (dois subplots empilhados e perfeitamente alinhados):
    - Subplot 1 (Superior): Curva do Pace Recomendado (% do pace base) com linha por cor de relevo,
      divisórias pontilhadas nas trocas de relevo e tags indicativas (Subida, Descida, Plano).
    - Subplot 2 (Inferior): Perfil Altimétrico contínuo com áreas sombreadas pelas cores dos relevos.
    """
    import numpy as np
    import utils.utils as utils

    # 1. Altimetria contínua
    dists_cum = [0.0]
    elevs = [points[0].get('elev', 0)]
    for p1, p2 in zip(points[:-1], points[1:]):
        d = utils.haversine_distance(p1, p2)
        dists_cum.append(dists_cum[-1] + d)
        elevs.append(p2.get('elev', 0))

    dists_km = [d / 1000.0 for d in dists_cum]
    total_km = total_dist / 1000.0

    # 2. Informações estruturadas de cada segmento
    cores_map = {
        enum.TipoRelevo.SUBIDA: ('#E74C3C', 'Subida', '🔺'),
        enum.TipoRelevo.DESCIDA: ('#27AE60', 'Descida', '🔻'),
        enum.TipoRelevo.PLANO: ('#2980B9', 'Plano', '➖')
    }

    seg_info = []
    curr_d = 0.0
    for idx, seg in enumerate(segments):
        d_seg = seg.get('dist', 0)
        s_km = curr_d / 1000.0
        e_km = (curr_d + d_seg) / 1000.0
        fator = seg.get('fator', 1.0 + seg.get('esforco_extra_pct', 0.0) / 100.0)
        pct = fator * 100.0
        r = seg.get('relevo')
        color, nome, icone = cores_map.get(r, ('#7F8C8D', 'Trecho', '•'))

        seg_info.append({
            'idx': idx + 1,
            'start_km': s_km,
            'end_km': e_km,
            'relevo': r,
            'relevo_nome': nome,
            'icone': icone,
            'color': color,
            'inc': seg.get('inc', 0),
            'fator': fator,
            'pct': pct,
            'diff': pct - 100.0
        })
        curr_d += d_seg

    # 3. Cria figura com 2 subplots empilhados compartilhando o eixo X
    fig, (ax_pace, ax_elev) = plt.subplots(
        2, 1, 
        figsize=(9, 5.4),
        dpi=220, 
        sharex=True, 
        gridspec_kw={'height_ratios': [1.35, 1.0], 'hspace': 0.12}
    )
    fig.suptitle(
        'O ajuste nas subidas varia com a inclinação; nos planos, o pace progride gradualmente.',
        fontsize=9.5,
        color='#566573',
        y=0.99,
    )

    # ------------------ SUBPLOT SUPERIOR: CURVA DE PACE (% DO BASE) ------------------
    all_pcts = [s['pct'] for s in seg_info]
    min_p, max_p = min(all_pcts), max(all_pcts)
    ax_pace.set_ylim(min(82.0, min_p - 8), max(118.0, max_p + 14))
    ax_pace.set_xlim(0, total_km)

    # Linha neutra de referência em 100% (Pace Base no Plano)
    ax_pace.axhline(100.0, color='#34495E', linestyle='--', linewidth=1.3, alpha=0.85, label='Pace Base Alvo (100%)')

    # Plota a curva em cada segmento com a cor do próprio relevo
    legendas_relevo = set()
    for s in seg_info:
        lbl = s['relevo_nome'] if s['relevo_nome'] not in legendas_relevo else None
        if lbl:
            legendas_relevo.add(s['relevo_nome'])

        # Linha horizontal do ritmo no segmento
        ax_pace.hlines(
            y=s['pct'], 
            xmin=s['start_km'], 
            xmax=s['end_km'], 
            color=s['color'], 
            linewidth=3.5, 
            label=lbl, 
            zorder=4
        )

        # Preenchimento translúcido até a linha de 100% para evidenciar ganho/perda de ritmo
        ax_pace.fill_between(
            [s['start_km'], s['end_km']], 
            [100.0, 100.0], 
            [s['pct'], s['pct']], 
            color=s['color'], 
            alpha=0.20, 
            zorder=2
        )

        # Ponto central e rótulo compacto; trechos curtos ficam sem texto para evitar colisões.
        x_mid = (s['start_km'] + s['end_km']) / 2.0
        largura_km = s['end_km'] - s['start_km']
        ax_pace.plot(x_mid, s['pct'], marker='o', markersize=4.5, color=s['color'], markeredgecolor='white', markeredgewidth=0.9, zorder=5)

        if largura_km >= 0.9:
            y_text = s['pct'] + 2.3 if s['pct'] >= 100.0 else s['pct'] - 2.8
            ax_pace.text(
                x_mid,
                y_text,
                f"{s['pct']:.1f}%",
                ha='center',
                va='bottom' if s['pct'] >= 100.0 else 'top',
                fontsize=8,
                fontweight='semibold',
                color=s['color'],
                zorder=6,
            )

    # Conecta os degraus verticais entre segmentos adjacentes
    for i in range(len(seg_info) - 1):
        x_trans = seg_info[i]['end_km']
        y1 = seg_info[i]['pct']
        y2 = seg_info[i + 1]['pct']
        ax_pace.vlines(x=x_trans, ymin=min(y1, y2), ymax=max(y1, y2), color='#7F8C8D', linestyle=':', linewidth=1.5, zorder=3)

    # Linhas divisórias pontilhadas verticais marcando a troca de relevo em ambos os gráficos
    for s in seg_info[:-1]:
        x_div = s['end_km']
        ax_pace.axvline(x_div, color='#BDC3C7', linestyle='--', linewidth=1.0, alpha=0.7, zorder=1)
        ax_elev.axvline(x_div, color='#BDC3C7', linestyle='--', linewidth=1.0, alpha=0.7, zorder=1)

    ax_pace.set_ylabel('Pace estimado (% do pace base)', fontsize=9.5, fontweight='bold', color='#2C3E50')
    ax_pace.set_title('Ajuste de pace por trecho', fontsize=11, fontweight='bold', pad=8)
    ax_pace.grid(True, linestyle=':', alpha=0.55)
    ax_pace.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.92, fontsize=8.5, ncol=4)

    # ------------------ SUBPLOT INFERIOR: PERFIL ALTIMÉTRICO ------------------
    min_elev, max_elev = min(elevs), max(elevs)
    elev_pad = (max_elev - min_elev) * 0.15 if max_elev > min_elev else 10
    y_min_elev = min_elev - elev_pad
    y_max_elev = max_elev + elev_pad * 1.5

    ax_elev.set_ylim(y_min_elev, y_max_elev)

    # Curva contínua de altimetria
    ax_elev.plot(dists_km, elevs, color='#1A5276', linewidth=2.4, zorder=4, label='Altimetria Real (m)')
    ax_elev.fill_between(dists_km, elevs, y_min_elev, color='#D4E6F1', alpha=0.45, zorder=2)

    # Sombra discreta de cor por relevo no fundo da altimetria.
    for s in seg_info:
        ax_elev.axvspan(s['start_km'], s['end_km'], color=s['color'], alpha=0.08, zorder=1)

    ax_elev.set_xlabel('Distância da Prova (km)', fontsize=10.5, fontweight='bold', color='#2C3E50')
    ax_elev.set_ylabel('Altitude (m)', fontsize=10.5, fontweight='bold', color='#1A5276')
    ax_elev.grid(True, linestyle=':', alpha=0.55)
    ax_elev.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.92, fontsize=8.5)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    return fig
