#!/usr/bin/env python3
import os
import json
from datetime import date, timedelta
from pathlib import Path

# --- Your existing SerpAPI / OpenRouter imports & setup ---
from serpapi import GoogleSearch
# … any other imports you have …

# List of your hotels exactly as your Streamlit app expects
HOTELS = [
    "Courtyard Beckley",
    "Hampton Inn Beckley",
    "Tru by Hilton Beckley",
    "Fairfield Inn Beckley",
    "Best Western Beckley",
    "Country Inn Beckley"
]

# where to write the JSON
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not SERPAPI_KEY or not OPENROUTER_API_KEY:
    print("Error: Missing SERPAPI_KEY or OPENROUTER_API_KEY in environment.")
    exit(1)

def fetch_rate(hotel_name: str, checkin_date: str) -> float:
    """
    Your existing logic for:
      1. hitting SerpAPI with hotel_name + date
      2. feeding result into OpenRouter GPT
      3. returning a numeric rate
    """
    # … copy your code here …
    return rate  # float

def main():
    # map labels → the dates you want
    labels = {
        "Today":    date.today(),
        "Tomorrow": date.today() + timedelta(days=1),
        "Friday":   date.today() + timedelta((4 - date.today().weekday()) % 7)
    }

    output = {
        "generated": date.today().isoformat(),
        "rates_by_day": {}
    }

    for label, dt in labels.items():
        iso = dt.isoformat()
        daily = {}
        for hotel in HOTELS:
            try:
                rate = fetch_rate(hotel, iso)
            except Exception as e:
                print(f"[{label}] error fetching {hotel}: {e}")
                rate = None
            daily[hotel] = rate
        output["rates_by_day"][label] = daily

    # write out exactly what streamlit_app.py expects
    out_file = DATA_DIR / "beckley_rates.json"
    with open(out_file, "w") as f:
        json.dump(output, f, indent=2)
    print(f"Wrote updated rates → {out_file}")

if __name__ == "__main__":
    main()
