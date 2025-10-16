import csv
import random
import time
from datetime import datetime
import requests
from typing import List, Dict, Optional
import sys


USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/119.0',
    'Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.76',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.76',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 OPR/105.0.0.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 OPR/105.0.0.0'
]


def get_headers() -> Dict[str, str]:
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }


def fetch_exchange_data(pair: str, session: requests.Session, retry: int = 0) -> Optional[Dict]:
    base, quote = pair.split('-')
    
    try:
        url = f'https://api.exchangerate-api.com/v4/latest/{base}'
        response = session.get(url, headers=get_headers(), timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if quote not in data.get('rates', {}):
            return None
            
        rate = data['rates'][quote]
        
        historical_url = f'https://api.exchangerate-api.com/v4/history/{base}/365'
        hist_response = session.get(historical_url, headers=get_headers(), timeout=10)
        hist_response.raise_for_status()
        hist_data = hist_response.json()
        
        rates_list = []
        if 'rates' in hist_data:
            for date_str, rates in hist_data['rates'].items():
                if quote in rates:
                    rates_list.append(rates[quote])
        
        if not rates_list:
            return {
                'x': pair,
                'r': rate,
                'l': '',
                'h': ''
            }
        
        week_52_low = min(rates_list)
        week_52_high = max(rates_list)
        
        low_change = ((rate - week_52_low) / week_52_low * 100) if week_52_low else ''
        high_change = ((rate - week_52_high) / week_52_high * 100) if week_52_high else ''
        
        return {
            'x': pair,
            'r': rate,
            'l': low_change if low_change != '' else '',
            'h': high_change if high_change != '' else ''
        }
        
    except Exception as e:
        if retry < 3:
            wait_times = [(4, 4.5), (6, 6.5), (8, 8.5)]
            wait = random.uniform(*wait_times[retry])
            time.sleep(wait)
            return fetch_exchange_data(pair, session, retry + 1)
        return None


def main():
    pairs = [
        'USD-GBP', 'USD-EUR', 'USD-CAD', 'USD-CHF',
        'GBP-USD', 'GBP-EUR', 'GBP-CAD', 'GBP-CHF',
        'EUR-USD', 'EUR-GBP', 'EUR-CAD', 'EUR-CHF',
        'CAD-USD', 'CAD-GBP', 'CAD-EUR', 'CAD-CHF',
        'CHF-USD', 'CHF-GBP', 'CHF-EUR', 'CHF-CAD'
    ]
    
    session = requests.Session()
    results = []
    
    processed_bases = {}
    
    for i, pair in enumerate(pairs):
        base = pair.split('-')[0]
        
        if base not in processed_bases:
            data = fetch_exchange_data(pair, session)
            if data:
                results.append(data)
            
            processed_bases[base] = True
            
            if i < len(pairs) - 1:
                next_base = pairs[i + 1].split('-')[0]
                if next_base != base:
                    time.sleep(random.uniform(2, 2.5))
        else:
            for existing in results:
                if existing['x'].startswith(base + '-'):
                    data = fetch_exchange_data(pair, session)
                    if data:
                        results.append(data)
                    break
    
    results_sorted = sorted(
        results,
        key=lambda x: float(x['l']) if x['l'] != '' and x['l'] is not None else float('-inf'),
        reverse=True
    )
    
    date_str = datetime.now().strftime('%d-%b').lower()
    
    for result in results_sorted:
        result['d'] = date_str
    
    with open('x.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['x', 'r', 'l', 'h', 'd'])
        writer.writeheader()
        writer.writerows(results_sorted)
    
    print(f"Successfully wrote {len(results_sorted)} exchange rates to x.csv")


if __name__ == '__main__':
    main()
