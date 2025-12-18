import requests
import cv2
import numpy as np
from PIL import Image, ImageDraw
from io import BytesIO
import os

API_KEY = os.getenv("GOOGLE_MAPS_KEY")
BASE_URL = "https://maps.googleapis.com/maps/api/staticmap"


def _gerar_imagem_mock():
    """Gera imagem cinza neutra caso falhe o download."""
    arr = np.full((600, 600, 3), 128, dtype=np.uint8)
    return Image.fromarray(arr, 'RGB')


def baixar_imagem_satelite(lat, long, zoom=19, size="600x600", scale=2):
    """
    Baixa a imagem. Zoom 19 evita o 'zoom digital' borrado do Google em áreas rurais.
    """
    if API_KEY:
        params = {
            'center': f"{lat},{long}", 'zoom': zoom, 'size': size,
            'scale': scale, 'maptype': 'satellite', 'key': API_KEY
        }
        try:
            response = requests.get(BASE_URL, params=params, timeout=5)
            if response.status_code == 200:
                return Image.open(BytesIO(response.content))
        except Exception:
            pass
    return _gerar_imagem_mock()


def analisar_imagem_telhado(lat, long, hsv_config=None):
    pil_img_raw = baixar_imagem_satelite(lat, long)
    if not pil_img_raw: return None, 0, False

    try:
        img_bgr = cv2.cvtColor(np.array(pil_img_raw), cv2.COLOR_RGB2BGR)


        img_final_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        pil_img_final = Image.fromarray(img_final_rgb)
        draw = ImageDraw.Draw(pil_img_final)
        w, h = pil_img_final.size

        draw.rectangle([0, 0, w - 1, h - 1], outline="#00c0f2", width=4)


        hsv_check = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        saturacao_media = np.mean(hsv_check[:, :, 1])

        tem_cor_util = saturacao_media > 20

        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

        blurred = cv2.GaussianBlur(gray, (11, 11), 0)

        clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(blurred)

        edges = cv2.Canny(enhanced, 50, 150)

        kernel = np.ones((3, 3), np.uint8)
        dilated = cv2.dilate(edges, kernel, iterations=1)

        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        detectou_gd = False
        score_final = 0.0

        for cnt in contours:
            area = cv2.contourArea(cnt)

            if area > 400:

                peri = cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)

                if 4 <= len(approx) <= 6:

                    x, y, w_rect, h_rect = cv2.boundingRect(approx)
                    aspect_ratio = float(w_rect) / h_rect

                    if 0.5 < aspect_ratio < 2.5:

                        eh_painel = False
                        motivo = ""

                        roi_edges = edges[y:y + h_rect, x:x + w_rect]

                        lines = cv2.HoughLinesP(roi_edges, 1, np.pi / 180, threshold=20,
                                                minLineLength=15, maxLineGap=10)

                        if lines is not None and len(lines) >= 2:
                            eh_painel = True
                            motivo = "ESTRUTURA"

                        if tem_cor_util and not eh_painel:
                            roi_hsv = hsv_check[y:y + h_rect, x:x + w_rect]

                            mean_h = np.mean(roi_hsv[:, :, 0])
                            mean_s = np.mean(roi_hsv[:, :, 1])
                            mean_v = np.mean(roi_hsv[:, :, 2])

                            if (90 < mean_h < 140) and (mean_s > 25) and (mean_v < 200):
                                eh_painel = True
                                motivo = "COR AZUL"

                        if eh_painel:
                            draw.rectangle([x, y, x + w_rect, y + h_rect], outline="#00FF00", width=3)
                            draw.text((x, y - 10), motivo, fill="#00FF00")

                            detectou_gd = True
                            score_final += area

        ratio = min(score_final / (w * h) * 10, 0.99)

        return pil_img_final, ratio, detectou_gd

    except Exception as e:
        print(f"Erro IA: {e}")
        return pil_img_raw, 0, False