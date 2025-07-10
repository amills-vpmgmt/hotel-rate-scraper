import json
from datetime import date, timedelta

# Generate today's mock hotel rates for Beckley
today = date.today()
tomorrow = today + timedelta(days=1)
weekday = today.weekday()

# Handle Friday logic
if weekday == 3:  # Thursday
    next_friday = today + timedelta(days=8)
else:
    next_friday = today + timedelta((4 - weekday) % 7)

checkin_dates = {
    "Today": today.strftime("%Y-%m-%d"),
    "Tomorrow": tomorrow.strftime("%Y-%m-%d"),
    "Friday": next_friday.strftime("%Y-%m-%d")
}

# Mock rate data
rates = {
    "Courtyard Beckley": 142,
    "Hampton Inn Beckley": 138,
    "Tru by Hilton Beckley": 124,
    "Fairfield Inn Beckley": 131,
    "Best Western Beckley": 122,
    "Country Inn Beckley": 127,
    "Comfort Inn Beckley": 129
}

# Create structured JSON data
output = {
    "generated": today.strftime("%Y-%m-%d"),
    "checkin_dates": checkin_dates,
    "rates_by_day": {
        label: {
            hotel: rate + i * 2  # Slightly vary prices per day
            for hotel, rate in rates.items()
        }
        for i, label in enumerate(["Today", "Tomorrow", "Friday"])
    }
}

# Save to JSON file
with open("data/beckley_rates.json", "w") as f:
    json.dump(output, f, indent=2)

print("✅ Hotel rates written to data/beckley_rates.json")
