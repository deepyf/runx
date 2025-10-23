import csv
import time
import random
from curl_cffi import requests
import yfinance as yf
from decimal import Decimal, ROUND_HALF_UP

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:115.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Build/TP1A.220624.014) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.5790.170 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edg/115.0.1901.203",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 OPR/101.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.5790.170 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-S916B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.5897.77 Mobile Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_6_8) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15"
]

def get_session():
    s = requests.Session()
    s.headers.update({"User-Agent": random.choice(USER_AGENTS)})
    return s

def round_half_up(value, decimals=1):
    if value == "":
        return ""
    decimal_value = Decimal(str(value))
    rounded = decimal_value.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)
    return float(rounded)

with open("ghInX", newline="") as fin:
    reader = csv.DictReader(fin)
    symbols = [row["T"] for row in reader]

data_rows = []

for sym in symbols:
    info = {}
    for attempt in range(4):
        try:
            sess = get_session()
            yf.utils.requests = sess
            info = yf.Ticker(sym).info or {}
            break
        except Exception:
            if attempt == 0:
                wait = random.uniform(4,4.5)
            elif attempt == 1:
                wait = random.uniform(6,6.5)
            elif attempt == 2:
                wait = random.uniform(8,8.5)
            else:
                break
            time.sleep(wait)
    R = info.get("regularMarketPrice","") or ""
    L_raw = info.get("fiftyTwoWeekLowChangePercent","") or ""
    H_raw = info.get("fiftyTwoWeekHighChangePercent","") or ""
    
    if L_raw != "" and H_raw != "":
        L_pct = float(L_raw) * 100
        H_pct = float(H_raw) * 100
        D = L_pct + H_pct
        sort_key = D
    else:
        L_pct = ""
        H_pct = ""
        D = ""
        sort_key = -float('inf')
    
    data_rows.append((sym, R, L_pct, H_pct, D, sort_key))

data_rows.sort(key=lambda x: x[5], reverse=True)

with open("ghOutX", "w", newline="", encoding="utf-8") as fout:
    writer = csv.writer(fout)
    writer.writerow(["T","D","L","H","R"])
    for row in data_rows:
        T, R, L, H, D, _ = row
        
        if D != "":
            D_rounded = round_half_up(D)
            L_rounded = round_half_up(L)
            H_rounded = round_half_up(H)
        else:
            D_rounded = ""
            L_rounded = ""
            H_rounded = ""
        
        writer.writerow([T, D_rounded, L_rounded, H_rounded, R])