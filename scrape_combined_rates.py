import os
import json
import time
import re
import datetime
import requests
from pathlib import Path

# DEBUG: Check SERPAPI_KEY
print("DEBUG: ENV SERPAPI_KEY =", os.getenv("SERPAPI_KEY"))

# Load API Keys from environment
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
RAPIDAI_API_KEY = os.getenv("RAPIDAI_API_KEY") or "HARDCODED_RAPID_API_KEY_IF_NEEDED"

# Fail if SERPAPI_KEY is missing
if not SERPAPI_KEY:
    print("\n❌ SERPAPI_KEY is not set. Check GitHub Secrets.")
    exit(1)

# Config Constants
RAPIDAPI_HOST = "expedia13.p.rapidapi.com"

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
COUNTRY = "United States"
DATA_DIR = Path("data")
PAUSE = 2  # seconds between API calls

# Function to fetch data from SerpAPI
def fetch_serpapi(query):
    params = {
        "engine": "google_hotels",
        "q": query,
        "location": f"{CITY}, {STATE}, {COUNTRY}",
        "hl": "en",
        "gl": "us",
        "api_key": SERPAPI_KEY
    }
    resp = requests.get("https://serpapi.com/search", params=params)
    resp.raise_for_status()
    return resp.json()

# Cleaned-up price extraction function
def extract_serp_rate(serp_json):
    prices = []

    # First priority: structured hotel_results prices
    for hotel in serp_json.get("hotel_results", []):
        price_str = hotel.get("price", "")
        if price_str.startswith("$"):
            amount = int(price_str.replace("$", "").replace(",", ""))
            prices.append(amount)

    # If no hotel_results found, fallback to knowledge_graph
    if not prices:
        kg = serp_json.get("knowledge_graph", {})
        for offer in kg.get("pricing", {}).get("offers", []):
            price_str = offer.get("price", "")
            if price_str.startswith("$"):
                amount = int(price_str.replace("$", "").replace(",", ""))
                prices.append(amount)

    if not prices:
        return "N/A"

    lo, hi = min(prices), max(prices)
    return f"{lo}-{hi}" if lo != hi else str(lo)

# Main function to scrape rates
def main():
    checkin_dates = {
        "Today": str(datetime.date.today()),
        "Tomorrow": str(datetime.date.today() + datetime.timedelta(days=1)),
        "Friday": str(datetime.date.today() + datetime.timedelta((4 - datetime.date.today().weekday()) % 7))
    }

    rate_data = {
        "generated": str(datetime.date.today()),
        "checkin_dates": checkin_dates,
        "rates_by_day": {}
    }

    for day_name, date in checkin_dates.items():
        print(f"\n=== {day_name} ({date}) ===")
        rate_data["rates_by_day"][day_name] = {}

        for hotel in HOTELS:
            serp_query = f"{hotel} {CITY} WV {date} hotel price"
            print(f"• {hotel}")

            try:
                serp_json = fetch_serpapi(serp_query)
                rate = extract_serp_rate(serp_json)
            except Exception as e:
                print(f"❌ Error fetching rate for {hotel}: {e}")
                rate = "N/A"
                serp_json = {}  # Ensure serp_json is always defined

            rate_data["rates_by_day"][day_name][hotel] = rate
            time.sleep(PAUSE)

            # Save debug JSON
            debug_file = DATA_DIR / f"debug_{hotel.replace(' ', '_').replace(',', '')}_{day_name}.json"
            debug_file.parent.mkdir(parents=True, exist_ok=True)
            with open(debug_file, "w") as f:
                json.dump(serp_json, f, indent=2)

    # Save final rates
    with open(DATA_DIR / "beckley_rates.json", "w") as f:
        json.dump(rate_data, f, indent=2)

if __name__ == "__main__":
    main()
