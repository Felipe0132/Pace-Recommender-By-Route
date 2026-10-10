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