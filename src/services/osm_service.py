import requests
import pandas as pd
import geopandas as gpd
from shapely.geometry import LineString, box
import streamlit as st
import time

# Coordenadas de emergência (Aracaju) caso a API falhe
MOCK_SUBESTACAO = [
    {'Nome': 'Subestação Jardins (Demo)', 'latitude': -10.9472, 'longitude': -37.0731, 'Tipo': 'distribution'},
    {'Nome': 'Subestação Centro (Demo)', 'latitude': -10.9167, 'longitude': -37.0500, 'Tipo': 'distribution'}
]


@st.cache_data(ttl=3600)
def buscar_subestacoes_osm(cidade="Aracaju"):
    """
    Busca subestações. Se falhar ou for bloqueado, retorna dados de exemplo (Mock)
    para não travar a apresentação.
    """
    servers = [
        "https://overpass-api.de/api/interpreter",
        "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter"
    ]

    # Query otimizada
    query = f"""
    [out:json][timeout:15];
    area["name"="{cidade}"]->.searchArea;
    (
      node["power"="substation"](area.searchArea);
      way["power"="substation"](area.searchArea);
      rel["power"="substation"](area.searchArea);
    );
    out center;
    """

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.google.com/'
    }

    print(f"📡 Buscando subestações em {cidade}...")

    for server in servers:
        try:
            response = requests.get(server, params={'data': query}, headers=headers, timeout=20)

            if response.status_code == 200:
                try:
                    data = response.json()
                    subestacoes = []

                    if 'elements' in data:
                        for element in data['elements']:
                            lat = element.get('lat') or element.get('center', {}).get('lat')
                            lon = element.get('lon') or element.get('center', {}).get('lon')
                            nome = element.get('tags', {}).get('name', 'Subestação (Sem Nome)')

                            if lat and lon:
                                subestacoes.append({'Nome': nome, 'latitude': lat, 'longitude': lon, 'Tipo': 'Real'})

                        if subestacoes:
                            print(f"✅ Encontradas {len(subestacoes)} subestações via OSM.")
                            return pd.DataFrame(subestacoes)
                except ValueError:
                    continue
        except Exception as e:
            print(f"⚠️ Erro no servidor {server}: {e}")
            continue

    # --- PLANO B: MOCK (Se tudo falhar) ---
    print("❌ Falha na API OSM (Bloqueio). Usando dados de demonstração.")
    st.toast("⚠️ API OSM instável/bloqueada. Usando dados de demonstração para a apresentação.")

    # Se a cidade for Aracaju, retorna o Mock. Se não, retorna vazio mas válido.
    if "aracaju" in cidade.lower():
        return pd.DataFrame(MOCK_SUBESTACAO)

    return pd.DataFrame()  # Retorna VAZIO, mas nunca None.


@st.cache_data(ttl=3600)
def buscar_ruas_box(lat_min, lon_min, lat_max, lon_max):
    """
    Baixa ruas para o filtro espacial. Se falhar, retorna vazio (sem filtrar) para não travar.
    """
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json][timeout:25];
    (
      way["highway"~"primary|secondary|tertiary|residential"]({lat_min},{lon_min},{lat_max},{lon_max});
    );
    out geom;
    """

    try:
        response = requests.get(overpass_url, params={'data': query}, timeout=30)
        if response.status_code == 200:
            data = response.json()
            ruas = []
            for element in data.get('elements', []):
                if 'geometry' in element:
                    coords = [(pt['lon'], pt['lat']) for pt in element['geometry']]
                    if len(coords) > 1:
                        ruas.append(LineString(coords))

            if ruas:
                return gpd.GeoDataFrame(geometry=ruas, crs="EPSG:4326")
    except:
        pass

    return gpd.GeoDataFrame()  # Retorna vazio, o código segue sem filtrar ruas


def filtrar_pontos_em_ruas(lista_pontos):
    """
    Filtra pontos em ruas. Se der erro no download das ruas, retorna a lista original.
    """
    if not lista_pontos: return []

    try:
        df_pontos = pd.DataFrame(lista_pontos)
        gdf_pontos = gpd.GeoDataFrame(
            df_pontos,
            geometry=gpd.points_from_xy(df_pontos.longitude, df_pontos.latitude),
            crs="EPSG:4326"
        )

        bounds = gdf_pontos.total_bounds
        # Baixa ruas
        gdf_ruas = buscar_ruas_box(bounds[1] - 0.002, bounds[0] - 0.002, bounds[3] + 0.002, bounds[2] + 0.002)

        if gdf_ruas.empty:
            return lista_pontos  # Sem ruas? Segue o jogo.

        # Buffer e Join
        gdf_zonas_rua = gdf_ruas.to_crs(epsg=3857).buffer(8).to_crs(epsg=4326)
        gdf_zonas_rua = gpd.GeoDataFrame(geometry=gdf_zonas_rua, crs="EPSG:4326")

        pontos_nas_ruas = gpd.sjoin(gdf_pontos, gdf_zonas_rua, how="inner", predicate="intersects")
        gdf_limpo = gdf_pontos[~gdf_pontos.index.isin(pontos_nas_ruas.index)]

        return gdf_limpo.drop(columns='geometry').to_dict('records')

    except Exception as e:
        print(f"Erro no filtro de ruas: {e}. Ignorando filtro.")
        return lista_pontos