import requests
import pandas as pd


def buscar_subestacoes_osm(cidade="Aracaju"):
    """
    Usa a API do OpenStreetMap (Overpass) para achar subestações de energia
    dentro de uma cidade.
    """
    overpass_url = "http://overpass-api.de/api/interpreter"

    # Query na linguagem do OSM: "Me dê nós (nodes) ou caminhos (ways)
    # marcados como 'power=substation' dentro da área da cidade"
    query = f"""
    [out:json];
    area["name"="{cidade}"]->.searchArea;
    (
      node["power"="substation"](area.searchArea);
      way["power"="substation"](area.searchArea);
      rel["power"="substation"](area.searchArea);
    );
    out center;
    """

    response = requests.get(overpass_url, params={'data': query})
    data = response.json()

    subestacoes = []
    for element in data['elements']:
        # O OSM às vezes retorna 'center' (se for uma área) ou 'lat'/'lon' (se for ponto)
        lat = element.get('lat') or element.get('center', {}).get('lat')
        lon = element.get('lon') or element.get('center', {}).get('lon')
        nome = element.get('tags', {}).get('name', 'Subestação Sem Nome')
        tipo = element.get('tags', {}).get('substation', 'distribution')  # Tenta ver o tipo

        if lat and lon:
            subestacoes.append({
                'Nome': nome,
                'Tipo': tipo,
                'latitude': lat,
                'longitude': lon
            })

    return pd.DataFrame(subestacoes)