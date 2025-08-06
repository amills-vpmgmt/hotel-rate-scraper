import os
import json
import time
import datetime
import requests
from pathlib import Path

# Load API Keys
SERPAPI_KEY = os.getenv("SERPAPI_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not SERPAPI_KEY or not OPENROUTER_API_KEY:
    print("\n❌ API keys are missing. Check GitHub Secrets.")
    exit(1)

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
DATA_DIR = Path("data")
PAUSE = 2  # seconds between API calls

# Function to fetch Google Search result using SerpAPI
def fetch_serpapi(query):
    params = {
        "engine": "google",
        "q": query,
        "hl": "en",
        "gl": "us",
        "api_key": SERPAPI_KEY
    }
    resp = requests.get("https://serpapi.com/search", params=params)
    resp.raise_for_status()
    return resp.json()

# Function to extract price using OpenRouter GPT
def extract_price_with_gpt(raw_text):
    prompt = f"""
    Extract the nightly hotel price in USD from the following search result text. Return only the price as a number (no dollar sign, no extra text). If no price is found, respond with N/A.

    Search Result Text:
    {raw_text}
    """

    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}]
    }

    resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
    resp.raise_for_status()
    reply = resp.json()["choices"][0]["message"]["content"].strip()

    if reply.lower() == "n/a":
        return "N/A"

    try:
        return int(reply)
    except ValueError:
        return "N/A"

# Main scraping function
def main():
    checkin_date = str(datetime.date.today() + datetime.timedelta((4 - datetime.date.today().weekday()) % 7))

    rate_data = {
        "generated": str(datetime.date.today()),
        "checkin_date": checkin_date,
        "rates": {}
    }

    for hotel in HOTELS:
        query = f"{hotel} {CITY} {STATE} site:expedia.com {checkin_date} price"
        print(f"\nSearching for: {query}")

        try:
            serp_json = fetch_serpapi(query)
            snippets = []

            for res in serp_json.get("organic_results", []):
                snippet = res.get("snippet", "")
                if snippet:
                    snippets.append(snippet)

            combined_snippets = " ".join(snippets)
            rate = extract_price_with_gpt(combined_snippets)

        except Exception as e:
            print(f"❌ Error for {hotel}: {e}")
            rate = "N/A"

        print(f"{hotel}: {rate}")
        rate_data["rates"][hotel] = rate
        time.sleep(PAUSE)

    # Save final rates
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_DIR / "beckley_rates.json", "w") as f:
        json.dump(rate_data, f, indent=2)

if __name__ == "__main__":
    main()
