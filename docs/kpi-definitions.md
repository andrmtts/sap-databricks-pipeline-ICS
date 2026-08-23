# KPI Definitions — Gold Layer

## Purpose
Documents the exact formula, business rationale, and edge-case handling for every
KPI calculated in `notebooks/03_gold_transformation.py`, at the grain of
`fact_delivery_item` (1 row per delivery item). These are the formulas Data
Engineering implements and Functional Analysts validate against UAT — see
`docs/uat-test-cases.md` and `docs/tracking-board.md` for the findings that shaped
the null-handling rules below.

---

## Lead Time (`lead_time_days`)

**Formula:**
```
lead_time_days = actual_delivery_date - order_date
```
`actual_delivery_date` uses the delivery's goods issue date (`LIKP.WADAT_IST`) as a
proxy for "delivered" — see `docs/mapping-spec.md` §5 for the open point on
switching to a proof-of-delivery date if one becomes available.

**Example:** order placed 2026-01-03, goods issued 2026-01-09 → `lead_time_days = 6`.

**Aggregation:** report as an average (or median, to reduce outlier sensitivity)
grouped by `business_unit`, `plant`, or `material_group`.

---

## OTIF — On-Time In-Full (`is_otif`)

OTIF is the AND of two independent flags, matching how Logistics Ops, Customer
Service, and Planning each track a piece of it today (see
`docs/business-requirements.md` — this fragmentation across teams is the core
business pain point the project addresses).

### On-time (`is_on_time`)
**Formula:**
```
is_on_time = actual_delivery_date <= planned_delivery_date + 24h tolerance
```
The 24-hour tolerance was confirmed as the single cross-team definition
(`docs/mapping-spec.md` §5).

**Null handling:** when `planned_delivery_date` is missing, `is_on_time` is left
**NULL** — never defaulted to `TRUE`. UAT #7 (ticket DELIVER-111) found the earlier
approach silently counted deliveries with no plan as on-time, which overstated the
KPI. A NULL flag surfaces those rows as a data-quality exception instead of hiding
them in the numerator.

### In-full (`is_in_full`)
**Formula:**
```
is_in_full = delivered_quantity >= order_quantity
```

### Combined (`is_otif`)
**Formula:**
```
is_otif = is_on_time AND is_in_full
```
NULL propagates: a delivery with no planned date has an unknown OTIF status, not a
failing one — it should be excluded from the OTIF rate denominator, not counted
against it, until the missing plan is resolved.

**Example:** planned 2026-01-08, delivered 2026-01-08 18:00 (within 24h tolerance)
and delivered_quantity 100 >= order_quantity 100 → `is_otif = TRUE`.

---

## Fill Rate

**Formula (per delivery item):**
```
fill_rate_item = delivered_quantity / order_quantity
```
This is `is_in_full`'s underlying ratio, kept at the item grain in
`fact_delivery_item` (`delivered_quantity`, `order_quantity`) rather than
pre-aggregated, so it can be rolled up at query time to whatever grain the
dashboard needs — see `sql/fill_rate_by_material_group.sql`.

**Aggregate fill rate**, used on dashboards:
```
fill_rate = SUM(delivered_quantity) / SUM(order_quantity)
```
(a quantity-weighted average, not a simple average of per-item ratios — this
avoids over-weighting small orders).

**Example:** material group with 3 items ordering (100, 50, 200) and delivering
(100, 40, 200) → `fill_rate = 340 / 350 = 97.1%`.
