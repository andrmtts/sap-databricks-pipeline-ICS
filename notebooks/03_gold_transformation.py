# Databricks notebook source
# MAGIC %md
# MAGIC # Gold Transformation — ISC DELIVER Domain
# MAGIC
# MAGIC Builds the governed gold layer from silver: the `fact_delivery_item` fact table
# MAGIC plus `dim_material` and `dim_warehouse` dimensions, and calculates the OTIF /
# MAGIC lead time / fill rate KPIs. Field-for-field, this follows
# MAGIC `docs/mapping-spec.md` §2-4; formulas are documented in
# MAGIC `docs/kpi-definitions.md`.
# MAGIC
# MAGIC **Parameters** (widgets, overridable at run time):
# MAGIC 1. `catalog` — Unity Catalog catalog. Currently `main`.
# MAGIC 2. `silver_schema` — schema holding silver tables. Currently `sap_deliver_silver`.
# MAGIC 3. `gold_schema` — schema to create gold tables in. Currently `sap_deliver_gold`.

# COMMAND ----------

dbutils.widgets.text("catalog", "main", "Catalog")
dbutils.widgets.text("silver_schema", "sap_deliver_silver", "Silver schema")
dbutils.widgets.text("gold_schema", "sap_deliver_gold", "Gold schema")

catalog = dbutils.widgets.get("catalog")
silver_schema = dbutils.widgets.get("silver_schema")
gold_schema = dbutils.widgets.get("gold_schema")

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{gold_schema}")

# COMMAND ----------

from pyspark.sql import functions as F

silver = lambda name: spark.table(f"{catalog}.{silver_schema}.silver_{name}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## `fact_delivery_item`
# MAGIC Grain: 1 row per delivery item (mapping-spec §2). Business unit is derived via
# MAGIC the plant → business unit lookup (mapping-spec §5, Open Points — resolved by
# MAGIC `data/mock_sap/plant_business_unit.csv`, closes ticket DELIVER-101).
# MAGIC
# MAGIC KPI rules (see `docs/kpi-definitions.md` for the full formulas + rationale):
# MAGIC - `lead_time_days` = actual_delivery_date - order_date
# MAGIC - `is_on_time` = actual_delivery_date <= planned_delivery_date + 24h tolerance,
# MAGIC   left **NULL** (not defaulted to TRUE) when planned_delivery_date is missing —
# MAGIC   fixes UAT #7 / ticket DELIVER-111.
# MAGIC - `is_in_full` = delivered_quantity >= order_quantity
# MAGIC - `is_otif` = is_on_time AND is_in_full (NULL propagates — an OTIF status can't be
# MAGIC   claimed for a delivery with no planned date)

# COMMAND ----------

delivery_item = silver("delivery_item").join(
    silver("plant_business_unit"), on="plant", how="left"
)

TOLERANCE_HOURS = 24

fact_delivery_item = (
    delivery_item
    .withColumn("lead_time_days", F.datediff("actual_delivery_date", "order_date"))
    .withColumn(
        "is_on_time",
        F.when(F.col("has_missing_planned_date"), F.lit(None).cast("boolean")).otherwise(
            F.col("actual_delivery_date")
            <= F.expr(f"planned_delivery_date + INTERVAL {TOLERANCE_HOURS} HOURS")
        ),
    )
    .withColumn("is_in_full", F.col("delivered_quantity") >= F.col("order_quantity"))
    .withColumn("is_otif", F.col("is_on_time") & F.col("is_in_full"))
    .select(
        "delivery_id",
        "delivery_item_id",
        "sales_order_id",
        "sales_order_item_id",
        "customer_id",
        "material_id",
        "material_description",
        "plant",
        "storage_location",
        "delivery_type_code",
        "delivery_type_description",
        "order_date",
        "planned_delivery_date",
        "actual_delivery_date",
        "order_quantity",
        "delivered_quantity",
        "lead_time_days",
        "is_on_time",
        "is_in_full",
        "is_otif",
        "business_unit",
    )
)

target_table = f"{catalog}.{gold_schema}.fact_delivery_item"
fact_delivery_item.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(target_table)
print(f"{target_table}: {fact_delivery_item.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## `dim_material` (mapping-spec §3)

# COMMAND ----------

dim_material = silver("mara").select(
    F.col("MATNR").alias("material_id"),
    F.col("MAKTX").alias("material_description"),
    F.col("MATKL").alias("material_group"),
)

target_table = f"{catalog}.{gold_schema}.dim_material"
dim_material.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(target_table)
print(f"{target_table}: {dim_material.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## `dim_warehouse` (mapping-spec §4)
# MAGIC MARD carries SAP field names (WERKS/LGORT) — mapped to plant/storage_location
# MAGIC per the target schema, joined to the same plant → business unit lookup as the
# MAGIC fact table for row-level-security consistency (mapping-spec §4).

# COMMAND ----------

dim_warehouse = (
    silver("mard")
    .select(F.col("WERKS").alias("plant"), F.col("LGORT").alias("storage_location"))
    .distinct()
    .join(silver("plant_business_unit"), on="plant", how="left")
    .select("plant", "storage_location", "business_unit")
)

target_table = f"{catalog}.{gold_schema}.dim_warehouse"
dim_warehouse.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(target_table)
print(f"{target_table}: {dim_warehouse.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Validation

# COMMAND ----------

display(spark.table(f"{catalog}.{gold_schema}.fact_delivery_item").limit(5))
