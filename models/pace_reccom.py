import utils.utils as utils

def pacer_ajusted(pace_seg, inc):
    i = inc/100
    if i < -0.045:
        i = -0.045

    gasto_inc = utils.custo_energetico_inclinacao(i)
    gasto_plan = utils.custo_energetico_inclinacao(0)

    fator_inc = gasto_inc/gasto_plan

    pace_in_inc = pace_seg*fator_inc
    esforco_extra_pct = (fator_inc - 1.0) * 100

    return pace_in_inc, esforco_extra_pct

def define_paces_by_segment(bloco_segments, pace):
    segmentos = dict()
    total_segmentos = len(bloco_segments)

    indices_planos = [
        idx for idx, seg in enumerate(bloco_segments, start=1)
        if "PLANO" in str(seg.get('relevo', seg.get('Relevo', ''))).upper()
    ]
    ultimo_plano = indices_planos[-1] if indices_planos else None

    contador_planos = 0  # Começa em 0 para o 1º plano ser 1
    for i, segment in enumerate(bloco_segments, start=1):
        relevo = str(segment.get('relevo', segment.get('Relevo', ''))).upper()
        inc = segment.get('inc', segment.get('inclinacao_pct', 0))
        is_plano = "PLANO" in relevo

        if is_plano:
            contador_planos += 1
            # Usa o pace alvo direto (ou suaviza a inclinação do falso plano: inc * 0.25)
            pace_base = pace
            
            if i == 1:
                # Se o 1º trecho da prova for plano, segura 5% p/ aquecer
                fator_progressao = 1.05
            else:
                # A partir do 2º plano, baixa 0.75% a cada plano
                fator_progressao = 1.0 - (contador_planos * 0.0075)
                
            pace_atual = pace_base * fator_progressao
        else:
            # Subidas e descidas reais usam 100% do polinômio de grau 5
            pace_atual, _ = pacer_ajusted(pace, inc)

        # Sprint final / último plano (sem acumular com descida forte)
        if i == ultimo_plano and i != 1:
            pace_atual = pace_base * fator_progressao*0.95

        fator_final = pace_atual / pace
        variacao_pct = (fator_final - 1.0) * 100

        segmentos[i] = round(pace_atual, 2)
        segment['fator'] = round(fator_final, 4)
        segment['esforco_extra_pct'] = round(variacao_pct, 2)
        segment['esforco_pct'] = round(variacao_pct, 2)
        
    return segmentos