# Databricks notebook source
# MAGIC %md
# MAGIC # Delta Lake Operations — Time Travel, OPTIMIZE, VACUUM, Liquid Clustering
# MAGIC
# MAGIC Run **after** `06_merge_and_cdf.py` — that notebook's MERGE is what gives
# MAGIC `fact_delivery_item` a real version history (v0 create, v1 enable CDF, v2
# MAGIC MERGE) to travel across. Everything here operates on the real gold table
# MAGIC built by this project, not a throwaway example table.

# COMMAND ----------

dbutils.widgets.text("catalog", "main", "Catalog")
dbutils.widgets.text("gold_schema", "sap_deliver_gold", "Gold schema")

catalog = dbutils.widgets.get("catalog")
gold_schema = dbutils.widgets.get("gold_schema")
fact_table = f"{catalog}.{gold_schema}.fact_delivery_item"

# COMMAND ----------

# MAGIC %md
# MAGIC ## Time Travel
# MAGIC `DESCRIBE HISTORY` lists every version with who/what/when. `VERSION AS OF`
# MAGIC (or `TIMESTAMP AS OF`) queries the table exactly as it looked at that point —
# MAGIC no separate backup/snapshot table needed, it's built into the transaction log.

# COMMAND ----------

display(spark.sql(f"DESCRIBE HISTORY {fact_table}"))

# COMMAND ----------

before_merge_count = spark.sql(f"SELECT COUNT(*) AS n FROM {fact_table} VERSION AS OF 1").collect()[0]["n"]
after_merge_count = spark.sql(f"SELECT COUNT(*) AS n FROM {fact_table} VERSION AS OF 2").collect()[0]["n"]
current_count = spark.table(fact_table).count()
print(f"v1 (pre-merge): {before_merge_count} rows")
print(f"v2 (post-merge): {after_merge_count} rows")
print(f"current (unversioned read): {current_count} rows")

# COMMAND ----------

# MAGIC %md
# MAGIC **`RESTORE TABLE`** would roll the live table back to an older version
# MAGIC (`RESTORE TABLE {fact_table} TO VERSION AS OF 1`) — logged as a new version
# MAGIC itself, so even a restore can be undone. Not executed here (it would discard
# MAGIC the MERGE just demonstrated); the syntax is the point.

# COMMAND ----------

# MAGIC %md
# MAGIC ## OPTIMIZE + Z-ORDER
# MAGIC Small Delta writes create many small files (each `saveAsTable`/`MERGE` run
# MAGIC added its own files). `OPTIMIZE` compacts them; `ZORDER BY` co-locates rows
# MAGIC with similar values in the given columns into the same files, so a query
# MAGIC filtering on `business_unit`/`plant` reads fewer files.

# COMMAND ----------

files_before = spark.sql(f"DESCRIBE DETAIL {fact_table}").select("numFiles").collect()[0]["numFiles"]

optimize_result = spark.sql(f"OPTIMIZE {fact_table} ZORDER BY (business_unit, plant)")
display(optimize_result)

files_after = spark.sql(f"DESCRIBE DETAIL {fact_table}").select("numFiles").collect()[0]["numFiles"]
print(f"numFiles before OPTIMIZE: {files_before}, after: {files_after}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## VACUUM
# MAGIC OPTIMIZE doesn't delete the old small files immediately — they're kept so
# MAGIC Time Travel / concurrent readers on older versions still work. `VACUUM`
# MAGIC removes files no longer referenced by any version **within the retention
# MAGIC window** (default 7 days = 168 hours). `DRY RUN` lists what *would* be
# MAGIC deleted without deleting anything — the safe way to check before running it
# MAGIC for real. This table is minutes old, so little/nothing is eligible yet at the
# MAGIC default retention; that's expected, not a bug.

# COMMAND ----------

display(spark.sql(f"VACUUM {fact_table} RETAIN 168 HOURS DRY RUN"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Liquid Clustering — the newer alternative to Z-ORDER
# MAGIC Z-ORDER is a one-time layout choice you have to re-run manually after every
# MAGIC batch of writes. Liquid Clustering (`CLUSTER BY`) is declared once on the
# MAGIC table and Delta maintains the clustering incrementally on every write —
# MAGIC no periodic OPTIMIZE ZORDER job to schedule. Demonstrated on a cheap clone
# MAGIC (`CREATE TABLE ... SHALLOW CLONE`) so the production fact table isn't
# MAGIC migrated as a side effect of a demo.

# COMMAND ----------

clone_table = f"{catalog}.{gold_schema}.fact_delivery_item_liquid_demo"
spark.sql(f"CREATE OR REPLACE TABLE {clone_table} SHALLOW CLONE {fact_table}")
spark.sql(f"ALTER TABLE {clone_table} CLUSTER BY (business_unit, plant)")
display(spark.sql(f"DESCRIBE {clone_table}"))
spark.sql(f"DROP TABLE {clone_table}")
print(f"{clone_table}: clustering syntax demonstrated, clone dropped")
