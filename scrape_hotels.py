import os
import json
import requests
import datetime
import time


def fetch_google_search_results(query):
    api_key = os.environ["SERPAPI_KEY"]  # ✅ FIXED to match GitHub secret name
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


def extract_rate_with_ai(search_result):
    import openai
    openai.api_key = os.environ["OPENROUTER_API_KEY"]
    openai.api_base = "https://openrouter.ai/api/v1"

    prompt = f"""
You're an AI assistant that extracts hotel nightly rates from search results. Your job is to look at the text and return just the number.

Rules:
- Output only the nightly rate as a number (e.g., "132").
- If multiple rates are mentioned, choose the lowest.
- If there's no price mentioned, return "N/A".

Search result:
{search_result}

Price:"""

    try:
        response = openai.ChatCompletion.create(
            model="openai/gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
        )

        print("🔍 AI got this result:\n", search_result)
        print("💬 AI response:", response)

        return response["choices"][0]["message"]["content"].strip()
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
            time.sleep(2)  # Respect SerpAPI rate limit

            serp_result = json.dumps(result)
            rate = extract_rate_with_ai(serp_result)

            rate_data["rates_by_day"][day_name][hotel] = rate
            print(f"✅ {hotel}: {rate}")

            # Save debug file
            debug_filename = f"data/debug_{hotel.replace(' ', '_').replace(',', '')}_{day_name}.json"
            with open(debug_filename, "w") as f:
                json.dump(result, f, indent=2)

    # Save final rates
    with open("data/beckley_rates.json", "w") as f:
        json.dump(rate_data, f, indent=2)


if __name__ == "__main__":
    run()
