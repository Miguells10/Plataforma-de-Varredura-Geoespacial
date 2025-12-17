import requests
import cv2
import numpy as np
from PIL import Image, ImageDraw
from io import BytesIO
import os

API_KEY = os.getenv("GOOGLE_MAPS_KEY")
BASE_URL = "https://maps.googleapis.com/maps/api/staticmap"


def baixar_imagem_satelite(lat, long, zoom=20, size="600x600", scale=2):
    """
    Função BÁSICA: Apenas baixa a imagem limpa do Google.
    Usada pelo Laboratório de Calibração e pelo Analisador.
    """
    if not API_KEY:
        print("ERRO: Sem API Key")
        return None

    params = {
        'center': f"{lat},{long}",
        'zoom': zoom,
        'size': size,
        'scale': scale,  # HD
        'maptype': 'satellite',
        'key': API_KEY
    }

    try:
        response = requests.get(BASE_URL, params=params)
        if response.status_code == 200:
            # Retorna imagem PIL pura
            return Image.open(BytesIO(response.content))
        else:
            print(f"Erro Google API: {response.status_code}")
            return None
    except Exception as e:
        print(f"Erro Conexão: {e}")
        return None


def analisar_imagem_telhado(lat, long):
    """
    Função INTELIGENTE: Baixa a imagem e roda o algoritmo de Visão Computacional
    para detectar painéis (Azul + Grid Branco + Preto).
    """
    # 1. Reusa a função de baixar para não duplicar código
    pil_img_raw = baixar_imagem_satelite(lat, long)

    if pil_img_raw:
        try:
            # Converte PIL para OpenCV (numpy)
            img_bgr = cv2.cvtColor(np.array(pil_img_raw), cv2.COLOR_RGB2BGR)

            # --- PREPARAÇÃO VISUAL ---
            # Cria uma cópia para desenhar o resultado final
            img_final_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            pil_img_final = Image.fromarray(img_final_rgb)
            draw = ImageDraw.Draw(pil_img_final)
            w_img, h_img = pil_img_final.size

            # Borda Ciano (Indica que a casa foi processada)
            draw.rectangle([5, 5, w_img - 5, h_img - 5], outline="#00c0f2", width=4)

            # --- PROCESSAMENTO DE IA ---
            hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

            # MÁSCARA 1: AZUL (Painéis Policristalinos)
            lower_blue = np.array([90, 40, 40])
            upper_blue = np.array([140, 255, 255])
            mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)

            # MÁSCARA 2: ESCURO/PRETO (Monocristalinos/Sombra)
            lower_dark = np.array([0, 0, 0])
            upper_dark = np.array([180, 255, 60])
            mask_dark = cv2.inRange(hsv, lower_dark, upper_dark)

            # Combina
            mask_combined = cv2.bitwise_or(mask_blue, mask_dark)

            # --- TRATAMENTO DO GRID BRANCO ---
            # Fecha os buracos brancos da grade do painel
            kernel = np.ones((7, 7), np.uint8)
            mask_closed = cv2.morphologyEx(mask_combined, cv2.MORPH_CLOSE, kernel)
            mask_clean = cv2.morphologyEx(mask_closed, cv2.MORPH_OPEN, kernel)

            contours, _ = cv2.findContours(mask_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            area_total_img = w_img * h_img
            detectou_gd = False
            score_final = 0.0

            for cnt in contours:
                area = cv2.contourArea(cnt)

                # Filtra tamanho (nem muito pequeno, nem a imagem toda)
                if area > 600 and area < (area_total_img * 0.8):

                    x, y, w, h = cv2.boundingRect(cnt)
                    aspect_ratio = float(w) / h

                    if 0.3 < aspect_ratio < 4.0:
                        # Checa solidez
                        hull = cv2.convexHull(cnt)
                        hull_area = cv2.contourArea(hull)
                        solidity = float(area) / hull_area if hull_area > 0 else 0

                        if solidity > 0.7:
                            # DESENHA CAIXA VERDE (GD)
                            draw.rectangle([x, y, x + w, y + h], outline="#00FF00", width=4)
                            draw.text((x, y - 15), "GD Detectada", fill="#00FF00")
                            detectou_gd = True
                            score_final += area

            ratio = min(score_final / area_total_img * 5, 0.99)

            return pil_img_final, ratio, detectou_gd

        except Exception as e:
            print(f"Erro no processamento CV: {e}")
            return pil_img_raw, 0, False  # Retorna a imagem sem caixa se der erro na IA

    return None, 0, False