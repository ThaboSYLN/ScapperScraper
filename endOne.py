import requests
import time
import os


sport_Type =['football',
'Basketball',
'Tennis',
'American Football',
'Baseball',
'Cricket',
'Ice Hockey',
'Handball',
'Volleyball',
'Rugby',
'Darts',
'Snooker',
'Table Tennis',
'MMA',
'Boxing',
'Cycling']
numbering = 0
for i in sport_Type:
    numbering = numbering+1
    print(numbering,"",i)
userSelection = int(input("Refer to the number And type the one assocuated with the one you want: "))
spotHolder =sport_Type[userSelection-1]    
URL = f"https://api.sofascore.com/api/v1/sport/{spotHolder.lower().replace(' ', '-')}/events/live"
#URL = "https://api.sofascore.com/api/v1/sport"


headers = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

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
        response = requests.get(URL, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()

        print("\n------ LIVE MATCHES ------\n")

        for match in data.get("events", []):
            home = match["homeTeam"]["name"]
            away = match["awayTeam"]["name"]

            home_score = match["homeScore"]["current"]
            away_score = match["awayScore"]["current"]

            status = match["status"]["description"]
            minute = get_match_minute(match)

            print(f"{home} {home_score} - {away_score} {away} | {status} {minute}")

    except Exception as e:
        print("Error:", e)


if __name__ == "__main__":
    while True:
        os.system("cls")  # Windows
        fetch_live_data()
        time.sleep(10)
