# Databricks notebook source
# MAGIC %md
# MAGIC # Silver Transformation — ISC DELIVER Domain
# MAGIC
# MAGIC Reads bronze Delta tables, applies cleaning/dedup/typing, and joins order ↔
# MAGIC delivery ↔ material into silver tables. No KPI calculation here — that
# MAGIC happens at the gold layer (see `03_gold_transformation.py`).
# MAGIC
# MAGIC **Parameters** (widgets, overridable at run time):
# MAGIC 1. `catalog` — Unity Catalog catalog. Currently `main`.
# MAGIC 2. `bronze_schema` — schema holding bronze tables. Currently `sap_deliver_bronze`.
# MAGIC 3. `silver_schema` — schema to create silver tables in. Currently `sap_deliver_silver`.

# COMMAND ----------

dbutils.widgets.text("catalog", "main", "Catalog")
dbutils.widgets.text("bronze_schema", "sap_deliver_bronze", "Bronze schema")
dbutils.widgets.text("silver_schema", "sap_deliver_silver", "Silver schema")

catalog = dbutils.widgets.get("catalog")
bronze_schema = dbutils.widgets.get("bronze_schema")
silver_schema = dbutils.widgets.get("silver_schema")

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{silver_schema}")

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window

bronze = lambda name: spark.table(f"{catalog}.{bronze_schema}.bronze_{name}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Deduplication — LIPS (delivery items)
# MAGIC UAT #14 found duplicate `delivery_id` + `delivery_item_id` combinations in the
# MAGIC source data (ticket DELIVER-110). Keep the most recently ingested row per key.

# COMMAND ----------

lips_dedup_window = Window.partitionBy("VBELN", "POSNR").orderBy(F.col("_ingested_at").desc())

silver_lips = (
    bronze("lips")
    .withColumn("_rn", F.row_number().over(lips_dedup_window))
    .filter(F.col("_rn") == 1)
    .drop("_rn")
)

dropped = bronze("lips").count() - silver_lips.count()
print(f"LIPS dedup: dropped {dropped} duplicate delivery-item rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Null-handling — planned_delivery_date
# MAGIC UAT #7 found that a NULL `planned_delivery_date` (LIKP.LFDAT) was defaulting
# MAGIC `is_on_time` to TRUE instead of being flagged (ticket DELIVER-111). Silver just
# MAGIC surfaces the flag; the gold layer uses it to keep `is_on_time` explicitly NULL
# MAGIC rather than defaulting either way.

# COMMAND ----------

silver_likp = bronze("likp").withColumn(
    "has_missing_planned_date", F.col("LFDAT").isNull()
)

missing = silver_likp.filter(F.col("has_missing_planned_date")).count()
print(f"LIKP: {missing} deliveries with missing planned_delivery_date, flagged for exception handling")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Joins — order ↔ delivery ↔ material
# MAGIC Per `docs/mapping-spec.md` §2: LIPS is the driving grain (1 row per delivery
# MAGIC item), joined back to its delivery header, source sales order/item, and
# MAGIC material master.

# COMMAND ----------

silver_delivery_item = (
    silver_lips.alias("lips")
    .join(silver_likp.alias("likp"), F.col("lips.VBELN") == F.col("likp.VBELN"), "left")
    .join(
        bronze("vbap").alias("vbap"),
        (F.col("lips.VGBEL") == F.col("vbap.VBELN")) & (F.col("lips.VGPOS") == F.col("vbap.POSNR")),
        "left",
    )
    .join(bronze("vbak").alias("vbak"), F.col("vbap.VBELN") == F.col("vbak.VBELN"), "left")
    .join(bronze("mara").alias("mara"), F.col("lips.MATNR") == F.col("mara.MATNR"), "left")
    .join(
        bronze("delivery_type_decode").alias("dtd"),
        F.col("likp.LFART") == F.col("dtd.LFART"),
        "left",
    )
    .select(
        F.col("likp.VBELN").alias("delivery_id"),
        F.col("lips.POSNR").alias("delivery_item_id"),
        F.col("vbap.VBELN").alias("sales_order_id"),
        F.col("vbap.POSNR").alias("sales_order_item_id"),
        F.col("vbak.KUNNR").alias("customer_id"),
        F.col("lips.MATNR").alias("material_id"),
        F.col("mara.MAKTX").alias("material_description"),
        F.col("lips.WERKS").alias("plant"),
        F.col("lips.LGORT").alias("storage_location"),
        F.col("likp.LFART").alias("delivery_type_code"),
        F.col("dtd.DESCRIPTION").alias("delivery_type_description"),
        F.col("vbak.ERDAT").alias("order_date"),
        F.col("likp.LFDAT").alias("planned_delivery_date"),
        F.col("likp.WADAT_IST").alias("actual_delivery_date"),
        F.col("likp.has_missing_planned_date"),
        F.col("vbap.KWMENG").alias("order_quantity"),
        F.col("lips.LFIMG").alias("delivered_quantity"),
    )
)

target_table = f"{catalog}.{silver_schema}.silver_delivery_item"
silver_delivery_item.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(target_table)
print(f"{target_table}: {silver_delivery_item.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Pass-through reference tables
# MAGIC `MARA`/`MARD` need no cleaning at this layer — carried to silver as-is (raw SAP
# MAGIC field names kept) so the gold layer only reads from `sap_deliver_silver`.
# MAGIC `plant_business_unit` is renamed to the target field names (`plant`,
# MAGIC `business_unit`) here since every downstream join keys on those names.

# COMMAND ----------

for name in ["mara", "mard"]:
    df = bronze(name)
    target_table = f"{catalog}.{silver_schema}.silver_{name}"
    df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(target_table)
    print(f"{target_table}: {df.count()} rows")

silver_plant_business_unit = bronze("plant_business_unit").select(
    F.col("WERKS").alias("plant"), F.col("BUSINESS_UNIT").alias("business_unit")
)
target_table = f"{catalog}.{silver_schema}.silver_plant_business_unit"
silver_plant_business_unit.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(target_table)
print(f"{target_table}: {silver_plant_business_unit.count()} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Validation

# COMMAND ----------

display(spark.table(f"{catalog}.{silver_schema}.silver_delivery_item").limit(5))
