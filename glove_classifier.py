import os
import cv2
import numpy as np
from pathlib import Path
import sys
import requests

# Paths to training image folders
BASE_DIR = Path(__file__).resolve().parent
FOLDERS = {
    "must_buy": BASE_DIR / "must_buy",
    "good_under_750": BASE_DIR / "good_under_750",
    "reject": BASE_DIR / "reject"
}

# Discord webhook URL (replace with your own)
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")  # Set this in Render environment variables

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

def send_discord_ping(label, left_path, right_path):
    if DISCORD_WEBHOOK_URL is None:
        print("No Discord webhook set.")
        return

    files = {
        "file1": open(left_path, "rb"),
        "file2": open(right_path, "rb")
    }

    payload = {
        "content": f"New Black Tie Gloves match: **{label.upper()}**"
    }

    response = requests.post(DISCORD_WEBHOOK_URL, data=payload, files=files)
    print(f"Discord notification sent. Status code: {response.status_code}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python glove_classifier.py path/to/left.png path/to/right.png")
    else:
        left_path = Path(sys.argv[1])
        right_path = Path(sys.argv[2])
        label = classify_glove_pair(left_path, right_path)
        print(f"Pair classified as: {label}")
        if label in ["must_buy", "good_under_750"]:
            send_discord_ping(label, left_path, right_path)
