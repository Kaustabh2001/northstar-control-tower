# Local development

## Fast path

```powershell
.\.venv\Scripts\python.exe -m uvicorn control_plane_api.main:app --app-dir services/control-plane-api/src --reload
```

In a second terminal:

```powershell
Set-Location apps/portal-web
npm run dev
```

The API is available at `http://localhost:8000` and its OpenAPI documentation at
`http://localhost:8000/docs`. The portal is available at
`http://localhost:5173`.

## Local Docker profile

```powershell
docker compose -f infra/compose/docker-compose.yml up --build
```

This slice starts PostgreSQL, the FastAPI control plane and the React portal.
Keycloak, ContextForge and observability remain separate future profiles so the
initial development footprint stays small.
