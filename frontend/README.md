# Cars Prediction ML Frontend

React + TypeScript + Vite frontend for the car price prediction API.

## Tech Stack

- React 18
- TypeScript
- Vite
- Tailwind CSS
- React Router v6
- Axios

## Project Structure

```
frontend/
├── src/
│   ├── api/client.ts          # Axios instance with auth interceptors
│   ├── components/
│   │   └── PredictionForm.tsx # Form with all car feature inputs
│   ├── context/AuthContext.tsx # Auth state (login, logout, tokens)
│   ├── pages/
│   │   ├── Login.tsx          # Login page
│   │   ├── Predict.tsx        # Prediction form page (protected)
│   │   └── ProtectedRoute.tsx # Route guard for authenticated pages
│   ├── types/api.ts           # TypeScript types for API requests/responses
│   ├── config/features.ts     # Feature options (brands, models, fuel types, etc.)
│   ├── App.tsx                # Routes
│   └── main.tsx               # Entry point
├── nginx.conf                 # Nginx config for SPA routing
├── Dockerfile                 # Multi-stage build (Node builder -> Nginx)
└── package.json
```

## Run Locally

```bash
cd frontend
npm install
npm run dev
```

Runs at `http://localhost:5173` (proxies API calls to `http://localhost:8000` via Vite config).

## Build for Production

```bash
npm run build
```

Outputs to `dist/` - served by Nginx in Docker.

## Docker

```bash
# From repository root
docker build -t cars-prediction-frontend -f frontend/Dockerfile .
docker run -p 3000:80 cars-prediction-frontend
```

Or via docker-compose (includes API, PostgreSQL, MinIO):

```bash
docker compose -f docker-compose.yml up -d frontend
```

## Features

- **Login page**: Username/password authentication against `/auth/login`
- **JWT tokens**: Access + refresh tokens stored in memory, auto-refreshed on 401
- **Prediction form**: All categorical fields (brand, model, gearbox, fuel type) as dropdowns; numeric fields (mileage, engine capacity, year) as inputs
- **Results display**: Shows predicted price in PLN
- **Logout**: Clears tokens and redirects to login

## Configuration

- `VITE_API_URL` - API base URL (default: `http://localhost:8000`)
- Set via `.env` or docker-compose `environment` section

## Pages

| Route | Auth | Description |
|-------|------|-------------|
| `/login` | Public | Login form |
| `/predict` | Required | Car feature form + prediction result |
| `/` | Redirects to `/predict` | |