import os
from ultralytics import YOLO


def main():
    # --- CONFIGURAÇÕES ---
    caminho_modelo = r"C:\Users\Miguel Lucas\PycharmProjects\radix\models\solar_v1.pt"

    pasta_imagens = r"C:\Users\Miguel Lucas\PycharmProjects\radix\dataset_solar\valid\images"

    print("🧠 Carregando o cérebro da IA...")
    model = YOLO(caminho_modelo)

    if not os.path.exists(pasta_imagens):
        print(f"❌ Erro: A pasta '{pasta_imagens}' não existe.")
        return

    arquivos = os.listdir(pasta_imagens)

    imagens = [f for f in arquivos if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

    print(f"📂 Encontrei {len(imagens)} imagens para analisar. Começando agora!\n")

    for i, imagem_nome in enumerate(imagens):
        caminho_completo = os.path.join(pasta_imagens, imagem_nome)

        results = model.predict(source=caminho_completo, save=True, device='cpu', conf=0.25, verbose=False)

        resultado = results[0]
        qtd_paineis = len(resultado.boxes)

        # --- RELATÓRIO INDIVIDUAL ---
        print(f"[{i + 1}/{len(imagens)}] Arquivo: {imagem_nome}")
        print(f"   ☀️  Painéis: {qtd_paineis}")

        if qtd_paineis > 20:
            print("   🏭 Tipo: INDÚSTRIA / COMÉRCIO")
        elif qtd_paineis > 0:
            print("   🏠 Tipo: RESIDENCIAL")
        else:
            print("   ❌ Nada detectado")

        print("-" * 30)

    print("\n✅ FIM DA ANÁLISE!")
    print("As imagens com os quadrados desenhados estão na pasta 'runs/detect/predict'.")


if __name__ == '__main__':
    main()