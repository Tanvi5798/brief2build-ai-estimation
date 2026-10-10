
import re

from app.schemas import ExtractionResult


FIELD_PATTERNS = {
    "length_mm": r"\b(?:length|long)\b",
    "width_mm": r"\b(?:width|wide)\b",
    "thickness_mm": r"\b(?:thickness|thick)\b",
}

MEASUREMENT_PATTERN = re.compile(
    r"(\d+(?:\.\d+)?)\s*"
    r"(mm|millimetres?|millimeters?|cm|centimetres?|centimeters?)\b",
    re.IGNORECASE,
)


def to_mm(value: float, unit: str) -> float:
    """Convert supported measurements to millimetres."""

    if unit.lower().startswith(("cm", "centimetre", "centimeter")):
        return value * 10

    return value



def check_measurement_consistency(
    customer_request: str,
    result: ExtractionResult,
) -> ExtractionResult:
    """Compare extracted dimensions with measurements in the request."""

    reasons = list(result.review_reasons)
    mentions = []

    # Find every occurrence of a dimension word.
    for field_name, pattern in FIELD_PATTERNS.items():
        for match in re.finditer(
            pattern,
            customer_request,
            re.IGNORECASE,
        ):
            mentions.append(
                (match.start(), match.end(), field_name)
            )

    mentions.sort()

    # Find measurements and associate each with the nearest dimension word.
    values_by_field = {
        field_name: []
        for field_name in FIELD_PATTERNS
    }
    positions_by_field = {
        field_name: []
        for field_name in FIELD_PATTERNS
    }

    for measurement in MEASUREMENT_PATTERN.finditer(customer_request):
        value = to_mm(
            float(measurement.group(1)),
            measurement.group(2),
        )

        if not mentions:
            continue

        nearest_mention = None
        nearest_distance = float("inf")

        for start, end, field_name in mentions:
            if measurement.end() <= start:
                distance = start - measurement.end()
            elif measurement.start() >= end:
                distance = measurement.start() - end
            else:
                distance = 0

            if distance < nearest_distance:
                nearest_distance = distance
                nearest_mention = field_name

        values_by_field[nearest_mention].append(value)
        positions_by_field[nearest_mention].append(
            (measurement.start(), measurement.end())
        )

    # Check whether multiple values describe a range or a conflict.
    for field_name, values in values_by_field.items():
        if not values:
            continue

        unique_values = sorted(set(values))
        extracted_value = getattr(result.spec, field_name)
        positions = positions_by_field[field_name]

        range_is_stated = False

        if len(unique_values) > 1:
            first_position = min(start for start, _ in positions)
            last_position = max(end for _, end in positions)

            context_start = max(0, first_position - 60)
            context_end = min(
                len(customer_request),
                last_position + 60,
            )
            context = customer_request[context_start:context_end]

            range_is_stated = bool(
                re.search(
                    r"\b(?:between|range|from|minimum|min\.?|maximum|max\.?)\b",
                    context,
                    re.IGNORECASE,
                )
            )

        if range_is_stated:
            lower = min(unique_values)
            upper = max(unique_values)

            if extracted_value is None or not (
                lower <= extracted_value <= upper
            ):
                reason = (
                    f"{field_name}: extracted value does not satisfy "
                    f"the stated range of {lower:g}–{upper:g} mm"
                )
                if reason not in reasons:
                    reasons.append(reason)
                result.review_required = True

        elif len(unique_values) > 1:
            reason = (
                f"{field_name}: conflicting measurements found "
                f"in the customer request: "
                f"{', '.join(f'{value:g} mm' for value in unique_values)}"
            )
            if reason not in reasons:
                reasons.append(reason)
            result.review_required = True

        else:
            requested_value = unique_values[0]

            if extracted_value is None:
                reason = (
                    f"{field_name}: the customer specified "
                    f"{requested_value:g} mm, but no value was extracted"
                )
                if reason not in reasons:
                    reasons.append(reason)
                result.review_required = True

            elif abs(extracted_value - requested_value) > 1e-6:
                reason = (
                    f"{field_name}: extracted value "
                    f"{extracted_value:g} mm does not match "
                    f"the customer's stated value "
                    f"{requested_value:g} mm"
                )
                if reason not in reasons:
                    reasons.append(reason)
                result.review_required = True

    result.review_reasons = reasons
    return result
