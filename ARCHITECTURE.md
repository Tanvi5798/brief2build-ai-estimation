# Brief2Build Architecture

## 1. Purpose

Brief2Build is a prototype API that turns a natural-language product brief, optionally accompanied by an image, into a structured product specification and a ranked list of matching inventory items. It also reports uncertainty and review requirements rather than treating every automated result as definitive.

This is an evaluation prototype, not a production-ready purchasing system.

## 2. High-level request flow

```text
Client
  |
  | POST /analyze (brief + optional image)
  v
app/main.py — FastAPI endpoint
  |
  +--> app/llm.py — extract structured specification using Gemini
  |        |
  |        v
  |    app/schemas.py — validate structured data
  |        |
  |        v
  |    app/consistency.py — check conflicts, missing values,
  |                         units and plausibility; flag review needs
  |
  +--> app/matcher.py — compare the resulting specification
  |                     with data/inventory.csv and rank candidates
  |
  +--> app/vision.py — when an image is supplied, estimate hole count
  |                    using OpenCV image processing
  |
  v
API response — extracted specification, confidence/review information,
               inventory candidates and image-derived information where used
```

The diagram is a logical overview. The exact order and conditional behavior are implemented in `app/main.py`; consult that file as the source of truth if the flow changes.

## 3. Main components

### `app/main.py` — API orchestration

- Defines the FastAPI application and the `/health` and `/analyze` endpoints.
- Accepts a brief and an optional uploaded image.
- Coordinates extraction, validation/consistency checks, inventory matching and image analysis.
- Converts expected failures into API responses instead of requiring callers to interpret raw internal exceptions.

### `app/schemas.py` — data contracts

- Defines Pydantic models for the product specification and analysis results.
- Represents product attributes such as product type, material, dimensions, finish and hole diameter.
- Carries confidence and review information so uncertain or conflicting outputs can be surfaced.
- Uses schema validation to reject data that does not conform to the declared contract.

### `app/llm.py` — language-model extraction

- Uses the Gemini API to extract structured attributes from the natural-language brief.
- Adapts the schema sent to Gemini to avoid unsupported schema keywords, while retaining application-side validation.
- Handles empty or malformed model output and API errors with fallback/error behavior.
- The language model proposes a specification; downstream validation and matching remain separate steps.

### `app/consistency.py` — specification checks

- Checks for missing values, conflicting measurements and implausible or inconsistent dimensions.
- Handles equivalent centimetre/millimetre expressions in the covered cases.
- Marks uncertain specifications for review rather than silently treating every extracted value as reliable.
- Measurement-to-dimension association is heuristic and may be ambiguous in more complex briefs.

### `app/matcher.py` — deterministic inventory ranking

- Loads inventory records from `data/inventory.csv`.
- Compares supplied specification fields with inventory attributes using configured field weights.
- Produces a score, match reasons, mismatch reasons and stock quantity for each candidate.
- Sorts by descending score, with SKU as a deterministic tie-breaker.
- **Known limitation:** the score is normalized over fields supplied by the request, so a very incomplete specification can receive a perfect score. Automatic selection should not be considered safe for incomplete specifications until a required-field policy is enforced and tested.

### `app/vision.py` — image-based hole-count estimate

- Uses OpenCV circle detection to estimate holes in an uploaded image.
- Reports an estimated count and review information for cases the implementation considers uncertain.
- The current image tests use generated synthetic images. They do not establish accuracy on real photographs, varied lighting, perspective, occlusion or complex backgrounds.

## 4. Data and evaluation assets

- `data/inventory.csv`: sample inventory used by the matcher.
- `data/evaluation_cases.json`: 20 labelled text cases; 15 include an expected SKU.
- `data/image_evaluation_cases.json`: image-evaluation labels.
- `data/images/`: synthetic images used by the image-count tests.
- `generate_test_images.py`: generates the controlled image examples.
- `evaluate.py`: evaluation harness for text and image cases.
- `test_api.py`, `test_llm.py`, `test_matcher.py`, `test_vision.py`: automated tests for the corresponding behavior.

## 5. Validation and error handling

The design separates model extraction from application-side validation and inventory ranking. This makes it possible to test matching without calling Gemini and to test API behavior with controlled inputs.

The recorded automated test run passed 23 tests. The local inventory-ranking check returned the expected SKU at rank one for all 15 labelled cases when each case's expected specification was supplied directly. That ranking result does **not** measure Gemini extraction accuracy or end-to-end accuracy.

The six synthetic image cases returned their expected hole counts in the recorded evaluation. This is evidence only for those controlled examples, not for real-world images.

Live text evaluation was not completed because Gemini API requests encountered availability/rate-limit errors. No overall text-extraction accuracy is claimed.

## 6. Key design decisions

1. **Structured data contract:** Pydantic models define the shape of extracted specifications and responses.
2. **Separate extraction and matching:** the language model extracts attributes; deterministic Python code ranks inventory candidates.
3. **Explicit uncertainty:** confidence and review flags make unresolved or conflicting inputs visible.
4. **Deterministic ranking:** identical inputs and inventory ordering rules produce a stable ranking, with SKU used to break score ties.
5. **Local tests first:** matcher, API and image behavior can largely be tested without spending Gemini API quota.

## 7. Limitations and next steps

- Complete a controlled text-extraction evaluation when API access permits, recording API failures separately from extraction failures.
- Require a sufficient set of identifying fields before allowing automatic SKU selection; add tests for incomplete specifications.
- Validate hole detection against representative real photographs before relying on it operationally.
- Expand evaluation cases beyond the current small, controlled datasets.
- Add production safeguards before deployment, including authentication, rate limiting, logging/monitoring, upload size/type limits and stronger operational error handling as appropriate.

## 8. Running and testing

Follow the setup and environment-variable instructions in `README.md`. Run the automated tests from the repository root with:

```bash
python -m pytest -v
```

Do not commit API credentials or `.env` files. The architecture and evaluation describe a prototype; they are not a claim of production readiness.
