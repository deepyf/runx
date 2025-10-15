import requests
import random
import time
import csv
import datetime
import os
import sys

UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edg/122.0.0.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 13; SM-S930B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Opera/9.80 (Windows NT 6.1; WOW64) Presto/2.12.388 Version/12.18",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

RATE_MAP = {
    "usd-gbp": "GBP",
    "usd-eur": "EUR",
    "usd-cad": "CAD",
    "usd-chf": "CHF"
}

API_URL = "https://api.exchangerate.host/latest"
symbols = ",".join(RATE_MAP.values())

session = requests.Session()

sleep_ranges = [(2, 2.5), (4, 4.5), (6, 6.5), (8, 8.5)]
max_attempts = len(sleep_ranges)
response_json = None

for attempt in range(max_attempts):
    ua = random.choice(UA_LIST)
    session.headers.update({"User-Agent": ua, "Accept": "application/json", "Accept-Language": "en-US,en;q=0.9"})
    rng = sleep_ranges[attempt]
    time.sleep(random.uniform(rng[0], rng[1]))
    try:
        resp = session.get(API_URL, params={"base": "USD", "symbols": symbols}, timeout=15)
        if resp.status_code == 200:
            response_json = resp.json()
            if isinstance(response_json, dict) and "rates" in response_json:
                break
    except requests.RequestException:
        pass

if not response_json or "rates" not in response_json:
    sys.exit(1)

rates = response_json.get("rates", {})
today = datetime.date.today().isoformat()
rows = []
for name, code in RATE_MAP.items():
    val = rates.get(code, "")
    if val is None:
        val = ""
    rows.append({"x": name, "r": (str(val) if val != "" else ""), "d": today})

out_path = os.path.join(os.getcwd(), "x")
with open(out_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["x", "r", "d"])
    writer.writeheader()
    for row in rows:
        writer.writerow(row)

session.close()

