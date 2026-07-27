# Local AI Governance Portal — product and backend blueprint

## Product boundary

The governance portal is the first product surface. It governs AI systems,
agentic workflow definitions, agents, models, prompts, datasets, knowledge
indexes, MCP servers and tools.
The employee access workflow will be onboarded later as the first governed AI
system.

The portal must remain useful before an LLM is connected. Inventory, ownership,
approvals, policy enforcement and runtime telemetry are ordinary application
capabilities. AI providers are replaceable runtime dependencies, not
prerequisites for the control plane.

## Personas and permissions

| Persona | Primary responsibilities |
|---|---|
| AI steward | Registers assets, reviews intended use, approves lifecycle transitions and suspends unsafe assets |
| Asset owner | Maintains metadata, evidence, dependencies, evaluations and deployment readiness |
| Risk reviewer | Assigns risk, checks controls, records exceptions and reviews policy evidence |
| Security analyst | Investigates unauthorized calls, prompt attacks, PII events and goal deviation |
| Platform operator | Operates gateways, model endpoints, observability and runtime health |
| Value analyst | Defines baselines, validates measurements and separates measured from projected value |
| Auditor | Reads immutable decisions, evidence, versions, approvals and runtime traces |

Keycloak roles:

```text
ai-steward
asset-owner
risk-reviewer
security-analyst
platform-operator
value-analyst
auditor
```

## Portal navigation

1. **Overview** — portfolio posture, urgent registry decisions, runtime health
   and security events.
2. **Inventory** — dependency-aware catalogue of systems, agents, models,
   agentic workflows, prompts, datasets, indexes, MCP servers and tools, with
   sidebar navigation for each asset type.
3. **Governance lifecycle** — onboarding, assessment, evaluation, registry
   approval, shadow, canary, production, suspension and retirement gates for a
   versioned asset. This is not the state of an executing workflow run.
4. **Runtime operations** — running workflow instances, current LangGraph node,
   progress, human-review interrupts, failures, retries, traces and MCP calls.
5. **Security** — access denials, prompt injection, PII, goal deviation and
   output/tool policy violations.

Backend architecture remains an engineering design artefact and is not a portal
navigation item.

## Backend service boundaries

### Web application

- React, TypeScript, Vite, Material UI and TanStack Query.
- OIDC login through Keycloak.
- Calls only the FastAPI control-plane API.
- Uses server-sent events or WebSockets for operational updates.

### Control-plane API

- FastAPI, Pydantic, SQLAlchemy and Alembic.
- Authoritative APIs for assets, relationships, lifecycle, controls, approvals,
  workflow runs and dashboard read models.
- Enforces tenant, role and object-level authorization.
- Writes a transactional outbox alongside every important state transition.

### Policy decision point

- Open Policy Agent for deterministic authorization and deployment gates.
- Inputs: actor, asset, lifecycle transition, risk, evidence, environment,
  requested MCP scope and approval artefact.
- Outputs: allow, deny or require approval with machine-readable reasons.
- Policies are versioned in Git and the evaluated version is stored with each
  decision.

### Discovery and reconciliation

- Dagster jobs reconcile Agent Cards, ContextForge, MLflow, Langfuse, Git,
  Keycloak and OpenSearch with the portal inventory.
- New assets enter as `discovered`.
- Changed versions create drift findings rather than silently overwriting
  approved records.
- Missing or unapproved runtime assets can be quarantined at the gateway.

### Runtime enforcement

- ContextForge is the unified MCP/A2A/REST gateway.
- Keycloak gives every service a short-lived identity.
- The gateway checks managed status, environment, agent identity, tool scope,
  rate limit and approval artefact before forwarding a call.
- Write tools require a request-bound capability; dashboard approval alone does
  not create a reusable privilege.

### Observability and evidence

- Langfuse stores prompts, generations, evaluation scores and AI traces.
- OpenTelemetry Collector correlates application, agent and gateway spans.
- Prometheus and Grafana provide metrics and alerts.
- Loki and Tempo provide logs and distributed traces.
- OpenSearch indexes searchable audit and security events.
- MinIO stores immutable evaluation reports and approval evidence.

