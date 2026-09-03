# Enterprise Knowledge Graph and Retrieval Architecture

## Purpose and status

This is the detailed working context for any agent helping design or implement the enterprise knowledge system. It combines:

1. the original knowledge-graph model covering application/infrastructure, code/deployment and operations; and
2. the retrieval model covering exact search, BM25, embeddings, graph-scoped RAG, reranking, MCP exposure and hypothesis-driven issue resolution.

The companion HTML is deliberately an executive presentation. This Markdown is the detailed source of context, constraints, accepted decisions, ambiguities and implementation logic.

This remains a working design. A node type, relationship, tool or technology mentioned here is not automatically a final commitment. Preserve the distinction between **decided direction**, **candidate design**, **something to measure** and **unknown source reality**.

---

## 1. What we are trying to achieve

The target is not simply a knowledge graph and not simply a RAG system. It is an **externalized enterprise troubleshooting memory and investigation space** that lets an issue-resolution agent behave like an experienced human resolver.

A human resolver typically:

- identifies the affected application or user capability;
- understands components and dependencies;
- checks deployments and configuration changes;
- searches similar historical incidents;
- reads work notes, runbooks and resolutions;
- locates relevant repositories, files or functions;
- reconstructs the exact version and configuration at incident time;
- forms several hypotheses;
- gathers supporting and contradicting evidence;
- eliminates weak explanations and deepens promising ones;
- returns a likely cause, confidence, evidence and next action.

The knowledge system should make this process explicit and navigable.

Core mental model:

- **Knowledge graph:** the agent's navigable model of the enterprise.
- **Search/RAG:** the evidence-finding mechanism.
- **Agent:** the investigation/search algorithm.
- **Historical incidents:** operational experience.
- **Graph relationships:** possible investigation paths.
- **MCP:** governed access to retrieval capabilities.

The agent can inspect more possibilities than a human, but should not blindly brute-force the graph. It should perform bounded hypothesis search: expand useful branches, retrieve evidence, update confidence, discard weak branches and stop when evidence or budget is sufficient.

---

## 2. Enterprise source posture

### 2.1 Backstage — maintained backbone

Backstage is maintained and should initially anchor application identity, ownership and broad repository scope.

Expected useful entities and fields:

- Domain;
- System/Application;
- Component;
- API;
- Resource;
- Group/Team;
- stable entity reference;
- `kind`;
- `spec.type`;
- ownership;
- repository links;
- declared relations such as `hasPart`, `partOf`, `ownerOf`, `ownedBy`, `providesApi`, `consumesApi` and `dependsOn` where populated.

Backstage tells us which catalog objects exist and who owns them. It may not explain what each component actually does in business or incident language.

### 2.2 ServiceNow ITSM — maintained operational history

Incidents and changes are maintained and should form the operational-history source.

Potential knowledge:

- incident/change identity;
- description, status, severity and timestamps;
- work notes/comments;
- explicit incident-change links;
- resolution notes;
- affected-service fields;
- service, host, error and configuration mentions;
- timeline and state changes.

The completeness of affected-application fields, root-cause fields, change links and resolution quality must be measured from real samples.

### 2.3 CMDB/CSDM — exists but low trust

CMDB exists but is not maintained. Initial rules:

- do not use it as canonical topology;
- do not let it override maintained Backstage relationships;
- retain it only as lower-trust evidence if useful;
- attach source and confidence to CMDB-derived assertions;
- reconsider only after a data-quality assessment.

### 2.4 Knowledge that must be constructed

- business/user capabilities such as Login or Payment Processing;
- semantic descriptions of systems and components;
- vocabulary linking incident language to capabilities and components;
- exact component-to-repository/file/symbol mappings;
- endpoint-to-handler mappings;
- configuration-to-code/deployment relationships;
- incident-to-application/component/capability mappings;
- cross-layer relationships;
- deployment/configuration snapshots at time T;
- search representations and embeddings.

### 2.5 Unknown access paths / black boxes

- logs;
- metrics and alerts;
- runtime topology;
- deployment state;
- effective environment configuration;
- feature flags;
- infrastructure state;
- secret references/metadata;
- cross-source ACL normalization.

Treat these as unresolved until source discovery establishes access, ownership, security and quality.

