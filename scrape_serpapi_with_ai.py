import os
import json
import requests
import datetime
import time
import openai

# ——— CONFIG ———
SERPAPI_KEY    = os.environ["SERPAPI_KEY"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
openai.api_key = OPENAI_API_KEY

# ——— FUNCTIONS ———
def fetch_serpapi_offers(hotel, date):
    """
    Get Google's hotel_results JSON from SerpAPI via the normal google engine.
    """
    params = {
        "engine":   "google",
        "q":        f"{hotel} Beckley WV {date} hotel price",
        "location": "Beckley, West Virginia, United States",
        "hl":       "en",
        "gl":       "us",
        "api_key":  SERPAPI_KEY,
    }
    r = requests.get("https://serpapi.com/search", params=params)
    r.raise_for_status()
    return r.json()

def ai_extract_range(raw_json):
    """
    Ask ChatGPT to extract the min/max price from the SerpAPI JSON blob.
    Returns a string like 'LOW-HIGH' or 'N/A'.
    """
    prompt = f"""
Here is a SerpAPI search JSON response containing the `hotel_results` list for a single hotel's check-in:

{json.dumps(raw_json)}

Please return **exactly** two numbers (no extra commentary), the **lowest** nightly price and the **highest** nightly price you find, separated by a hyphen (`-`), for example:

114-165

If you can’t find any price, reply N/A.
"""
    resp = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    return resp.choices[0].message.content.strip()

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

    today = datetime.date.today()
    friday = today + datetime.timedelta((4 - today.weekday()) % 7)

    rate_data = {
        "generated": str(today),
        "checkin_dates": {
            "Today":    str(today),
            "Tomorrow": str(today + datetime.timedelta(days=1)),
            "Friday":   str(friday),
        },
        "rates_by_day": {},
    }

    for day_name, date_str in rate_data["checkin_dates"].items():
        print(f"\n📅 {day_name} → {date_str}")
        rate_data["rates_by_day"][day_name] = {}

        for hotel in hotels:
            print(f"🔎 {hotel} on {date_str}")
            raw = fetch_serpapi_offers(hotel, date_str)

            # Optional: dump raw JSON for debugging
            debug_fn = f"data/debug_{hotel.replace(' ', '_')}_{day_name}.json"
            with open(debug_fn, "w") as dbg:
                json.dump(raw, dbg, indent=2)

            low_high = ai_extract_range(raw)
            rate_data["rates_by_day"][day_name][hotel] = low_high
            print(f"✅ {hotel}: {low_high}")

            time.sleep(2)  # be gentle to the API

    # write out the consolidated rates
    with open("data/beckley_rates.json", "w") as out:
        json.dump(rate_data, out, indent=2)
    print("\nAll done — rates written to data/beckley_rates.json")

if __name__ == "__main__":
    run()
