-- Fill rate by material group, quantity-weighted (SUM(delivered)/SUM(ordered))
-- rather than an average of per-item ratios, so small orders don't get
-- over-weighted — see docs/kpi-definitions.md "Fill Rate".
-- Source: main.sap_deliver_gold.fact_delivery_item joined to dim_material for material_group.

SELECT
    dm.material_group,
    COUNT(*) AS delivery_items,
    SUM(f.order_quantity) AS total_ordered_qty,
    SUM(f.delivered_quantity) AS total_delivered_qty,
    ROUND(SUM(f.delivered_quantity) / SUM(f.order_quantity), 4) AS fill_rate
FROM main.sap_deliver_gold.fact_delivery_item f
JOIN main.sap_deliver_gold.dim_material dm ON f.material_id = dm.material_id
GROUP BY dm.material_group
ORDER BY fill_rate ASC;
