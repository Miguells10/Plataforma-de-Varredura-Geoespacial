import requests
import pandas as pd
import streamlit as st

try:
    import geopandas as gpd
    from shapely.geometry import LineString
except ImportError:
    gpd = None

# --- DADOS DE EMERGÊNCIA (MOCK) ---
MOCK_SUBESTACOES = [
    {'Nome': 'Subestação Jardins (Demo)', 'latitude': -10.9472, 'longitude': -37.0731, 'Tipo': 'distribution'},
    {'Nome': 'Subestação Centro (Demo)', 'latitude': -10.9167, 'longitude': -37.0500, 'Tipo': 'distribution'}
]


@st.cache_data(ttl=3600)
def buscar_subestacoes_osm(cidade="Aracaju"):
    """
    Busca subestações. Se der erro de conexão ou JSON vazio, retorna dados de demonstração.
    """
    servers = [
        "https://overpass-api.de/api/interpreter",
        "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter"
    ]

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

    for server in servers:
        try:
            response = requests.get(server, params={'data': query}, headers=headers, timeout=10)

            if response.status_code == 200 and len(response.content) > 0:
                try:
                    data = response.json()
                    subestacoes = []

                    if 'elements' in data:
                        for el in data['elements']:
                            lat = el.get('lat') or el.get('center', {}).get('lat')
                            lon = el.get('lon') or el.get('center', {}).get('lon')
                            if lat and lon:
                                subestacoes.append({
                                    'Nome': el.get('tags', {}).get('name', 'Subestação Sem Nome'),
                                    'latitude': lat,
                                    'longitude': lon,
                                    'Tipo': 'Real'
                                })

                        if subestacoes:
                            return pd.DataFrame(subestacoes)
                except ValueError:
                    continue
        except Exception:
            continue

    print("⚠️ API OSM falhou. Usando dados de demonstração.")
    return pd.DataFrame(MOCK_SUBESTACOES)


@st.cache_data(ttl=3600)
def buscar_ruas_box(lat_min, lon_min, lat_max, lon_max):
    """
    Tenta baixar ruas. Se falhar, retorna vazio e segue a vida.
    """
    if gpd is None: return None  # Se não tiver geopandas, aborta

    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json][timeout:15];
    (
      way["highway"~"primary|secondary|tertiary|residential"]({lat_min},{lon_min},{lat_max},{lon_max});
    );
    out geom;
    """
    try:
        response = requests.get(overpass_url, params={'data': query}, timeout=20)
        if response.status_code == 200 and len(response.content) > 0:
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
    return gpd.GeoDataFrame()


def filtrar_pontos_em_ruas(lista_pontos):
    """
    Se geopandas funcionar, filtra ruas. Se não, devolve a lista original.
    """
    if not lista_pontos or gpd is None:
        return lista_pontos

    try:
        df_pontos = pd.DataFrame(lista_pontos)
        gdf_pontos = gpd.GeoDataFrame(
            df_pontos,
            geometry=gpd.points_from_xy(df_pontos.longitude, df_pontos.latitude),
            crs="EPSG:4326"
        )

        bounds = gdf_pontos.total_bounds
        gdf_ruas = buscar_ruas_box(bounds[1] - 0.002, bounds[0] - 0.002, bounds[3] + 0.002, bounds[2] + 0.002)

        if gdf_ruas is None or gdf_ruas.empty:
            return lista_pontos

        # Filtro Espacial
        gdf_zonas_rua = gdf_ruas.to_crs(epsg=3857).buffer(8).to_crs(epsg=4326)
        gdf_zonas_rua = gpd.GeoDataFrame(geometry=gdf_zonas_rua, crs="EPSG:4326")

        pontos_nas_ruas = gpd.sjoin(gdf_pontos, gdf_zonas_rua, how="inner", predicate="intersects")
        gdf_limpo = gdf_pontos[~gdf_pontos.index.isin(pontos_nas_ruas.index)]

        return gdf_limpo.drop(columns='geometry').to_dict('records')

    except Exception as e:
        print(f"Erro filtro ruas: {e}")
        return lista_pontos