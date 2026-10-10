import json
import time
from pathlib import Path

from app.llm import extract_product_spec
from app.matcher import rank_inventory
from app.vision import estimate_hole_count


PROJECT_DIR = Path(__file__).resolve().parent
TEXT_CASES_PATH = PROJECT_DIR / "data" / "evaluation_cases.json"
IMAGE_CASES_PATH = PROJECT_DIR / "data" / "image_evaluation_cases.json"

FIELDS = [
    "product_type",
    "material",
    "length_mm",
    "width_mm",
    "thickness_mm",
    "finish",
    "hole_diameter_mm",
]


def load_cases(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as file:
        cases = json.load(file)

    if not isinstance(cases, list):
        raise ValueError(f"Expected a list of cases in {path.name}")

    return cases


def values_match(expected, actual) -> bool:
    if isinstance(expected, str) and isinstance(actual, str):
        return expected.strip().casefold() == actual.strip().casefold()
    return expected == actual


def evaluate_images(image_cases: list[dict]) -> None:
    absolute_errors = []
    review_matches = 0
    failures = []

    print("\nIMAGE EVALUATION")

    for case in image_cases:
        try:
            result = estimate_hole_count(PROJECT_DIR / case["image"])
            expected = case["expected_hole_count"]
            predicted = result["estimated_hole_count"]
            error = abs(predicted - expected)

            absolute_errors.append(error)
            review_matches += (
                result["review_required"] == case["expected_review_required"]
            )

            print(
                f'{case["id"]}: expected={expected}, predicted={predicted}, '
                f"absolute_error={error}, "
                f'review_required={result["review_required"]}'
            )

            if error != 0:
                failures.append(
                    f'{case["id"]}: expected {expected} holes, got {predicted}'
                )
            if result["review_required"] != case["expected_review_required"]:
                failures.append(
                    f'{case["id"]}: review flag did not match expected value'
                )

        except Exception as exc:
            failures.append(f'{case["id"]}: {type(exc).__name__}: {exc}')
            print(f'  ERROR: {case["id"]}: {type(exc).__name__}: {exc}')

    print("\nIMAGE METRICS")
    print(f"Total cases: {len(image_cases)}")
    print(f"Successful cases: {len(absolute_errors)}")
    print(f"Failed cases: {len(image_cases) - len(absolute_errors)}")

    if absolute_errors:
        print(f"Image count MAE (successful cases): "
              f"{sum(absolute_errors) / len(absolute_errors):.3f}")

    if image_cases:
        print(f"Review-flag agreement: {review_matches / len(image_cases):.1%}")

    print("Image failures:")
    if failures:
        for failure in failures:
            print(f"- {failure}")
    else:
        print("- None")


def evaluate_text(text_cases: list[dict]) -> None:
    field_correct = 0
    field_total = 0
    successful_cases = 0
    api_error_count = 0
    review_count = 0

    sku_cases = 0
    top1_hits = 0
    top3_hits = 0
    sku_case_errors = 0

    failures = []

    print("\nTEXT EVALUATION")

    for index, case in enumerate(text_cases):
        case_id = case["id"]
        expected_sku = case.get("expected_sku")
        print(f"Evaluating {case_id}...", flush=True)

        try:
            extraction = extract_product_spec(case["brief"])
            spec = extraction.spec.model_dump()
            candidates = rank_inventory(extraction.spec)

        except Exception as exc:
            api_error_count += 1
            failures.append(
                f'{case_id}: API/processing error: {type(exc).__name__}: {exc}'
            )
            if expected_sku:
                sku_cases += 1
                sku_case_errors += 1

            print(f"  ERROR: {type(exc).__name__}: {exc}")

        else:
            successful_cases += 1
            case_correct = 0
            case_total = 0

            for field in FIELDS:
                if field not in case["expected_spec"]:
                    continue

                expected = case["expected_spec"][field]
                actual = spec.get(field)

                field_total += 1
                case_total += 1

                if values_match(expected, actual):
                    field_correct += 1
                    case_correct += 1
                else:
                    failures.append(
                        f"{case_id}: field '{field}' expected "
                        f"{expected!r}, got {actual!r}"
                    )

            if extraction.review_required:
                review_count += 1

            if expected_sku:
                sku_cases += 1
                ranked_skus = [item["sku"] for item in candidates]

                if ranked_skus and ranked_skus[0] == expected_sku:
                    top1_hits += 1
                else:
                    failures.append(
                        f"{case_id}: top-1 SKU expected {expected_sku}, "
                        f"got {ranked_skus[0] if ranked_skus else 'no candidates'}"
                    )

                if expected_sku in ranked_skus[:3]:
                    top3_hits += 1
                else:
                    failures.append(
                        f"{case_id}: expected SKU {expected_sku} not in top 3"
                    )

            print(
                f"  field accuracy: {case_correct}/{case_total}; "
                f"candidates: {len(candidates)}; "
                f"review: {extraction.review_required}"
            )

        if index < len(text_cases) - 1:
            time.sleep(15)

    print("\nTEXT METRICS")
    print(f"Total cases: {len(text_cases)}")
    print(f"Successful cases: {successful_cases}")
    print(f"API/processing errors: {api_error_count}")
    print(f"Evaluation completion rate: "
          f"{successful_cases / len(text_cases):.1%}" if text_cases
          else "Evaluation completion rate: N/A")

    print(f"Field accuracy (successful responses): "
          f"{field_correct / field_total:.1%} ({field_correct}/{field_total})"
          if field_total else "Field accuracy: N/A")

    print(f"Review-flag rate among successful cases: "
          f"{review_count / successful_cases:.1%}" if successful_cases
          else "Review-flag rate: N/A")

    print(f"Cases with expected SKU: {sku_cases}")
    if sku_cases:
        print(f"Top-1 hit rate (all expected-SKU cases; API errors count as misses): "
              f"{top1_hits / sku_cases:.1%} ({top1_hits}/{sku_cases})")
        print(f"Top-3 hit rate (all expected-SKU cases; API errors count as misses): "
              f"{top3_hits / sku_cases:.1%} ({top3_hits}/{sku_cases})")
        print(f"Expected-SKU cases with API/processing errors: {sku_case_errors}")

    print("\nTEXT FAILURE DETAILS")
    if failures:
        for failure in failures:
            print(f"- {failure}")
    else:
        print("- None recorded")


def main():
    text_cases = load_cases(TEXT_CASES_PATH)
    image_cases = load_cases(IMAGE_CASES_PATH)

    print(f"Text evaluation cases: {len(text_cases)}")
    print(f"Image evaluation cases: {len(image_cases)}")

    evaluate_images(image_cases)
    evaluate_text(text_cases)


if __name__ == "__main__":
    main()