---

## 3. Three knowledge dimensions, one reasoning layer

The dimensions may live in one Neo4j database, but they remain conceptually separate and independently useful.

### 3.1 Application / infrastructure graph — what the system is

Candidate nodes:

- Domain;
- System/Application;
- Capability;
- Component;
- API;
- Endpoint;
- Resource;
- Team/Group.

Backstage entities and relations should retain their entity refs and provenance.

#### Constructed Capability layer

Capabilities matter because incidents use human language rather than catalog names.

Example mapping:

```text
“users cannot sign in after OTP”
→ Capability: Login / Authentication
→ Component: authentication-api
→ Resource: identity-db
→ Endpoint: POST /login
```

Example semantic profile:

```yaml
entity_ref: component:default/authentication-api
kind: Component
spec_type: service
owner: group:default/identity-platform
summary: >
  Handles interactive authentication after OTP, credential validation,
  token/session creation and calls to identity services.
capabilities: [Login, Authentication, Token issuance]
endpoints: [POST /login, POST /token]
incident_language: [login, sign in, auth, token, credential, session, OTP]
evidence: [Backstage, API spec, code routes, README/ADR, historical mappings]
```

`entity_ref`, `kind`, `spec.type` and owner may be authoritative Backstage fields. Summary, capability and incident-language fields are constructed and confidence-scored.

Never trust one source alone. Names, comments and LLM summaries are evidence; validated semantic profiles become incident-routing surfaces.

Pilot questions:

- Which Backstage kinds are actually populated?
- Are Domain and System used consistently?
- Are repositories linked at System or Component level?
- How complete is `dependsOn`?
- Where are API specifications referenced?
- Can Backstage entity refs be canonical graph IDs?

### 3.2 Code/deployment graph — how it is implemented and running

Candidate nodes:

- Repository;
- Directory/Module;
- File;
- Class;
- Function/Symbol;
- ConfigKey;
- Commit;
- Pipeline/BuildRun;
- BuildArtifact;
- Deployment;
- Environment;
- DeploymentSnapshot;
- ConfigSnapshot.

Candidate relationships:

- `CONTAINS`;
- `DECLARES`;
- `CALLS`;
- `IMPORTS`;
- `READS_CONFIG`;
- `MODIFIES`;
- `BUILT_FROM`;
- `PRODUCES`;
- `DEPLOYS`;
- `TARGETS`;
- `BINDS`;
- `REFERENCES`.

Cross-layer mappings:

- `(Component)-[:IMPLEMENTED_BY]->(Repository|File|Symbol)`;
- `(Capability)-[:IMPLEMENTED_BY]->(File|Class|Function)`;
- `(Endpoint)-[:HANDLED_BY]->(Function)`;
- `(Resource)-[:DECLARED_BY]->(File|ConfigKey)`;
- `(Component)-[:HAS_DEPLOYMENT_SNAPSHOT]->(DeploymentSnapshot)`.

#### Structure versus runtime state

Do not duplicate the code graph for PROD, UAT and DEV. Maintain one code/version lineage and overlay environment-specific snapshots.

```yaml
deployment_snapshot:
  component: authentication-api
  environment: PROD
  deployed_at: 2026-08-25T13:42:00
  commit: fa9182...
  artifact: authentication-api:4.8.2
  pipeline_run: 3381
  config_snapshot: cfg-891

config_snapshot:
  AUTH_SERVICE_URL: reference/value metadata
  TOKEN_TIMEOUT: 300
  REDIS_CLUSTER: redis-prod
  secrets: references only
```

This should answer: **What exact code and configuration were active in PROD when the incident occurred?**

Rules:

- deterministic evidence before semantic inference;
- use manifests, module IDs, service names, builds and deployment files first;
- treat LLM/semantic mapping as lower-confidence enrichment;
- never store plaintext secrets;
- store keys, references, redacted metadata and provenance;
- deep AST/call graphs may remain in a subordinate code index;
- the enterprise graph needs enough code granularity to route to the relevant repository, file or symbol.

### 3.3 Operations graph — what happened

Candidate nodes:

- Incident;
- Change;
- WorkNote/Comment;
- TimelineEvent;
- Resolution;
- later: Problem, Alert, KnownError.

