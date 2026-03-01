# Official Inference Interface for MyNRC-OCR Paper

## Overview
This repository hosts a lightweight UI used to validate the proprietary Dinger MMNRC OCR model API. It is designed for internal QA and partner handoffs so stakeholders can upload sample NRC images, observe the parsed fields, and review detection overlays without needing access to the underlying model artifacts or backend service code.

- **Purpose:** Quickly smoke-test the OCR pipeline end-to-end via HTTPS requests.
- **Scope:** UI-only. Model weights, preprocessing logic, and post-processing are maintained elsewhere.
- **Status:** Proprietary. Please keep distribution limited to authorized collaborators.

## Architecture Snapshot
**Model weights** (not included here).
**Inference backend** (not included here).
**This Streamlit tester** sends binary image payloads to the backend API and visualizes the response.

## Support
This project is proprietary to Dinger. For access requests or operational issues, contact the platform/ML engineering team through the usual internal channels.

Need to exercise the hosted tester? Reach out to the maintainer zaw.linn.htet03@gmail.com to obtain the current admin credentials, then use the Streamlit URL you were provided to log in and run evaluations. 
