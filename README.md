# DocSanct – AI-Powered Redaction System

## 🚀 Overview
DocSanct automates redaction of sensitive information (text + visuals) from documents using Vision-Language Models (VLMs).  
It ensures privacy by default with AI-driven detection, metadata scrubbing, PDF flattening, and secure access controls.

## 📂 Repo Structure
- `frontend/` → React/Streamlit UI  
- `backend/` → FastAPI APIs  
- `ai/` → VLM-based redaction + sanitization  
- `batch/` → Celery + Redis batch processing  
- `docs/` → Architecture + API docs  

## 👥 Team Roles
- Frontend Developer → `frontend/`
- AI/ML Engineer → `ai/`,'docs/'
- Backend Engineer → `backend/`, `batch/`
- Batch Processing workr → Docs, reviews, merges

## ⚡ How to Run (Dev Mode)
```bash
# Backend setup
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend setup
cd frontend/react-app
npm install
npm start.
