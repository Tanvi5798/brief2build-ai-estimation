
from fastapi.testclient import TestClient

from app.main import app
from app.schemas import (
    ConfidenceReport,
    ExtractionResult,
    ProductSpec,
)

client = TestClient(app)


def make_result(stated_count=None):
    return ExtractionResult(
        spec=ProductSpec(
            product_type="bracket",
            material="stainless steel",
            stated_count=stated_count,
        ),
        confidence=ConfidenceReport(),
        extraction_status="success",
    )


def test_analyze_without_image(monkeypatch):
    monkeypatch.setattr(
        "app.main.extract_product_spec",
        lambda brief: make_result(),
    )
    monkeypatch.setattr(
        "app.main.rank_inventory",
        lambda spec: [{"sku": "BR002", "score": 100.0}],
    )

    response = client.post(
        "/analyze",
        data={"brief": "Stainless steel bracket"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["result"]["spec"]["product_type"] == "bracket"
    assert body["inventory_candidates"][0]["sku"] == "BR002"
    assert body["image_estimate"] is None


def test_analyze_with_image_and_count_mismatch(monkeypatch):
    monkeypatch.setattr(
        "app.main.extract_product_spec",
        lambda brief: make_result(stated_count=3),
    )
    monkeypatch.setattr(
        "app.main.rank_inventory",
        lambda spec: [],
    )
    monkeypatch.setattr(
        "app.main.estimate_hole_count",
        lambda path: {
            "estimated_hole_count": 2,
            "confidence": {
                "level": "medium",
                "reason": "Test estimate",
            },
            "review_required": False,
            "method": "test",
        },
    )

    with open("data/images/holes_3.png", "rb") as image_file:
        response = client.post(
            "/analyze",
            data={"brief": "Bracket with 3 holes"},
            files={
                "image": (
                    "holes_3.png",
                    image_file,
                    "image/png",
                )
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["image_estimate"]["estimated_hole_count"] == 2
    assert body["result"]["review_required"] is True
    assert any(
        "Brief states 3" in reason
        for reason in body["result"]["review_reasons"]
    )
