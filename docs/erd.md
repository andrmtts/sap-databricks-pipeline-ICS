# ERD — Gold Layer Dimensional Model

## Purpose
Shows the resulting star schema after `notebooks/03_gold_transformation.py`,
alongside the source tables each gold table derives from. Field-for-field mapping
and transformation rules are in `docs/mapping-spec.md`; formulas for the
calculated fields are in `docs/kpi-definitions.md`.

## Star schema

```mermaid
erDiagram
    FACT_DELIVERY_ITEM {
        string delivery_id
        string delivery_item_id
        string sales_order_id
        string sales_order_item_id
        string customer_id
        string material_id FK
        string plant FK
        string storage_location
        string business_unit
        date order_date
        date planned_delivery_date
        date actual_delivery_date
        int order_quantity
        int delivered_quantity
        int lead_time_days
        boolean is_on_time
        boolean is_in_full
        boolean is_otif
    }
    DIM_MATERIAL {
        string material_id PK
        string material_description
        string material_group
    }
    DIM_WAREHOUSE {
        string plant PK
        string storage_location PK
        string business_unit
    }

    DIM_MATERIAL ||--o{ FACT_DELIVERY_ITEM : "material_id"
    DIM_WAREHOUSE ||--o{ FACT_DELIVERY_ITEM : "plant"
```

**Grain:** `fact_delivery_item` = 1 row per delivery item (LIPS line). No
`dim_customer` or `dim_date` — the mapping spec doesn't define a customer master
or calendar dimension in scope for this project; `customer_id` and the three date
fields are carried as degenerate attributes on the fact table.

## Source → gold lineage

```mermaid
flowchart LR
    VBAK[VBAK<br/>sales order header] --> SILVER[silver_delivery_item]
    VBAP[VBAP<br/>sales order item] --> SILVER
    LIKP[LIKP<br/>delivery header] --> SILVER
    LIPS[LIPS<br/>delivery item] --> SILVER
    MARA[MARA<br/>material master] --> SILVER
    SILVER --> FACT[fact_delivery_item]
    PBU[plant_business_unit<br/>reference] --> FACT
    MARA --> DIMMAT[dim_material]
    MARD[MARD<br/>stock] --> DIMWH[dim_warehouse]
    PBU --> DIMWH
```

Bronze and silver layer table-by-table detail: `docs/data-dictionary.md`.
