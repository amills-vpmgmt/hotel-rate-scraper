# scrape_hotels.py
import os
import json
from datetime import datetime, timedelta
import pytz
import requests

# Hotel search queries
hotels = {
    "Courtyard Beckley": "Courtyard Beckley WV",
    "Hampton Inn Beckley": "Hampton Inn Beckley WV",
    "Tru by Hilton Beckley": "Tru by Hilton Beckley WV",
    "Fairfield Inn Beckley": "Fairfield Inn Beckley WV",
    "Best Western Beckley": "Best Western Beckley WV",
    "Country Inn Beckley": "Country Inn and Suites Beckley WV",
    "Comfort Inn Beckley": "Comfort Inn Beckley WV"
}

# OpenRouter AI model and key
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = "openai/gpt-3.5-turbo"

# SerpAPI config
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
SEARCH_ENGINE = "google"

# Today's and next two days' dates
import pytz
eastern = pytz.timezone("US/Eastern")
now = datetime.now(eastern)
checkin_dates = {
    "Today": now.strftime("%Y-%m-%d"),
    "Tomorrow": (now + timedelta(days=1)).strftime("%Y-%m-%d"),
    "Friday": (now + timedelta(days=(4 - now.weekday()) % 7)).strftime("%Y-%m-%d")
}

# Run SerpAPI search
def get_search_result(hotel, date):
    url = "https://serpapi.com/search"
    params = {
        "engine": SEARCH_ENGINE,
        "q": f"{hotel} {date}",
        "api_key": SERPAPI_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    return json.dumps(data)

# Ask AI to extract rate from SERP result
def extract_rate_with_ai(serp_result):
    prompt = f"""
You are a hotel pricing assistant. Based on the following search result, extract the lowest nightly rate in USD (numbers only, no dollar sign or text). If no rate is found, say "N/A".

Search result:
{serp_result}
"""
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    response = requests.post("https://openrouter.ai/api/v1/chat/completions", json={
        "model": OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": prompt}]
    }, headers=headers)

    result = response.json()
    print("🧠 RAW AI RESPONSE:", result)

    try:
        return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print("❌ Error parsing AI result:", e)
        return "N/A"

# Main loop
def run():
    output = {
        "generated": now.strftime("%Y-%m-%d"),
        "checkin_dates": checkin_dates,
        "rates_by_day": {}
    }

    for label, date in checkin_dates.items():
        print(f"📅 Processing rates for {label} ({date})")
        output["rates_by_day"][label] = {}
        for hotel_name, search_query in hotels.items():
            serp_result = get_search_result(search_query, date)
            rate = extract_rate_with_ai(serp_result)
            print(f"🏨 {hotel_name}: {rate}")
            output["rates_by_day"][label][hotel_name] = rate

    os.makedirs("data", exist_ok=True)
    with open("data/beckley_rates.json", "w") as f:
        json.dump(output, f, indent=2)

if __name__ == "__main__":
    run()

import requests
import json
from datetime import datetime, timedelta
import pytz
import os

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")

hotels = [
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
    return {
        "Today": today.strftime("%Y-%m-%d"),
        "Tomorrow": (today + timedelta(days=1)).strftime("%Y-%m-%d"),
        "Friday": (today + timedelta(days=(4 - today.weekday()) % 7)).strftime("%Y-%m-%d")
    }

def query_serpapi(query):
    params = {
        "engine": "google",
        "q": query,
        "api_key": SERPAPI_KEY
    }
    response = requests.get("https://serpapi.com/search", params=params)
    return response.json()

def extract_rate_with_ai(search_results, model="openai/gpt-3.5-turbo"):
    prompt = f"""
Your job is to extract the **nightly hotel price in USD** from the following Google search results (in JSON format). 
The price is usually shown like "$139", "USD 149", or "$159 per night".

Return only the **number** (e.g. 139). If you find multiple prices, return the **lowest** one. 
If no valid price is found, just return "N/A".

Here are the results:
{json.dumps(search_results)}
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

def run():
    checkin_dates = get_checkin_dates()
    data = {
        "generated": str(datetime.now(pytz.timezone("US/Eastern")).date()),
        "checkin_dates": checkin_dates,
        "rates_by_day": {"Today": {}, "Tomorrow": {}, "Friday": {}}
    }

    for day, checkin in checkin_dates.items():
        for hotel in hotels:
            query = f"{hotel} Beckley WV room price {checkin}"
            serp_result = query_serpapi(query)
            rate = extract_rate_with_ai(serp_result)

            data["rates_by_day"][day][hotel] = rate

            # Save debug info
            with open(f"data/debug_{hotel.replace(' ', '_')}_{day}.json", "w", encoding="utf-8") as f:
                json.dump(serp_result, f, indent=2)

    with open("data/beckley_rates.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    run()
