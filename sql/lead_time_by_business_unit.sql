-- Average and median lead time (order-to-delivery) by business unit.
-- Median included alongside the average since lead time is outlier-sensitive
-- (a handful of very late deliveries can skew a mean but not a median).
-- Source: main.sap_deliver_gold.fact_delivery_item

SELECT
    business_unit,
    COUNT(*) AS delivery_items,
    ROUND(AVG(lead_time_days), 2) AS avg_lead_time_days,
    ROUND(percentile_approx(lead_time_days, 0.5), 2) AS median_lead_time_days
FROM main.sap_deliver_gold.fact_delivery_item
WHERE lead_time_days IS NOT NULL
GROUP BY business_unit
ORDER BY avg_lead_time_days DESC;
