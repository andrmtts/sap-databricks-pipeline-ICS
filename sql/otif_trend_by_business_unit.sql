-- OTIF trend by business unit, monthly.
-- Excludes deliveries with a missing planned_delivery_date (is_on_time IS NULL) from
-- the denominator instead of counting them as failures — see docs/kpi-definitions.md.
-- Source: main.sap_deliver_gold.fact_delivery_item

SELECT
    business_unit,
    date_trunc('month', actual_delivery_date) AS delivery_month,
    COUNT(*) AS deliveries_with_known_otif,
    SUM(CASE WHEN is_otif THEN 1 ELSE 0 END) AS otif_count,
    ROUND(SUM(CASE WHEN is_otif THEN 1 ELSE 0 END) / COUNT(*), 4) AS otif_rate
FROM main.sap_deliver_gold.fact_delivery_item
WHERE is_on_time IS NOT NULL
GROUP BY business_unit, date_trunc('month', actual_delivery_date)
ORDER BY business_unit, delivery_month;
