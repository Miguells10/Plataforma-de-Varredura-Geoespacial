# ⚡ Radix Hackathon: Detector de Geração Distribuída (GD)

> **Solução de Inteligência Geoespacial para identificação de ativos de energia solar não cadastrados.**

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-red.svg)
![Status](https://img.shields.io/badge/Status-PoC%20Validada-success)

## 🎯 O Problema
A Geração Distribuída (painéis solares) cresce exponencialmente, mas as distribuidoras de energia têm dificuldade em mapear onde esses ativos estão instalados. Isso gera perdas comerciais e riscos técnicos para a rede.

## 💡 A Solução
Desenvolvemos um sistema automatizado que cruza dados públicos e imagens de satélite para auditar a rede elétrica. O sistema opera em três pilares:

1.  **Localização:** Mapeamento automático de subestações e edificações (OpenStreetMap).
2.  **Visualização:** Captura de imagens de satélite de alta resolução (Google Maps).
3.  **Inteligência:** Análise de imagem para detecção de padrões de painéis solares.

---

## 🚀 Diferenciais Técnicos (Validação PoC)

O projeto foi construído com foco em **resiliência** e **robustez** para operação em campo:

* **🛡️ Arquitetura "Anti-Falha":** O sistema possui *fallbacks* automáticos. Se as APIs externas (OSM/Google) caírem ou limitarem o acesso, o sistema gera dados sintéticos (mock) para garantir a continuidade da operação/demonstração.
* **📍 Grid Matemático Personalizado:** Desenvolvemos um algoritmo próprio de varredura geoespacial, eliminando dependências complexas (como H3) e garantindo compatibilidade total com Windows.
* **👁️ Visão Computacional Híbrida:** * Em imagens coloridas: Detecção por espectro de cor (Azul/Roxo).
    * Em imagens P&B (comuns em áreas rurais): Detecção por geometria e textura (Linhas/Grades) usando OpenCV.

---

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3.x
* **Interface:** Streamlit (Dashboard Interativo)
* **Mapas:** Folium & Leaflet
* **Dados:** * API ANEEL (Dados Abertos)
    * OpenStreetMap (Overpass API)
    * Google Static Maps API
* **Visão Computacional:** OpenCV (Atual), migrando para YOLOv8 (Roadmap).

---

## 📦 Como Rodar o Projeto

### Pré-requisitos
* Python instalado
* Chave de API do Google Maps (Opcional - o sistema roda em modo Mock sem ela)

### Instalação

1. Clone o repositório:
```bash
git clone [https://github.com/seu-usuario/radix-hackathon-gd.git](https://github.com/seu-usuario/radix-hackathon-gd.git)
cd radix-hackathon-gd