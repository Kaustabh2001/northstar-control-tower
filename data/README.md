# Local dataset catalogue

The raw datasets are downloaded into `data/raw/` and deliberately excluded from
Git. This file records provenance, intended use, licensing, and integrity
information so that the data can be reproduced and audited.

## 1. IT Service Ticket Classification Dataset

- Local file:
  `data/raw/it-service-ticket-classification/all_tickets_processed_improved_v3.csv`
- Source:
  <https://www.kaggle.com/datasets/adisongoh/it-service-ticket-classification-dataset>
- Download endpoint:
  <https://www.kaggle.com/api/v1/datasets/download/adisongoh/it-service-ticket-classification-dataset>
- License shown by the publisher: CC0 / Public Domain
- SHA-256:
  `044fdace33fa564e1e60453f2941dafc95539c99878b0d32746950394b9dd4d4`
- Shape: 47,837 rows, two columns (`Document`, `Topic_group`)
- Intended use: classical ML benchmark for ticket category/routing.

This corpus contains already-processed text and eight ticket categories. It has
no timestamps, resolution text, SLA events, priority labels, requester identity,
asset context, or agent actions. It must not be used to claim MTTR, SLA, cost,
or end-to-end business improvement.

## 2. Customer Support Tickets

- Local file: `data/raw/customer-support-tickets-multilingual.csv`
- Source:
  <https://huggingface.co/datasets/Tobi-Bueck/customer-support-tickets>
- Downloaded source object:
  `aa_dataset-tickets-multi-lang-5-2-50-version.csv`
- License shown by the publisher: CC BY-NC 4.0
- DOI: <https://doi.org/10.57967/hf/6184>
- SHA-256:
  `f187c090e59581c2bbf3aa1377c8db4dd647464ecf2ae51bf8966e42e0ed6bc0`
- Downloaded shape: 28,587 rows, 16 columns
- Intended use: non-commercial hackathon benchmarking of ticket type, queue,
  priority, retrieval, response drafting, and governance.

The English subset has 16,338 rows. The selected IT-oriented English subset has
10,416 rows across Technical Support, Product Support, IT Support, and Service
Outages and Maintenance.

Because the license is non-commercial and the data is synthetic, this corpus is
demo-only. A production deployment must replace it with organization-owned,
anonymized ticket history and approved knowledge documents.

## Reproduction policy

Raw inputs remain immutable. Derived splits, normalized text, synthetic event
logs, embeddings, and evaluation artefacts belong under ignored `data/processed`
or `data/artifacts` directories. Every derived dataset must record:

- source SHA-256 values;
- transformation code/version;
- random seed and split strategy;
- license and data-use restrictions;
- PII scan result;
- row counts before and after each filter;
- exclusions and leakage checks.