Candidate relationships:

- `HAS_WORKNOTE`;
- `PART_OF`;
- `RELATED_TO_CHANGE`;
- `SYMPTOM_OBSERVED_ON`;
- `AFFECTS`;
- `ROOT_CAUSED_BY`;
- `TARGETS`;
- `MENTIONS`;
- `RESOLVED_BY`;
- `OCCURRED_DURING`.

#### Preserve operational meaning

Keep these separate:

1. symptom observed on — where failure is seen;
2. affected component — what is functionally impacted;
3. root-cause component/resource — what caused the failure.

Example:

```text
SYMPTOM_OBSERVED_ON → web-ui
AFFECTS             → authentication-api
ROOT_CAUSED_BY      → identity-db pool exhaustion
```

Collapsing them into one `AFFECTS` relationship removes the causal structure the agent needs.

#### Work notes are evidence, not topology

An extracted relationship must retain provenance:

```yaml
relationship: MENTIONS
source_node: servicenow-worknote:8841-3
target_node: resource:identity-db
assertion_type: EXTRACTED  # or INFERRED
confidence: 0.62
source_record: SN worknote 8841-3
evidence_text: retained and source-linked
```

### 3.4 Cross-layer relationship discipline

Avoid making `RELATED_TO` the default. Use a small vocabulary of typed edges such as:

- `AFFECTS`;
- `SYMPTOM_OBSERVED_ON`;
- `ROOT_CAUSED_BY`;
- `RELATED_TO_CHANGE`;
- `TARGETS`;
- `IMPLEMENTED_BY`;
- `HANDLED_BY`;
- `DECLARED_BY`;
- `HAS_DEPLOYMENT_SNAPSHOT`;
- `RESOLVED_BY`.

Define allowed relationship signatures:

```text
(source_type, relationship_type, target_type)
```

Examples:

```text
(Incident, AFFECTS, Component)
(Incident, ROOT_CAUSED_BY, Resource)
(Service, DEPENDS_ON, Service)
(Service, OWNED_BY, Team)
(Service, IMPLEMENTED_BY, Repository)
(Deployment, DEPLOYS, BuildArtifact)
(BuildArtifact, BUILT_FROM, Commit)
```

This signature catalog is the grammar of the enterprise graph. Validate it in Neo4j where available and in ingestion regardless.

### 3.5 Provenance, confidence and time

Every non-authoritative assertion should identify:

- source system and source record;
- extraction method;
- assertion type: authoritative, extracted, inferred, derived or human-validated;
- confidence;
- evidence locator/text;
- creation time;
- validity interval;
- pipeline/model version;
- human review state where relevant.

Store direct dependencies. Compute transitive impact during bounded investigation unless profiling later justifies a cached projection.

---

## 4. Knowledge construction pipeline

Graph construction and runtime retrieval are separate workstreams.

1. **Ingest sources:** connector/webhook/polling/CDC; retain source version and deletion state.
2. **Normalize:** canonical IDs, source IDs, schema, timestamps and ACL labels.
3. **Resolve entities:** aliases, naming variants, repository-component alignment and merge confidence.
4. **Extract/enrich:** capabilities, endpoints, code mappings, incident entities and evidence relations.
5. **Validate:** node types, relationship signatures, identifiers and property types; quarantine invalid assertions.
6. **Upsert graph:** canonical nodes, edges, provenance, confidence and time validity.
7. **Project to search:** searchable representations, chunks, BM25 fields and embeddings.
8. **Reconcile:** missing documents, orphan vectors, stale versions, deletions and ACL mismatches.

---

## 5. Graph and search representation contract

### 5.1 Accepted model

```text
Graph = canonical identity, structure, topology, provenance and time
Search index = lexical/semantic projection over graph nodes and passages
Retrieval service = planner and controlled executor
Agent = investigation strategy
```

Every search hit must return canonical `node_id` so retrieval can re-enter the graph.

### 5.2 Node, search document and chunk are different

- Component semantic profile: usually one representation.
- Incident: summary plus optional work-note/resolution chunks.
- Runbook: section chunks.
- File: file summary, symbol summaries or selected code chunks.
- Some graph nodes require no embedding.

Suggested search document:

