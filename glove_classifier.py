import os
import cv2
import numpy as np
from pathlib import Path
import sys

# Paths to training image folders
BASE_DIR = Path(__file__).resolve().parent
FOLDERS = {
    "must_buy": BASE_DIR / "must_buy",
    "good_under_750": BASE_DIR / "good_under_750",
    "reject": BASE_DIR / "reject"
}

def calculate_brightness(image_path):
    img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"Cannot read image at {image_path}")
    return np.mean(img)

def average_brightness_for_folder(folder):
    values = []
    for file in Path(folder).glob("*.png"):
        try:
            val = calculate_brightness(file)
            values.append(val)
        except:
            continue
    return np.mean(values) if values else 0

# Pre-calculate reference brightness for each label
REFERENCE = {
    label: average_brightness_for_folder(path) for label, path in FOLDERS.items()
}

def classify_glove(image_path):
    img_brightness = calculate_brightness(image_path)
    best_match = None
    smallest_diff = float("inf")

    for label, ref_brightness in REFERENCE.items():
        diff = abs(img_brightness - ref_brightness)
        if diff < smallest_diff:
            smallest_diff = diff
            best_match = label

    return best_match

def classify_glove_pair(left_path, right_path):
    left_label = classify_glove(left_path)
    right_label = classify_glove(right_path)

    if left_label == right_label:
        return left_label
    elif "reject" in (left_label, right_label):
        return "reject"
    else:
        return "good_under_750"

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python glove_classifier.py path/to/left.png path/to/right.png")
    else:
        left_path = Path(sys.argv[1])
        right_path = Path(sys.argv[2])
        label = classify_glove_pair(left_path, right_path)
        print(f"Pair classified as: {label}")
