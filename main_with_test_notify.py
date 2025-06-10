import requests
import time
import json
from PIL import Image
from io import BytesIO
import numpy as np
import os

# ========== CONFIG ==========
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
PRICE_THRESHOLD = 780.00
SEARCH_URL = "https://csfloat.com/api/v1/listings?type=gloves&paint=black%20tie&exterior=minimal%20wear&sort=asc"
CHECK_INTERVAL = 600  # 10 minutes
# ============================

def image_hash(image):
    image = image.convert("L").resize((8, 8), Image.ANTIALIAS)
    pixels = np.array(image).flatten()
    avg = pixels.mean()
    return ''.join(['1' if px > avg else '0' for px in pixels])

def is_clean_knuckles(image_url):
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content))
        hash_value = image_hash(image)
        # TODO: Add hash comparison if needed
        return True
    except Exception as e:
        print(f"[❌] Image check failed: {e}")
        return False

def notify_discord(item):
    if not DISCORD_WEBHOOK_URL:
        print("[⚠️] Webhook URL ekki skilgreint (env var ekki sett).")
        return
    data = {
        "embeds": [
            {
                "title": f"New Clean Black Tie Gloves - ${item['price']}",
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
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, data=json.dumps(data), headers=headers)
        print(f"[✅] Sent alert to Discord (status: {response.status_code})")
    except Exception as e:
        print(f"[❌] Error sending to Discord: {e}")

def test_notify():
    if not DISCORD_WEBHOOK_URL:
        print("[⚠️] Webhook URL ekki skilgreint (env var ekki sett).")
        return
    data = {
        "content": "✅ Botinn er ræstur og virkar! Þú færð tilkynningu þegar góð díl finnst. 🔍🧤"
    }
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, data=json.dumps(data), headers=headers)
        print(f"[✅] Test notification sent (status: {response.status_code})")
    except Exception as e:
        print(f"[❌] Error sending test notification: {e}")

def check_csfloat():
    try:
        print("[🔍] Checking CSFloat...")
        res = requests.get(SEARCH_URL)
        res.raise_for_status()
        listings = res.json().get("items", [])
        print(f"[ℹ️] Found {len(listings)} items")

        for item in listings:
            if item['price'] <= PRICE_THRESHOLD:
                print(f"[💰] Under threshold: ${item['price']} – checking image...")
                if is_clean_knuckles(item['image']):
                    notify_discord(item)
    except Exception as e:
        print(f"[❌] Error checking CSFloat: {e}")

if __name__ == "__main__":
    test_notify()
    while True:
        check_csfloat()
        time.sleep(CHECK_INTERVAL)
