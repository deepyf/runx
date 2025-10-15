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
    except requests.RequestException as e:
        print(f"attempt {attempt+1}/{max_attempts} request exception: {e}", file=sys.stderr)
        resp = None
    if resp is not None:
        status = resp.status_code
        if status == 200:
            try:
                j = resp.json()
            except ValueError:
                print(f"attempt {attempt+1}/{max_attempts} invalid json", file=sys.stderr)
                j = None
            if isinstance(j, dict) and "rates" in j:
                response_json = j
                break
            else:
                print(f"attempt {attempt+1}/{max_attempts} missing 'rates' key or bad payload", file=sys.stderr)
        else:
            body_snippet = resp.text[:200].replace("\n", " ")
            print(f"attempt {attempt+1}/{max_attempts} http {status} body {body_snippet}", file=sys.stderr)

rates = {}
if response_json and isinstance(response_json.get("rates"), dict):
    rates = response_json.get("rates", {})
else:
    print("no valid rates fetched; proceeding to write empty values", file=sys.stderr)

today = datetime.date.today().isoformat()

rows = []
for name, code in RATE_MAP.items():
    val = rates.get(code, "")
    if val is None:
        val_out = ""
    else:
        val_out = str(val)
    rows.append({"x": name, "r": (val_out if val_out != "" else ""), "d": today})

out_path = os.path.join(os.getcwd(), "x.csv")
try:
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["x", "r", "d"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    print(f"wrote {out_path}")
except Exception as e:
    print(f"failed to write {out_path}: {e}", file=sys.stderr)
    session.close()
    sys.exit(1)

session.close()

