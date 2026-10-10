
from pathlib import Path

import pytest

from app.vision import estimate_hole_count


IMAGE_DIR = Path("data/images")


@pytest.mark.parametrize(
    "filename, expected_count",
    [
        ("holes_0.png", 0),
        ("holes_3.png", 3),
        ("holes_5.png", 5),
        ("holes_8.png", 8),
        ("holes_10.png", 10),
        ("holes_12.png", 12),
    ],
)
def test_hole_count_on_synthetic_images(filename, expected_count):
    image_path = IMAGE_DIR / filename

    result = estimate_hole_count(image_path)

    assert result["estimated_hole_count"] == expected_count
    assert result["confidence"]["level"] in {"high", "medium", "low"}
    assert "reason" in result["confidence"]
    assert result["method"] == "opencv_hough_circles"

    if expected_count == 0:
        assert result["review_required"] is True
        assert result["confidence"]["level"] == "low"


def test_missing_image_raises_error():
    with pytest.raises(ValueError, match="Could not read image"):
        estimate_hole_count(IMAGE_DIR / "does_not_exist.png")
