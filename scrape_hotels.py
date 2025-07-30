# scrape_hotels.py
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
