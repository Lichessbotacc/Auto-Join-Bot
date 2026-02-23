import requests
import json
import os
import time

TEAM_ID = "darkonteams"
BEARER_TOKEN = os.environ["LICHESS_TOKEN"]

HEADERS = {
    "Authorization": f"Bearer {BEARER_TOKEN}"
}

JOIN_DELAY = 2 # sehr konservativ

def join_team_tournaments():
    arena_url = f"https://lichess.org/api/team/{TEAM_ID}/arena?status=created"

    resp = requests.get(arena_url, headers=HEADERS, timeout=15)

    # ⛔ Rate limit schon beim Laden
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

    for t in tournaments:
        tid = t.get("id")

        # 🤖 HARD FILTER: NUR explizit bot-erlaubte Turniere
        if t.get("noBots") is not False:
            print(f"Skipping {tid}: bots not explicitly allowed")
            continue

        # 🔒 Andere Restriktionen → skip
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
            print("Rate limit reached on POST – stopping immediately.")
            break

        if "joining too many tournaments" in join_resp.text.lower():
            print("Tournament join limit reached – stopping.")
            break

        print(f"Failed {tid}: {join_resp.status_code} | {join_resp.text}")
        time.sleep(JOIN_DELAY)

if __name__ == "__main__":
    join_team_tournaments()
