import os
import json
import requests
import datetime
import time
import re

def fetch_google_search_results(query):
    api_key = os.environ.get("SERPAPI_KEY")
    params = {
        "engine": "google",
        "q": query,
        "location": "Beckley, West Virginia, United States",
        "hl": "en",
        "gl": "us",
        "api_key": api_key,
    }
    response = requests.get("https://serpapi.com/search", params=params)
    return response.json()

def extract_rate_from_serpapi(result):
    """
    Try to extract dollar amounts from SerpAPI response by checking both
    'hotel_results' prices and 'organic_results' snippets.
    Returns the lowest price found or 'N/A'.
    """
    try:
        prices = []
        # Extract from structured hotel_results if available
        for hotel in result.get("hotel_results", []):
            price_str = hotel.get("price", "")
            if price_str.startswith("$"):
                # normalize and parse
                amount = int(price_str.replace("$", "").replace(",", ""))
                prices.append(amount)
        # Extract from organic_results snippets
        for item in result.get("organic_results", []):
            snippet = item.get("snippet", "")
            # find all $NNN patterns
            for match in re.findall(r"\$[\d,]+", snippet):
                amount = int(match.replace("$", "").replace(",", ""))
                prices.append(amount)
        # Return the lowest price found
        if prices:
            return str(min(prices))
        return "N/A"
    except Exception as e:
        print("❌ Error extracting rate:", e)
        return "N/A"

def run():
    hotels = [
        "Courtyard Beckley",
        "Hampton Inn Beckley",
        "Tru by Hilton Beckley",
        "Fairfield Inn Beckley",
        "Best Western Beckley",
        "Country Inn Beckley",
        "Comfort Inn Beckley",
    ]

    rate_data = {
        "generated": str(datetime.date.today()),
        "checkin_dates": {
            "Today": str(datetime.date.today()),
            "Tomorrow": str(datetime.date.today() + datetime.timedelta(days=1)),
            "Friday": str(
                datetime.date.today() + datetime.timedelta((4 - datetime.date.today().weekday()) % 7)
            ),
        },
        "rates_by_day": {},
    }

    for day_name, date in rate_data["checkin_dates"].items():
        print(f"\n📅 {day_name} ({date})")
        rate_data["rates_by_day"][day_name] = {}

        for hotel in hotels:
            query = f"{hotel} Beckley WV {date} hotel price"
            print(f"\n🔎 Searching: {query}")

            result = fetch_google_search_results(query)
            time.sleep(2)

            rate = extract_rate_from_serpapi(result)
            rate_data["rates_by_day"][day_name][hotel] = rate
            print(f"✅ {hotel}: {rate}")

            # save raw JSON for debug
            debug_name = f"data/debug_{hotel.replace(' ', '_').replace(',', '')}_{day_name}.json"
            with open(debug_name, "w") as f:
                json.dump(result, f, indent=2)

    # write out consolidated rates
    with open("data/beckley_rates.json", "w") as f:
        json.dump(rate_data, f, indent=2)

if __name__ == "__main__":
    run()
