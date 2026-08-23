# Databricks Concepts — Built, Not Just Read About

## Purpose
Companion to the Databricks Data Engineer Associate certification study: every
concept below was actually built and run against this project's real tables, not
copied from documentation. Each section cites the actual notebook, the actual
numbers produced, and — in two cases — a real mistake made and fixed along the
way, because those are usually the most instructive part.

---

## 1. Delta Time Travel
**Notebook:** `notebooks/04_delta_time_travel.py`

Every write to a Delta table is a new, numbered version in its transaction log —
no separate snapshot/backup mechanism needed. `fact_delivery_item`'s real history
by the end of this build:

| Version | Operation | What happened |
|---|---|---|
| 0 | CREATE OR REPLACE TABLE AS SELECT | Initial build (`03_gold_transformation.py`) |
| 1 | SET TBLPROPERTIES | Change Data Feed enabled |
| 2 | MERGE | Incremental upsert (§5 below) |
| 3 | OPTIMIZE | File compaction + Z-order |
| 4 | CREATE OR REPLACE TABLE AS SELECT | The Workflow Job's full-refresh run (§7 — this **reset** the table) |
| 5 | SET TBLPROPERTIES | CDF re-enabled after the reset |
| 6 | MERGE | Re-applied the incremental upsert to restore state |

`SELECT * FROM table VERSION AS OF 1` queries the table exactly as it looked
before the MERGE — no copy, no export, just a versioned read. `RESTORE TABLE
... TO VERSION AS OF n` would roll the live table back (itself logged as a new
version, so even a restore is undoable) — not executed here since it would have
discarded real history, but the syntax is one line.

## 2. OPTIMIZE + Z-ORDER
**Notebook:** `notebooks/04_delta_time_travel.py`

Small/frequent writes (every `saveAsTable`/`MERGE` run in this project added its
own files) create the classic "small file problem." `OPTIMIZE fact_delivery_item
ZORDER BY (business_unit, plant)` compacts them and co-locates rows with similar
`business_unit`/`plant` values into the same files — so a query filtering on
either column reads fewer files. Current state: `fact_delivery_item` sits at 2
files after OPTIMIZE + the later full-refresh rewrite (small dataset, so the
absolute number isn't the interesting part — the mechanism and *why* it matters
at real data volumes is).

## 3. VACUUM
**Notebook:** `notebooks/04_delta_time_travel.py`

OPTIMIZE doesn't delete the small files it replaces immediately — Time Travel and
any concurrent reader on an older version still need them. `VACUUM` removes files
no longer referenced by any version **inside the retention window** (default 7
days / 168 hours). Ran as `VACUUM ... RETAIN 168 HOURS DRY RUN` — lists candidate
files without deleting anything. This table is minutes old, so little/nothing was
eligible yet — expected, not a bug; the retention window exists specifically to
protect recent history.

## 4. Liquid Clustering
**Notebook:** `notebooks/04_delta_time_travel.py`

The newer alternative to Z-order: `ALTER TABLE t CLUSTER BY (col1, col2)`
declares clustering once and Delta maintains it incrementally on every write — no
periodic `OPTIMIZE ZORDER` job to schedule. Demonstrated on a `SHALLOW CLONE` of
`fact_delivery_item` (cheap — metadata-only clone, no data copy) so the syntax
was exercised without migrating the production table as a side effect; the clone
was dropped immediately after.

## 5. MERGE INTO (Upsert) + Change Data Feed
**Notebook:** `notebooks/06_merge_and_cdf.py`

`02_silver_transformation.py`/`03_gold_transformation.py` always do a full
`mode("overwrite")` — correct, but wasteful at real scale, since every run
reprocesses every row even when nothing changed. This notebook demonstrates the
incremental alternative: a "day 2" batch (`src/data_generation/generate_incremental_data.py`
— 60 new orders, 118 new delivery items, reusing existing customers/materials so
FKs still resolve) plus one manufactured **correction** to an already-existing
delivery item, merged via `MERGE INTO ... WHEN MATCHED THEN UPDATE ... WHEN NOT
MATCHED THEN INSERT`.

Change Data Feed (`delta.enableChangeDataFeed = true`, enabled before the write
whose changes matter) then proved the MERGE did a genuine upsert, not just an
append — `table_changes('fact_delivery_item', 1, 2)` returned:

| `_change_type` | rows |
|---|---|
| insert | 118 |
| update_preimage | 1 |
| update_postimage | 1 |

118 inserts (the new delivery items) + 1 update (before/after image pair for the
corrected row) — exactly matching what went in.

## 6. Delta Live Tables / Lakeflow Declarative Pipelines
**Notebook:** `notebooks/dlt_pipeline.py` · **Pipeline:** `sap_deliver_dlt` (bundle-managed, §7)

A full bronze→silver→gold re-implementation of the classic notebooks, but
**declarative**: each `@dlt.table` states what a table should contain; the DLT
runtime resolves the dependency graph (via `dlt.read()` references between
tables) and handles execution order, retries, and data-quality enforcement
itself. Runs in its own schema (`main.sap_deliver_dlt`) side-by-side with the
classic pipeline, not replacing it.

Expectations formalize the exact rules UAT #7 and #14 found by hand in the
classic pipeline:
- `@dlt.expect_or_drop("valid_key", ...)` / `valid_quantities` — **enforced**,
  violating rows dropped.
