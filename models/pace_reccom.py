import utils.utils as utils

def fator_esforco_inclinacao(inc):
    i = inc / 100.0
    if i < -0.02:
        i = -0.02

    gasto_inc = utils.custo_energetico_inclinacao(i)
    gasto_plan = utils.custo_energetico_inclinacao(0)

    fator_inc = gasto_inc / gasto_plan
    esforco_extra_pct = (fator_inc - 1.0) * 100.0

    return fator_inc, esforco_extra_pct

def pacer_ajusted(pace_seg, inc):
    fator_inc, esforco_extra_pct = fator_esforco_inclinacao(inc)
    pace_in_inc = pace_seg * fator_inc
    return pace_in_inc, esforco_extra_pct

def calcular_esforcos_e_juntar_blocos(blocos, min_dist_progressao=700):
    """
    Calcula o fator de esforço para cada bloco de relevo (usando 70% dos 20% da prova
    como corte para progressão nos planos) e junta blocos sequenciais (adjacentes)
    que possuam o mesmo esforço.
    """
    if not blocos:
        return []

    contador_planos = 0
    ultimo_fator_plano = 1.0

    for i, bloco in enumerate(blocos, start=1):
        relevo_str = str(bloco.get('relevo', '')).upper()
        inc = bloco.get('inc', 0)
        dist_seg = bloco.get('distance', bloco.get('dist', 0))
        is_plano = "PLANO" in relevo_str

        if is_plano:
            contador_planos += 1
            if contador_planos == 1:
                # 1º trecho plano: começa exatamente no ritmo base (fator 1.0)
                fator = 1.0
            elif dist_seg > min_dist_progressao:
                # Trechos planos seguintes acima de 70% dos 20% progridem (teto de 5% de melhora, fator >= 0.95)
                fator = max(0.95, 1.0 - ((contador_planos - 1) * 0.0075))
            else:
                # Trecho plano curto (<= 70% dos 20%): mantém o esforço do plano anterior
                fator = ultimo_fator_plano

            ultimo_fator_plano = fator
        else:
            fator, _ = fator_esforco_inclinacao(inc)

        bloco['fator'] = fator

    # Junta blocos sequenciais (adjacentes) que ficaram com o mesmo esforço
    blocos_juntados = []
    for bloco in blocos:
        if (
            blocos_juntados
            and bloco.get('relevo') == blocos_juntados[-1].get('relevo')
            and round(bloco.get('fator', 1.0), 4) == round(blocos_juntados[-1].get('fator', 1.0), 4)
        ):
            anterior = blocos_juntados[-1]
            anterior['v'] = bloco['v']
            anterior['distance'] += bloco['distance']
            anterior['coords'].extend(bloco['coords'])
            anterior['up'] += bloco['up']
            anterior['down'] += bloco['down']
            anterior['inc_seg'].extend(bloco.get('inc_seg', [bloco.get('inc', 0)]))
            anterior['inc'] = max(anterior['inc_seg'], key=abs) if anterior['inc_seg'] else 0
        else:
            blocos_juntados.append(bloco)

    # Identifica o último plano após a junção para o sprint final
    indices_planos = [
        idx for idx, b in enumerate(blocos_juntados, start=1)
        if "PLANO" in str(b.get('relevo', '')).upper()
    ]
    ultimo_plano = indices_planos[-1] if indices_planos else None

    for i, bloco in enumerate(blocos_juntados, start=1):
        fator_final = bloco['fator']
        is_plano = "PLANO" in str(bloco.get('relevo', '')).upper()
        if i == ultimo_plano and i != 1:
            fator_final = fator_final * 0.95

        # Teto de 5% de melhora para trechos planos (fator mínimo 0.95 / esforço até -5%)
        if is_plano:
            fator_final = max(0.95, fator_final)

        variacao_pct = (fator_final - 1.0) * 100.0
        bloco['fator'] = round(fator_final, 4)
        bloco['esforco_extra_pct'] = round(variacao_pct, 2)
        bloco['esforco_pct'] = round(variacao_pct, 2)

    return blocos_juntados

def define_paces_by_segment(bloco_segments, pace):
    segmentos = dict()

    for i, segment in enumerate(bloco_segments, start=1):
        fator_final = segment.get('fator')
        if fator_final is None:
            # Fallback caso algum segmento não tenha passado pelo cálculo prévio
            relevo = str(segment.get('relevo', segment.get('Relevo', ''))).upper()
            inc = segment.get('inc', segment.get('inclinacao_pct', 0))
            if "PLANO" in relevo:
                fator_final = 1.0
            else:
                fator_final, _ = fator_esforco_inclinacao(inc)
            variacao_pct = (fator_final - 1.0) * 100.0
            segment['fator'] = round(fator_final, 4)
            segment['esforco_extra_pct'] = round(variacao_pct, 2)
            segment['esforco_pct'] = round(variacao_pct, 2)

        pace_atual = pace * fator_final
        segmentos[i] = round(pace_atual, 2)

    return segmentos