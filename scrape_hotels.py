import os
import json
import requests
import datetime
import time

def fetch_google_search_results(query):
    api_key = os.environ["SERPAPI_KEY"]
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
    try:
        if "hotel_results" in result:
            prices = []
            for hotel in result["hotel_results"]:
                if "price" in hotel and hotel["price"].startswith("$"):
                    price = int(hotel["price"].replace("$", "").replace(",", ""))
                    prices.append(price)
            return str(min(prices)) if prices else "N/A"
        return "N/A"
    except Exception as e:
        print("❌ Error extracting rate from SerpAPI:", e)
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
            "Friday": str(datetime.date.today() + datetime.timedelta((4 - datetime.date.today().weekday()) % 7)),
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
            time.sleep(2)  # To avoid hitting rate limits

            rate = extract_rate_from_serpapi(result)

            rate_data["rates_by_day"][day_name][hotel] = rate
            print(f"✅ {hotel}: {rate}")

            debug_filename = f"data/debug_{hotel.replace(' ', '_').replace(',', '')}_{day_name}.json"
            with open(debug_filename, "w") as f:
                json.dump(result, f, indent=2)

    with open("data/beckley_rates.json", "w") as f:
        json.dump(rate_data, f, indent=2)

if __name__ == "__main__":
    run()
