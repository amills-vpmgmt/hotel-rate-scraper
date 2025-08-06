#!/usr/bin/env python3
import os, json, time
from datetime import date, timedelta
from pathlib import Path
import requests

# --- Constants ---
HOTELS = [
    "Courtyard Beckley",
    "Hampton Inn Beckley",
    "Tru by Hilton Beckley",
    "Fairfield Inn Beckley",
    "Best Western Beckley",
    "Country Inn Beckley",
    "Comfort Inn Beckley"
]
CITY = "Beckley"
STATE = "WV"
PAUSE = 2  # seconds between each API call
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# --- Load API keys ---
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not SERPAPI_KEY or not OPENROUTER_API_KEY:
    print("❌ Missing SERPAPI_KEY or OPENROUTER_API_KEY in environment.")
    exit(1)

def fetch_serpapi(query: str) -> dict:
    params = {
        "engine": "google",
        "q": query,
        "hl": "en",
        "gl": "us",
        "api_key": SERPAPI_KEY
    }
    resp = requests.get("https://serpapi.com/search", params=params)
    resp.raise_for_status()
    return resp.json()

def extract_price_with_gpt(raw_text: str):
    prompt = f"""
Extract the nightly hotel price in USD from the following search result text.
Return only the number (no dollar sign or extra text). If no price is found, reply N/A.

Search Result Text:
{raw_text}
"""
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
    body = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}]
    }
    resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=body)
    resp.raise_for_status()
    reply = resp.json()["choices"][0]["message"]["content"].strip()
    if reply.lower() == "n/a":
        return None
    try:
        return int(reply)
    except ValueError:
        return None

def fetch_rate(hotel: str, checkin_date: str):
    query = f"{hotel} {CITY} {STATE} site:expedia.com {checkin_date} price"
    serp = fetch_serpapi(query)
    snippets = [r.get("snippet","") for r in serp.get("organic_results",[]) if r.get("snippet")]
    combined = " ".join(snippets)
    return extract_price_with_gpt(combined)

def main():
    # Build labels → dates
    today = date.today()
    labels = {
        "Today":    today,
        "Tomorrow": today + timedelta(days=1),
        "Friday":   today + timedelta((4 - today.weekday()) % 7)
    }

    output = {
        "generated": today.isoformat(),
        "rates_by_day": {}
    }

    for label, dt in labels.items():
        iso = dt.isoformat()
        daily = {}
        for hotel in HOTELS:
            try:
                rate = fetch_rate(hotel, iso)
            except Exception as e:
                print(f"❌ [{label}] error fetching {hotel}: {e}")
                rate = None
            print(f"{label} | {hotel} → {rate}")
            daily[hotel] = rate
            time.sleep(PAUSE)
        output["rates_by_day"][label] = daily

    # Write JSON exactly as Streamlit expects
    out_file = DATA_DIR / "beckley_rates.json"
    with open(out_file, "w") as f:
        json.dump(output, f, indent=2)
    print(f"✅ Wrote updated rates → {out_file}")

if __name__ == "__main__":
    main()
