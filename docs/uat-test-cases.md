# UAT Test Cases
## DELIVER Domain Data Product — Gold Layer Validation

**Purpose:** Business sign-off checklist to validate that `fact_delivery_item` and related KPIs
(lead time, OTIF, fill rate) behave as defined in the Business Requirements and Mapping Spec
before the data product is released to Nexus Case, Biodiscovery, and Precision Vanguard
stakeholders.

**Sign-off owner:** Sofia Bergmann (Global Process Owner, Deliver Domain), supported by
Data Functional Lead ISC.

---

| # | Scenario | Input | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|
| 1 | Delivery on time, in full | order_qty = 100, delivered_qty = 100, planned = actual date | is_on_time = TRUE, is_in_full = TRUE, is_otif = TRUE | | |
| 2 | Delivery late beyond tolerance | planned_date = Jan 10, actual_date = Jan 12 | is_on_time = FALSE, is_otif = FALSE | | |
| 3 | Delivery late within 24h tolerance | planned_date = Jan 10 08:00, actual_date = Jan 11 06:00 | is_on_time = TRUE (within 24h), is_otif = TRUE if also in full | | |
| 4 | Delivery late exactly at tolerance boundary | planned_date + 24h == actual_date (exact) | is_on_time = TRUE (inclusive boundary) | | |
| 5 | Partial delivery, on time | order_qty = 100, delivered_qty = 60, on-time date | is_in_full = FALSE, is_otif = FALSE | | |
| 6 | Over-delivery | order_qty = 100, delivered_qty = 110 | is_in_full = TRUE (>= order_qty rule) | | |
| 7 | Missing planned_delivery_date | planned_delivery_date = NULL | is_on_time = NULL/FALSE (not silently TRUE); record flagged for data quality review | | |
| 8 | Missing actual_delivery_date (not yet delivered) | actual_delivery_date = NULL | Excluded from OTIF calculation (not counted as failure); flagged as "in transit" | | |
| 9 | Lead time calculation, standard case | order_date = Jan 1, actual_delivery_date = Jan 6 | lead_time_days = 5 | | |
| 10 | Business unit mapping — Nexus Case | plant belongs to Nexus Case plant list | business_unit = "Nexus Case" | | |
| 11 | Business unit mapping — Biodiscovery | plant belongs to Biodiscovery plant list | business_unit = "Biodiscovery" | | |
| 12 | Business unit mapping — Precision Vanguard | plant belongs to Precision Vanguard plant list | business_unit = "Precision Vanguard" | | |
| 13 | Row-level security — cross-BU access blocked | User with access only to Nexus Case queries the gold table | Only Nexus Case rows returned; Biodiscovery and Precision Vanguard rows hidden | | |
| 14 | Duplicate delivery item | Same delivery_id + delivery_item_id appears twice in source | Deduplicated in silver layer; only one row in gold | | |
| 15 | Orphan delivery item (no matching sales order) | LIPS.VGBEL does not match any VBAP.VBELN | Record flagged as orphan/data quality exception, not silently dropped | | |
| 16 | Aggregated OTIF % matches manual calculation | Sample of 20 known delivery items, manually calculated OTIF % | Gold layer OTIF % matches manual calculation exactly | | |

## Sign-off

| Role | Name | Date | Approved (Y/N) |
|---|---|---|---|
| Global Process Owner | Sofia Bergmann | | |
| Data Functional Lead ISC | | | |
| Data Governance | | | |
