# Brief to Priced Estimate

## Overview

Brief to Priced Estimate is an AI-assisted prototype that converts a natural-language product brief into a structured product specification, ranks matching inventory items, and optionally estimates the number of holes in an uploaded image.

The project combines language-model extraction, schema validation, deterministic inventory matching, and a classical computer-vision baseline.

## Features

- **Structured extraction:** Uses the Gemini API to extract product attributes from a text brief.
- **Schema validation:** Uses Pydantic models to validate structured product data.
- **Consistency checks:** Identifies missing or conflicting dimensions and potential mismatches between the brief and extracted specification.
- **Inventory matching:** Ranks products from a local CSV inventory using weighted attribute matching.
- **Image analysis:** Uses OpenCV's Hough Circle Transform to estimate hole counts in uploaded images.
- **Review flags:** Highlights uncertain extractions and disagreements between the brief and image estimate.
- **REST API:** Exposes the workflow through FastAPI.
- **Automated tests:** Includes tests for extraction handling, inventory matching, API behavior, and synthetic image analysis.

## Technology Stack

- Python
- FastAPI
- Pydantic
- Google Gemini API (`google-genai`)
- OpenCV
- pandas is not required for the current CSV-based matcher
- pytest
- python-dotenv

## Project Structure

```text
ML engineer Skandor/
├── app/
│   ├── main.py
│   ├── schemas.py
│   ├── llm.py
│   ├── consistency.py
│   ├── matcher.py
│   └── vision.py
├── data/
│   ├── inventory.csv
│   ├── evaluation_cases.json
│   ├── image_evaluation_cases.json
│   └── images/
├── evaluate.py
├── generate_test_images.py
├── test_api.py
├── test_llm.py
├── test_matcher.py
├── test_vision.py
├── requirements.txt
└── README.md
```

## Setup

### 1. Create and activate a virtual environment

Python 3.10 or a compatible version is recommended.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 3. Configure the Gemini API key

Create a `.env` file in the project root:

```text
GEMINI_API_KEY=your_api_key_here
```

Replace the placeholder with your own Gemini API key.

**Security:** Do not commit `.env` or publish API keys. The project `.gitignore` should exclude `.env` and `.venv/`.

## Run the API

From the project root, with the virtual environment activated:

```bash
uvicorn app.main:app --reload
```

The API runs locally at:

```text
http://127.0.0.1:8000
```

Interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

### Health check

Send a `GET` request to `/health`.

### Analyze a brief

Send a `POST` request to `/analyze` using multipart form data:

- `brief`: required product description.
- `image`: optional product image.

Example using `curl`:

```bash
curl -X POST "http://127.0.0.1:8000/analyze" \
  -F "brief=Stainless steel bracket, 120 mm long, 40 mm wide, 3 mm thick"
```

To include an image:

```bash
curl -X POST "http://127.0.0.1:8000/analyze" \
  -F "brief=Stainless steel bracket with 3 holes" \
  -F "image=@data/images/holes_3.png"
```

The response includes the structured result, ranked inventory candidates, and an optional image estimate.

## Run Automated Tests

Run the test suite from the project root:

```bash
python -m pytest -v
```

The current recorded test run completed with **23 passed** and one non-fatal deprecation warning.

## Evaluation

The project includes a text evaluation dataset and a synthetic image evaluation dataset, along with an evaluation script.

Run the evaluation with:

```bash
python evaluate.py
```

Text evaluation calls the configured Gemini model and may be subject to API rate limits or quotas. Image evaluation uses local test images.

Final evaluation metrics should be reported in `EVALUATION.md` only after the evaluation has completed and the results have been checked. API failures must be reported separately rather than silently excluded from performance claims.

## Limitations

- The inventory is a small local CSV dataset intended for prototype evaluation.
- Attribute matching uses deterministic weighted scoring; it is not a trained ranking model.
- Gemini extraction can return incomplete, ambiguous, or inconsistent information. Validation and review flags reduce risk but do not guarantee correctness.
- The OpenCV hole-counting method is a classical computer-vision baseline. Its performance on synthetic images does not establish reliability on real-world photographs.
- Image estimates depend on image quality, lighting, scale, perspective, and the visibility of holes.
- A ranked inventory candidate is a recommendation, not a guarantee of a correct product selection or a final priced quotation.
- The prototype has not been demonstrated to be production-ready.

## Future Improvements

- Evaluate extraction and matching on a larger, independently labelled dataset.
- Test image counting on real product photographs.
- Improve confidence calibration and matching behavior when only a few attributes are specified.
- Add upload validation, file-size limits, and more robust error handling.
- Record latency, API errors, and model usage during evaluation.
- Containerize the service and document deployment options.

## Responsible Use of AI

The language model assists with extracting product attributes; deterministic validation and matching logic handle subsequent checks. Uncertain or conflicting results should be reviewed by a human rather than treated as verified specifications.


### Use of AI Tools

I used the Gemini API to extract structured product specifications from natural-language briefs and used ChatGPT as a development assistant for implementation guidance, debugging, test design, and documentation. I reviewed and adapted AI-generated suggestions rather than treating them as authoritative: for example, I adjusted the schema sent to Gemini to remove unsupported schema keywords while retaining application-side validation, and kept inventory ranking deterministic instead of delegating SKU selection to the language model. I also used automated tests and explicit review flags to check outputs and document uncertainty. The current evaluation limitations—including incomplete live text evaluation due to API limits and the lack of real-photo validation—are reported rather than presented as successful results.
