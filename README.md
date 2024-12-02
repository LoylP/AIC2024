# ArtemisSearch: A Multimodal Search Engine for Efficient Video Log-Life Event Retrieval Using Time-Segmented Queries and Vision Transformer-based Feature Extraction

## Overview
This text-based multimodal search engine is specifically designed to retrieve log life events within videos. The engine is equipped with advanced search capabilities and can extract keyframes based on a lengthy series query. Additionally, it enables the identification of words within the images contained in the videos. Our motivation is driven by the desire to learn, innovate, and make a difference.

![](/static/image/UI.png)
---

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Installation](#installation)
- [Poster](#poster)

## Introduction

**ArtemisSearch**, a text-based multimodal search engine designed for temporal event retrieval in videos. In the proposed system, an efficient algorithm for Content-Based Image Retrieval (CBIR) using **ViT-H/14** and **BEiT3** for feature extraction and an opensource vector database, **Milvus**. To further enhance the model’s performance, we propose using **EasyOCR** for Optical Character Recognition (OCR)-based queries on text in images or videos.

![](/static/image/flow.png)

## Features
### 1. Video Frame Extraction: 
- We extract frames from videos in our dataset at a predefined interval (e.g., every second) to ensure we capture a representative sample of the video’s content.

### 2. Feature Extraction: 
- Each extracted frame is fed into the CLIP-ViT-H/14 or BEiT3 model, generating a high-dimensional feature vector that captures the visual semantics of the frame.
### 3. Embedding Storage:
- The resulting feature vectors are stored in a Milvus database for efficient retrieval during the query phase.

### 4. Full-text Search/ Search with image: 
- This feature allows for searching keyframes across a lengthy sentence. Furthermore, our engine supports breaking down long-series queries into individual sentences, which is very userfull for retrieval.

### 5. OCR Filter: Utilizing this enables users to extract events from the text in the keyframes.

- Besides, users have the ability to view the video associated with selected keyframes. This feature also enables users to observe the keyframes both before and after the chosen event, enhancing the overall viewing experience.

![](/static/image/show.png)

## Technologies Used
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![React](https://img.shields.io/badge/react-%2320232a.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Elasticsearch](https://img.shields.io/badge/elasticsearch-%230377CC.svg?style=for-the-badge&logo=elasticsearch&logoColor=white)


## Installation
```bash
# 1. Clone the respority:
git clone https://github.com/LoylP/AIC2024

# 2. Install dependencies:
pip install -r requirement.txt

# 3. Start the search engine:
unicorn serve:app -–reload

# 4. Start the frontend app:
npm run start
```

## Poster

![](/static/image/poster.png)