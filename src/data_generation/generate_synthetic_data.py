"""
Generates synthetic SAP-style source data for the ISC DELIVER domain
(VBAK/VBAP/LIKP/LIPS/MARA/MARD), plus the reference tables called out as
open points in docs/mapping-spec.md (plant -> business unit, LFART decode).

Output: CSV files under data/mock_sap/.
Tunable volumes/rates live in config/data_generation_config.json; fixed
domain reference values (plants, business units, delivery/order types,
material groups) are defined below as constants.
"""
import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "data_generation_config.json"
OUTPUT_DIR = ROOT / "data" / "mock_sap"

PLANTS_BY_BU = {
    "Nexus Case": ["1000", "1010"],
    "Biodiscovery": ["2000", "2010"],
    "Precision Vanguard": ["3000", "3010"],
}
ALL_PLANTS = [plant for plants in PLANTS_BY_BU.values() for plant in plants]
STORAGE_LOCATIONS = ["0001", "0002"]

DELIVERY_TYPES = {
    "LF": "Standard Delivery",
    "LR": "Returns Delivery",
}
DELIVERY_TYPE_WEIGHTS = [0.95, 0.05]

ORDER_TYPES = {
    "TA": "Standard Order",
    "RE": "Returns Order",
}
ORDER_TYPE_WEIGHTS = [0.95, 0.05]

MATERIAL_GROUPS = ["RAW", "PACK", "FIN"]
SALES_ORG = "1000"
DISTR_CHANNEL = "10"
DIVISION = "00"
UNIT = "EA"

SALES_ORDER_NUMBER_START = 45000000
DELIVERY_NUMBER_START = 80000000


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return json.load(f)


def random_date_between(start: date, end: date) -> date:
    return start + timedelta(days=random.randint(0, (end - start).days))


def generate_plant_business_unit() -> list[dict]:
    return [
        {"WERKS": plant, "BUSINESS_UNIT": bu}
        for bu, plants in PLANTS_BY_BU.items()
        for plant in plants
    ]


def generate_delivery_type_decode() -> list[dict]:
    return [{"LFART": code, "DESCRIPTION": label} for code, label in DELIVERY_TYPES.items()]


def generate_mara(num_materials: int) -> list[dict]:
    rows = []
    for i in range(1, num_materials + 1):
        group = random.choice(MATERIAL_GROUPS)
        rows.append({
            "MATNR": f"1{i:05d}",
            "MAKTX": f"Material {i:04d} ({group})",
            "MATKL": group,
            "MEINS": UNIT,
        })
    return rows


def generate_mard(mara_rows: list[dict]) -> list[dict]:
    rows = []
    for mat in mara_rows:
        plants = random.sample(ALL_PLANTS, k=random.randint(1, min(3, len(ALL_PLANTS))))
        for plant in plants:
            rows.append({
                "MATNR": mat["MATNR"],
                "WERKS": plant,
                "LGORT": random.choice(STORAGE_LOCATIONS),
                "LABST": random.randint(50, 2000),
            })
    return rows


def generate_customers(num_customers: int) -> list[str]:
    return [f"{1000 + i:07d}" for i in range(num_customers)]


def generate_vbak(num_orders: int, customers: list[str], start_date: date, end_date: date) -> list[dict]:
    rows = []
    for i in range(1, num_orders + 1):
        order_type = random.choices(list(ORDER_TYPES), weights=ORDER_TYPE_WEIGHTS)[0]
        rows.append({
            "VBELN": str(SALES_ORDER_NUMBER_START + i),
            "ERDAT": random_date_between(start_date, end_date).isoformat(),
            "AUART": order_type,
            "KUNNR": random.choice(customers),
            "VKORG": SALES_ORG,
            "VTWEG": DISTR_CHANNEL,
            "SPART": DIVISION,
        })
    return rows


