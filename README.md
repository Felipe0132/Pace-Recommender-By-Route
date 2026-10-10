# 🏃 Pace Recommender By Route

O **Pace Recommender By Route** é uma aplicação em Python/Streamlit que analisa rotas de corrida considerando o **relevo e a altimetria real do terreno** para sugerir estratégias de ritmo (*pace*).

---

## 🎯 A Ideia do Projeto

Calcular o ritmo de um corredor apenas com base na **distância total** pode ser ilusório. Um percurso de 10 km completamente plano exige um esforço muito diferente do mesmo percurso com grandes subidas ou descidas acentuadas.

* **Subidas:** Exigem maior custo energético, demandando uma redução controlada do pace para evitar fadiga precoce.
* **Descidas:** Permitem ganhos de velocidade e menor impacto cardiovascular se executadas com técnica adequada.
* **Trechos Planos:** Permitem estabilizar o ritmo de cruzeiro e recuperar a cadência.

Este projeto busca decompor o trajeto e entender as nuances do relevo para orientar qual pace o corredor **deve ou pode realizar em cada segmento da prova**.

---

## ⚙️ Como Funciona o Pipeline

1. **Definição da Rota:** Seleção interativa de pontos no mapa (com algoritmo de menor caminho Dijkstra via OSMnx) ou upload de arquivos `.gpx`.
2. **Discretização em Segmentos (~300m):** O trajeto contínuo é fatiado em pequenos blocos ponderados com elevação real via satélite.
3. **Classificação de Relevo:** Cada trecho é categorizado dinamicamente em **Subida**, **Descida** ou **Plano** com base no percentual de inclinação.
4. **Agrupamento Consolidado (`groupByRelevo`):** Blocos adjacentes com o mesmo tipo de relevo são agrupados em super-trechos para criar um mapa de estratégia limpo e compreensível.

---

## 🚀 Como Executar Localmente

### 1. Clonar o repositório
```bash
git clone https://github.com/Felipe0132/Pace-Recommender-By-Route.git
cd Pace-Recommender-By-Route
```

### 2. Criar e ativar o ambiente virtual
```bash
python3 -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

### 3. Instalar dependências
```bash
pip install -r requirements.txt
```

### 4. Executar a aplicação Streamlit
```bash
streamlit run main.py
```

---

## 🛠️ Tecnologias Utilizadas
* **Python 3**
* **Streamlit & Streamlit-Folium** (Interface web e mapas interativos)
* **OSMnx & NetworkX** (Malha viária e grafos espaciais)
* **gpxpy** (Leitura e processamento de arquivos GPX)
* **Matplotlib** (Visualização e plotagem de grafos)
