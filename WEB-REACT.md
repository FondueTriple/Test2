React Frontend + Flask API
==========================

Overview
- Backend: Flask JSON API under `/api/...` implemented in `app_flask.py`.
- Frontend: React (Vite) app in `frontend/`.

Prerequisites
- Python 3.10+
- Node.js 18+ and npm

Backend (Flask)
1) Create/activate a virtualenv and install deps:

```bash
pip install -r requirements.txt
```

2) Run the API server:

```bash
python app_flask.py
```

The API lives at `http://127.0.0.1:5000/api/...`.

Frontend (React + Vite)
1) Install dependencies:

```bash
cd frontend
npm install
```

2) Start the dev server:

```bash
npm run dev
```

Open `http://127.0.0.1:5173`. The Vite dev server proxies `/api` to the Flask server.

Production Build
```bash
cd frontend
npm run build
cd ..
python app_flask.py
```

When `frontend/dist` exists, Flask serves the React build at `/` and keeps `/api/*` for the JSON API.