def generate_vbap(vbak_rows: list[dict], mara_rows: list[dict]) -> list[dict]:
    rows = []
    for order in vbak_rows:
        for pos in range(1, random.randint(1, 3) + 1):
            mat = random.choice(mara_rows)
            rows.append({
                "VBELN": order["VBELN"],
                "POSNR": f"{pos * 10:06d}",
                "MATNR": mat["MATNR"],
                "WERKS": random.choice(ALL_PLANTS),
                "KWMENG": random.randint(1, 100),
                "MEINS": UNIT,
            })
    return rows


def generate_likp_lips(vbak_rows: list[dict], vbap_rows: list[dict], config: dict) -> tuple[list[dict], list[dict]]:
    items_by_order: dict[str, list[dict]] = {}
    for item in vbap_rows:
        items_by_order.setdefault(item["VBELN"], []).append(item)

    likp_rows: list[dict] = []
    lips_rows: list[dict] = []
    delivery_counter = DELIVERY_NUMBER_START

    lead_time_range = config["lead_time_days_range"]
    late_range = config["late_delivery_days_range"]
    on_time_range = config["on_time_delta_days_range"]
    short_range = config["short_shipment_qty_range"]

    for order in vbak_rows:
        if random.random() < config["pct_orders_without_delivery"]:
            continue  # order still open, not yet delivered

        items = items_by_order.get(order["VBELN"], [])
        if not items:
            continue

        delivery_counter += 1
        delivery_id = str(delivery_counter)

        order_date = date.fromisoformat(order["ERDAT"])
        planned_date = order_date + timedelta(days=random.randint(*lead_time_range))
        if random.random() < config["pct_late_delivery"]:
            delta_days = random.randint(*late_range)
        else:
            delta_days = random.randint(*on_time_range)
        actual_date = planned_date + timedelta(days=delta_days)

        delivery_type = random.choices(list(DELIVERY_TYPES), weights=DELIVERY_TYPE_WEIGHTS)[0]

        likp_rows.append({
            "VBELN": delivery_id,
            "LFART": delivery_type,
            "ERDAT": order_date.isoformat(),
            "LFDAT": planned_date.isoformat(),
            "WADAT_IST": actual_date.isoformat(),
        })

        for pos, item in enumerate(items, start=1):
            if random.random() < config["pct_short_shipment"]:
                delivered_qty = max(1, round(item["KWMENG"] * random.uniform(*short_range)))
            else:
                delivered_qty = item["KWMENG"]

            lips_rows.append({
                "VBELN": delivery_id,
                "POSNR": f"{pos * 10:06d}",
                "VGBEL": item["VBELN"],
                "VGPOS": item["POSNR"],
                "MATNR": item["MATNR"],
                "WERKS": item["WERKS"],
                "LGORT": random.choice(STORAGE_LOCATIONS),
                "LFIMG": delivered_qty,
                "MEINS": UNIT,
            })

    return likp_rows, lips_rows


def write_csv(rows: list[dict], filename: str) -> None:
    if not rows:
        return
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / filename
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows):>5} rows -> {path.relative_to(ROOT)}")


def main() -> None:
    config = load_config()
    random.seed(config["seed"])

    start_date = date.fromisoformat(config["order_date_range"]["start"])
    end_date = date.fromisoformat(config["order_date_range"]["end"])

    plant_bu_rows = generate_plant_business_unit()
    delivery_type_rows = generate_delivery_type_decode()
    mara_rows = generate_mara(config["num_materials"])
    mard_rows = generate_mard(mara_rows)
    customers = generate_customers(config["num_customers"])
    vbak_rows = generate_vbak(config["num_sales_orders"], customers, start_date, end_date)
    vbap_rows = generate_vbap(vbak_rows, mara_rows)
    likp_rows, lips_rows = generate_likp_lips(vbak_rows, vbap_rows, config)

    write_csv(plant_bu_rows, "plant_business_unit.csv")
    write_csv(delivery_type_rows, "delivery_type_decode.csv")
    write_csv(mara_rows, "MARA.csv")
    write_csv(mard_rows, "MARD.csv")
    write_csv(vbak_rows, "VBAK.csv")
    write_csv(vbap_rows, "VBAP.csv")
    write_csv(likp_rows, "LIKP.csv")
    write_csv(lips_rows, "LIPS.csv")


if __name__ == "__main__":
    main()
