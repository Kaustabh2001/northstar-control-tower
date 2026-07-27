# ServiceOps AI Control Plane — exact implementation blueprint

## Decision

Build one closed-loop workflow: **Ticket-to-Verified-Resolution**.

The system receives an IT support ticket, protects sensitive data, classifies
and routes it, retrieves approved evidence, proposes a diagnosis and response,
gates risky actions through a human, writes the result back to the ticket system,
and learns only from approved outcomes.

This is not a general chatbot. The ticket lifecycle is the product spine; every
agent, model, tool, metric, and pipeline exists to improve that lifecycle.

## Local-first technology decisions

| Concern | Selected technology | Exact role |
|---|---|---|
| End-user and operator UI | React, TypeScript, Vite, Material UI, TanStack Query | Ticket submission, AI evidence panel, approvals, evaluation dashboard |
| Application API | FastAPI, Pydantic, SQLAlchemy/Alembic | Canonical API, webhook intake, authorization enforcement, workflow facade |
| Ticket system of record | GLPI Community + MariaDB | Local Docker-hosted tickets, SLA fields, history, users and assets |
| Optional ticket adapter | Jira Cloud Free | Demo-only external adapter; not part of strict local deployment |
| Online workflow | LangGraph | Durable ticket state machine, branching, retries, human interrupts |
| Agent interoperability | Official A2A Python SDK | Every independently deployable agent exposes an Agent Card and A2A tasks |
| Tool interoperability | IBM ContextForge | Unified MCP/A2A/REST gateway, registry, auth, scopes, rate limits and audit |
| Identity | Keycloak + PostgreSQL | OIDC login, service identities, roles, short-lived tokens |
| App state and audit | PostgreSQL | Workflow checkpoints, outbox, decisions, evaluation and immutable audit references |
| Cache and async work | Redis + Celery | Semantic/result cache, locks, rate limits and background jobs |
| Retrieval | OpenSearch | BM25, vector k-NN, hybrid fusion, metadata filters and similar tickets |
| Embeddings/reranking | Sentence Transformers | Local embeddings and cross-encoder reranking |
| Local model gateway | LiteLLM Proxy | One OpenAI-compatible endpoint, routing, budgets and model metadata |
| Local generation | Ollama for development; vLLM for GPU deployment | Local instruct models without a SaaS dependency |
| Classical ML | scikit-learn, LightGBM, calibration | Queue/type/priority, confidence, abstention, drift and later SLA risk |
| ML experiment registry | MLflow + MinIO + PostgreSQL | Runs, metrics, datasets, model artefacts and promotion aliases |
| Data/ML pipelines | Dagster OSS | RAG ingestion, evaluation, retraining, drift and scheduled replay |
| LLM observability | Langfuse self-hosted | Traces, prompts, generations, scores, datasets and experiment comparison |
| Platform telemetry | OpenTelemetry Collector, Prometheus, Grafana, Loki, Tempo | Correlated metrics, logs and distributed traces |
| Edge routing | Traefik | Local TLS termination, routing and service exposure |
| Packaging | Docker Compose profiles | Reproducible local deployment with optional heavyweight profiles |

### Important product constraint

Jira Free is a cloud service. Atlassian's self-managed Jira Data Center is
commercial and time-limited for evaluation. Therefore GLPI Community is the
local system of record. Jira Cloud Free is supported only through an adapter.

GLPI's core application, API and webhook path can be hosted locally. Its
official Keycloak/OAuth SSO plugin requires a GLPI Network subscription, so the
free build uses Keycloak for the React app, APIs, agents and gateway while GLPI
keeps a separate local service identity. Paid GLPI SSO can be added later
without changing the workflow.

## Canonical ticket state

Every workflow run persists this state:

```text
ticket_id, workflow_id, trace_id, tenant_id, actor
raw_ticket_ref, normalized_ticket, pii_vault_ref
ticket_type, queue, priority, confidence, abstained
asset_context, requester_context, similar_ticket_ids
evidence[{document_id, chunk_id, score, version, citation}]
diagnosis, proposed_response, proposed_actions[]
risk_tier, policy_decisions[], approval
executed_actions[], final_response, outcome
model_versions, prompt_versions, token_usage, latency, compute_cost
```

