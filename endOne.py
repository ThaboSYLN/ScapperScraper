import requests
import time
import os


sport_Type = [
    "Football",
    "Rugby",
    "Cricket",
    "Basketball",
    "Tennis",
    "Table Tennis",
    "Ice Hockey",
    "Baseball",
    "Motorsport",
    "MMA",
    "Darts",
    "American Football",
    "Esports",
    "Volleyball",
    "Futsal",
    "Handball",
    "Badminton",
    "Water polo",
    "Aussie Rules",
    "Snooker",
    "Beach Volleyball",
    "Floorball",
    "Cycling",
    "Bandy",
    "Minifootball"
]

numbering = 0
for i in sport_Type:
    numbering = numbering+1
    print(numbering,"",i)

userSelection = int(input("Refer to the number And type the one assocuated with the one you want: "))

spotHolder =sport_Type[userSelection-1]    

URL = f"https://api.sofascore.com/api/v1/sport/{spotHolder.lower().replace(' ', '-')}/events/live"
#https://api.sofascore.com/api/v1/sport/{spotHolder}/categories

#URL = "https://api.sofascore.com/api/v1/sport"


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.sofascore.com/",
    "Origin": "https://www.sofascore.com",
    "Connection": "keep-alive"
}
# CREATE SESSION (more professional)
session = requests.Session()
session.headers.update(headers)

def get_match_minute(match):
    status = match.get("status", {})
    time_data = match.get("time", {})

    if status.get("type") != "inprogress":
        return ""

    period_start = time_data.get("currentPeriodStartTimestamp")
    if not period_start:
        return ""

    now = int(time.time())
    elapsed = (now - period_start) // 60

    description = status.get("description", "").lower()

    # If second half, add 45 minutes
    if "2nd" in description:
        elapsed += 45

    return f"{elapsed}'"


def fetch_live_data():
    try:
        # Using session instead of requests.get (keeps cookies + connection alive)
        response = session.get(URL, timeout=15)

        # Debugging protection (Cloudflare / blocking detection)
        if response.status_code != 200:
            print("Status Code:", response.status_code)
            print("Response Preview:", response.text[:200])
            return

        response.raise_for_status()
        data = response.json()

        print("\n------ LIVE MATCHES ------\n")

        events = data.get("events", [])

        # If no live matches
        if not events:
            print("No live matches currently available.")
            return

        for match in events:
            home = match["homeTeam"]["name"]
            away = match["awayTeam"]["name"]

            home_score = match["homeScore"]["current"]
            away_score = match["awayScore"]["current"]

            status = match["status"]["description"]
            minute = get_match_minute(match)

            print(f"{home} {home_score} - {away_score} {away} | {status} {minute}")

    except requests.exceptions.JSONDecodeError:
        print("JSON Decode Error - Possibly blocked by Cloudflare")
    except requests.exceptions.RequestException as e:
        print("Request Error:", e)
    except Exception as e:
        print("Unexpected Error:", e)


if __name__ == "__main__":
    while True:
        os.system("cls")  # Windows
        fetch_live_data()
        print("\nRefreshing in 10 seconds... (CTRL+C to exit)")
        time.sleep(10)
