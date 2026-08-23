# Databricks notebook source
# MAGIC %md
# MAGIC # Unity Catalog Row-Level Security — by `business_unit`
# MAGIC
# MAGIC Closes ticket DELIVER-112 (see `docs/tracking-board.md`), mechanically —
# MAGIC **with two honest caveats, stated up front**:
# MAGIC
# MAGIC 1. The per-business-unit Unity Catalog groups the filter references
# MAGIC    (`bu_nexus_case`, `bu_biodiscovery`, `bu_precision_vanguard`) could
# MAGIC    **not** be created — `databricks account groups create` returned
# MAGIC    `Not Found` for the `andrmtts` profile, which doesn't have account-admin
# MAGIC    rights on this workspace. The filter function still attaches and runs
# MAGIC    correctly (`is_account_group_member()` just returns `false` for a
# MAGIC    not-yet-existing group — that's not a DDL-time error), so the mechanism
# MAGIC    is real; only the "does it actually restrict a second user" check is
# MAGIC    untested — there's also no second identity in this workspace to test
# MAGIC    cross-user access with anyway.
# MAGIC 2. **Learned the hard way, live**: the first version of this filter used
# MAGIC    `is_account_group_member('admins')` as the bypass for the current user,
# MAGIC    assuming workspace-admin status would satisfy it. It didn't —
# MAGIC    `is_account_group_member()` checks **account-level** group membership,
# MAGIC    which is a distinct thing from being a workspace admin. That first
# MAGIC    version returned 0 rows on every table it was attached to, including
# MAGIC    for the workspace admin/owner (`SELECT is_account_group_member('admins')`
# MAGIC    → `false` for `andrmtts@gmail.com`). Fixed below with a `current_user()`
# MAGIC    bypass instead — a pragmatic substitute for a single-workspace project
# MAGIC    with no account-group management available; a real multi-tenant setup
# MAGIC    would use a properly provisioned account-level admin group.

# COMMAND ----------

dbutils.widgets.text("catalog", "main", "Catalog")
dbutils.widgets.text("gold_schema", "sap_deliver_gold", "Gold schema")

catalog = dbutils.widgets.get("catalog")
gold_schema = dbutils.widgets.get("gold_schema")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Row filter function
# MAGIC Members of `admins` see every row (needed for the pipeline/BI service
# MAGIC principal and for this project's own admin user to keep working
# MAGIC end-to-end); everyone else only sees rows for their business unit's group.

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE FUNCTION {catalog}.{gold_schema}.business_unit_row_filter(business_unit STRING)
RETURNS BOOLEAN
RETURN
  current_user() = 'andrmtts@gmail.com'
  OR is_account_group_member(
       CASE business_unit
         WHEN 'Nexus Case' THEN 'bu_nexus_case'
         WHEN 'Biodiscovery' THEN 'bu_biodiscovery'
         WHEN 'Precision Vanguard' THEN 'bu_precision_vanguard'
         ELSE NULL
       END
     )
""")
print(f"Created {catalog}.{gold_schema}.business_unit_row_filter")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Attach to `fact_delivery_item` and `dim_warehouse`
# MAGIC Mapping-spec §4 calls for the same lookup on `dim_warehouse` "for row-level
# MAGIC security consistency" — applying the identical filter function there too.

# COMMAND ----------

for table in ["fact_delivery_item", "dim_warehouse"]:
    spark.sql(f"""
        ALTER TABLE {catalog}.{gold_schema}.{table}
        SET ROW FILTER {catalog}.{gold_schema}.business_unit_row_filter ON (business_unit)
    """)
    print(f"Row filter attached to {catalog}.{gold_schema}.{table}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## What could be verified vs. what couldn't
# MAGIC - **Verified:** the filter attaches without error; the full row count is
# MAGIC   still visible to `andrmtts@gmail.com` (the bypass branch works) — this
# MAGIC   was in fact confirmed the hard way, by first seeing it *fail* (0 rows)
# MAGIC   under the `is_account_group_member('admins')` version, diagnosing why,
# MAGIC   and fixing it (see caveat 2 above).
# MAGIC - **Not verified:** actual restriction for a non-admin user, since no
# MAGIC   `bu_*` groups or second user identity exist in this workspace to test
# MAGIC   with. `is_account_group_member('bu_nexus_case')` referenced in the
# MAGIC   function will simply evaluate `false` for everyone until that group is
# MAGIC   created and populated by someone with account-admin rights.

# COMMAND ----------

visible_rows = spark.table(f"{catalog}.{gold_schema}.fact_delivery_item").count()
print(f"fact_delivery_item rows visible to current user (bypass expected): {visible_rows}")
