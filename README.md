# KisanMind — Expert AI Farming Assistant 🌾

KisanMind is a production-ready AI farming assistant designed specifically for Indian farmers. It operates with low connectivity, speaks Telugu, Hindi, and English, and is powered by Google Gemini 1.5 Flash.

## Core Features
1. **Pesticides & Crop Management**: Knowledge of regional crops (Paddy, Cotton, Chilli, Tomato, etc.) and safe dosages.
2. **Offline-First PWA Support**: Fallback templates for crop diseases and AP/Telangana schemes when internet is unavailable.
3. **Voice Mode**: Integrates Web Speech API for hands-free queries.
4. **Mandi Prices & Weather forecasts**: Live lookup of crop prices and precipitation data.
5. **Google OAuth 2.0 & Supabase**: Persistent chat sync and profile configuration.

## Project Structure
```
├── backend/            # FastAPI (Python 3.11)
├── frontend/           # React 18 + Vite + TailwindCSS
├── .env.example        # Environment variables templates
├── docker-compose.yml  # Local multi-service orchestration
└── README.md
```

## Quick Start (Docker)

To launch the backend and frontend using Docker, simply run:
```bash
docker-compose up --build
```
- Frontend will be available at `http://localhost:5173`
- Backend API will be available at `http://localhost:8000`

---

## Local Development Setup

### Backend Setup
1. Navigate to the backend folder:
   ```bash
   cd backend
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the development server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

### Frontend Setup
1. Navigate to the frontend folder:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start Vite dev server:
   ```bash
   npm run dev
   ```

---
*KisanMind — Built for farmers, by AI. జై కిసాన్! 🌾*
