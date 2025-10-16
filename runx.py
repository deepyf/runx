import requests
import random
import time
import datetime
import csv
import os
import subprocess
import sys
from math import isfinite

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "curl/7.88.1",
    "Wget/1.21.3 (linux-gnu)"
]

PAUSE_RANGES = [(2.0,2.5),(4.0,4.5),(6.0,6.5),(8.0,8.5)]

CURRENCIES = ["USD","GBP","EUR","CAD","CHF"]
PAIRS = [
"USD-GBP","USD-EUR","USD-CAD","USD-CHF",
"GBP-USD","GBP-EUR","GBP-CAD","GBP-CHF",
"EUR-USD","EUR-GBP","EUR-CAD","EUR-CHF",
"CAD-USD","CAD-GBP","CAD-EUR","CAD-CHF",
"CHF-USD","CHF-GBP","CHF-EUR","CHF-CAD"
]

def choose_headers():
    ua = random.choice(USER_AGENTS)
    return {
        "User-Agent": ua,
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive"
    }

def fetch_usd_timeseries(start_date, end_date, symbols):
    session = requests.Session()
    url = f"https://api.frankfurter.app/{start_date}..{end_date}?base=USD&symbols={','.join(symbols)}"
    last_exc = None
    for attempt in range(4):
        pause = random.uniform(*PAUSE_RANGES[attempt])
        time.sleep(pause)
        headers = choose_headers()
        try:
            resp = session.get(url, headers=headers, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                return data
            else:
                last_exc = Exception(f"HTTP {resp.status_code}")
        except Exception as e:
            last_exc = e
    raise last_exc

def build_series(data):
    rates_by_date = data.get("rates", {})
    all_dates = sorted(rates_by_date.keys())
    series = {}
    for date in all_dates:
        day_rates = rates_by_date.get(date, {})
        v = {}
        for c in CURRENCIES:
            if c == "USD":
                v["USD"] = 1.0
            else:
                val = day_rates.get(c)
                v[c] = val if isinstance(val, (int,float)) else None
        series[date] = v
    return series

def compute_pair_series(series, a, b):
    arr = []
    for date in sorted(series.keys()):
        v = series[date]
        a_val = v.get(a)
        b_val = v.get(b)
        if a_val is None or b_val is None or a_val == 0:
            arr.append(None)
        else:
            arr.append(b_val / a_val)
    return arr

def safe_min(values):
    nums = [v for v in values if isinstance(v,(int,float))]
    return min(nums) if nums else None

def safe_max(values):
    nums = [v for v in values if isinstance(v,(int,float))]
    return max(nums) if nums else None

def format_number(x):
    if x is None:
        return ""
    if not isfinite(x):
        return ""
    return f"{x:.6f}"

def format_percent(x):
    if x is None:
        return ""
    if not isfinite(x):
        return ""
    return f"{x:.6f}"

def main():
    today = datetime.date.today()
    start = today - datetime.timedelta(days=365)
    start_s = start.isoformat()
    end_s = today.isoformat()
    symbols = [c for c in CURRENCIES if c != "USD"]
    try:
        data = fetch_usd_timeseries(start_s, end_s, symbols)
    except Exception:
        data = {"rates": {}}
    series = build_series(data)
    if not series:
        last_date = datetime.date.today().isoformat()
    else:
        last_date = sorted(series.keys())[-1]
    rows = []
    for pair in PAIRS:
        a,b = pair.split("-")
        pair_series = compute_pair_series(series, a, b)
        latest = None
        if pair_series:
            latest = next((v for v in reversed(pair_series) if isinstance(v,(int,float))), None)
        low = safe_min(pair_series)
        high = safe_max(pair_series)
        if low is None or low == 0 or latest is None:
            lpercent = ""
        else:
            lpercent = format_percent(((latest - low) / low) * 100.0)
        if high is None or high == 0 or latest is None:
            hpercent = ""
        else:
            hpercent = format_percent(((latest - high) / high) * 100.0)
        rstr = format_number(latest)
        dstr = datetime.datetime.now().strftime("%d-%b")
        rows.append({"x": pair, "r": rstr, "l": lpercent, "h": hpercent, "d": dstr})
    def sort_key(item):
        try:
            return float(item["l"]) if item["l"] != "" else float("-inf")
        except Exception:
            return float("-inf")
    rows_sorted = sorted(rows, key=sort_key, reverse=True)
    fn = "x.csv"
    with open(fn, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["x","r","l","h","d"])
        for r in rows_sorted:
            writer.writerow([r["x"] if r["x"] is not None else "", r["r"] if r["r"] is not None else "", r["l"] if r["l"] is not None else "", r["h"] if r["h"] is not None else "", r["d"] if r["d"] is not None else ""])
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if token and repo:
        try:
            branch = subprocess.check_output(["git","rev-parse","--abbrev-ref","HEAD"]).decode().strip()
        except Exception:
            branch = os.environ.get("GITHUB_REF", "").split("/")[-1] or "main"
        remote = f"https://x-access-token:{token}@github.com/{repo}.git"
        try:
            subprocess.run(["git","config","user.name","github-actions[bot]"], check=False)
            subprocess.run(["git","config","user.email","github-actions[bot]@users.noreply.github.com"], check=False)
            subprocess.run(["git","add",fn], check=False)
            subprocess.run(["git","commit","-m","Update x.csv"], check=False)
            subprocess.run(["git","remote","set-url","origin",remote], check=False)
            subprocess.run(["git","push","origin",branch], check=False)
        except Exception:
            pass

if __name__ == "__main__":
    main()

