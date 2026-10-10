
from app.matcher import load_inventory, rank_inventory
from app.schemas import ProductSpec


def test_exact_match_ranks_first():
    spec = ProductSpec(
        product_type="bracket",
        material="stainless steel",
        length_mm=120,
        width_mm=40,
        thickness_mm=3,
        finish="brushed",
        hole_diameter_mm=8,
    )

    results = rank_inventory(spec, load_inventory())

    assert results[0]["sku"] == "BR002"
    assert results[0]["score"] == 100.0
    assert results[0]["auto_select"] is True


def test_mismatched_dimensions_prevent_auto_selection():
    spec = ProductSpec(
        product_type="bracket",
        material="stainless steel",
        length_mm=120,
        width_mm=40,
        thickness_mm=3,
        finish="brushed",
        hole_diameter_mm=8,
    )

    results = rank_inventory(spec, load_inventory())
    candidate = next(
        item for item in results if item["sku"] == "BR001"
    )

    assert candidate["score"] == 85.0
    assert candidate["auto_select"] is False
    assert candidate["mismatch_reasons"]


def test_ranking_is_deterministic():
    spec = ProductSpec(
        product_type="bracket",
        material="stainless steel",
        length_mm=120,
        width_mm=40,
        thickness_mm=3,
        finish="brushed",
        hole_diameter_mm=8,
    )

    inventory = load_inventory()

    first_run = rank_inventory(spec, inventory)
    second_run = rank_inventory(spec, inventory)

    assert [
        (item["sku"], item["score"])
        for item in first_run
    ] == [
        (item["sku"], item["score"])
        for item in second_run
    ]
