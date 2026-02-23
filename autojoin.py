import requests
import json
import os
import time
from pathlib import Path

TEAM_ID = "darkonweakbot"
BEARER_TOKEN = os.environ["LICHESS_TOKEN"]

HEADERS = {
    "Authorization": f"Bearer {BEARER_TOKEN}"
}

JOIN_DELAY = 15
CACHE_FILE = Path("checked_tournaments.json")

def load_checked():
    if CACHE_FILE.exists():
        return set(json.loads(CACHE_FILE.read_text()))
    return set()

def save_checked(checked):
    CACHE_FILE.write_text(json.dumps(sorted(checked), indent=2))

def join_team_tournaments():
    checked = load_checked()

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

    print(f"Found {len(tournaments)} tournaments")

    for t in tournaments:
        tid = t["id"]

        # 🗂️ Schon geprüft? → skip
        if tid in checked:
            continue

        checked.add(tid)  # sofort merken

        # 🤖 NUR explizit bot-erlaubt
        if t.get("noBots") is not False:
            print(f"Skipping {tid}: bots not allowed")
            continue

        # 🔒 Andere Restrictions
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

    save_checked(checked)

if __name__ == "__main__":
    join_team_tournaments()
