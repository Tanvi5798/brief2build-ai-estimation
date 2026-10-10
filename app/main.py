
from pathlib import Path
import tempfile

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from google.genai.errors import ServerError

from app.llm import extract_product_spec
from app.matcher import rank_inventory
from app.schemas import AnalyzeRequest, AnalyzeResponse
from app.vision import estimate_hole_count

app = FastAPI(title="Product Brief Analyzer")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/analyze")
async def analyze_product(
    brief: str = Form(...),
    image: UploadFile | None = File(None),
):
    try:
        result = extract_product_spec(brief)
        candidates = rank_inventory(result.spec)

        image_estimate = None

        if image is not None:
            suffix = Path(image.filename or "").suffix or ".png"

            with tempfile.NamedTemporaryFile(
                suffix=suffix,
                delete=False,
            ) as temp_file:
                temp_path = Path(temp_file.name)
                temp_file.write(await image.read())

            try:
                image_estimate = estimate_hole_count(temp_path)
            finally:
                temp_path.unlink(missing_ok=True)

        review_reasons = list(result.review_reasons)

        if image_estimate is not None:
            stated_count = result.spec.stated_count
            detected_count = image_estimate["estimated_hole_count"]

            if stated_count is not None and stated_count != detected_count:
                result.review_required = True
                review_reasons.append(
                    f"Brief states {stated_count} items/holes, "
                    f"but image estimate is {detected_count}."
                )

            if image_estimate["review_required"]:
                result.review_required = True
                review_reasons.append(
                    "Image count requires manual review."
                )

        result.review_reasons = list(dict.fromkeys(review_reasons))

        return {
            "result": result,
            "inventory_candidates": candidates[:3],
            "image_estimate": image_estimate,
        }

    except ServerError as exc:
        raise HTTPException(
            status_code=503,
            detail="Gemini service is temporarily unavailable. Please try again later.",
        ) from exc

    except RuntimeError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc
