# Project: SAP DELIVER Domain → Databricks Data Product

## Context
Portfolio project to apply for a BI & Data Business Analyst role (techno-functional profile,
bridge between business and engineering). Domain: ISC - DELIVER (shipments, deliveries, warehouse
management). Goal: simulate a SAP-style → Databricks pipeline, with functional documentation
equivalent to a real project (discovery, mapping specs, UAT, tracking).

This project uses SYNTHETIC data (not real SAP) to simulate extraction and modeling of a
typical Supply Chain/Logistics domain.

## Stack
- Python (data generation, notebooks)
- Databricks (notebook execution — done manually by the user, you only write the code)
- Delta Lake (bronze/silver/gold)
- SQL for final dashboard queries

## Folder structure to maintain
```
/data/raw          -> synthetic CSVs/Parquet generated
/notebooks          -> notebooks .py or .ipynb (bronze, silver, gold)
/sql                -> final queries used for the dashboard
/docs               -> functional documentation (specs, ERD, UAT, requirements)
/dashboards         -> exports/screenshots of the final dashboard
README.md           -> project overview, must link everything
```

## Important rules
- You (Claude Code) do NOT have access to the Databricks workspace. You write the notebook code,
  but the user runs, validates, and adjusts it in the real environment. Always make clear in the
  notebooks which parameters/paths need manual adjustment (e.g. catalog.schema.table).
- Synthetic data should be realistic but simple to audit: field and table names inspired by
  classic SAP structures from the DELIVER domain:
  - VBAK / VBAP (sales order: header and items)
  - LIKP / LIPS (delivery: header and items)
  - MARA / MARD (material and stock per plant/warehouse)
  Use plausible field names (e.g. VBELN, WERKS, LFART, LGORT) but document the meaning of each
  one in the data dictionary — don't assume the reader knows SAP.
- Every table or transformation created must be documented in /docs/data-dictionary.md with:
  field, source table, type, description, transformation rule (if any).
- KPIs to calculate at the gold layer: lead time (order-to-delivery), OTIF (on-time-in-full),
  fill rate. Document the exact formula used for each KPI in /docs/kpi-definitions.md.
- Don't generate excessive data volumes — a few thousand rows per table is enough, the focus is
  modeling quality and clarity, not scale.

## Project phases (follow in this order, one at a time, waiting for user validation between phases)

### Phase 0 — Setup
- Create the folder structure above.
- Create initial README.md with: project goal, domain, stack, how to navigate the repo.

### Phase 1 — Synthetic data generation
- Python script (using Faker or custom logic) generating VBAK/VBAP/LIKP/LIPS with consistent
  relationships (FKs matching across tables).
- Include date fields (order date, delivery date, planned vs actual) to allow lead time and
  OTIF calculation later.
- Export to /data/raw as CSV or Parquet.
- Stop here and wait for the user to review the fields before continuing.

### Phase 2 — Ingestion (bronze)
- Databricks notebook (.py, Databricks source format) that reads the files from /data/raw and
  creates bronze Delta tables, with no transformation, just schema applied.
- Make clear at the top of the notebook where the user needs to adjust path/catalog/schema.
- Create /docs/data-dictionary.md with the origin of each field.

### Phase 3 — Transformation (silver and gold)
- Silver notebook: cleaning, typing, deduplication, joins across tables.
- Gold notebook: delivery fact table (grain = 1 row per delivery item) + dimensions
  (customer, material, warehouse, date).
- Calculate KPIs (lead time, OTIF, fill rate) at the gold layer.
- Create /docs/erd.md (can use Mermaid) showing the resulting dimensional model.
- Create /docs/kpi-definitions.md with the formulas used.

### Phase 4 — Dashboard
- Write the final SQL query(ies) in /sql, ready to plug into PBI or Databricks AI/BI Dashboard.
- Do not build the dashboard itself (that's done manually by the user) — just leave the
  queries tested and documented.

### Phase 5 — Functional documentation
Help structure (business content comes from the user) in /docs:
- business-requirements.md — fictional discovery with business pain points, discovery questions.
- mapping-spec.md — table of source field (simulated SAP) → gold field, with transformation rule.
- uat-test-cases.md — test case table (scenario, input, expected result, actual result).
- tracking-board.md — simplified Jira-style board, showing how progress would be tracked.

### Phase 6 — Wrap-up
- Update final README.md linking: ERD, notebooks, docs, queries, dashboard.
- Review naming consistency across all files.

## How to work
- At the end of each phase, summarize what was done and stop for the user to validate before
  moving to the next phase.
- If a business decision is needed (e.g. hour tolerance to consider something "on time" for OTIF),
  ask the user instead of assuming.
- Prioritize clarity and documentation over code volume — the project's goal is to demonstrate
  functional reasoning + technical capability, not to build a complex system.
