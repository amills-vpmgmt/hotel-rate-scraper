import os, json, requests, datetime, time
import openai

# ─── CONFIG ───────────────────────────────────────────────────────────────────
SERPAPI_KEY    = os.environ["SERPAPI_KEY"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
openai.api_key = OPENAI_API_KEY

# ─── FUNCTIONS ─────────────────────────────────────────────────────────────────
def fetch_serpapi_offers(hotel, date):
    """Get the raw google_hotels JSON from SerpAPI."""
    params = {
        "engine":    "google_hotels",
        # <-- FIX: include the full "WV"
        "q":         f"{hotel} Beckley WV hotel for {date}",
        "location":  "Beckley, West Virginia, United States",
        "hl":        "en",
        "gl":        "us",
        "api_key":   SERPAPI_KEY,
    }
    # use the .json endpoint
    resp = requests.get("https://serpapi.com/search.json", params=params)
    resp.raise_for_status()
    return resp.json()

def ai_extract_range(raw_json):
    """Ask ChatGPT to extract the min/max price from the SerpAPI JSON blob."""
    # pull out just the 'offers' list so the prompt stays under token limits
    offers = raw_json.get("pricing", {}).get("offers", [])
    prompt = (
        "Here is a list of nightly offers for one hotel:\n\n"
        f"{json.dumps(offers, indent=2)}\n\n"
        "Please return exactly the lowest and highest price you see, "
        "formatted as LOW–HIGH.  If there are no numeric prices, reply N/A."
    )

    resp = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role":"user","content":prompt}],
        temperature=0
    )
    return resp.choices[0].message.content.strip()

# ─── MAIN ──────────────────────────────────────────────────────────────────────
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
    dates = {
      "Today":    today.isoformat(),
      "Tomorrow": (today + datetime.timedelta(days=1)).isoformat(),
      "Friday":   (today + datetime.timedelta((4 - today.weekday()) % 7)).isoformat(),
    }

    output = {
      "generated":    str(today),
      "checkin_dates": dates,
      "rates_by_day": {}
    }

    for label, dt in dates.items():
        output["rates_by_day"][label] = {}
        for hotel in hotels:
            raw  = fetch_serpapi_offers(hotel, dt)
            time.sleep(1)  # throttle
            rng  = ai_extract_range(raw)
            output["rates_by_day"][label][hotel] = rng

    os.makedirs("data", exist_ok=True)
    with open("data/beckley_rates.json", "w") as f:
        json.dump(output, f, indent=2)

if __name__ == "__main__":
    run()

