import requests
import cv2
import numpy as np
from PIL import Image, ImageDraw
from io import BytesIO
import os

API_KEY = os.getenv("GOOGLE_MAPS_KEY")
BASE_URL = "https://maps.googleapis.com/maps/api/staticmap"


def baixar_imagem_satelite(lat, long, zoom=20, size="600x600", scale=2):
    if not API_KEY:
        return None
    params = {
        'center': f"{lat},{long}", 'zoom': zoom, 'size': size,
        'scale': scale, 'maptype': 'satellite', 'key': API_KEY
    }
    try:
        response = requests.get(BASE_URL, params=params)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
        return None
    except Exception:
        return None


# CORREÇÃO: Adicionado hsv_config=None nos argumentos
def analisar_imagem_telhado(lat, long, hsv_config=None):
    pil_img_raw = baixar_imagem_satelite(lat, long)

    if pil_img_raw:
        try:
            img_bgr = cv2.cvtColor(np.array(pil_img_raw), cv2.COLOR_RGB2BGR)
            img_final_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            pil_img_final = Image.fromarray(img_final_rgb)
            draw = ImageDraw.Draw(pil_img_final)
            w_img, h_img = pil_img_final.size

            # Marca de processamento (Ciano)
            draw.rectangle([5, 5, w_img - 5, h_img - 5], outline="#00c0f2", width=4)

            # Melhoria de imagem
            lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            limg = cv2.merge((clahe.apply(l), a, b))
            img_enhanced = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
            hsv = cv2.cvtColor(img_enhanced, cv2.COLOR_BGR2HSV)

            # --- LÓGICA DE MÁSCARAS ---
            if hsv_config:
                # Calibração Manual (Vinda do Slider)
                lower_user = np.array(hsv_config[0])
                upper_user = np.array(hsv_config[1])
                mask_combined = cv2.inRange(hsv, lower_user, upper_user)
            else:
                # Automático
                mask_blue = cv2.inRange(hsv, np.array([85, 30, 30]), np.array([145, 255, 255]))
                mask_dark = cv2.inRange(hsv, np.array([0, 0, 0]), np.array([180, 90, 110]))
                mask_combined = cv2.bitwise_or(mask_blue, mask_dark)

            # --- DETECÇÃO ---
            edges = cv2.Canny(img_enhanced, 50, 150)
            kernel_connect = np.ones((5, 5), np.uint8)
            mask_connected = cv2.dilate(mask_combined, kernel_connect, iterations=2)
            mask_closed = cv2.morphologyEx(mask_connected, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))

            contours, _ = cv2.findContours(mask_closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            detectou_gd = False
            score_final = 0.0

            for cnt in contours:
                area = cv2.contourArea(cnt)
                # Área > 150px (Pequenos residenciais)
                if area > 150 and area < (w_img * h_img * 0.9):
                    x, y, w, h = cv2.boundingRect(cnt)
                    aspect_ratio = float(w) / h

                    if 0.2 < aspect_ratio < 5.0:
                        # Validação por textura/bordas internas
                        roi_edges = edges[y:y + h, x:x + w]
                        edge_density = cv2.countNonZero(roi_edges) / area

                        if edge_density > 0.02:
                            draw.rectangle([x, y, x + w, y + h], outline="#00FF00", width=3)
                            detectou_gd = True
                            score_final += area

            ratio = min(score_final / (w_img * h_img) * 5, 0.99)
            return pil_img_final, ratio, detectou_gd

        except Exception as e:
            print(f"Erro IA: {e}")
            return pil_img_raw, 0, False

    return None, 0, False