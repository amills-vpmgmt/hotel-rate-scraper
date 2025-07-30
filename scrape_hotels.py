import os
import json
import re
import requests
from datetime import datetime, timedelta
import pytz

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")

HOTELS = [
    "Courtyard Beckley",
    "Hampton Inn Beckley",
    "Tru by Hilton Beckley",
    "Fairfield Inn Beckley",
    "Best Western Beckley",
    "Country Inn Beckley",
    "Comfort Inn Beckley"
]

def get_checkin_dates():
    today = datetime.now(pytz.timezone("US/Eastern")).date()
    tomorrow = today + timedelta(days=1)
    friday = today + timedelta((4 - today.weekday()) % 7 or 7)
    return {
        "Today": today.isoformat(),
        "Tomorrow": tomorrow.isoformat(),
        "Friday": friday.isoformat()
    }

def search_hotel_rates(hotel_name, checkin_date):
    query = f"{hotel_name} Beckley WV site:expedia.com OR site:booking.com rate for {checkin_date}"
    params = {
        "engine": "google",
        "q": query,
        "api_key": SERPAPI_KEY,
        "location": "Beckley, WV"
    }
    response = requests.get("https://serpapi.com/search", params=params)
    return response.json()

def extract_rate_with_ai(search_results, model="openai/gpt-3.5-turbo"):
    prompt = f"""
Here is a search result JSON for a hotel query. Your task is to extract the nightly price for the hotel.

Search Results:
{json.dumps(search_results)}

Return just the number (no $ symbol or explanation). If you can't find a rate, respond with "N/A".
"""
    res = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {OPENROUTER_KEY}"},
        json={
            "model": model,
            "messages": [{"role": "user", "content": prompt}]
        }
    )
    try:
        return res.json()["choices"][0]["message"]["content"].strip()
    except KeyError:
        return "N/A"

def extract_rate_with_regex(search_results):
    text_dump = json.dumps(search_results)
    matches = re.findall(r"\$\s?(\d{2,4})", text_dump)
    if matches:
        return matches[0]
    return "N/A"

def run():
    checkin_dates = get_checkin_dates()
    all_rates = {}

    for label, date_str in checkin_dates.items():
        daily_rates = {}
        for hotel in HOTELS:
            print(f"🔍 {hotel} for {label} ({date_str})")
            serp_result = search_hotel_rates(hotel, date_str)

            # Save raw output for debugging
            debug_file = f"data/debug_{hotel.replace(' ', '_')}_{label}.json"
            with open(debug_file, "w") as dbg:
                json.dump(serp_result, dbg, indent=2)

            rate = extract_rate_with_ai(serp_result)
            if rate == "N/A":
                print("⚠️  AI couldn't find price, trying regex fallback...")
                rate = extract_rate_with_regex(serp_result)

            daily_rates[hotel] = int(rate) if rate.isdigit() else "N/A"

        all_rates[label] = daily_rates

    out = {
        "generated": datetime.now(pytz.timezone("US/Eastern")).strftime("%Y-%m-%d"),
        "checkin_dates": checkin_dates,
        "rates_by_day": all_rates
    }

    with open("data/beckley_rates.json", "w") as f:
        json.dump(out, f, indent=2)

    print("✅ Done! Data written to data/beckley_rates.json")

if __name__ == "__main__":
    run()