```yaml
search_doc_id: unique indexed representation
node_id: canonical graph node
chunk_id: optional passage identity
representation_type: incident_summary | worknote | runbook_section | symbol_summary
node_type: Incident | Component | File
dimension: application | code | operations
source_system: backstage | servicenow | bitbucket
source_locator: exact record/section reference
source_version: source modification/version marker
timestamps: {created_at, updated_at}
status: intrinsic lifecycle status
language: en
acl_labels: mandatory security metadata
embedding_model: model identifier
embedding_version: version identifier
text_hash: change detector
```

### 5.3 Intrinsic metadata only by default

Keep:

- `node_id`, `chunk_id`;
- node type, dimension;
- source and timestamps;
- intrinsic status/environment;
- representation/embedding version;
- language;
- mandatory ACL labels.

Avoid canonical duplication of:

- parent application;
- grandparent domain;
- all service/dependency ancestors;
- copied ownership hierarchy;
- materialized transitive impact.

Those describe graph position and should normally come from traversal.

Reason: if Component X moves from Application A to B, update one graph edge. Do not update thousands of parental tags in vectors.

Selective denormalization is permitted only as a measured, rebuildable cache—not as ontology truth.

---

## 6. Retrieval modes

“Search” is a family of operations.

### Exact/structured lookup

For incident/change IDs, error codes, commit SHAs, artifact versions, environment names and config keys. Dense embeddings are not sufficient for `INC00123941`, `ORA-12541` or `payment-router-v23`.

### Graph traversal

For dependencies, ownership, membership, impact, deployments, related incidents/changes and implementation mappings. Bound by relation, direction, node type, depth, fan-out and time.

### Path search

For explaining how entities connect. Shortest path is not always most causally useful; score by edge meaning, time, confidence and authority.

### BM25/lexical search

For identifiers, exact error messages, rare terminology, stack traces, service names, code tokens and config keys.

### Dense semantic search

For symptoms, paraphrases, capability mapping, similar incidents and resolution narratives. Alone it is vulnerable to semantic collisions and generic distractors.

### Hybrid search

Expected default for mixed enterprise questions:

- exact lane;
- BM25 lane;
- dense lane;
- graph prior;
- rank fusion;
- reranking;
- diversity-aware context assembly.

### Temporal retrieval

For recent changes, deployment/configuration at time T and incident/change correlation. Never substitute current state for historical state.

---

## 7. Query planning

Extract:

- entities and candidate graph IDs;
- identifiers/error codes;
- intent and desired evidence;
- node/relationship types;
- environment and time window;
- caller ACL context;
- confidence for inferred constraints.

### Graph-first

Use when an entity is known:

```text
resolve entity
→ bounded graph traversal
→ candidate node IDs/scope token
→ hybrid search inside scope
→ rerank
→ graph expansion from top node IDs
```

### Search-first

Use for an ambiguous symptom:

```text
typed broad hybrid search
→ top incident/component IDs
→ enter graph
→ discover service/dependencies/changes
→ focused re-search
```

### Exact-first

Use when an identifier exists:

```text
exact lookup
→ canonical node
→ neighborhood/path retrieval
→ supporting semantic evidence
```

### Avoid destructive over-filtering

An LLM guess such as “Payments only” may exclude a relevant shared-dependency incident.

Use:

- a focused graph-scoped lane;
- a smaller broad-recall lane;
- fusion/reranking;
- progressive relaxation of low-confidence topical filters;
- never relax ACL filters.

---

## 8. Enterprise-scale strategy

Do not treat 10,000 vectors as a hard system ceiling. The real problem is retrieval quality as distractors grow.

Desired flow:

```text
100M physical representations
→ entity/intent/time understanding
→ graph-derived candidate universe
→ perhaps 5K–50K candidate nodes
→ BM25 + dense top 100
→ reranked 8–15 evidence items
→ graph expansion and agent context
```

Controls:

- default traversal depth 1–2;
- hard maximum depth;
- per-hop fan-out cap;
- relation/node-type allowlists;
- temporal bounds;
- candidate budget;
- per-node/per-source caps;
- deduplication;
- broad-recall quota;
- search/rerank limits;
- final context budget.

Use server-side opaque `scope_token` for large candidate sets rather than sending massive ID arrays through MCP.

