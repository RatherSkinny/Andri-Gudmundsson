import requests
import time
import json
from PIL import Image
from io import BytesIO
import numpy as np

# ========== CONFIG ==========
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1381787709194108929/dlq3QwQ-HQ46U8ZdvjrQTT0zv5Hggr2oI8CJooDQwwQtTiWBWga985sS6si2YBhLLDN7"
PRICE_THRESHOLD = 780.00
SEARCH_URL = "https://csfloat.com/api/v1/listings?type=gloves&paint=black%20tie&exterior=minimal%20wear&sort=asc"
CHECK_INTERVAL = 600  # in seconds (10 min)
BAD_EXAMPLE_HASH = 'placeholder_hash_value'
# ============================

def image_hash(image):
    image = image.convert("L").resize((8, 8), Image.ANTIALIAS)
    pixels = np.array(image).flatten()
    avg = pixels.mean()
    return ''.join(['1' if px > avg else '0' for px in pixels])

def is_clean_knuckles(image_url):
    try:
        response = requests.get(image_url)
        image = Image.open(BytesIO(response.content))
        hash_value = image_hash(image)
        return hash_value != BAD_EXAMPLE_HASH
    except Exception as e:
        print(f"Image check failed: {e}")
        return False

def notify_discord(item):
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
    requests.post(DISCORD_WEBHOOK_URL, data=json.dumps(data), headers=headers)

def check_csfloat():
    try:
        res = requests.get(SEARCH_URL)
        res.raise_for_status()
        listings = res.json()['items']
        for item in listings:
            if item['price'] <= PRICE_THRESHOLD and is_clean_knuckles(item['image']):
                notify_discord(item)
    except Exception as e:
        print(f"Error checking CSFloat: {e}")

if __name__ == "__main__":
    while True:
        check_csfloat()
        time.sleep(CHECK_INTERVAL)