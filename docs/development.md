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
`http://localhost:5173`. Direct Python runs use fixture authentication by
default; local clients send `Authorization: Bearer fixture-admin`.

## Local Docker profile

```powershell
docker compose -f infra/compose/docker-compose.yml up --build
```

This slice starts Keycloak, PostgreSQL, the FastAPI control plane and the React
portal. Keycloak is available at `http://localhost:8080`.

Add the standards-based local MCP tool service with the optional `tools`
profile:

```powershell
docker compose -f infra/compose/docker-compose.yml --profile tools up --build
```

Its Streamable HTTP endpoint is `http://localhost:8090/mcp`. The control plane
uses MCP initialize and list-tools requests to discover the live protocol
version, server identity and input schemas shown on the MCP asset detail page.
The fixture tools are deterministic and never mutate a real identity system.

The imported local accounts all use password `northstar`:

- `admin@northstar.local` — viewer, operator, reviewer and admin
- `operator@northstar.local` — viewer and operator
- `reviewer@northstar.local` — viewer and reviewer

These credentials are development fixtures and must not be used outside the
local profile. ContextForge and observability remain separate future profiles
so the development footprint stays controlled.
