# Tracking Board
## DELIVER Domain Data Product — Development Progress

**Purpose:** Simulates how the Business/Functional Analyst tracks Data Engineering progress
against the Mapping Spec, and how UAT findings feed back into new tickets. Board format
mirrors Jira (To Do / In Progress / In Review / Done).

**Board owner:** BI & Data Business Analyst (this role)
**Contributors:** Data Engineers, Data Governance

---

## To Do

| Ticket | Description | Linked Artifact | Priority |
|---|---|---|---|
| DELIVER-102 | Confirm delivery type decode table (LFART) with Logistics Ops SMEs | Mapping Spec — Open Points | Medium |
| DELIVER-103 | Validate whether actual_delivery_date should use proof-of-delivery instead of goods issue date | Mapping Spec — Open Points | Medium |

## In Progress

*(none — all in-flight work from the last cycle moved to Done below)*

## In Review

| Ticket | Description | Linked Artifact | Reviewer | Notes |
|---|---|---|---|---|
| DELIVER-080 | Implement OTIF logic (on-time + in-full) in gold layer | KPI Definitions / Mapping Spec | Functional Analyst | Implemented with UAT #7 null-fix; pending final sign-off on tolerance boundary (UAT #2, #3, #4) |
| DELIVER-112 | Apply Unity Catalog row-level security policy by business_unit | `notebooks/07_row_level_security.py`, `docs/databricks-concepts.md` §8 | Data Governance | Filter mechanism built and attached to `fact_delivery_item`/`dim_warehouse`; **not** Done per this board's own rule (access-control tickets need Data Governance sign-off) — the per-BU account groups it depends on couldn't be created (no account-admin rights available), so live cross-user restriction is unverified |

## Done

| Ticket | Description | Linked Artifact | Validated By |
|---|---|---|---|
| DELIVER-050 | Generate synthetic source data (VBAK/VBAP/LIKP/LIPS) | Data Dictionary | Functional Analyst |
| DELIVER-051 | Draft Business Requirements Document | Business Requirements | Sofia Bergmann (pending final sign-off) |
| DELIVER-052 | Draft Functional Mapping Spec | Mapping Spec | Data Functional Lead ISC |
| DELIVER-090 | Build bronze ingestion — VBAK/VBAP/LIKP/LIPS | `notebooks/01_bronze_ingestion.py` | Data Engineering |
| DELIVER-101 | Create plant-to-business-unit reference table | `data/mock_sap/plant_business_unit.csv` | Data Governance |
| DELIVER-091 | Implement silver layer joins (order ↔ delivery) | `notebooks/02_silver_transformation.py` | Data Engineering |
| DELIVER-081 | Implement lead_time_days calculation | `docs/kpi-definitions.md`, `notebooks/03_gold_transformation.py` | Functional Analyst |
| DELIVER-110 | Add deduplication logic in silver layer (duplicate delivery_id + delivery_item_id) | `notebooks/02_silver_transformation.py` | Functional Analyst — UAT #14 re-run passed |
| DELIVER-111 | Fix null-handling in is_on_time logic; route to data quality exception instead of defaulting TRUE | `docs/kpi-definitions.md`, `notebooks/03_gold_transformation.py` | Functional Analyst — UAT #7 re-run passed |

---

## UAT Findings → New Tickets (feedback loop example)

| UAT Case | Finding | New Ticket Raised |
|---|---|---|
| UAT #14 — Duplicate delivery item | Source data contains duplicate delivery_id + delivery_item_id combinations | DELIVER-110: Add deduplication logic in silver layer |
| UAT #7 — Missing planned_delivery_date | NULL dates were defaulting to TRUE for is_on_time instead of being flagged | DELIVER-111: Fix null-handling in is_on_time logic; route to data quality exception table |
| UAT #13 — Row-level security | Cross-BU access not yet enforced at Unity Catalog level | DELIVER-112: Apply Unity Catalog row-level security policy by business_unit |

---

## Notes on Process

- Tickets are opened directly from Mapping Spec open points or UAT failures — no work is
  started without a traceable source (business requirement, spec gap, or test failure).
- Weekly sync with Data Engineering to move tickets across columns; Functional Analyst owns
  reprioritization based on business urgency (e.g. Sofia Bergmann's board reporting deadline).
- "Done" requires: code merged + corresponding UAT case passed + Data Governance sign-off
  where applicable (e.g. access control tickets).