Sensitive values are never copied into traces. The trace stores tokenized or
redacted fields plus a reference to the protected record.

## Online workflow

### 1. Intake

- Ticket enters through React or GLPI.
- A GLPI webhook calls FastAPI.
- FastAPI validates and converts it to a versioned `TicketEnvelope`.
- An idempotency key prevents duplicate runs.
- The event and an outbox record are committed atomically to PostgreSQL.

### 2. Privacy and deterministic safety

- Detect and tokenize email, phone, account, secret and organization-specific
  identifiers.
- Reject unsupported attachments and malware-scan accepted files.
- Apply deterministic emergency rules before any LLM call.
- Security incidents, privileged access and destructive change requests are
  immediately marked human-required.

### 3. Classical ML triage

- Predict queue and ticket type with a calibrated word/character TF-IDF linear
  classifier.
- Predict priority with LightGBM using text-class probabilities, tags, requester
  tier, asset criticality, outage scope and deterministic severity signals.
- Detect out-of-distribution tickets from calibrated confidence, entropy and
  embedding distance.
- Abstain instead of forcing a label when confidence is below the validated
  class-specific threshold.

This fast path handles routine routing without spending LLM compute. The LLM may
explain or refine uncertain predictions but may not silently override a
high-risk deterministic rule.

### 4. A2A agent workflow

LangGraph acts as the supervisor and A2A client. Each agent runs as a FastAPI/A2A
service and publishes `/.well-known/agent-card.json`.

| Agent | A2A skills | Output |
|---|---|---|
| Triage Agent | `classify_ticket`, `estimate_priority`, `explain_abstention` | Calibrated labels and reasons |
| Context Agent | `get_requester_context`, `get_asset_context`, `get_ticket_history` | Minimal authorized context |
| Retrieval Agent | `search_knowledge`, `find_similar_resolutions`, `verify_citations` | Ranked evidence bundle |
| Diagnosis Agent | `form_hypotheses`, `select_runbook`, `identify_missing_information` | Evidence-linked diagnosis |
| Resolution Agent | `draft_response`, `draft_resolution_plan`, `summarize_for_agent` | Cited response and action proposal |
| Governance Agent | `assess_risk`, `check_policy`, `set_approval_requirement` | Allow, require approval, or deny |
| Action Agent | `execute_approved_action`, `write_back_ticket`, `verify_result` | Tool receipts and rollback evidence |
| Evaluation Agent | `score_trace`, `compare_variants`, `detect_failure_pattern` | Offline evaluation records |

The agent card declares skills, input/output schemas, supported transports,
authentication and version. Keycloak client credentials identify services.
A2A task IDs, LangGraph run IDs and OpenTelemetry trace IDs are correlated.

### 5. MCP tools through one gateway

Agents never call GLPI, OpenSearch, Keycloak or runbooks directly. ContextForge
registers MCP servers and enforces scopes:

| MCP server | Tools | Default authority |
|---|---|---|
| `glpi-mcp` | get/search ticket, add note, assign, change priority, resolve | Read; writes gated |
| `knowledge-mcp` | hybrid search, fetch versioned chunk, list citations | Read-only |
| `cmdb-mcp` | asset, dependency and service-impact lookup | Read-only |
| `identity-mcp` | requester group/role lookup | Read-only, minimal claims |
| `telemetry-mcp` | query service health, metrics and recent alerts | Read-only |
| `runbook-mcp` | dry-run, execute allowlisted step, verify, rollback | Approval-bound |

Tool schemas are versioned. Tokens carry tenant, role and tool scopes. Gateway
policy rejects unregistered tools, excessive arguments, cross-tenant access and
write calls without an approval artefact.

### 6. Retrieval and response

- OpenSearch runs BM25 plus local vector search.
- Metadata filters enforce tenant, product, document status, confidentiality,
  validity dates and user entitlements.
