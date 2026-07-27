# Dataset profile and fitness assessment

Profiled on 2026-07-27 from the immutable local raw files documented in
`data/README.md`.

## Profile summary

| Measure | CC0 IT classification corpus | Rich multilingual ticket corpus |
|---|---:|---:|
| Rows downloaded | 47,837 | 28,587 |
| English rows | 47,837 | 16,338 |
| Selected English IT rows | 47,837 | 10,416 |
| Full-row duplicates | 0 | 0 |
| Normalized text duplicates | 0 | 8 English ticket bodies |
| Average ticket body length | 43.6 words | 53.9 words in English |
| Average answer length | Not available | 56.5 words in English |
| Missing ticket body | 0 | 0 |
| Missing subject | Not available | 2,607 English rows |
| Missing answer | Not available | 3 English rows |

## CC0 classification labels

| Topic group | Rows | Share |
|---|---:|---:|
| Hardware | 13,617 | 28.47% |
| HR Support | 10,915 | 22.82% |
| Access | 7,125 | 14.89% |
| Miscellaneous | 7,060 | 14.76% |
| Storage | 2,777 | 5.81% |
| Purchase | 2,464 | 5.15% |
| Internal Project | 2,119 | 4.43% |
| Administrative rights | 1,760 | 3.68% |

The imbalance is material. Accuracy alone is invalid; macro-F1, balanced
accuracy, per-class recall, calibration, and confidence-based abstention are
required.

## Selected English IT subset

Selection rule: English tickets whose queue is Technical Support, Product
Support, IT Support, or Service Outages and Maintenance.

### Queue

| Queue | Rows |
|---|---:|
| Technical Support | 4,737 |
| Product Support | 3,073 |
| IT Support | 1,942 |
| Service Outages and Maintenance | 664 |

### Ticket type

| Type | Rows |
|---|---:|
| Incident | 4,901 |
| Problem | 2,223 |
| Request | 2,159 |
| Change | 1,133 |

### Priority

| Priority | Rows |
|---|---:|
| High | 5,065 |
| Medium | 3,957 |
| Low | 1,394 |

The rich corpus supports queue, type and priority prediction plus response
recommendation. It does not contain event timestamps, actual handling time,
human edits, reopen events, SLA breaches, costs, approvals, tool calls, CSAT, or
asset/user context.

## Leakage controls

- Split the CC0 corpus 70/15/15 with stratification by topic.
- Split the synthetic rich corpus by generation `version`, not random rows, to
  reduce template leakage.
- Never index held-out answers into the retrieval corpus.
- Build the knowledge index only from training answers and separately sourced
  approved runbooks.
- Reserve a balanced 300-ticket golden set for manual review.
- Keep the final test set frozen; tune thresholds only on validation data.
- Record dataset SHA-256 values, transformation version, and random seed in
  every MLflow run.

## What must be collected from the running system

GLPI and the AI control plane must emit immutable events for:

- creation, first response, assignment, escalation, resolution, closure and
  reopen timestamps;
- original and final queue/type/priority;
- model predictions, calibrated confidence and abstention;
- retrieved document IDs, ranks, scores and citations;
- generated draft, final human-edited response and edit distance;
- proposed action, approval/rejection, executor, result and rollback;
- model, prompt, token, latency, cache, CPU/GPU and energy estimates;
- CSAT, resolution code, first-contact resolution and SLA outcome.

Only these observed events can support credible MTTR, SLA, productivity, risk,
and ROI claims.
