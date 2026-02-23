import requests
import json
import os
import time

TEAM_ID = "darkonteams"
BEARER_TOKEN = os.environ["LICHESS_TOKEN"]

HEADERS = {
    "Authorization": f"Bearer {BEARER_TOKEN}"
}

JOIN_DELAY = 2
MAX_TOURNAMENTS_TO_CHECK = 20  # 🔥 NUR die 5 neuesten

def join_team_tournaments():
    arena_url = f"https://lichess.org/api/team/{TEAM_ID}/arena?status=created"

    resp = requests.get(arena_url, headers=HEADERS, timeout=15)

    if resp.status_code == 429:
        print("Rate limited on GET – aborting run.")
        return

    resp.raise_for_status()

    tournaments = [
        json.loads(line)
        for line in resp.text.splitlines()
        if line.strip()
    ]

    if not tournaments:
        print("No tournaments found.")
        return

    # 🧠 SORTIEREN: neueste zuerst
    tournaments.sort(key=lambda t: t.get("createdAt", 0), reverse=True)

    # ✂️ BEGRENZEN: nur die neuesten X
    tournaments = tournaments[:MAX_TOURNAMENTS_TO_CHECK]

    print(f"Checking {len(tournaments)} newest tournaments")

    for t in tournaments:
        tid = t["id"]

        # 🤖 NUR explizit bot-erlaubt
        if t.get("noBots") is not False:
            print(f"Skipping {tid}: bots not explicitly allowed")
            continue

        # 🔒 sonstige Restriktionen
        if t.get("conditions"):
            print(f"Skipping {tid}: has restrictions")
            continue

        join_url = f"https://lichess.org/api/tournament/{tid}/join"
        join_resp = requests.post(join_url, headers=HEADERS, timeout=15)

        if join_resp.status_code == 200:
            print(f"Joined {tid}")
            time.sleep(JOIN_DELAY)
            continue

        if join_resp.status_code == 429:
            print("Rate limit reached on POST – stopping.")
            break

        if "joining too many tournaments" in join_resp.text.lower():
            print("Tournament join limit reached – stopping.")
            break

        print(f"Failed {tid}: {join_resp.status_code} | {join_resp.text}")
        time.sleep(JOIN_DELAY)

if __name__ == "__main__":
    join_team_tournaments()