- Reciprocal-rank fusion combines lexical and semantic results.
- A local cross-encoder reranks the top candidates.
- The response agent receives only the top evidence, not the entire corpus.
- Every factual operational claim must cite a retrieved document or be marked
  as a hypothesis.

### 7. Risk gate and human control

| Tier | Example | Behavior |
|---|---|---|
| Green | Read-only lookup, known FAQ, reversible low-impact action | May auto-draft; auto-execution only after policy validation |
| Amber | Account change, uncertain diagnosis, customer-impacting update | Human approval required |
| Red | Security, privileged access, destructive action, production change | No autonomous execution; mandatory specialist handoff |

The UI shows the model prediction, confidence, evidence, policy decision,
proposed action and expected effect. The reviewer can approve, edit, reject or
escalate. Every choice becomes a labeled feedback event.

### 8. Execution and closure

- Action Agent receives a signed, short-lived approval artefact.
- MCP Gateway executes only the approved tool and arguments.
- The action returns a receipt, result and rollback reference.
- Resolution Agent prepares the final response.
- GLPI receives the note, assignment/status update and audit correlation ID.
- Closure collects resolution code, human edits, first-contact resolution,
  reopen status, SLA result and optional CSAT.

## Offline learning pipelines

### Knowledge ingestion

Dagster sensor → source snapshot → malware/PII scan → parse → normalize →
semantic chunk → metadata enrich → embed → shadow OpenSearch index → retrieval
evaluation → human approval → atomic index alias promotion.

Only approved, current documents and approved historical resolutions enter the
production index. Held-out benchmark answers never enter it.

### Classical ML retraining

Dagster schedule/sensor → approved labels → point-in-time feature build →
grouped split → train candidate → calibrate → offline test → bias/error slices →
MLflow registration → human promotion → canary → rollback alias.

Retraining is triggered only when at least 200 new approved labels exist and
either a schedule or validated drift condition is met. Human edits are not
automatically treated as truth until the ticket is resolved and accepted.

### Continuous evaluation

Nightly frozen-set replay compares the current champion and candidate. A release
is blocked if routing macro-F1, critical miss rate, retrieval recall, grounded
answer score, policy compliance, latency or compute budget violates its gate.

## Before/after design without a legacy system

“Before” is a frozen, executable baseline—not an invented historical number.
Both variants run on the same immutable test tickets, model hardware, random
seed and measurement harness.

| Dimension | Before baseline | Optimized workflow |
|---|---|---|
| Routing | Majority/keyword rules, then TF-IDF benchmark | Calibrated ML, abstention and context |
| Retrieval | BM25 top-5 | Hybrid BM25/vector, filters and reranker |
| Response | One local model, fixed prompt, no retrieval | Evidence-limited RAG, citations, model routing and cache |
| Governance | Static forbidden-word checks | Deterministic policy, identity scopes, risk tiers and approval artefacts |
| Tool use | No execution | Allowlisted MCP tools with dry-run, approval and receipts |
| Observability | Request log and stopwatch | Langfuse plus correlated OTel traces, metrics and costs |

### Required metrics

- ML: macro-F1, balanced accuracy, per-class recall, top-2 recall, expected
  calibration error, selective accuracy and abstention coverage.
- Retrieval: Recall@5, MRR@10, nDCG@10 and citation precision.
- Generation: groundedness, answer relevance, unsupported-claim rate, citation
  correctness, human acceptance and normalized edit distance.
- Safety: PII leakage, unauthorized tool attempts blocked, unsafe-action rate,
  approval bypasses and audit completeness.
- Operations: p50/p95 latency, model calls, input/output tokens, cache hit rate,
  CPU/GPU seconds, energy estimate and failures/retries.
- Business pilot: time to route, first response, human minutes per ticket, MTTR,
  first-contact resolution, reopen rate, SLA breach and CSAT.

No business ROI is claimed from the public datasets. Business metrics begin when
the running GLPI pilot generates timestamps and human outcomes. Until then,
projected savings are shown separately from measured savings.

## Local compute-cost model

