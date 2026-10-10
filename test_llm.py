from unittest.mock import patch, Mock

from app.llm import extract_product_spec
from app.schemas import (
    ProductSpec,
    FieldConfidence,
    ConfidenceReport,
    ExtractionResult,
)
from app.llm import enforce_review_rules
from app.consistency import check_measurement_consistency

def test_low_confidence_requires_review():
    result = ExtractionResult(
        spec=ProductSpec(product_type="bracket"),
        confidence=ConfidenceReport(
            length_mm=FieldConfidence(
                level="low",
                reason="Conflicting values: 100 mm and 120 mm",
            )
        ),
        extraction_status="success",
        review_required=False,
    )

    updated = enforce_review_rules(result)

    assert updated.review_required is True
    assert (
        "length_mm: Conflicting values: 100 mm and 120 mm"
        in updated.review_reasons
    )


def test_high_confidence_does_not_force_review():
    result = ExtractionResult(
        spec=ProductSpec(product_type="bracket"),
        confidence=ConfidenceReport(
            length_mm=FieldConfidence(
                level="high",
                reason="Explicitly stated as 120 mm",
            )
        ),
        extraction_status="success",
        review_required=False,
    )

    updated = enforce_review_rules(result)

    assert updated.review_required is False
    assert updated.review_reasons == []

def make_result(length_mm):
    return ExtractionResult(
        spec=ProductSpec(
            product_type="bracket",
            length_mm=length_mm,
        ),
        confidence=ConfidenceReport(),
        extraction_status="success",
    )


def test_equivalent_cm_and_mm_pass():
    result = make_result(120)

    updated = check_measurement_consistency(
        "The length is 12 cm.",
        result,
    )

    assert updated.review_required is False


def test_extracted_value_inside_explicit_range_passes():
    result = make_result(110)

    updated = check_measurement_consistency(
        "The length must be between 100 mm and 120 mm.",
        result,
    )

    assert updated.review_required is False


def test_conflicting_exact_lengths_require_review():
    result = make_result(100)

    updated = check_measurement_consistency(
        "The length is 100 mm. The required length is 120 mm.",
        result,
    )

    assert updated.review_required is True
    assert any(
        "conflicting measurements" in reason
        for reason in updated.review_reasons
    )


def test_extracted_value_mismatch_requires_review():
    result = make_result(12)

    updated = check_measurement_consistency(
        "The bracket length should be 12 cm.",
        result,
    )

    assert updated.review_required is True
    assert any(
        "does not match" in reason
        for reason in updated.review_reasons
    )
def test_missing_extracted_length_requires_review():
    result = make_result(None)

    updated = check_measurement_consistency(
        "The length is 100 mm.",
        result,
    )

    assert updated.review_required is True
    assert any(
        "no value was extracted" in reason
        for reason in updated.review_reasons
    )

def test_measurements_before_dimension_words_pass():
    request = (
        "I need 100 stainless steel washers, "
        "20 mm in length, 10 mm wide, and 2 mm thick, "
        "with a polished finish."
    )

    result = make_result(length_mm=20)
    result.spec.width_mm = 10
    result.spec.thickness_mm = 2

    from app.consistency import check_measurement_consistency

    checked = check_measurement_consistency(request, result)

    assert checked.review_required is False
    assert checked.review_reasons == []

from fastapi.testclient import TestClient
from google.genai.errors import ServerError
from unittest.mock import patch

from app.main import app

client = TestClient(app)


def test_gemini_server_error_returns_503():
    with patch(
        "app.main.extract_product_spec",
        side_effect=ServerError(
            "Temporary Gemini outage",
            response_json={"error": {"code": 503}},
        ),
    ):
        response = client.post(
    "/analyze",
    data={"brief": "100 steel washers"},
)

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Gemini service is temporarily unavailable. Please try again later."
    )

def test_empty_gemini_response_returns_fallback():
    mock_response = Mock()
    mock_response.text = ""

    with patch(
        "app.llm.genai.Client"
    ) as mock_client:
        mock_client.return_value.models.generate_content.return_value = (
            mock_response
        )

        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            result = extract_product_spec("100 steel washers")

    assert result.extraction_status == "fallback"
    assert result.review_required is True
    assert result.spec.product_type is None


def test_invalid_gemini_json_returns_fallback():
    mock_response = Mock()
    mock_response.text = '{"unexpected": "invalid data"}'

    with patch(
        "app.llm.genai.Client"
    ) as mock_client:
        mock_client.return_value.models.generate_content.return_value = (
            mock_response
        )

        with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
            result = extract_product_spec("100 steel washers")

    assert result.extraction_status == "fallback"
    assert result.review_required is True
    assert result.spec.product_type is None
