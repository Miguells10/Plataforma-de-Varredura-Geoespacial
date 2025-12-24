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
        data=r"C:\Users\Miguel Lucas\PycharmProjects\radix\dataset_solar\data.yaml",  # Seu caminho absoluto
        epochs=50,  # Reduzi para 50 pra acabar rápido
        imgsz=640,
        device='cpu',  # <--- O SEGREDO ESTÁ AQUI. Mude para 'cpu' (com aspas)
        batch=8,  # Batch menor para não travar o PC
        name='modelo_hackathon_cpu'
    )

if __name__ == '__main__':
    main()