Local inference is not free. Report both resource units and a configurable
currency estimate:

```text
ticket_cost =
  GPU_seconds × GPU_hourly_amortization / 3600
  + CPU_seconds × CPU_hourly_amortization / 3600
  + energy_kWh × electricity_rate
  + allocated_storage_and_operations
```

Optimization levers are measured independently: ML fast path, small/large model
routing, semantic cache, prompt size, retrieval top-k, batching, quantization,
early exit and abstention. Langfuse records per-step token and latency data;
LiteLLM enforces budgets; Prometheus records hardware utilization.

## Docker deployment profiles

To remain laptop-hostable, do not force every enterprise component into one
always-on Compose file:

- `core`: React, FastAPI, PostgreSQL, Redis, LangGraph agents, ContextForge,
  Keycloak, OpenSearch, LiteLLM and Ollama.
- `itsm`: GLPI and MariaDB.
- `mlops`: Dagster, MLflow and MinIO.
- `observability`: Langfuse dependencies, OpenTelemetry Collector, Prometheus,
  Grafana, Loki and Tempo.
- `gpu`: vLLM and local embedding/reranking services.

Development can run `core + itsm`. Evaluation enables `mlops`; demo and release
validation enable `observability`. Production pins image digests, stores secrets
outside Compose, uses TLS, backup/restore tests and separate persistent volumes.

## Repository layout

```text
apps/
  web/                       React operator and approval console
services/
  api/                       FastAPI facade, webhook and audit APIs
agents/
  triage/ context/ retrieval/ diagnosis/
  resolution/ governance/ action/ evaluation/
mcp-servers/
  glpi/ knowledge/ cmdb/ identity/ telemetry/ runbook/
packages/
  contracts/                 TicketEnvelope, A2A artifacts, tool schemas
ml/
  training/ evaluation/ features/
pipelines/
  dagster/
infra/
  compose/ keycloak/ otel/ grafana/ opensearch/
data/
  README.md                  Provenance; raw and derived data ignored
docs/
  planning/
```

## Milestones and merge gates

1. **Data and contracts** — reproducible splits, schemas, dataset cards and
   baseline profiler. Gate: checksums, leakage tests and validation pass.
2. **Deterministic ticket path** — React → FastAPI → GLPI with Keycloak and
   audit/outbox. Gate: idempotent create/update and RBAC tests.
3. **ML triage** — calibrated queue/type/priority with abstention. Gate:
   reproducible MLflow run and minimum per-class thresholds.
4. **Grounded recommendation** — OpenSearch hybrid retrieval and cited drafts.
   Gate: frozen-set retrieval/generation results beat baseline.
5. **A2A/MCP control plane** — agent cards, ContextForge and read-only tools.
   Gate: contract, auth, tenant isolation and trace-correlation tests.
6. **Human-approved action** — risk tiers, approvals, safe runbook and rollback.
   Gate: no write without valid approval; complete audit receipt.
7. **Closed-loop learning** — Dagster ingestion/retraining and champion/candidate
   promotion. Gate: no leakage and automatic rollback.
8. **Enterprise demo** — observability, failure injection, backup/restore,
   security tests and before/after dashboard.

Each milestone is developed on a `codex/` feature branch and merged to `master`
only after its gate passes.

## Primary technical references

- A2A protocol and Agent Cards: <https://github.com/a2aproject/A2A>
- Official A2A Python SDK: <https://github.com/a2aproject/a2a-python>
- ContextForge gateway: <https://github.com/IBM/mcp-context-forge>
- OpenSearch hybrid search:
  <https://docs.opensearch.org/latest/vector-search/ai-search/hybrid-search/index/>
- Keycloak Docker:
  <https://www.keycloak.org/getting-started/getting-started-docker>
- GLPI Docker image: <https://hub.docker.com/r/glpi/glpi>
- GLPI API:
  <https://help.glpi-project.org/documentation/modules/configuration/general/api/restful-api-v2>
- Langfuse self-hosting:
  <https://langfuse.com/faq/all/self-hosting-langfuse>
