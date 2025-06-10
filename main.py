import requests
import time
import json
from PIL import Image
from io import BytesIO
import os
from glove_classifier import classify_glove_pair
from pathlib import Path

# ========== CONFIG ==========
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
PRICE_THRESHOLD_MUSTBUY = 820
PRICE_THRESHOLD_GOOD = 750
SEARCH_URL = "https://csfloat.com/api/v1/listings?type=gloves&paint=black%20tie&exterior=minimal%20wear&sort=asc"
CHECK_INTERVAL = 600  # in seconds (10 min)
# ============================

def is_clean_knuckles(image_url):
    try:
        response = requests.get(image_url)
        image = Image.open(BytesIO(response.content))

        # Split image in half (left/right gloves)
        width, height = image.size
        left = image.crop((0, 0, width // 2, height))
        right = image.crop((width // 2, 0, width, height))

        # Save temporarily
        left_path = Path("left_tmp.png")
        right_path = Path("right_tmp.png")
        left.save(left_path)
        right.save(right_path)

        label = classify_glove_pair(left_path, right_path)

        os.remove(left_path)
        os.remove(right_path)

        return label
    except Exception as e:
        print(f"Image check failed: {e}")
        return "reject"

def notify_discord(item, label):
    data = {
        "embeds": [
            {
                "title": f"{label.replace('_', ' ').title()} - ${item['price']}",
                "url": f"https://csfloat.com/item/{item['id']}",
                "image": {"url": item['image']},
                "fields": [
                    {"name": "Price", "value": f"${item['price']}", "inline": True},
                    {"name": "Wear", "value": item['wear'], "inline": True}
                ]
            }
        ]
    }
    headers = {'Content-Type': 'application/json'}
    requests.post(DISCORD_WEBHOOK_URL, data=json.dumps(data), headers=headers)

def test_notify():
    data = {
        "content": "✅ Bottinn er ræstur og virkar! Þú færð tilkynningar þegar flott pair kemur inn. 🧤"
    }
    headers = {'Content-Type': 'application/json'}
    requests.post(DISCORD_WEBHOOK_URL, data=json.dumps(data), headers=headers)

def check_csfloat():
    try:
        res = requests.get(SEARCH_URL)
        res.raise_for_status()
        listings = res.json()['items']

        for item in listings:
            label = is_clean_knuckles(item['image'])

            if label == "must_buy" and item['price'] <= PRICE_THRESHOLD_MUSTBUY:
                notify_discord(item, label)
            elif label == "good_under_750" and item['price'] <= PRICE_THRESHOLD_GOOD:
                notify_discord(item, label)

    except Exception as e:
        print(f"Error checking CSFloat: {e}")

if __name__ == "__main__":
    test_notify()
    while True:
        check_csfloat()
        time.sleep(CHECK_INTERVAL)
