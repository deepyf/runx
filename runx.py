import requests
import csv
import time
import random
from datetime import date

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/118.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
]

TARGET_CURRENCIES = ['GBP', 'EUR', 'CAD', 'CHF']
API_URL = "https://api.frankfurter.app/latest"
OUTPUT_FILE = "x.csv"

def fetch_exchange_rates():
    params = {
        'from': 'USD',
        'to': ",".join(TARGET_CURRENCIES)
    }
    
    response = None
    for attempt in range(4):
        pause_duration = random.uniform(2 * attempt + 2, 2 * attempt + 2.5)
        time.sleep(pause_duration)
        
        try:
            with requests.Session() as s:
                headers = {'User-Agent': random.choice(USER_AGENTS)}
                s.headers.update(headers)
                response = s.get(API_URL, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
        except requests.RequestException:
            continue
            
    if response is not None:
        raise ConnectionError(f"Failed to fetch data after 4 attempts. Last status code: {response.status_code}")
    else:
        raise ConnectionError("Failed to fetch data after 4 attempts. No response received.")

def write_to_csv(data):
    today = date.today().isoformat()
    fieldnames = ['x', 'r', 'd']
    
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        rates = data.get('rates', {})
        for currency in TARGET_CURRENCIES:
            rate = rates.get(currency, "")
            writer.writerow({'x': currency, 'r': rate, 'd': today})

if __name__ == "__main__":
    try:
        rate_data = fetch_exchange_rates()
        write_to_csv(rate_data)
    except Exception as e:
        print(f"An error occurred: {e}")
        exit(1)
