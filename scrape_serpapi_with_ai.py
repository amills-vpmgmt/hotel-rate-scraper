import os
import json
import requests
import datetime
import time
from openai import OpenAI

# ——— CONFIG ———
SERPAPI_KEY    = os.environ["SERPAPI_KEY"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

# instantiate the new OpenAI v1 client
client = OpenAI(api_key=OPENAI_API_KEY)

# ——— FUNCTIONS ———
def fetch_serpapi_offers(hotel: str, date: str) -> dict:
    """
    Fetch the raw Google hotel_results JSON from SerpAPI.
    """
    params = {
        "engine":   "google",
        "q":        f"{hotel} Beckley WV {date} hotel price",
        "location": "Beckley, West Virginia, United States",
        "hl":       "en",
        "gl":       "us",
        "api_key":  SERPAPI_KEY,
    }
    resp = requests.get("https://serpapi.com/search", params=params)
    resp.raise_for_status()
    return resp.json()

def ai_extract_range(raw_json: dict) -> str:
    """
    Ask the LLM to pull out the lowest and highest nightly price,
    returning a string like "114-165" or "N/A".
    """
    prompt = f"""
Here is a SerpAPI JSON response for a single hotel's check-in (look inside "hotel_results"):

{json.dumps(raw_json)}

Please return **exactly** two numbers (no extra text), the **lowest** nightly price and the **highest** nightly price, separated by a hyphen, e.g.:

114-165

If no prices are found, reply only "N/A".
"""
    resp = client.chat.completions.create(
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

    today  = datetime.date.today()
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

            # Debug‐dump each hotel's raw JSON
            dbg_path = f"data/debug_{hotel.replace(' ', '_')}_{day_name}.json"
            with open(dbg_path, "w") as dbg_f:
                json.dump(raw, dbg_f, indent=2)

            low_high = ai_extract_range(raw)
            rate_data["rates_by_day"][day_name][hotel] = low_high
            print(f"✅ {hotel}: {low_high}")

            time.sleep(2)  # avoid SerpAPI rate limits

    # Write consolidated output
    out_path = "data/beckley_rates.json"
    with open(out_path, "w") as out_f:
        json.dump(rate_data, out_f, indent=2)

    print(f"\n✨ Done! Wrote updated rates → {out_path}")

if __name__ == "__main__":
    run()
