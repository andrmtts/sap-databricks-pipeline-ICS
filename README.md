# SAP DELIVER Domain → Databricks Data Product

Portfolio project simulating a SAP-style → Databricks data pipeline for the
ISC **DELIVER** domain (shipments, deliveries, warehouse management), built
with functional documentation equivalent to a real project: discovery,
mapping specs, UAT, tracking.

All data is **synthetic** — no real SAP system or data is involved.

## Stack
- Python (synthetic data generation)
- Databricks notebooks (PySpark, run manually by the project owner)
- Delta Lake (bronze / silver / gold)
- SQL (final dashboard queries)

## Repo layout
| Path | Contents |
|---|---|
| [`data/mock_sap/`](data/mock_sap) | Synthetic source CSVs (VBAK/VBAP/LIKP/LIPS/MARA/MARD + reference tables) |
| [`src/data_generation/`](src/data_generation) | Script that generates the synthetic data |
| [`config/`](config) | Tunable parameters for data generation |
| [`notebooks/`](notebooks) | Databricks notebooks (bronze/silver/gold), run manually in Databricks |
| [`sql/`](sql) | Final SQL queries for the dashboard |
| [`docs/`](docs) | Functional documentation — business requirements, mapping spec, data dictionary, KPI definitions, ERD, UAT, tracking board |
| [`dashboards/`](dashboards) | Dashboard exports/screenshots |

## Status
- **Phase 1 — Synthetic data generation**: done. See [`docs/data-dictionary.md`](docs/data-dictionary.md).
- **Phase 2 — Bronze ingestion**: notebook written ([`notebooks/01_bronze_ingestion.py`](notebooks/01_bronze_ingestion.py)), pending manual run in Databricks.
- **Phase 3 — Silver/gold transformation + KPIs**: not started.
- **Phase 4 — Dashboard SQL**: not started.
- **Phase 5 — Functional documentation**: business requirements, mapping spec, UAT test cases, and tracking board drafted in [`docs/`](docs).

## Documentation
- [Business requirements](docs/business-requirements.md)
- [Mapping spec (source → gold)](docs/mapping-spec.md)
- [Data dictionary](docs/data-dictionary.md)
- [UAT test cases](docs/uat-test-cases.md)
- [Tracking board](docs/tracking-board.md)