### Model and data operations

- MLflow registers classical ML and LLM-related evaluation runs.
- LiteLLM presents one optional OpenAI-compatible provider interface.
- Ollama can supply a CPU-friendly development model; vLLM can be enabled for a
  GPU deployment.
- The portal runs without either service and reports the provider as
  `not configured`.

## Logical data model

```text
Tenant
  ├── User / Team / Role
  ├── AI System
  │     ├── Asset Version
  │     ├── Intended Use
  │     ├── Asset Relationship
  │     ├── Control Assessment
  │     ├── Evaluation Result
  │     ├── Approval
  │     └── Deployment
  ├── Agent
  ├── Model
  ├── Prompt
  ├── Dataset
  ├── Knowledge Index
  ├── MCP Server
  │     └── MCP Tool
  ├── Finding
  ├── Runtime Event / Trace Reference
  └── Workflow Run / Human Review
```

PostgreSQL stores governance truth and relationships. High-volume trace bodies
stay in their specialized stores; PostgreSQL holds stable references,
summaries, retention status and correlations.

## Principal APIs

```text
GET    /api/v1/dashboard
GET    /api/v1/assets
POST   /api/v1/assets
GET    /api/v1/assets/{asset_id}
POST   /api/v1/assets/{asset_id}/versions
POST   /api/v1/assets/{asset_id}/relationships
POST   /api/v1/assets/{asset_id}/transitions
POST   /api/v1/approvals/{approval_id}/decisions
GET    /api/v1/controls
POST   /api/v1/assessments
GET    /api/v1/runtime/traces
GET    /api/v1/security/events
GET    /api/v1/workflow-runs
GET    /api/v1/workflow-runs/{run_id}
POST   /api/v1/workflow-runs/{run_id}/decisions
POST   /api/v1/workflow-runs/{run_id}/retry
POST   /api/v1/discovery/runs
GET    /api/v1/providers
POST   /api/v1/providers/{provider_id}/test
```

## Asset lifecycle gates

| Transition | Required evidence |
|---|---|
| Discovered → Registered | Owner, purpose, source, version and dependency inventory |
| Registered → Assess | Intended/prohibited use, data classification and autonomy level |
| Assess → Build/Test | Risk tier, required controls and threat model |
| Build/Test → Steward review | Frozen evaluation, security tests, cost/latency budget and rollback plan |
| Steward review → Shadow | Steward and risk approval; read-only runtime scopes |
| Shadow → Canary | Shadow evidence passes; constrained user/traffic segment |
| Canary → Production | Canary SLO, quality, safety and business gates pass |
| Production → Suspended | Automated critical policy trigger or authorized human decision |
| Any managed stage → Retired | Impact assessment, dependency owners notified and evidence retained |

## No-model operating mode

Until an AI endpoint exists:

- The inventory and lifecycle are fully functional.
- Provider status is explicitly `not configured`; it is never shown as healthy.
- Mock runtime events are loaded from versioned JSON fixtures.
- Evaluation runs use deterministic classifiers, policy rules and stored
  responses.
- A simulator emits traces, MCP allow/deny events, incidents and value
  measurements.
- Provider-dependent controls are marked `not tested`, not passed.
- Deployment policy blocks any asset requiring generation from reaching
  production without a tested provider.

When an endpoint becomes available, implement one provider adapter:

```text
Governed workflow → LiteLLM-compatible interface → Ollama, vLLM or external API
```

No portal API, database schema or lifecycle model needs to change.

## Docker deployment

```text
portal:
  web, api, postgres, redis, keycloak, opa

gateway:
  contextforge

observability:
  langfuse, otel-collector, prometheus, grafana, loki, tempo, opensearch

mlops:
  dagster, mlflow, minio

models-optional:
  litellm, ollama or vllm
```

The first implementation profile is `portal`. The interactive HTML prototype
uses no backend and can be opened directly from disk.
