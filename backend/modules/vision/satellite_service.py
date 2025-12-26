import os
import requests
import numpy as np
from PIL import Image, ImageDraw
from io import BytesIO
from ultralytics import YOLO

# Configurações
API_KEY = os.getenv("GOOGLE_MAPS_KEY")
MODEL_PATH = "models/solar_v1.pt"

# --- SINGLETON DO MODELO ---
# Carrega o modelo apenas uma vez quando o servidor inicia
_model_instance = None


def get_model():
    global _model_instance
    if _model_instance is None:
        print("🧠 Carregando Modelo YOLO na memória...")
        if os.path.exists(MODEL_PATH):
            _model_instance = YOLO(MODEL_PATH)
        else:
            print(f"❌ ERRO CRÍTICO: Modelo não encontrado em {MODEL_PATH}")
            return None
    return _model_instance


def baixar_imagem_satelite(lat, long):
    """Baixa imagem via Google Static Maps API"""
    if API_KEY:
        params = {
            'center': f"{lat},{long}",
            'zoom': 19,
            'size': "600x600",
            'scale': 2,
            'maptype': 'satellite',
            'key': API_KEY
        }
        try:
            resp = requests.get("https://maps.googleapis.com/maps/api/staticmap", params=params, timeout=5)
            if resp.status_code == 200:
                return Image.open(BytesIO(resp.content))
        except Exception as e:
            print(f"Erro download imagem: {e}")

    return None


def analisar_imagem_com_ia(lat, lon):
    """
    Pipeline completo: Download -> Inferência -> Desenho -> JSON
    """
    img = baixar_imagem_satelite(lat, lon)
    if not img:
        return None, {"tem_gd": False, "erro": "Falha download"}

    model = get_model()
    if not model:
        return img, {"tem_gd": False, "erro": "Modelo offline"}

    # Inferência
    results = model.predict(img, conf=0.4, verbose=False)  # Confiança ajustada
    result = results[0]

    # Desenha na imagem (Bounding Boxes)
    # Convertemos o array BGR do OpenCV/YOLO de volta para RGB para o Pillow
    im_array = result.plot()  # Gera array numpy com as caixas
    img_desenhada = Image.fromarray(im_array[..., ::-1])  # Inverte BGR -> RGB

    # Cálculos
    area_px = 0
    qtd_paineis = len(result.boxes)

    for box in result.boxes:
        w, h = box.xywh[0][2].item(), box.xywh[0][3].item()
        area_px += w * h

    # Regra de Negócio (Estimativa)
    # Assumindo ~400px por painel de 550W
    n_paineis = int(area_px / 400)
    if qtd_paineis > 0:
        n_paineis = max(n_paineis, qtd_paineis)

    potencia_kw = n_paineis * 0.55

    classe = "Residencial"
    if potencia_kw > 75:
        classe = "Industrial (Grupo A)"
    elif potencia_kw > 15:
        classe = "Comercial"

    dados = {
        "tem_gd": qtd_paineis > 0,
        "potencia_kw": round(potencia_kw, 2),
        "classe": classe,
        "area_px": int(area_px)
    }

    return img_desenhada, dados