import requests
import time
import random
import datetime
import csv
import uuid
from math import inf

USER_AGENTS = [
"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
"Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
"Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
"Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36",
"Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
"Mozilla/5.0 (Macintosh; Intel Mac OS X 12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
"Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
"Mozilla/5.0 (Linux; Android 13; SM-S916B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
"Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
"curl/7.88.1"
]

PAUSE_RANGES = [(2.0, 2.5), (4.0, 4.5), (6.0, 6.5), (8.0, 8.5)]

PAIRS = [
"USD-GBP","USD-EUR","USD-CAD","USD-CHF",
"GBP-USD","GBP-EUR","GBP-CAD","GBP-CHF",
"EUR-USD","EUR-GBP","EUR-CAD","EUR-CHF",
"CAD-USD","CAD-GBP","CAD-EUR","CAD-CHF",
"CHF-USD","CHF-GBP","CHF-EUR","CHF-CAD"
]

BASES = ["USD","GBP","EUR","CAD","CHF"]

def pause_attempt(attempt):
    lo,hi = PAUSE_RANGES[min(attempt,len(PAUSE_RANGES)-1)]
    time.sleep(random.uniform(lo,hi))

def fetch_timeseries(session, base, symbols, start_date, end_date, ua):
    url = "https://api.exchangerate.host/timeseries"
    params = {"start_date": start_date, "end_date": end_date, "base": base, "symbols": ",".join(symbols)}
    headers = {"User-Agent": ua, "Accept": "application/json", "X-Request-Id": str(uuid.uuid4())}
    for attempt in range(4):
        try:
            resp = session.get(url, params=params, headers=headers, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict) and data.get("rates"):
                    return data.get("rates")
            raise Exception("bad response")
        except Exception:
            if attempt == 3:
                return None
            pause_attempt(attempt+1)
    return None

def main():
    today = datetime.date.today()
    end_date = today.isoformat()
    start_date = (today - datetime.timedelta(days=365)).isoformat()
    session = requests.Session()
    timeseries_by_base = {}
    for idx, base in enumerate(BASES):
        symbols = [c for c in BASES if c != base]
        ua = USER_AGENTS[idx % len(USER_AGENTS)]
        rates = fetch_timeseries(session, base, symbols, start_date, end_date, ua)
        timeseries_by_base[base] = rates
        pause_attempt(0)
    rows = []
    for pair in PAIRS:
        base,quote = pair.split("-")
        rates = timeseries_by_base.get(base)
        r = ""
        l = ""
        h = ""
        if rates:
            dates = sorted(rates.keys())
            if dates:
                last_date = dates[-1]
                rate_vals = [rates[d].get(quote) for d in dates if rates[d].get(quote) is not None]
                current = rates.get(last_date, {}).get(quote)
                if current is not None:
                    r = ("{:.6f}".format(current))
                if rate_vals:
                    low = min(rate_vals)
                    high = max(rate_vals)
                    if low is not None and current is not None and low != 0:
                        l = ("{:.6f}".format(((current - low) / low) * 100))
                    if high is not None and current is not None and high != 0:
                        h = ("{:.6f}".format(((current - high) / high) * 100))
        d = today.strftime("%d-%b")
        rows.append({"x": pair, "r": r if r is not None else "", "l": l if l is not None else "", "h": h if h is not None else "", "d": d})
    def sort_key(item):
        try:
            return float(item["l"])
        except:
            return -inf
    rows_sorted = sorted(rows, key=sort_key, reverse=True)
    with open("x.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["x","r","l","h","d"])
        for row in rows_sorted:
            writer.writerow([row["x"], row["r"] if row["r"] != None else "", row["l"] if row["l"] != None else "", row["h"] if row["h"] != None else "", row["d"]])
if __name__ == "__main__":
    main()

