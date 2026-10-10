
import csv
from pathlib import Path

from app.schemas import ProductSpec


INVENTORY_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "inventory.csv"
)

FIELD_WEIGHTS = {
    "product_type": 25,
    "material": 20,
    "length_mm": 15,
    "width_mm": 15,
    "thickness_mm": 10,
    "finish": 10,
    "hole_diameter_mm": 5,
}


def load_inventory() -> list[dict]:
    """Load inventory records from the CSV file."""

    with INVENTORY_PATH.open(
        mode="r",
        newline="",
        encoding="utf-8",
    ) as file:
        return list(csv.DictReader(file))


def score_candidate(
    spec: ProductSpec,
    item: dict,
) -> dict:
    """Score one inventory item against the requested specification."""

    matched_weight = 0
    compared_weight = 0
    match_reasons = []
    mismatch_reasons = []

    for field, weight in FIELD_WEIGHTS.items():
        requested = getattr(spec, field)
        available = item.get(field, "")

        # Missing requirements cannot count as confirmed matches.
        if requested is None or str(requested).strip() == "":
            continue

        compared_weight += weight

        if field.endswith("_mm"):
            try:
                requested_value = float(requested)
                available_value = float(available)
            except (TypeError, ValueError):
                mismatch_reasons.append(f"{field}: unavailable")
                continue

            if abs(requested_value - available_value) <= 0.001:
                matched_weight += weight
                match_reasons.append(f"{field}: exact match")
            else:
                mismatch_reasons.append(
                    f"{field}: requested {requested_value:g}, "
                    f"inventory has {available_value:g}"
                )
        else:
            if str(requested).strip().casefold() == str(
                available
            ).strip().casefold():
                matched_weight += weight
                match_reasons.append(f"{field}: exact match")
            else:
                mismatch_reasons.append(
                    f"{field}: requested {requested}, "
                    f"inventory has {available}"
                )

    if compared_weight == 0:
        score = 0.0
    else:
        score = round(
            matched_weight / compared_weight * 100,
            2,
        )

    return {
        "sku": item["sku"],
        "score": score,
        "stock_quantity": int(item["stock_quantity"]),
        "match_reasons": match_reasons,
        "mismatch_reasons": mismatch_reasons,
        "auto_select": (
            compared_weight > 0
            and score >= 80
            and not mismatch_reasons
        ),
    }


def rank_inventory(
    spec: ProductSpec,
    inventory: list[dict] | None = None,
) -> list[dict]:
    """Return inventory candidates in deterministic score order."""

    if inventory is None:
        inventory = load_inventory()

    results = [
        score_candidate(spec, item)
        for item in inventory
    ]

    results.sort(
        key=lambda result: (
            -result["score"],
            result["sku"],
        )
    )

    return results
