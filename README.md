# Northstar AI Governance Control Tower

Northstar is a local-first governance control plane for AI systems, agentic
workflows, A2A agents, traditional ML models, prompts, datasets, knowledge
indexes, and MCP servers.

The current milestone provides:

- Keycloak OIDC authentication and role-based access
- a versioned AI asset registry
- evidence-gated lifecycle approvals
- runtime workflow stages and human-review decisions
- a default-deny MCP gateway with invocation auditing
- PostgreSQL persistence managed through Alembic
- an explicitly non-final dummy workflow for integration testing

## Start the complete stack

Requirements:

- Docker Desktop
- Windows PowerShell 5.1 or PowerShell 7

From the repository root:

```powershell
.\start.ps1
```

The script builds and starts PostgreSQL, Keycloak, the FastAPI control plane,
the React portal, and the fixture MCP server. It waits for the user-facing
services to become ready and prints their addresses.

To reuse existing local images without rebuilding:

```powershell
.\start.ps1 -NoBuild
```

To open the portal automatically:

```powershell
.\start.ps1 -Open
```

Portal: <http://localhost:5173>

Demo administrator:

```text
admin@northstar.local
northstar
```

Additional users are defined in
[`infra/keycloak/northstar-realm.json`](infra/keycloak/northstar-realm.json).

## Stop the stack

```powershell
docker compose -f infra/compose/docker-compose.yml --profile tools down
```

The PostgreSQL named volume is retained. Add `-v` only when you intentionally
want to remove persisted local data.

## Repository layout

```text
apps/portal-web/                 React governance portal
services/control-plane-api/      FastAPI control plane and Alembic migrations
services/fixture-mcp/             Local MCP integration fixture
packages/contracts/               Shared domain contracts
infra/compose/                    Complete local Docker stack
infra/keycloak/                   Importable Keycloak realm
docs/                             Architecture and planning material
tests/                            API and governance enforcement tests
```

## Development status

The governance foundation is functional. The final business workflow is
intentionally undecided, and observability integrations such as Langfuse and
OpenTelemetry are not included in this milestone.

Local use-case reference material and downloaded/generated datasets remain
excluded through `.gitignore`.
