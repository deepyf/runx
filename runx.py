import requests
import time
import random
import datetime
import csv
import uuid
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
PAUSE_RANGES = [(2.0,2.5),(4.0,4.5),(6.0,6.5),(8.0,8.5)]
PAIRS = [
"USD-GBP","USD-EUR","USD-CAD","USD-CHF",
"GBP-USD","GBP-EUR","GBP-CAD","GBP-CHF",
"EUR-USD","EUR-GBP","EUR-CAD","EUR-CHF",
"CAD-USD","CAD-GBP","CAD-EUR","CAD-CHF",
"CHF-USD","CHF-GBP","CHF-EUR","CHF-CAD"
]
BASES = ["USD","GBP","EUR","CAD","CHF"]
def sleep_between(attempt):
    lo,hi = PAUSE_RANGES[min(attempt,len(PAUSE_RANGES)-1)]
    time.sleep(random.uniform(lo,hi))
def fetch_timeseries(session, base, symbols, start_date, end_date):
    url = "https://api.exchangerate.host/timeseries"
    params = {"start_date": start_date, "end_date": end_date, "base": base, "symbols": ",".join(symbols)}
    for attempt in range(4):
        ua = random.choice(USER_AGENTS)
        headers = {"User-Agent": ua, "Accept": "application/json", "X-Request-Id": str(uuid.uuid4())}
        try:
            resp = session.get(url, params=params, headers=headers, timeout=30)
            if resp.status_code == 200:
                payload = resp.json()
                rates = payload.get("rates")
                if isinstance(rates, dict) and rates:
                    return rates
            raise Exception("bad response")
        except Exception:
            if attempt == 3:
                return None
            sleep_between(attempt+1)
    return None
def parse_date(d):
    try:
        return datetime.datetime.strptime(d, "%Y-%m-%d").date()
    except Exception:
        return None
def safe_float(v):
    try:
        return float(v)
    except Exception:
        return None
def main():
    today = datetime.date.today()
    end_date = today.isoformat()
    start_date = (today - datetime.timedelta(days=365)).isoformat()
    session = requests.Session()
    timeseries_by_base = {}
    for i,base in enumerate(BASES):
        symbols = [c for c in BASES if c != base]
        rates = fetch_timeseries(session, base, symbols, start_date, end_date)
        timeseries_by_base[base] = rates
        sleep_between(0)
    rows = []
    for pair in PAIRS:
        base,quote = pair.split("-")
        rates = timeseries_by_base.get(base)
        r = ""
        l = ""
        h = ""
        if isinstance(rates, dict):
            parsed = []
            for d,rate_map in rates.items():
                dt = parse_date(d)
                if not dt:
                    continue
                if isinstance(rate_map, dict):
                    val = safe_float(rate_map.get(quote))
                    if val is not None:
                        parsed.append((dt,val))
            if parsed:
                parsed.sort(key=lambda x: x[0])
                last_dt, last_val = parsed[-1]
                r = "{:.6f}".format(last_val)
                vals = [v for (_,v) in parsed]
                low = min(vals) if vals else None
                high = max(vals) if vals else None
                if low is not None and low != 0:
                    l = "{:.6f}".format(((last_val - low) / low) * 100)
                if high is not None and high != 0:
                    h = "{:.6f}".format(((last_val - high) / high) * 100)
        d = today.strftime("%d-%b")
        rows.append({"x": pair, "r": r or "", "l": l or "", "h": h or "", "d": d})
    def lk(item):
        try:
            return float(item["l"])
        except Exception:
            return float("-inf")
    rows_sorted = sorted(rows, key=lk, reverse=True)
    with open("x.csv","w",encoding="utf-8",newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["x","r","l","h","d"])
        for row in rows_sorted:
            writer.writerow([row["x"] or "", row["r"] or "", row["l"] or "", row["h"] or "", row["d"] or ""])
if __name__ == "__main__":
    main()

