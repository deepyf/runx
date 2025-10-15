import requests
import csv
import time
import random
from datetime import datetime

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/109.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/109.0",
    "Mozilla/5.0 (iPad; CPU OS 16_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/109.0.5414.112 Mobile/15E148 Safari/604.1",
]
TARGET_CURRENCIES = ['GBP', 'EUR', 'CAD', 'CHF']
BASE_CURRENCY = 'USD'
API_URL = f"https://api.frankfurter.app/latest?from={BASE_CURRENCY}&to={','.join(TARGET_CURRENCIES)}"
OUTPUT_FILE = 'x'
MAX_RETRIES = 4

rates = None
session = requests.Session()

for attempt in range(MAX_RETRIES):
    try:
        pause_base = 2 * attempt
        sleep_duration = random.uniform(2 + pause_base, 2.5 + pause_base)
        time.sleep(sleep_duration)
        headers = {'User-Agent': random.choice(USER_AGENTS)}
        response = session.get(API_URL, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        rates = data.get('rates', {})
        break
    except requests.exceptions.RequestException:
        if attempt == MAX_RETRIES - 1:
            rates = {}

if rates is None:
    rates = {}

run_date = datetime.now().strftime('%d-%b')
rows_to_write = []
for currency in TARGET_CURRENCIES:
    rate_value = rates.get(currency, "")
    rows_to_write.append({
        'x': currency,
        'r': rate_value,
        'd': run_date
    })

with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as csv_file:
    writer = csv.DictWriter(csv_file, fieldnames=['x', 'r', 'd'])
    writer.writeheader()
    writer.writerows(rows_to_write)
