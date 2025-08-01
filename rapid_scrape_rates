#!/usr/bin/env python3
"""
scrape_combined_rates.py

Fetches nightly rates for a list of Beckley hotels from:
  1) SerpApi’s Google Hotels engine
  2) Expedia RapidAPI (via location search + get-details)

Merges them and writes debug + consolidated JSON to ./data/
"""

import os
import json
import time
import re
import datetime
from pathlib import Path

import requests

# ─────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────

# API keys (export these before running)
SERPAPI_KEY   = os.getenv("SERPAPI_KEY")
# changed here to match your GitHub secret name
RAPIDAPI_KEY  = os.getenv("RAPIDAI_API_KEY")
RAPIDAPI_HOST = "expedia1.p.rapidapi.com"

# Hotels you care about
HOTELS = [
    "Courtyard Beckley",
    "Hampton Inn Beckley",
    "Tru by Hilton Beckley",
    "Fairfield Inn Beckley",
    "Best Western Beckley",
    "Country Inn Beckley",
    "Comfort Inn Beckley",
]

# City context for both APIs
CITY    = "Beckley"
STATE   = "WV"
COUNTRY = "United States"

# Where to dump JSON
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# Sleep between API calls to respect rate-limits
PAUSE = 1.5


# ─────────────────────────────────────────────────────────────
# UTILS
# ─────────────────────────────────────────────────────────────

def fetch_serpapi(query: str) -> dict:
    resp = requests.get(
        "https://serpapi.com/search",
        params={
            "engine":   "google_hotels",
            "q":        query,
            "location": f"{CITY}, {STATE}, {COUNTRY}",
            "hl":       "en",
            "gl":       "us",
            "api_key":  SERPAPI_KEY,
        },
    )
    resp.raise_for_status()
    return resp.json()

def extract_serp_rate(r: dict) -> str:
    prices = []
    for h in r.get("hotel_results", []):
        p = h.get("price", "")
        if p.startswith("$"):
            prices.append(int(p.replace("$","").replace(",","")))
    for o in r.get("organic_results", []):
        for m in re.findall(r"\$[\d,]+", o.get("snippet","")):
            prices.append(int(m.replace("$","").replace(",","")))
    kg = r.get("knowledge_graph",{})
    for offer in kg.get("pricing",{}).get("offers",[]):
        p = offer.get("price","")
        if p.startswith("$"):
            prices.append(int(p.replace("$","").replace(",","")))
    if not prices:
        return "N/A"
    lo, hi = min(prices), max(prices)
    return f"{lo}-{hi}" if lo != hi else str(lo)

def fetch_rapidapi_price(hotel: str, checkin: str, checkout: str) -> (float, str):
    headers = {
        "X-RapidAPI-Host": RAPIDAPI_HOST,
        "X-RapidAPI-Key":  RAPIDAPI_KEY,
    }
    loc_resp = requests.get(
        f"https://{RAPIDAPI_HOST}/locations/search",
        headers=headers,
        params={"query": f"{hotel}, {CITY}, {STATE}"}
    )
    loc_resp.raise_for_status()
    results = loc_resp.json().get("results", [])
    if not results:
        return None, None

    hotel_id = results[0]["id"]
    time.sleep(PAUSE)

    det_resp = requests.get(
        f"https://{RAPIDAPI_HOST}/hotels/get-details",
        headers=headers,
        params={
            "id":      hotel_id,
            "checkIn":  checkin,
            "checkOut": checkout,
        }
    )
    det_resp.raise_for_status()
    offers = det_resp.json().get("offers", [])
    if not offers:
        return None, None

    price_obj = offers[0].get("price", {})
    return price_obj.get("total") or price_obj.get("current"), price_obj.get("currency")


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def main():
    today = datetime.date.today()
    dates = {
        "Today":    today.isoformat(),
        "Tomorrow": (today + datetime.timedelta(days=1)).isoformat(),
        "Friday":   (today + datetime.timedelta((4 - today.weekday()) % 7)).isoformat(),
    }

    output = {
        "generated":     today.isoformat(),
        "checkin_dates": dates,
        "rates_by_day":  {},
    }

    for label, date in dates.items():
        print(f"\n=== {label} ({date}) ===")
        output["rates_by_day"][label] = {}

        for hotel in HOTELS:
            print(f" • {hotel}")

            serp_query = f"{hotel} Beckley WV {date} hotel price"
            serp_json  = fetch_serpapi(serp_query)
            serp_rate  = extract_serp_rate(serp_json)
            with open(DATA_DIR / f"debug_serpapi_{hotel.replace(' ','_')}_{label}.json","w") as f:
                json.dump(serp_json, f, indent=2)
            time.sleep(PAUSE)

            try:
                rap_price, rap_curr = fetch_rapidapi_price(hotel, date, date)
            except Exception as e:
                print("   ⚠️ RapidAPI error:", e)
                rap_price, rap_curr = None, None

            output["rates_by_day"][label][hotel] = {
                "serpapi":  serp_rate,
                "rapidapi": f"{rap_price} {rap_curr}" if rap_price else "N/A"
            }

        time.sleep(PAUSE)

    with open(DATA_DIR / "beckley_rates_combined.json","w") as f:
        json.dump(output, f, indent=2)

    print("\n✅ Done! See data/beckley_rates_combined.json")


if __name__ == "__main__":
    main()
