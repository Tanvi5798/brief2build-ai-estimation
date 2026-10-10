
# Evaluation Report — Brief to Priced Estimate

## 1. Overview

This report documents the current evaluation status of the Brief to Priced Estimate prototype. It separates automated software tests, synthetic-image evaluation, and live Gemini-based text evaluation.

Results reflect the tests actually run; they should not be interpreted as evidence of production readiness.

## 2. Automated Test Suite

**Latest recorded result: 23 passed, 0 failed.**

The test suite covers:

- API behavior with and without an uploaded image.
- Review flags for low-confidence and inconsistent specifications.
- Measurement consistency, including centimetres versus millimetres, explicit ranges, and conflicting dimensions.
- Fallback handling for empty or malformed model responses.
- Deterministic inventory ranking and mismatch handling.
- OpenCV hole counting on synthetic images and missing-image errors.

One non-fatal deprecation warning was reported in the test-client dependency stack. It did not cause any test failures.

## 3. Synthetic-Image Evaluation

Six synthetic images were evaluated using the OpenCV Hough Circle Transform baseline.

| Case | Expected holes | Predicted holes | Absolute error |
| ---- | -------------: | --------------: | -------------: |
| I01  |              0 |               0 |              0 |
| I02  |              3 |               3 |              0 |
| I03  |              5 |               5 |              0 |
| I04  |              8 |               8 |              0 |
| I05  |             10 |              10 |              0 |
| I06  |             12 |              12 |              0 |

### Metrics

- **Cases completed:** 6/6
- **Mean absolute error (MAE):** 0 holes
- **Review-flag agreement:** 100%
- **Evaluation failures:** 0

MAE is the mean of the absolute differences between predicted and expected hole counts.

### Interpretation and limitations

The method matched all six controlled synthetic test images. The dataset is small and deliberately controlled, so these results do not establish performance on real-world product photographs. Lighting, perspective, image resolution, overlapping features, and non-circular holes may affect detection. Testing on representative real images remains necessary.

## 4. Text Evaluation

The text evaluation dataset contains 20 labelled cases:

- **T01–T15:** Complete product briefs with expected inventory SKUs.
- **T16–T18:** Briefs with unspecified attributes.
- **T19:** Conflicting length values.
- **T20:** A length range rather than a single unambiguous dimension.

The evaluation script uses the Gemini API to extract specifications and then ranks inventory candidates. It reports field accuracy, inventory top-1 and top-3 hit rates, completion rate, API/processing failures, and failure details.

**Status: Final text evaluation metrics are pending.**

Earlier evaluation attempts encountered Gemini API errors and rate limits. Those attempts did not provide a complete, reliable evaluation across all 20 cases. The updated evaluation script now reports successful calls and failures separately; API failures on cases with expected SKUs count as misses in the operational top-1 and top-3 rates.

Final metrics must be added after a successful evaluation run. No overall text-accuracy result is claimed in this report.

## 5. Failure Analysis

The following failure categories are relevant to the current evaluation:

1. **API availability:** Gemini rate limits or service errors can prevent an evaluation case from completing. These failures must be counted and reported separately from extraction mistakes.
2. **Ambiguous specifications:** Conflicting dimensions or ranges should not silently become a single trusted value. They should be preserved or flagged for review.
3. **Incomplete specifications:** Missing information should remain unspecified rather than being invented by the model.
4. **Inventory ranking:** Correct extraction does not guarantee the correct inventory candidate will rank first. Matching performance must be evaluated independently.
5. **Real-image generalization:** Synthetic-image performance does not establish reliability on real product photographs.

These are failure categories and limitations to investigate; they should not be represented as three experimentally confirmed worst failures until the detailed text evaluation results have been reviewed.

## 6. Overall Assessment

The prototype has a working API, schema-based extraction workflow, deterministic inventory matching, a classical computer-vision baseline, and an automated test suite with 23 passing tests.

The synthetic-image evaluation is complete for the six available test images. The text evaluation remains incomplete because of Gemini API errors and rate limits.

Before submission, the remaining priorities are to complete and review the text evaluation, record actual metrics and representative failures, verify setup instructions, and ensure API credentials are excluded from version control.

The current results support describing this project as a tested prototype, not as a production-ready system.