Sharding, partitioning, caching and hierarchy denormalization should follow profiling. Intrinsic dimension/type may help partitioning, but must not destroy cross-domain recall.

---

## 9. Ranking and evidence assembly

Potential ranking signals:

- dense score;
- BM25/exact rank;
- graph distance;
- relationship-type prior;
- time/freshness;
- source authority;
- assertion confidence;
- environment/status match;
- human validation.

Do not assume scores from different engines are comparable. Use reciprocal-rank fusion, calibrated normalization or learned fusion.

Reranking determines which evidence deserves context space.

Prefer diversity: one incident summary, relevant work note, linked change, deployment snapshot, exact config diff and runbook section can be better than ten chunks from one incident.

Evidence result should include:

- `node_id`, optional `chunk_id`;
- node type/title;
- relevant passage;
- source locator/version/time;
- graph path summary;
- lexical/semantic/graph scorecard;
- authority/confidence;
- selection explanation;
- truncation state.

---

## 10. Agent hypothesis search

Loop:

1. Observe and characterize issue.
2. Generate plausible hypotheses.
3. Choose the highest-value evidence request.
4. Call tools.
5. Record supporting, contradicting and missing evidence.
6. Update confidence.
7. expand, retain or discard branches.
8. stop on evidence, risk or budget.
9. return conclusion, evidence, uncertainty and next action.

This resembles beam search. Keep perhaps three to five active branches rather than expanding everything.

```yaml
hypothesis_id: H-02
claim: deployment changed connection-pool behaviour
status: active
supporting_evidence: [incident:INC-9182, change:CHG-1092]
contradicting_evidence: [metric:db_cpu_normal]
missing_evidence: [deployment_snapshot:prod@incident_time]
confidence: 0.67
next_best_tool: get_deployment_at_time
budget_remaining: {tool_calls: 8, graph_depth: 2}
```

Do not silently rewrite hypotheses after contradiction. Preserve the trace.

Stop when:

- cause has sufficient evidence;
- safe validation/remediation is clear;
- no useful evidence is found;
- budget is exhausted;
- required data is unavailable;
- human escalation is required;
- action risk exceeds authority.

---

## 11. Knowledge MCP design

MCP and Cypher are not alternatives. MCP is the protocol; Cypher may run underneath.

```text
Agent
→ Knowledge MCP
→ Retrieval Service
→ Graph adapter / Search adapter / Reranker
→ Neo4j + search indexes
```

The agent controls investigation strategy. The retrieval service controls query execution.

### Reusable primitives

- `resolve_entity`;
- `get_node`;
- `traverse`;
- `find_paths`;
- `hybrid_search`;
- `retrieve_evidence`;
- `get_schema`.

Avoid hundreds of overly specific tools.

### Opinionated issue skills

- `map_incident_to_application`;
- `find_similar_incidents`;
- `get_dependency_paths`;
- `find_recent_changes`;
- `get_deployment_at_time`;
- `get_code_config_logs`;
- `get_component_code`;
- `search_code`.

These can compose primitives internally.

Example request:

```json
{
  "tool": "hybrid_search",
  "arguments": {
    "query": "connection exhaustion after deployment",
    "candidate_scope": "scope:payment-api:2hop",
    "node_types": ["Incident", "Problem"],
    "time_range": "P18M",
    "broad_recall_lane": true,
    "limit": 20
  }
}
```

Response:

```json
{
  "hits": [{
    "node_id": "incident:INC-9182",
    "chunk_id": "incident:INC-9182:resolution",
    "passage": "...",
    "lexical_rank": 4,
    "semantic_score": 0.91,
    "graph_distance": 2,
    "provenance": {"source_system": "ServiceNow", "source_record": "INC-9182"}
  }],
  "scope": {"candidate_count": 4217},
  "truncated": false,
  "retrieval_id": "ret_..."
}
```

### Raw-Cypher escape hatch

`execute_read_cypher` may exist only for specialist use with:

- read-only credentials;
- role restriction;
- timeout and row limits;
- audit;
- parameterization;
- no write procedures;
- procedure/function allowlist;
- query/depth protection.

Arbitrary Cypher is not the default production agent interface.

---

## 12. Security and governance

