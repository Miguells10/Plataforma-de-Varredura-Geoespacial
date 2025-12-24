from ultralytics import YOLO

def main():
    # 1. Carregar o modelo
    # 'yolov8n.pt' = Nano (Rapidão, menos preciso)
    # 'yolov8m.pt' = Medium (Equilíbrio perfeito pra sua RTX 5060)
    print("Carregando modelo...")
    model = YOLO('yolov8m.pt')

    # 2. Treinar
    # data: TEM QUE SER O CAMINHO para o seu arquivo data.yaml
    # epochs: 100 rodadas (se demorar muito, pode parar antes)
    # imgsz: 640 é o padrão
    # device: 0 (Isso força o uso da sua NVIDIA RTX)
    print("Iniciando treinamento na CPU (Modo de Compatibilidade)...")
    model.train(
        data=r'C:\Users\migue\OneDrive\Documentos\deploy\Plataforma-de-Varredura-Geoespacial\dataset_solar\data.yaml',
        epochs=100,  # Pode voltar pra 100, a GPU aguenta!
        imgsz=640,
        device=0,  # <--- AQUI! Volte para 0 (Zero) para usar a RTX 2050
        batch=8,  # Mantenha 8 ou 16 (A 2050 tem 4GB de VRAM, 16 pode estourar)
        name='modelo_hackathon_gpu'
    )

if __name__ == '__main__':
    main()