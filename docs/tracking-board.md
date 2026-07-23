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
| DELIVER-101 | Create plant-to-business-unit reference table (Nexus Case, Biodiscovery, Precision Vanguard) | Mapping Spec — Open Points | High |
| DELIVER-102 | Confirm delivery type decode table (LFART) with Logistics Ops SMEs | Mapping Spec — Open Points | Medium |
| DELIVER-103 | Validate whether actual_delivery_date should use proof-of-delivery instead of goods issue date | Mapping Spec — Open Points | Medium |

## In Progress

| Ticket | Description | Linked Artifact | Owner | Notes |
|---|---|---|---|---|
| DELIVER-090 | Build bronze ingestion — VBAK/VBAP/LIKP/LIPS | Mapping Spec §2 | Data Engineering | Path/catalog params pending confirmation from workspace admin |
| DELIVER-091 | Implement silver layer joins (order ↔ delivery) | Mapping Spec §2 | Data Engineering | Blocked by DELIVER-101 for business_unit derivation |

## In Review

| Ticket | Description | Linked Artifact | Reviewer | Notes |
|---|---|---|---|---|
| DELIVER-080 | Implement OTIF logic (on-time + in-full) in gold layer | KPI Definitions / Mapping Spec | Functional Analyst | Pending validation against UAT #2, #3, #4 (tolerance boundary) |
| DELIVER-081 | Implement lead_time_days calculation | KPI Definitions | Functional Analyst | Pending validation against UAT #9 |

## Done

| Ticket | Description | Linked Artifact | Validated By |
|---|---|---|---|
| DELIVER-050 | Generate synthetic source data (VBAK/VBAP/LIKP/LIPS) | Data Dictionary | Functional Analyst |
| DELIVER-051 | Draft Business Requirements Document | Business Requirements | Sofia Bergmann (pending final sign-off) |
| DELIVER-052 | Draft Functional Mapping Spec | Mapping Spec | Data Functional Lead ISC |

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
