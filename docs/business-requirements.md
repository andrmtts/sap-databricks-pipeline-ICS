# Business Requirements Document
## DELIVER Domain Data Product — Governance & Analytics Enablement

**Author:** Andre M, BI & Data Business Analyst (Techno-Functional)
**Domain:** ISC — DELIVER (Shipments, Deliveries, Warehouse Management)
**Status:** Draft for stakeholder review

---

## 1. Background

The ISC DELIVER domain operates across multiple SAP S/4HANA instances, with data further
replicated into local spreadsheets, legacy data marts, and ad-hoc extracts maintained
independently by different analytics squads (Logistics Ops, Customer Service, Planning).

There is no single, governed data model for shipments, deliveries, and warehouse operations.
Each team maintains its own definition of core metrics — most critically, "on-time delivery" —
leading to inconsistent reporting and duplicated engineering effort.

## 2. Problem Statement

- **Multiple sources of truth**: Logistics Ops, Customer Service, and Planning each report OTIF
  for the same period with different numbers, due to divergent calculation logic.
- **No access governance**: warehouse data from one region is visible in reports belonging to
  another region, with no row- or column-level access control.
- **Redundant engineering effort**: Data Engineers receive repeated extraction requests because
  no catalog exists of what has already been modeled or productized.
- **No formal data products**: reporting is built ad-hoc, with no data contract, no versioning,
  and no clearly assigned data owner.
- **Business impact**: operational decisions (stock reallocation, prioritization of delayed
  shipments) are made on outdated or inconsistent data across teams.

## 3. Business Objective

Deliver a **governed data product for the DELIVER domain** that acts as the single source of
truth for core operational metrics (lead time, OTIF, fill rate), enabling Planning and
Logistics Ops to make daily decisions on consistent, trusted data.

## 4. Primary Stakeholder

**Sofia Bergmann — Global Process Owner, Deliver Domain**
Business owner of the process, non-technical. Needs to trust the numbers she reports to the
board and uses for daily operational decisions.

> "I don't trust the number each team sends me."

## 5. Supporting Stakeholders

| Role | Responsibility |
|---|---|
| Data Functional Lead ISC | Validates that the solution addresses the business need |
| Data Engineers | Build bronze/silver/gold layers from the functional mapping spec |
| Data Governance | Approves access model and catalog registration |
| Analytics Partners / SMEs | Provide domain input during discovery |

## 6. Discovery Questions (to validate with Sofia and SMEs)

1. What is the current, exact definition each team uses for "on-time delivery"? Where do
   they diverge?
2. What granularity does the business need — order line, delivery item, or aggregated daily?
3. How frequently does the business need this data refreshed (real-time, daily, weekly)?
4. Who should have access to which regions/warehouses, and is any of this data
   commercially sensitive (e.g. customer-specific SLAs)?
5. What decisions are currently blocked or delayed by inconsistent data?
6. Is there an existing system of record considered "closest to correct" today, to use as a
   validation baseline?
7. What would make Sofia trust a number enough to stop cross-checking it manually?

## 7. Scope

**In scope (Phase 1 — DELIVER domain):**
- Shipments, deliveries, and warehouse stock movements.
- Core KPIs: lead time (order-to-delivery), OTIF, fill rate.
- Single governed gold layer with documented mapping specs.
- Role-based access control by region/warehouse.

**Out of scope (future phases):**
- PLANNING domain (demand/supply planning) — to be addressed once DELIVER is stabilized and
  adopted as the reference model.
- Predictive analytics (e.g. delay forecasting) — dependent on DELIVER data maturity first.

## 8. Success Criteria

- A single OTIF definition, calculated one way, adopted by all three teams within 30 days
  of go-live.
- Data Governance has approved and cataloged the data product, with access rules enforced.
- Data Engineers have zero duplicate extraction requests for DELIVER data within one quarter.
- Sofia reports DELIVER metrics to the board directly from the governed dashboard, with no
  manual cross-checking.

## 9. Assumptions & Dependencies

- Source data availability and quality from SAP S/4HANA is assumed sufficient; a source data
  quality assessment may be required as a pre-step.
- Databricks Unity Catalog is available for access governance and cataloging.
- Data Governance team has capacity to review and approve the data product within the project
  timeline.
