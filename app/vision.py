
from pathlib import Path

import cv2


def estimate_hole_count(image_path: str | Path) -> dict:
    """Estimate circular hole count using OpenCV."""

    image = cv2.imread(str(image_path))

    if image is None:
        raise ValueError(f"Could not read image: {image_path}")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (9, 9), 2)

    circles = cv2.HoughCircles(
        blurred,
        cv2.HOUGH_GRADIENT,
        dp=1.2,
        minDist=35,
        param1=100,
        param2=25,
        minRadius=10,
        maxRadius=30,
    )

    count = 0 if circles is None else len(circles[0])

    if count == 0:
        confidence = {
            "level": "low",
            "reason": "No circular holes detected; manual review is needed.",
        }
    else:
        confidence = {
            "level": "medium",
            "reason": (
                "Circular features detected, but accuracy on real product "
                "photographs has not yet been validated."
            ),
        }

    return {
        "estimated_hole_count": count,
        "confidence": confidence,
        "review_required": count == 0,
        "method": "opencv_hough_circles",
    }
