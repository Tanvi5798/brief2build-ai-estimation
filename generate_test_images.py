
from pathlib import Path

import cv2
import numpy as np


OUTPUT_DIR = Path("data/images")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Each image has a known number of circular holes.
TEST_CASES = {
    "holes_0.png": 0,
    "holes_3.png": 3,
    "holes_5.png": 5,
    "holes_8.png": 8,
    "holes_10.png": 10,
    "holes_12.png": 12,
}

IMAGE_WIDTH = 640
IMAGE_HEIGHT = 400


for filename, hole_count in TEST_CASES.items():
    # Light grey background represents a simple metal surface.
    image = np.full(
        (IMAGE_HEIGHT, IMAGE_WIDTH, 3),
        210,
        dtype=np.uint8,
    )

    # Arrange holes in a grid.
    columns = max(1, min(hole_count, 6))
    rows = (hole_count + columns - 1) // columns

    for index in range(hole_count):
        row = index // columns
        column = index % columns

        x = int((column + 1) * IMAGE_WIDTH / (columns + 1))
        y = int((row + 1) * IMAGE_HEIGHT / (rows + 1))

        # Draw a dark outer rim and a darker inner circle.
        cv2.circle(image, (x, y), 24, (80, 80, 80), -1)
        cv2.circle(image, (x, y), 16, (25, 25, 25), -1)

    output_path = OUTPUT_DIR / filename
    cv2.imwrite(str(output_path), image)

    print(f"Created {output_path}: {hole_count} holes")