MCP is not the security boundary. Enforce each tool call in the retrieval service.

### Identity and ACL

- pass caller identity/context;
- normalize source ACLs into graph/search labels;
- enforce before returning results;
- avoid semantic post-filtering as the only control;
- ACL filters are hard and non-relaxable.

### Ontology governance

- allowlist node/relationship types;
- define endpoint signatures and direction;
- version the grammar;
- quarantine invalid writes;
- prevent vocabulary drift such as several synonyms of `AFFECTS`.

### Query budgets

- maximum depth, paths and fan-out;
- rows and timeout;
- candidate/search/rerank limits;
- total tool calls;
- context/token budget.

### Write isolation

The issue agent should initially have no direct graph writes. A separate ingestion/write service owns synchronization, inferred assertions, validation, ontology changes and feedback updates.

### Sensitive data

- no plaintext secrets;
- preserve source classification;
- field-level redaction;
- least-necessary code/config/log content;
- audit sensitive retrieval.

---

## 13. Freshness and synchronization

Structural and textual changes have different lifecycles.

### Structural change

Component X moves from Application A to B:

- update one graph relationship;
- do not rewrite parental hierarchy across vectors;
- invalidate any cached scopes;
- searchable text may remain unchanged.

### Textual change

Incident/runbook/profile changes:

- rebuild affected search document;
- rechunk if required;
- update BM25 fields;
- re-embed changed chunks;
- retain source version.

### Embedding-model change

- build versioned parallel index;
- evaluate;
- switch atomically;
- retain rollback;
- retire old version after verification.

### Deletion/authorization change

- remove or tombstone promptly in graph and search;
- stale embeddings must not remain retrievable;
- preserve audit per retention policy;
- reconcile ACL mismatches.

Define freshness SLOs by source/type: near real time for ACL/active incidents, minutes for deployments/changes where possible, scheduled repository/document reindexing and periodic full reconciliation.

---

## 14. End-to-end example

Issue: customers receive intermittent 503s; pod restart helps briefly; issue began after deployment.

1. `resolve_entity`: resolve Payment API, PROD and incident time.
2. Generate hypotheses: deployment, DB pool, upstream dependency, capacity, network.
3. `traverse`: Payment API → dependencies, resources, deployments, changes and incidents; return scope token.
4. `hybrid_search`: search similar incident language inside scope plus small global recall lane.
5. `traverse` top incidents: follow `ROOT_CAUSED_BY`, `RELATED_TO_CHANGE`, `RESOLVED_BY`.
6. `get_deployment_at_time`: recover artifact, commit, pipeline and config at incident time.
7. `retrieve_evidence`: config diff, deployment, prior resolution, runbook and graph path.
8. Update hypotheses: deployment/config branch rises; other branches fall; current pool metric remains missing.
9. Conclude: likely pool configuration regression, with evidence, confidence and safe validation/rollback step.

Final response separates:

- symptom location;
- affected service;
- root cause;
- supporting and contradicting evidence;
- unresolved uncertainty;
- next action.

---

## 15. Evaluation and traces

### Graph quality

Entity/edge precision and recall, duplicates, missing entities, direction errors, provenance, confidence calibration, temporal accuracy and staleness.

### Retrieval quality

Exact-ID hit rate, recall@k, MRR/nDCG, reranker lift, scope recall, broad-lane rescue, distractor rate, evidence diversity, corpus-growth degradation, latency and cost.

### Tool quality

Schema failures, authorization denials, timeouts, truncation, empty results, candidate counts, latency and evidence completeness.

### Agent outcome

Correct mapping/root cause, evidence faithfulness, unsupported claims, tool calls/time, unnecessary branches, escalation quality, human acceptance and remediation safety.

Trace:

- raw/normalized question;
- resolved entities/confidence;
- retrieval plan;
- query/template IDs;
- scope/candidate counts;
- hard versus soft filters;
- lexical/semantic/graph scores;
- reranker output;
- context shown to model;
- hypothesis updates;
- stopping reason;
- conclusion/citations;
- human feedback.

Attribute failures to construction, retrieval, ranking, tool use, reasoning or missing data. Do not treat every failure as “the LLM was wrong.”

---

## 16. Incremental implementation plan

### Phase 0 — pilot selection

