# Databricks notebook source
# MAGIC %md
# MAGIC # Delta Live Tables / Lakeflow Declarative Pipeline — ISC DELIVER Domain
# MAGIC
# MAGIC A **declarative** re-implementation of the classic PySpark notebooks
# MAGIC (`01_bronze_ingestion.py` → `02_silver_transformation.py` →
# MAGIC `03_gold_transformation.py`): instead of writing imperative
# MAGIC read/transform/write steps, each `@dlt.table` declares *what* the table
# MAGIC should contain, and the DLT runtime figures out execution order from the
# MAGIC dependency graph (`dlt.read`/`spark.table` references between tables) and
# MAGIC handles orchestration, retries, and data-quality enforcement.
# MAGIC
# MAGIC Runs in its own catalog/schema (`main.sap_deliver_dlt`, set via the
# MAGIC pipeline's `target` config, not touching `sap_deliver_bronze/silver/gold`)
# MAGIC so it stands as a side-by-side comparison to the classic notebooks rather
# MAGIC than replacing them.
# MAGIC
# MAGIC **Expectations** are the headline feature this pipeline exists to
# MAGIC demonstrate: the same data-quality rules found by UAT in the classic
# MAGIC pipeline (UAT #7, #14 — see `docs/uat-test-cases.md`) are declared as code
# MAGIC here, enforced automatically on every run instead of relying on someone
# MAGIC remembering to write the check.

# COMMAND ----------

import dlt
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DateType
from pyspark.sql.window import Window

raw_path = spark.conf.get("raw_path", "/Volumes/main/sap_deliver/raw_files")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Bronze — raw source tables, schema applied, no business logic
# MAGIC Same explicit schemas as `01_bronze_ingestion.py`, one `@dlt.table` per
# MAGIC source file.

# COMMAND ----------

BRONZE_SCHEMAS = {
    "vbak": StructType([
        StructField("VBELN", StringType()), StructField("ERDAT", DateType()),
        StructField("AUART", StringType()), StructField("KUNNR", StringType()),
        StructField("VKORG", StringType()), StructField("VTWEG", StringType()),
        StructField("SPART", StringType()),
    ]),
    "vbap": StructType([
        StructField("VBELN", StringType()), StructField("POSNR", StringType()),
        StructField("MATNR", StringType()), StructField("WERKS", StringType()),
        StructField("KWMENG", IntegerType()), StructField("MEINS", StringType()),
    ]),
    "likp": StructType([
        StructField("VBELN", StringType()), StructField("LFART", StringType()),
        StructField("ERDAT", DateType()), StructField("LFDAT", DateType()),
        StructField("WADAT_IST", DateType()),
    ]),
    "lips": StructType([
        StructField("VBELN", StringType()), StructField("POSNR", StringType()),
        StructField("VGBEL", StringType()), StructField("VGPOS", StringType()),
        StructField("MATNR", StringType()), StructField("WERKS", StringType()),
        StructField("LGORT", StringType()), StructField("LFIMG", IntegerType()),
        StructField("MEINS", StringType()),
    ]),
    "mara": StructType([
        StructField("MATNR", StringType()), StructField("MAKTX", StringType()),
        StructField("MATKL", StringType()), StructField("MEINS", StringType()),
    ]),
    "plant_business_unit": StructType([
        StructField("WERKS", StringType()), StructField("BUSINESS_UNIT", StringType()),
    ]),
    "delivery_type_decode": StructType([
        StructField("LFART", StringType()), StructField("DESCRIPTION", StringType()),
    ]),
}


BRONZE_FILENAMES = {
    "vbak": "VBAK.csv",
    "vbap": "VBAP.csv",
    "likp": "LIKP.csv",
    "lips": "LIPS.csv",
    "mara": "MARA.csv",
    "plant_business_unit": "plant_business_unit.csv",
    "delivery_type_decode": "delivery_type_decode.csv",
}


def make_bronze_table(name, schema, filename):
    @dlt.table(name=f"bronze_{name}", comment=f"Raw {name.upper()} — schema applied, no transformation.")
    def _bronze():
        return (
            spark.read.format("csv")
            .option("header", "true")
            .schema(schema)
            .load(f"{raw_path}/{filename}")
        )
    return _bronze


