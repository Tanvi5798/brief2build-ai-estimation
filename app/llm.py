
import os
from dotenv import load_dotenv

load_dotenv()
from google import genai
from pydantic import ValidationError

from app.schemas import (
    ConfidenceReport,
    ExtractionResult,
    ProductSpec,
)
from app.consistency import check_measurement_consistency


def make_gemini_schema() -> dict:
    """Build a Gemini-compatible schema."""

    schema = ExtractionResult.model_json_schema()

    def remove_unsupported_keys(value):
        if isinstance(value, dict):
            value.pop("additionalProperties", None)
            value.pop("exclusiveMinimum", None)

            for child in value.values():
                remove_unsupported_keys(child)

        elif isinstance(value, list):
            for child in value:
                remove_unsupported_keys(child)

    remove_unsupported_keys(schema)
    return schema


def enforce_review_rules(
    result: ExtractionResult,
) -> ExtractionResult:
    """Require human review for low-confidence fields."""

    reasons = list(result.review_reasons)

    confidence_fields = result.confidence.model_dump(
        exclude_none=True
    )

    for field_name, details in confidence_fields.items():
        if details["level"] == "low":
            result.review_required = True

            reason = f"{field_name}: {details['reason']}"

            if reason not in reasons:
                reasons.append(reason)

    result.review_reasons = reasons
    return result


def make_fallback_result(reason: str) -> ExtractionResult:
    """Return an empty result when extraction fails."""

    return ExtractionResult(
        spec=ProductSpec(),
        confidence=ConfidenceReport(),
        extraction_status="fallback",
        fallback_reason=reason,
        review_required=True,
        review_reasons=[
            "Extraction failed. Human review is required."
        ],
    )


def extract_product_spec(
    customer_request: str,
) -> ExtractionResult:
    """Extract structured product details from a customer request."""

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    client = genai.Client(api_key=api_key)

    prompt = f"""
Extract product details from the customer request.

Rules:
- Do not invent missing values.
- Use null when a value is not stated or cannot be determined.
- Dimensions must use millimetres.
- Mark uncertain extractions with an appropriate confidence level.
- Require human review for ambiguous or conflicting requirements.
- Return only data that follows the requested schema.

Customer request:
{customer_request}
"""

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": make_gemini_schema(),
        },
    )

    if not response.text:
        return make_fallback_result(
            "Gemini returned an empty response."
        )

    try:
        result = ExtractionResult.model_validate_json(response.text)

        result = check_measurement_consistency(
            customer_request,
            result,
        )

        return enforce_review_rules(result)

    except ValidationError:
        return make_fallback_result(
            "Gemini returned data that failed schema validation."
        )
