import math
import Enums.enum as enums
import pandas as pd

def setStart(lat, lon, points):
    if points:
        last = points[-1]
        return [last['lat'], last['lng']]  # Folium espera [lat, lng]
    else:
        return [lat, lon]

def elevation(p1, p2):
    e1 = p1.get('elev', p1.get('elevation', 0))
    e2 = p2.get('elev', p2.get('elevation', 0))

    diff = e2 - e1 
    
    ganho = max(0, diff)
    perda = max(0, -diff)

    return ganho, perda

def haversine_distance(p1, p2):
    """
    Calcule distance between two points in superface real
    """

    R = 6371000  # Raio da Terra em metros
    lat1, lon1 = math.radians(p1['lat']), math.radians(p1['lng'])
    lat2, lon2 = math.radians(p2['lat']), math.radians(p2['lng'])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

def segment_to_list(segments):
    table_sheet = []
    for i, seg in enumerate(segments, start=1):
        relevo = seg.get('relevo')

        if relevo == enums.TipoRelevo.SUBIDA:
            relevo = "Subida"
        elif relevo == enums.TipoRelevo.DESCIDA:
            relevo = "Descida"
        else:
            relevo = "Plano"

        table_sheet.append({
            "Trecho": f"Segmento #{i}",
            "Relevo": relevo,
            "Distância": f"{seg.get('dist', 0):.0f} m",
            "Inclinação Média": f"{seg.get('inc', 0):+.1f}%"
        })

    return table_sheet

def custo_energetico_inclinacao(inc):
    return (155.4*pow(inc,5) - 30.4*pow(inc,4) - 43.3*pow(inc,3) + 46.3*pow(inc,2) + 19.5*inc + 3.6)

def paces_to_dataframe(segments, paces_by_segment, pace_base_seg=330):
    """
    Recebe os segmentos e os paces calculados por segmento e retorna:
    - DataFrame formatado com os trechos e a linha final de total/médias.
    - tempo_total_str: string formatada do tempo total previsto (hh:mm:ss ou mm:ss).
    - pace_medio_str: string formatada do pace médio geral (mm:ss min/km).
    """
    paces_data = []
    total_dist = 0
    total_tempo_seg = 0

    for i, seg in enumerate(segments, start=1):
        pace_seg_val = paces_by_segment.get(i, pace_base_seg)
        min_p = int(pace_seg_val // 60)
        sec_p = int(pace_seg_val % 60)
        
        dist_m = seg.get('dist', 0)
        total_dist += dist_m

        tempo_seg_estimado = (dist_m / 1000.0) * pace_seg_val
        total_tempo_seg += tempo_seg_estimado

        min_t = int(tempo_seg_estimado // 60)
        sec_t = int(tempo_seg_estimado % 60)

        relevo = seg.get('relevo')
        if relevo == enums.TipoRelevo.SUBIDA:
            icone = "🔺 Subida"
        elif relevo == enums.TipoRelevo.DESCIDA:
            icone = "🔻 Descida"
        else:
            icone = "➖ Plano"

        paces_data.append({
            "Trecho": f"Segmento #{i}",
            "Relevo": icone,
            "Distância": f"{dist_m:.0f} m",
            "Inclinação": f"{seg.get('inc', 0):+.1f}%",
            "Pace Sugerido": f"{min_p:02d}:{sec_p:02d} min/km",
            "Tempo no Trecho": f"{min_t:02d}:{sec_t:02d}"
        })

    pace_medio_seg = total_tempo_seg / (total_dist / 1000.0) if total_dist > 0 else pace_base_seg
    min_pm = int(pace_medio_seg // 60)
    sec_pm = int(pace_medio_seg % 60)
    pace_medio_str = f"{min_pm:02d}:{sec_pm:02d} min/km"

    if total_tempo_seg >= 3600:
        h = int(total_tempo_seg // 3600)
        m = int((total_tempo_seg % 3600) // 60)
        s = int(total_tempo_seg % 60)
        tempo_total_str = f"{h:02d}:{m:02d}:{s:02d}"
    else:
        m = int(total_tempo_seg // 60)
        s = int(total_tempo_seg % 60)
        tempo_total_str = f"{m:02d}:{s:02d}"

    # Linha final com o resumo da prova completa
    paces_data.append({
        "Trecho": "🏁 Total / Geral",
        "Relevo": "—",
        "Distância": f"{total_dist:.0f} m",
        "Inclinação": "—",
        "Pace Sugerido": pace_medio_str,
        "Tempo no Trecho": tempo_total_str
    })

    return pd.DataFrame(paces_data), tempo_total_str, pace_medio_str