One representative application with maintained Backstage data, repository scope, usable ServiceNow history, known resolved incidents and manageable dependencies.

Exit: owners, sources, ground truth and questions agreed.

### Phase 1 — retrieval grammar

Define pilot node types, relationship signatures, IDs, provenance/confidence, time, search document/chunk schema, ACL fields and evidence envelope.

Exit: representative data fits without ad-hoc relations.

### Phase 2 — pilot graph

Ingest Backstage, construct capability profiles, ingest ServiceNow history, map incidents, attach evidence/confidence and add enough code/deployment lineage for golden cases.

Exit: golden incident paths are inspectable.

### Phase 3 — retrieval v0

Exact lookup, BM25, embeddings, graph scoping, broad recall lane, fusion, reranking and evidence packets. Compare with global-RAG baseline.

Exit: golden evidence retrieval improves materially.

### Phase 4 — Knowledge MCP

Implement primitives and selected issue skills, ACLs, limits, traces, errors and truncation semantics.

Exit: contract, safety and latency tests pass.

### Phase 5 — agent loop

Hypothesis state, beam width, budgets, evidence comparison, stopping and escalation.

Exit: historical incidents replay with traceable conclusions.

### Phase 6 — scale/harden

Freshness, reconciliation, monitoring, corpus-size evaluation, profile-driven caching/denormalization, index migrations and disaster recovery.

Exit: quality and latency remain stable as sources grow.

---

## 17. Accepted decisions

1. Graph is canonical structure; search indexes are rebuildable projections.
2. Every hit resolves to a canonical graph `node_id`.
3. Prefer node-based graph scoping over hierarchy tags.
4. Use exact, lexical, semantic, graph and temporal retrieval—not dense alone.
5. Graph-first when an entity is known; search-first when ambiguous; exact-first for identifiers.
6. Focused retrieval plus a smaller broad-recall lane.
7. Rerank and diversify evidence before context.
8. Agent controls investigation; retrieval service controls queries.
9. Expose governed tools through MCP.
10. Unrestricted Cypher is not the normal agent interface.
11. Backstage anchors identity/ownership.
12. ServiceNow provides operational history.
13. Unmaintained CMDB is not initial topology.
14. Code structure is separate from environment snapshots.
15. Symptom, affected component and root cause stay distinct.
16. Extracted/inferred knowledge retains provenance/confidence.
17. Start with one representative application.

---

## 18. Must measure / unresolved

Must measure:

- one combined hybrid engine versus separate BM25/vector stores;
- Neo4j-native vector suitability;
- candidate-set sizes;
- fusion and reranker;
- chunking by node type;
- searchable representations;
- graph priors;
- broad-lane size;
- traversal depth/fan-out;
- beam width/stopping threshold;
- cache/denormalization need;
- freshness, cost and latency budgets.

Outstanding black boxes:

- Backstage completeness and repo-link convention;
- ServiceNow application, change, root-cause and resolution quality;
- logs, metrics, deployment, config and feature-flag access;
- ACL normalization;
- Neo4j edition/version and schema enforcement;
- ownership of semantic profiles;
- human validation of inferred edges;
- retention/deletion requirements;
- production SLOs and scale estimates.

---

## 19. Guidance for future agents

1. Keep graph construction separate from retrieval.
2. Do not embed every object by default.
3. Do not flatten hierarchy into search metadata without measured need.
4. Preserve graph/search joins through canonical `node_id`.
5. Prefer typed signatures over vague relationships.
6. Distinguish authoritative, extracted, inferred and derived assertions.
7. Keep symptom, affected entity and root cause separate.
8. Separate current state from historical state at time T.
9. Do not expose unbounded graph queries as the production default.
10. Enforce ACLs server-side.
11. Return compact evidence packets, not graph dumps.
12. Include provenance, confidence, time and source locators.
13. Do not hard-filter on low-confidence scope without a recall-preserving lane.
14. Attribute failures to the correct layer.
15. Keep vendor choices replaceable under the retrieval/MCP contract.
16. Mark assumptions, measurements and black boxes explicitly.

The design objective is:

> Help an agent reproduce the investigation process of an experienced issue resolver, then exceed human breadth through systematic, bounded and evidence-backed exploration.