for _name, _schema in BRONZE_SCHEMAS.items():
    make_bronze_table(_name, _schema, BRONZE_FILENAMES[_name])

# COMMAND ----------

# MAGIC %md
# MAGIC ## Silver — cleaned, deduped, joined
# MAGIC `expect_or_drop` **enforces** a rule by discarding violating rows (and DLT
# MAGIC tracks how many were dropped, per run, in the pipeline's event log).
# MAGIC `expect` **flags** a rule without dropping rows — the right choice for
# MAGIC UAT #7's missing-planned-date case, where the row is still valid data, just
# MAGIC incomplete for one KPI.

# COMMAND ----------

@dlt.table(name="silver_delivery_item", comment="Deduped, joined delivery items — mirrors 02_silver_transformation.py.")
@dlt.expect_or_drop("valid_key", "delivery_id IS NOT NULL AND delivery_item_id IS NOT NULL")
@dlt.expect_or_drop("valid_quantities", "order_quantity IS NOT NULL AND delivered_quantity IS NOT NULL")
@dlt.expect("has_planned_date", "planned_delivery_date IS NOT NULL")
def silver_delivery_item():
    lips = (
        dlt.read("bronze_lips")
        .withColumn("_rn", F.row_number().over(Window.partitionBy("VBELN", "POSNR").orderBy(F.lit(1))))
        .filter(F.col("_rn") == 1)
        .drop("_rn")
    )
    likp = dlt.read("bronze_likp")
    vbap = dlt.read("bronze_vbap")
    vbak = dlt.read("bronze_vbak")
    mara = dlt.read("bronze_mara")
    dtd = dlt.read("bronze_delivery_type_decode")

    return (
        lips.alias("lips")
        .join(likp.alias("likp"), F.col("lips.VBELN") == F.col("likp.VBELN"), "left")
        .join(
            vbap.alias("vbap"),
            (F.col("lips.VGBEL") == F.col("vbap.VBELN")) & (F.col("lips.VGPOS") == F.col("vbap.POSNR")),
            "left",
        )
        .join(vbak.alias("vbak"), F.col("vbap.VBELN") == F.col("vbak.VBELN"), "left")
        .join(mara.alias("mara"), F.col("lips.MATNR") == F.col("mara.MATNR"), "left")
        .join(dtd.alias("dtd"), F.col("likp.LFART") == F.col("dtd.LFART"), "left")
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
            F.col("vbap.KWMENG").alias("order_quantity"),
            F.col("lips.LFIMG").alias("delivered_quantity"),
        )
    )

# COMMAND ----------

# MAGIC %md
# MAGIC ## Gold — KPIs, same formulas as `docs/kpi-definitions.md`
# MAGIC `is_on_time` stays NULL (not dropped, not defaulted) when
# MAGIC `planned_delivery_date` is missing — same UAT #7 fix as the classic
# MAGIC pipeline, expressed here as an expectation instead of a code comment.

# COMMAND ----------

@dlt.table(name="fact_delivery_item", comment="Gold fact table with OTIF/lead-time/fill-rate KPIs.")
@dlt.expect("valid_otif_logic", "is_on_time IS NULL OR is_otif = (is_on_time AND is_in_full)")
def fact_delivery_item():
    TOLERANCE_HOURS = 24
    delivery_item = dlt.read("silver_delivery_item").join(
        dlt.read("bronze_plant_business_unit")
        .select(F.col("WERKS").alias("plant"), F.col("BUSINESS_UNIT").alias("business_unit")),
        on="plant",
        how="left",
    )

    return (
        delivery_item
        .withColumn("lead_time_days", F.datediff("actual_delivery_date", "order_date"))
        .withColumn(
            "is_on_time",
            F.when(F.col("planned_delivery_date").isNull(), F.lit(None).cast("boolean")).otherwise(
                F.col("actual_delivery_date") <= F.expr(f"planned_delivery_date + INTERVAL {TOLERANCE_HOURS} HOURS")
            ),
        )
        .withColumn("is_in_full", F.col("delivered_quantity") >= F.col("order_quantity"))
        .withColumn("is_otif", F.col("is_on_time") & F.col("is_in_full"))
    )
