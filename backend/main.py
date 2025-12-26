import sys
import os
import base64
from io import BytesIO
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.modules.ingestion.osm_service import buscar_subestacoes_osm
from backend.modules.geo.building_service import buscar_edificacoes_raio
# Importamos a função inteligente que você já tinha:
from backend.modules.geo.processing import prepare_scan_data
from backend.modules.geo.voronoi_logic import filtrar_por_voronoi
from backend.modules.vision.satellite_service import analisar_imagem_com_ia

app = FastAPI(title="Radix GeoIntelligence", version="2.2")


# --- MODELOS ---
class ScanRequest(BaseModel):
    subestacao_nome: str
    latitude: float
    longitude: float
    raio_km: float = 0.5
    usar_voronoi: bool = True
    modo: str = "osm"


def imagem_para_base64(pil_img):
    buffered = BytesIO()
    pil_img.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


@app.get("/")
def health_check():
    return {"status": "online", "service": "Radix Neural Engine V2.2"}


@app.get("/subestacoes")
def get_subestacoes(cidade: str = "Aracaju"):
    df = buscar_subestacoes_osm(cidade)
    if df.empty: return []
    return df[['Nome', 'latitude', 'longitude']].to_dict('records')


@app.post("/scan")
def realizar_scan(request: ScanRequest):
    print(f"🛰️ Scan: {request.subestacao_nome} | Modo: {request.modo} | Raio: {request.raio_km}km")

    # 1. Busca Edificações Brutas (OSM)
    # Mesmo se o modo for Grid, buscamos para tentar aproveitar,
    # mas a função prepare_scan_data vai decidir se usa ou não.
    casas_df = buscar_edificacoes_raio(request.latitude, request.longitude, radius_km=request.raio_km)

    buildings_raw = []
    if not casas_df.empty:
        buildings_raw = casas_df.to_dict('records')

    # 2. Prepara os Alvos (Aqui entra a sua lógica inteligente)
    # Ele decide: Usa OSM? Gera Grid? Faz Fallback?
    lista_alvos = prepare_scan_data(
        request.latitude,
        request.longitude,
        buildings=buildings_raw,
        radius_km=request.raio_km,
        modo=request.modo  # Passamos "osm" ou "grid"
    )

    # 3. Filtro Voronoi
    if request.usar_voronoi:
        try:
            todas = buscar_subestacoes_osm("Aracaju")
            lista_alvos = filtrar_por_voronoi(lista_alvos, todas, request.subestacao_nome)
        except:
            pass

    # 4. Visão Computacional
    resultados = []
    # Aumentando amostra para demonstrar poder do Grid
    amostra = lista_alvos[:20]

    for item in amostra:
        lat = item.get('latitude')
        lon = item.get('longitude')

        if lat and lon:
            img_pintada, dados = analisar_imagem_com_ia(lat, lon)

            if dados.get('tem_gd'):
                img_b64 = imagem_para_base64(img_pintada)

                resultados.append({
                    "id": item.get('id', 'N/A'),
                    "lat": lat,
                    "lon": lon,
                    "potencia": dados.get('potencia_kw', 0),
                    "classe": dados.get('classe', 'Desc'),
                    "tipo_osm": item.get('categoria_osm', 'N/A'),
                    "imagem_base64": img_b64
                })

    return {
        "subestacao": request.subestacao_nome,
        "total_analisado": len(lista_alvos),
        "gds_encontradas": len(resultados),
        "detalhes": resultados
    }