import requests
import json
import os
import time

TEAM_ID = "darkonteams"
BEARER_TOKEN = os.environ["LICHESS_TOKEN"]

HEADERS = {
    "Authorization": f"Bearer {BEARER_TOKEN}"
}

JOIN_DELAY = 5  # Sekunden Pause zwischen Joins

def join_team_tournaments():
    arena_url = f"https://lichess.org/api/team/{TEAM_ID}/arena?status=created"

    resp = requests.get(arena_url, headers=HEADERS, timeout=15)
    resp.raise_for_status()

    tournaments = [
        json.loads(line)
        for line in resp.text.splitlines()
        if line.strip()
    ]

    if not tournaments:
        print("No new tournaments found.")
        return

    for t in tournaments:
        tid = t["id"]

        # 🔒 1️⃣ Restriction-Checks (wenn vorhanden)
        if t.get("conditions"):
            print(f"Skipping {tid}: has tournament restrictions")
            continue

        # 🤖 2️⃣ Bot-Check
        if t.get("noBots", False):
            print(f"Skipping {tid}: bots not allowed")
            continue

        join_url = f"https://lichess.org/api/tournament/{tid}/join"
        join_resp = requests.post(join_url, headers=HEADERS, timeout=15)

        # ✅ Erfolgreich
        if join_resp.status_code == 200:
            print(f"Joined {tid} successfully")
            time.sleep(JOIN_DELAY)
            continue

        # ⛔ Join-Limit erreicht → sofort abbrechen
        if "joining too many tournaments" in join_resp.text.lower():
            print("Join limit reached. Stopping further attempts.")
            break

        # ❌ Sonstige Fehler
        print(f"Skipping {tid}: {join_resp.status_code} | {join_resp.text}")

        time.sleep(JOIN_DELAY)

if __name__ == "__main__":
    join_team_tournaments()
