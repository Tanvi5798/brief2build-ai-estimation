
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ProductSpec(BaseModel):
    """Structured product details extracted from a sales brief."""

    model_config = ConfigDict(extra="forbid")

    product_type: str | None = None
    material: str | None = None

    length_mm: float | None = Field(default=None, gt=0)
    width_mm: float | None = Field(default=None, gt=0)
    thickness_mm: float | None = Field(default=None, gt=0)

    finish: str | None = None
    hole_diameter_mm: float | None = Field(default=None, gt=0)
    stated_count: int | None = Field(default=None, ge=0)



class FieldConfidence(BaseModel):
    level: Literal["high", "medium", "low"]
    reason: str


class ConfidenceReport(BaseModel):
    product_type: FieldConfidence | None = None
    material: FieldConfidence | None = None
    length_mm: FieldConfidence | None = None
    width_mm: FieldConfidence | None = None
    thickness_mm: FieldConfidence | None = None
    finish: FieldConfidence | None = None
    hole_diameter_mm: FieldConfidence | None = None
    stated_count: FieldConfidence | None = None


class ExtractionResult(BaseModel):
    spec: ProductSpec
    confidence: ConfidenceReport

    extraction_status: Literal["success", "fallback"]
    fallback_reason: str | None = None

    review_required: bool = False
    review_reasons: list[str] = Field(default_factory=list)

class AnalyzeRequest(BaseModel):
    brief: str


class AnalyzeResponse(BaseModel):
    result: ExtractionResult