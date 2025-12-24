# 🛰️ Plataforma de Varredura Geoespacial (PVG)
> **Solução de Inteligência Artificial para Detecção e Auditoria de Ativos de Energia Solar (Geração Distribuída).**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![YOLOv8](https://img.shields.io/badge/Model-YOLOv8-purple.svg)
![PyTorch](https://img.shields.io/badge/Framework-PyTorch-orange.svg)
![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-red.svg)
![Status](https://img.shields.io/badge/Status-MVP%20Validado-success)

## 🎯 O Desafio
O crescimento não planejado da Geração Distribuída (GD) cria "pontos cegos" na rede elétrica. As distribuidoras enfrentam dificuldades em auditar onde estão os painéis solares, resultando em perdas comerciais e desbalanceamento de carga nas subestações.

## 🔄 Evolução da Arquitetura (Devlog)

Este projeto foi desenvolvido em ciclos iterativos durante o Hackathon da Radix, evoluindo de uma solução heurística para um modelo de Deep Learning robusto.

### 📅 Fase 1: Prototipagem e Geoprocessamento (v0.1)
Nesta etapa inicial, o foco foi a **infraestrutura espacial** e a visualização de dados.
* **Mapeamento de Subestações:** Utilização de dados do OpenStreetMap (OSM) para localizar subestações de energia.
* **Limitação:** A detecção visual inicial (baseada em OpenCV/Filtros de Cor) provou-se ineficaz contra telhados de diferentes cores e condições de iluminação variáveis em imagens de satélite.

### 🧠 Fase 2: Visão Computacional Avançada (v0.2 - Atual)
Para superar as limitações da v0.1, migramos para uma abordagem baseada em **Redes Neurais Convolucionais (CNNs)**.
* **Dataset Customizado:** Coleta manual e anotação de imagens de satélite de Aracaju/SE e do Rio de Janeiro/RJ utilizando **Roboflow**.
* **Segmentação Assistida (SAM):** Uso do *Segment Anything Model* para garantir *bounding boxes* precisas em painéis irregulares.
* **Modelo:** Treinamento de um modelo **YOLOv8 (You Only Look Once)**, otimizado para inferência em tempo real.
* **Hardware:** Treinamento realizado via aceleração GPU (NVIDIA RTX/CUDA), garantindo convergência rápida e alta precisão (mAP).

---

## ⚙️ A Lógica de Classificação (Heurística de Área)

Durante os testes de validação, identificamos que o modelo de detecção (YOLO) tende a agrupar painéis adjacentes em uma única *bounding box* (cluster). Isso tornava a contagem simples de caixas ineficaz: **3 caixas poderiam representar 3 painéis (Residência) ou 3 arrays gigantes com 50 painéis cada (Indústria).**

Para resolver isso, implementamos um algoritmo de **Estimativa por Densidade de Área**:

1.  **Cálculo Geométrico:** O sistema extrai as coordenadas `(x1, y1, x2, y2)` de cada detecção e calcula a área total em pixels ocupada por ativos solares na imagem.
2.  **Normalização:** Dividimos a área total por uma constante calibrada (`AREA_MEDIA_PAINEL_PX`), que representa a área média de um painel padrão na resolução do satélite (GSD).
3.  **Classificação:** O número estimado de painéis define a categoria.

```python

# Pseudo-código da Lógica Final
def classificar_imovel(deteccoes):
    area_total_pixels = sum([box.width * box.height for box in deteccoes])
    
    # Estimativa baseada na área ocupada, corrigindo o efeito de agrupamento do YOLO
    paineis_estimados = area_total_pixels / AREA_MEDIA_UNITARIA_PX
    
    if paineis_estimados > 40:
        return "🏭 INDÚSTRIA/COMÉRCIO (Alta Geração)"
    elif paineis_estimados > 0:
        return "🏠 RESIDENCIAL (Microgeração)"
    else:
        return "❌ Sem Geração Distribuída"
```

Essa abordagem garante velocidade de processamento e simplifica a manutenção do modelo.

## 🛠️ Stack Tecnológico

### 🧠 Core & IA

* **Ultralytics YOLOv8:** Detecção de objetos SOTA (State of the Art).
* **PyTorch (CUDA):** Backend de processamento tensorial.
* **Roboflow:** Gestão de Dataset e versionamento de imagens.

### 🗺️ Geoespacial & Matemática

* **Scipy (Voronoi):** Cálculo de áreas de influência de subestações.
* **Folium / Leaflet:** Renderização de mapas interativos.
* **OSMnx:** Extração de dados viários e de infraestrutura.

### 💻 Interface

* **Streamlit:** Dashboard interativo para visualização dos resultados em tempo real.


## 📊 Performance e Métricas

O modelo foi validado em cenários urbanos reais de Aracaju, demonstrando capacidade de generalização para:

* ✅ Painéis em telhados coloniais (vermelhos/laranjas).
* ✅ Painéis em telhados de fibrocimento (cinzas).
* ✅ Usinas de solo e topos de prédios comerciais.


## 📦 Como Rodar o Projeto

### Pré-requisitos

* Python 3.10+
* Placa de Vídeo NVIDIA (Recomendado para treino, opcional para inferência)

### Instalação

1. Clone o repositório:

```bash
git clone [https://github.com/seu-usuario/radix-hackathon.git](https://github.com/seu-usuario/radix-hackathon.git)
cd radix-hackathon

```

2. Instale as dependências:

```bash
pip install -r requirements.txt

```

3. Instale o PyTorch (Versão compatível com seu Hardware):

> *Verifique em [pytorch.org*](https://pytorch.org/)

4. Execute o Dashboard:

```bash
streamlit run app.py

```

### Estrutura de Pastas

```
radix/
├── .env                    # Variáveis de ambiente 
├── .gitignore              
├── README.md
├── requirements.txt
├── data/                   # Dados brutos e datasets
│   └── dataset_solar/
├── models/                 # Todos os arquivos .pt (v8m, v11n, custom)
│   ├── solar_v1.pt
│   └── yolo11n.pt
├── runs/                   # Saídas do YOLO (Ignorar no git)
├── scripts/                # Scripts de automação e treinamento
│   └── train_model.py      # Antigo src/training/treino.py
├── src/                    # Apenas código da aplicação
│   ├── __init__.py
│   ├── app.py              # Ponto de entrada
│   ├── config.py           # Gerenciamento de configurações
│   ├── services/           # Lógica de negócios e APIs
│   ├── ui/                 # Interface gráfica
│   └── utils/              # Funções auxiliares
└── tests/                  
    ├── __init__.py
    ├── test_processing.py
    └── test_services.py

```




