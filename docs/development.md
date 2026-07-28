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

Its Streamable HTTP endpoint is available only on the Compose network at
`http://fixture-mcp:8000/mcp`. The control plane uses MCP initialize and
list-tools requests to discover the live protocol version, server identity and
input schemas shown on the MCP asset detail page. The fixture tools are
deterministic and never mutate a real identity system. No host port is
published, preventing workflows or users from bypassing the gateway.

## Control-plane demonstrations

The seeded local database now includes:

- evidence-gated governance approvals for every registered asset type;
- four workflow runs covering running, waiting-for-human, failed and completed
  states, with persistent stages, correlations and trace events;
- one review task that can be approved or rejected by a reviewer;
- a default-deny MCP gateway policy that evaluates identity, workflow run,
  stage, tool allowlist and approved human evidence before forwarding a call.

The Runtime and Security pages use deterministic records while remaining
compatible with future LangGraph checkpoints, A2A task IDs and Langfuse trace
IDs. The MCP fixture must still be reached through the control-plane gateway
for governed invocations; its host port exists for protocol development and
health testing only.

The imported local accounts all use password `northstar`:

- `admin@northstar.local` — viewer, operator, reviewer and admin
- `operator@northstar.local` — viewer and operator
- `reviewer@northstar.local` — viewer and reviewer

These credentials are development fixtures and must not be used outside the
local profile. ContextForge and observability remain separate future profiles
so the development footprint stays controlled.
