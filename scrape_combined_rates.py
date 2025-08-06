#!/usr/bin/env python3
import json, time, re
from datetime import date, timedelta
from pathlib import Path
import requests
from bs4 import BeautifulSoup

HOTELS = [
    "Courtyard Beckley",
    "Hampton Inn Beckley",
    "Tru by Hilton Beckley",
    "Fairfield Inn Beckley",
    "Best Western Beckley",
    "Country Inn Beckley",
    "Comfort Inn Beckley"
]
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# build check-in/check-out labels
today = date.today()
labels = {
    "Today":    today,
    "Tomorrow": today + timedelta(days=1),
    "Friday":   today + timedelta((4 - today.weekday()) % 7)
}

def fetch_price_from_expedia(hotel: str, checkin: date) -> int | None:
    # use a one-night stay
    checkout = checkin + timedelta(days=1)
    params = {
        "destination": f"{hotel}, Beckley, WV",
        "startDate":   checkin.isoformat(),
        "endDate":     checkout.isoformat(),
        "rooms":       "1"
    }
    # build a query string manually to avoid URL-escaping surprises
    q = "&".join(f"{k}={requests.utils.quote(v)}" for k, v in params.items())
    url = f"https://www.expedia.com/Hotel-Search?{q}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    text = soup.get_text(separator=" ")
    m = re.search(r"\$(\d{2,4})", text)
    return int(m.group(1)) if m else None

def main():
    output = {
        "generated": today.isoformat(),
        "rates_by_day": {}
    }

    for label, dt in labels.items():
        daily = {}
        for hotel in HOTELS:
            try:
                rate = fetch_price_from_expedia(hotel, dt)
            except Exception as e:
                print(f"❌ [{label}] {hotel}: {e}")
                rate = None
            print(f"{label} | {hotel} → {rate}")
            daily[hotel] = rate
            time.sleep(2)
        output["rates_by_day"][label] = daily

    out_file = DATA_DIR / "beckley_rates.json"
    with open(out_file, "w") as f:
        json.dump(output, f, indent=2)
    print(f"✅ Wrote {out_file}")

if __name__ == "__main__":
    main()
