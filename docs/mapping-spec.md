# Functional Mapping Specification
## DELIVER Domain Data Product — Source to Gold Mapping

**Domain:** ISC — DELIVER
**Purpose:** Traceable mapping from simulated SAP source tables to the governed gold layer,
including business transformation rules. This spec is the handoff artifact between the
Business/Functional Analyst and the Data Engineers building bronze/silver/gold pipelines.

---

## 1. Source Tables Overview

| Table | Description | Grain |
|---|---|---|
| VBAK | Sales order header | 1 row per sales order |
| VBAP | Sales order item | 1 row per order line |
| LIKP | Delivery header | 1 row per delivery |
| LIPS | Delivery item | 1 row per delivery line |
| MARA | Material master | 1 row per material |
| MARD | Material stock per plant/storage location | 1 row per material/plant/storage location |

## 2. Target: Gold Fact Table — `fact_delivery_item`

**Grain:** 1 row per delivery item (LIPS line).

| Gold Field | Source Table.Field | Type | Transformation Rule |
|---|---|---|---|
| delivery_id | LIKP.VBELN | string | Direct copy |
| delivery_item_id | LIPS.POSNR | string | Direct copy |
| sales_order_id | VBAP.VBELN | string | Join LIPS.VGBEL → VBAP.VBELN |
| sales_order_item_id | VBAP.POSNR | string | Join LIPS.VGPOS → VBAP.POSNR |
| customer_id | VBAK.KUNNR | string | Join via sales_order_id |
| material_id | LIPS.MATNR | string | Direct copy |
| material_description | MARA.MAKTX | string | Lookup via material_id |
| plant | LIPS.WERKS | string | Direct copy |
| storage_location | LIPS.LGORT | string | Direct copy |
| delivery_type | LIKP.LFART | string | Direct copy; decoded to readable label
  (e.g. "LF" → "Standard Delivery") in a reference table |
| order_date | VBAK.ERDAT | date | Direct copy |
| planned_delivery_date | LIKP.LFDAT | date | Direct copy |
| actual_delivery_date | LIKP.WADAT_IST | date | Direct copy (goods issue date used as
  proxy for actual delivery) |
| order_quantity | VBAP.KWMENG | decimal | Direct copy |
| delivered_quantity | LIPS.LFIMG | decimal | Direct copy |
| lead_time_days | *calculated* | integer | `actual_delivery_date - order_date` (see
  KPI definitions) |
| is_on_time | *calculated* | boolean | `actual_delivery_date <= planned_delivery_date + 24h
  tolerance` (see KPI definitions) |
| is_in_full | *calculated* | boolean | `delivered_quantity >= order_quantity` |
| is_otif | *calculated* | boolean | `is_on_time AND is_in_full` |
| business_unit | derived from plant | string | Lookup: plant → business unit, via a
  plant-to-BU reference table. Values: **Nexus Case**, **Biodiscovery**, **Precision Vanguard**
  (to be confirmed with Data Governance for access control mapping) |

## 3. Target: Dimension — `dim_material`

| Gold Field | Source Table.Field | Type | Transformation Rule |
|---|---|---|---|
| material_id | MARA.MATNR | string | Direct copy |
| material_description | MARA.MAKTX | string | Direct copy |
| material_group | MARA.MATKL | string | Direct copy |

## 4. Target: Dimension — `dim_warehouse`

| Gold Field | Source Table.Field | Type | Transformation Rule |
|---|---|---|---|
| plant | MARD.WERKS | string | Direct copy |
| storage_location | MARD.LGORT | string | Direct copy |
| business_unit | derived | string | Same plant → BU lookup as fact table (Nexus Case,
  Biodiscovery, Precision Vanguard), kept consistent for access control (row-level
  security by business unit) |

## 5. Open Points for Data Engineering / Governance

- **Plant-to-business-unit mapping table** does not exist as a source field — needs to be
  created and maintained as a reference table. Three business units in scope: **Nexus Case**,
  **Biodiscovery**, **Precision Vanguard**. Owner TBD with Data Governance.
- **Delivery type decode table** (LFART → readable label) to be confirmed with Logistics Ops
  SMEs for completeness.
- **actual_delivery_date** uses goods issue date (WADAT_IST) as a proxy; to validate with
  business whether "delivered" should instead use proof-of-delivery date if available in a
  future source system.
- **OTIF on-time tolerance confirmed at 24 hours**: `is_on_time = actual_delivery_date <=
  planned_delivery_date + 24h`.
- Row-level security by `business_unit` to be implemented at the Unity Catalog level — pending
  Data Governance sign-off on access matrix (see Business Requirements, Discovery Question 4).

## 6. Change Control

Any change to this mapping (new field, changed transformation rule, new KPI definition) must be
reflected here, versioned, and re-validated with the Data Functional Lead before Data Engineers
implement it in silver/gold notebooks.
