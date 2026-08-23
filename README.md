
# SAP DELIVER Domain → Databricks Data Product
Portfolio project simulating a SAP-style → Databricks data pipeline for the
ISC **DELIVER** domain (shipments, deliveries, warehouse management), built
with functional documentation equivalent to a real project: discovery,
mapping specs, UAT, tracking.

All data is **synthetic** — no real SAP system or data is involved.

## Stack
- Python (synthetic data generation)
- Databricks notebooks (PySpark, run via Databricks Connect / CLI)
- Delta Lake (bronze / silver / gold)
- SQL (final dashboard queries)

## Repo layout
| Path | Contents |
|---|---|
| [`data/mock_sap/`](data/mock_sap) | Synthetic source CSVs (VBAK/VBAP/LIKP/LIPS/MARA/MARD + reference tables) |
| [`src/data_generation/`](src/data_generation) | Script that generates the synthetic data |
| [`config/`](config) | Tunable parameters for data generation |
| [`notebooks/`](notebooks) | Databricks notebooks (bronze/silver/gold), run via Databricks Connect / CLI |
| [`sql/`](sql) | Final SQL queries for the dashboard |
| [`docs/`](docs) | Functional documentation — business requirements, mapping spec, data dictionary, KPI definitions, ERD, UAT, tracking board |
| [`dashboards/`](dashboards) | Dashboard exports/screenshots (manual — see Phase 4) |

## Status
- **Phase 0 — Setup**: done. Local environment (`sdpICS.venv`, Python 3.12) and Databricks Connect
  are configured end-to-end — notebooks now run directly from this repo against the workspace's
  serverless compute, no manual copy-paste into the Databricks UI required.
- **Phase 1 — Synthetic data generation**: done. See [`docs/data-dictionary.md`](docs/data-dictionary.md).
- **Phase 2 — Bronze ingestion**: done. [`notebooks/01_bronze_ingestion.py`](notebooks/01_bronze_ingestion.py)
  run against `main.sap_deliver_bronze` (8 bronze Delta tables), source CSVs landed in the
  `main.sap_deliver.raw_files` volume.
- **Phase 3 — Silver/gold transformation + KPIs**: done.
  [`notebooks/02_silver_transformation.py`](notebooks/02_silver_transformation.py) and
  [`notebooks/03_gold_transformation.py`](notebooks/03_gold_transformation.py) run against
  `main.sap_deliver_silver` and `main.sap_deliver_gold` (`fact_delivery_item`, `dim_material`,
  `dim_warehouse`). KPI formulas in [`docs/kpi-definitions.md`](docs/kpi-definitions.md),
  resulting model in [`docs/erd.md`](docs/erd.md).
- **Phase 4 — Dashboard SQL**: done. Tested queries in [`sql/`](sql) for OTIF trend, lead time,
  and fill rate — ready to plug into a Databricks AI/BI Dashboard or Power BI. Building the
  dashboard itself is a manual step, out of scope for this repo.
- **Phase 5 — Functional documentation**: business requirements, mapping spec, UAT test cases,
  and tracking board drafted in [`docs/`](docs).
- **Phase 6 — Wrap-up**: done.

## Documentation
- [Business requirements](docs/business-requirements.md)
- [Mapping spec (source → gold)](docs/mapping-spec.md)
- [Data dictionary](docs/data-dictionary.md)
- [KPI definitions](docs/kpi-definitions.md)
- [ERD](docs/erd.md)
- [UAT test cases](docs/uat-test-cases.md)
- [Tracking board](docs/tracking-board.md)
