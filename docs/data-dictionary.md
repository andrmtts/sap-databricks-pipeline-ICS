# Data Dictionary — Bronze Layer

## Purpose
Documents the origin and meaning of every field in the synthetic source files
(`data/mock_sap/`) as ingested into bronze Delta tables by
`notebooks/01_bronze_ingestion.py`. No transformation happens at this layer —
schema typing only. Fields are inspired by classic SAP ISC-DELIVER structures;
descriptions assume no prior SAP knowledge.

Bronze tables are named `bronze_<source_table>` (e.g. `bronze_vbak`) in the
catalog/schema set via the notebook's widgets.

---

## VBAK — Sales Order Header
*Grain: 1 row per sales order.*

| Field | Type | Description | Transformation |
|---|---|---|---|
| VBELN | string | Sales order number (unique ID for the order). | None |
| ERDAT | date | Date the order was created. | None |
| AUART | string | Order type code (`TA` = Standard Order, `RE` = Returns Order). | None |
| KUNNR | string | Customer number (sold-to party) placing the order. | None |
| VKORG | string | Sales organization code. | None |
| VTWEG | string | Distribution channel code. | None |
| SPART | string | Division code. | None |

## VBAP — Sales Order Item
*Grain: 1 row per order line.*

| Field | Type | Description | Transformation |
|---|---|---|---|
| VBELN | string | Sales order number. FK to VBAK.VBELN. | None |
| POSNR | string | Order line item number (increments of 10, e.g. `000010`). | None |
| MATNR | string | Material number ordered. FK to MARA.MATNR. | None |
| WERKS | string | Plant assigned to fulfill this line. | None |
| KWMENG | integer | Order quantity. | None |
| MEINS | string | Unit of measure. | None |

## LIKP — Delivery Header
*Grain: 1 row per delivery.*

| Field | Type | Description | Transformation |
|---|---|---|---|
| VBELN | string | Delivery number (unique ID for the delivery; distinct number range from sales orders). | None |
| LFART | string | Delivery type code. Decoded via `delivery_type_decode`. | None |
| ERDAT | date | Date the delivery document was created (mirrors the source order date). | None |
| LFDAT | date | Planned delivery date. | None |
| WADAT_IST | date | Actual goods issue date — used as the proxy for actual delivery date (see `docs/mapping-spec.md`, open point). | None |

## LIPS — Delivery Item
*Grain: 1 row per delivery line.*

| Field | Type | Description | Transformation |
|---|---|---|---|
| VBELN | string | Delivery number. FK to LIKP.VBELN. | None |
| POSNR | string | Delivery line item number. | None |
| VGBEL | string | Reference (preceding) sales order number. FK to VBAK.VBELN / VBAP.VBELN. | None |
| VGPOS | string | Reference sales order line item. FK to VBAP.POSNR. | None |
| MATNR | string | Material number delivered. FK to MARA.MATNR. | None |
| WERKS | string | Plant the line ships from (copied from the source order line). | None |
| LGORT | string | Storage location within the plant. | None |
| LFIMG | integer | Delivered quantity (may be less than VBAP.KWMENG for a short shipment). | None |
| MEINS | string | Unit of measure. | None |

## MARA — Material Master
*Grain: 1 row per material.*

| Field | Type | Description | Transformation |
|---|---|---|---|
| MATNR | string | Material number (unique ID). | None |
| MAKTX | string | Material description. | None |
| MATKL | string | Material group code (`RAW`, `PACK`, `FIN`). | None |
| MEINS | string | Base unit of measure. | None |

## MARD — Material Stock per Plant/Storage Location
*Grain: 1 row per material/plant/storage location combination.*

| Field | Type | Description | Transformation |
|---|---|---|---|
| MATNR | string | Material number. FK to MARA.MATNR. | None |
| WERKS | string | Plant. | None |
| LGORT | string | Storage location within the plant. | None |
| LABST | integer | Unrestricted stock quantity on hand. | None |

## plant_business_unit — Reference Table
*Grain: 1 row per plant. Created to fill the open point in `docs/mapping-spec.md` (no source field maps plants to business units).*

| Field | Type | Description | Transformation |
|---|---|---|---|
| WERKS | string | Plant code. | None |
| BUSINESS_UNIT | string | Business unit the plant belongs to (`Nexus Case`, `Biodiscovery`, `Precision Vanguard`). | None |

## delivery_type_decode — Reference Table
*Grain: 1 row per delivery type. Created to fill the open point in `docs/mapping-spec.md` (LFART → readable label).*

| Field | Type | Description | Transformation |
|---|---|---|---|
| LFART | string | Delivery type code. | None |
| DESCRIPTION | string | Readable label (e.g. `LF` → "Standard Delivery"). | None |

---

## Bronze-layer technical columns
Added by the ingestion notebook to every table, not present in the source files:

| Field | Type | Description |
|---|---|---|
| _source_file | string | Name of the source CSV the row was loaded from. |
| _ingested_at | timestamp | Timestamp the bronze write ran. |