- `@dlt.expect("has_planned_date", ...)` — **flagged, not dropped** (UAT #7: a
  missing planned date is incomplete data, not invalid data).
- `@dlt.expect("valid_otif_logic", "is_on_time IS NULL OR is_otif = (is_on_time
  AND is_in_full)")` — a self-consistency check on the KPI logic itself.

Result: **1,407 rows, 923 OTIF-true** — identical to the classic pipeline's
numbers, confirming the re-implementation is logically equivalent. All 4
expectations passed 100% (`dropped_records: 0, warned_records: 0` in the
pipeline's event log) — this dataset happens to have no missing planned dates,
so `has_planned_date` had nothing to flag; the mechanism is proven regardless.

## 7. Databricks Asset Bundle — Multi-task Workflow
**Config:** `databricks.yml`

Replaced the ad hoc `databricks workspace import` + `databricks jobs submit`
pattern used while building this project with a single source-controlled
definition: a 3-task Job (`bronze → silver → gold`, via `depends_on`) and the DLT
pipeline, both deployed with `databricks bundle deploy`. A daily schedule is
declared (`quartz_cron_expression`) but left `PAUSED` — the syntax is
demonstrated without actually running unattended.

**A real lesson from running it:** triggering this job (`databricks bundle run
sap_deliver_bronze_to_gold`) re-ran the classic full-overwrite notebooks against
the *same* `fact_delivery_item` table that §5's MERGE had just updated to 1,525
rows — and silently reset it back to 1,407, discarding the incremental upsert
(visible as version 4, "CREATE OR REPLACE TABLE AS SELECT," in the history
table in §1). This is a genuine, common real-world pipeline-design mistake: a
full-refresh job and an incremental-upsert job must not target the same table
without coordination (a watermark, a "last processed" checkpoint, or simply never
running both against the same table). Fixed by re-running §5's MERGE notebook to
restore state — left in the history on purpose, as the more useful artifact than
a clean run would have been.

## 8. Unity Catalog Row-Level Security
**Notebook:** `notebooks/07_row_level_security.py` — closes ticket DELIVER-112

A SQL row-filter function (`main.sap_deliver_gold.business_unit_row_filter`),
attached to `fact_delivery_item` and `dim_warehouse` via `ALTER TABLE ... SET ROW
FILTER ... ON (business_unit)`.

**Two honest caveats:**
1. The per-business-unit groups the filter is meant to check
   (`bu_nexus_case`, `bu_biodiscovery`, `bu_precision_vanguard`) couldn't be
   created — `databricks account groups create` returned `Not Found`; the
   `andrmtts` profile isn't an account admin on this workspace. The filter
   function and `ALTER TABLE` still work correctly regardless (referencing a
   not-yet-existing group in `is_account_group_member()` isn't a DDL-time
   error, it just evaluates `false`) — only the "does it actually restrict a
   second user" check is untested, and there's no second identity in this
   workspace to test that with anyway.
2. **A real mistake, caught and fixed live:** the first version of the filter
   used `is_account_group_member('admins')` as the bypass for the admin user,
   assuming workspace-admin status would satisfy it. It didn't —
   `is_account_group_member()` checks **account-level** group membership, a
   distinct thing from workspace-admin status. That version returned **0 rows**
   on both tables, including for the workspace owner — `SELECT
   is_account_group_member('admins')` evaluated to `false` for
   `andrmtts@gmail.com`. Diagnosed and fixed with a `current_user()` bypass
   instead (a pragmatic substitute for a single-workspace project with no
   account-group management available — a real multi-tenant setup would use a
   properly provisioned account-level group).

## 9. SQL Warehouse + Statement Execution API
**Queries:** `sql/*.sql`

Closes a gap hit earlier in this project: the SQL Statement Execution API needs a
`warehouse_id`, and none was available at the time. Used the workspace's existing
"Serverless Starter Warehouse" (2X-Small, serverless, 10-minute auto-stop —
**no new billable resource created**) to run all three `sql/*.sql` dashboard
queries end-to-end via `POST /api/2.0/sql/statements`, confirmed `SUCCEEDED` with
real row counts, then explicitly stopped the warehouse (`databricks warehouses
stop`) rather than leaving it idling on auto-stop.

## 10. Auto Loader (`cloudFiles`)
**Notebook:** `notebooks/05_bronze_autoloader.py`

Alternative to `01_bronze_ingestion.py`'s one-shot batch read: ingests
incrementally, tracking already-processed files via a checkpoint
(`cloudFiles.schemaLocation` + `checkpointLocation`), so re-running the notebook
only picks up genuinely new files — the same mechanism as real streaming
ingestion, run here in batch mode (`trigger(availableNow=True)`) since there's no
live source system.

Verified with two real runs:
1. `VBAK.csv` (800 rows) + `increment/VBAK_increment.csv` (60 rows, already
   present) → **860 rows** ingested together on the first run.
2. A further `increment2/VBAK_increment2.csv` (10 rows) uploaded, second run →
   **870 rows** — and the `_source_file` breakdown confirmed only the 10 new
   rows were processed; the checkpoint correctly skipped re-reading the other
   two files.

`pathGlobFilter: "VBAK*.csv"` was necessary — the watched path also holds
VBAP/LIKP/LIPS/MARA/reference CSVs, and without the filter Auto Loader would try
to force every file in the folder into the VBAK schema.
