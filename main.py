import time
import requests
from bs4 import BeautifulSoup
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from pathlib import Path
from glove_classifier import classify_glove_pair

# === CONFIG ===
LISTING_URL = "https://csfloat.com/listings?type=Gloves&search=driver%20black%20tie&sort=price_asc"
DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")  # Set this in Render.com env variables
TEMP_DIR = Path("tmp")
TEMP_DIR.mkdir(exist_ok=True)

SEEN = set()

def setup_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)

def get_listings():
    response = requests.get(LISTING_URL)
    soup = BeautifulSoup(response.text, "html.parser")
    cards = soup.find_all("div", class_="item-card")
    listings = []
    for card in cards:
        try:
            price_str = card.find("div", class_="price-tag").text.strip().replace("$", "").replace(",", "")
            price = float(price_str)
            float_val = float(card.find("div", class_="float-text").text.strip())
            link = "https://csfloat.com" + card.find("a")["href"]
            listings.append({"price": price, "float": float_val, "url": link})
        except:
            continue
    return listings

def capture_images(url):
    driver = setup_driver()
    driver.get(url)
    time.sleep(3)
    try:
        button = driver.find_element(By.CLASS_NAME, 'screenshot-button')
        button.click()
        time.sleep(3)
        images = driver.find_elements(By.TAG_NAME, 'img')
        left, right = None, None
        for img in images:
            src = img.get_attribute("src")
            if "glove0" in src:
                left = src
            elif "glove1" in src:
                right = src
        if not (left and right):
            raise Exception("Could not find both glove images")
        left_path = TEMP_DIR / "left.png"
        right_path = TEMP_DIR / "right.png"
        with open(left_path, 'wb') as f:
            f.write(requests.get(left).content)
        with open(right_path, 'wb') as f:
            f.write(requests.get(right).content)
        return left_path, right_path
    finally:
        driver.quit()

def send_discord_message(text):
    if not DISCORD_WEBHOOK:
        print("[!] No webhook set.")
        return
    requests.post(DISCORD_WEBHOOK, json={"content": text})

def main():
    while True:
        try:
            listings = get_listings()
            for listing in listings:
                key = f"{listing['url']}-{listing['price']}"
                if key in SEEN:
                    continue
                SEEN.add(key)
                left_img, right_img = capture_images(listing['url'])
                label = classify_glove_pair(left_img, right_img)
                if label == "must_buy" and listing['price'] <= 820:
                    send_discord_message(f"MUST BUY (${listing['price']}): {listing['url']}")
                elif label == "good_under_750" and listing['price'] <= 750:
                    send_discord_message(f"Good pair under $750 (${listing['price']}): {listing['url']}")
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(900)  # 15 min

if __name__ == "__main__":
    main()
