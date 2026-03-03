# myNRC-OCR: A Hybrid OCR Framework for Handwritten Myanmar NRCs

[![Conference](https://img.shields.io/badge/Accepted-JCSSE2026-success)](#) 

This repository contains the official reproducibility code and resources for the paper **"myNRC-OCR: A Hybrid OCR Framework for Handwritten Myanmar NRCs Integrating YOLOv8, Tesseract LSTM, TrOCR, and Post-OCR Correction"**. 

Accurate OCR for Myanmar's National Registration Cards (NRCs) is essential for digital KYC but remains challenging due to complex script orthography, handwritten entries, and low-resource data. This project proposes an end-to-end framework integrating object detection, multi-model recognition, and a 3-tier linguistic post-OCR correction module.

## Repository Contents

To support partial reproducibility and foster ongoing research in low-resource OCR, we have provided the following core pipeline notebooks:

* **`preprocessing.ipynb`**: Demonstrates the image and text preparation pipeline. This includes the logic for OpenCV-based image cleaning (Otsu thresholding, morphological operations), label normalization using `unicodedata` and `regex` (standardizing to Unicode NFC, stripping zero-width characters), and spatial/photometric data augmentations via Albumentations.
* **`train_public.ipynb`**: Contains the Hugging Face `Seq2SeqTrainer` configuration for fine-tuning the TrOCR model. This notebook includes the exact model architecture (ViT encoder + SEA-LION BERT decoder) and hyperparameters described in Section III.B of our paper (e.g., FP16 mixed-precision, gradient accumulation of 4, 30 epochs, 1e-5 learning rate). 

## Dataset & Privacy Notice

Due to commercial licensing constraints with Dinger Research and stringent regional data privacy regulations regarding National Registration Cards, the complete private NRC dataset and the fine-tuned model weights remain proprietary. 

To enable researchers to test the preprocessing and training pipelines, we are providing a **Synthetic Sample Dataset** hosted on Hugging Face: https://huggingface.co/datasets/PyaeLinn/myNRC-OCR_Sample-Dataset

This synthetic dataset mimics the statistical distribution, morphological complexity, and background artifacts of the original data without exposing any real Personally Identifiable Information (PII) or violating user consent.

*Note: In `sanitized_training.ipynb`, proprietary database connectors and internal MLOps tracking hooks have been removed to comply with company security policies. The core machine learning logic remains fully intact.*

## Live Demonstration

A deployed version of the myNRC-OCR system is accessible via our frontend API wrapper at: **https://dingerkyc.streamlit.app/**

*(Note: Due to KYC data privacy regulations, the live demo is access-controlled. Credentials for academic verification or testing purposes may be requested by contacting the corresponding author.)*

## Support
This project is proprietary to Dinger. For access requests or operational issues, contact the platform/ML engineering team through the usual internal channels.

Reach out to the maintainer zaw.linn.htet03@gmail.com to obtain the current admin credentials, then use the Streamlit URL you were provided to log in and run evaluations. 
