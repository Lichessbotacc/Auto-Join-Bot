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

JOIN_DELAY = 5  # kleiner Delay zwischen Join-Versuchen
CACHE_FILE = Path("checked_tournaments.json")
RETRY_DELAY = 10  # Sekunden warten, wenn Turnier noch nicht joinbar
MAX_RETRIES = 5


# --- Cache laden / speichern ---
def load_checked():
    if CACHE_FILE.exists():
        content = CACHE_FILE.read_text().strip()
        if content:
            try:
                return set(json.loads(content))
            except json.JSONDecodeError:
                print("Warning: invalid JSON in cache file, resetting.")
    return set()


def save_checked(checked):
    CACHE_FILE.write_text(json.dumps(sorted(checked), indent=2))


# --- Join-Funktion mit Retry ---
def try_join(tid):
    join_url = f"https://lichess.org/api/tournament/{tid}/join"
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.post(join_url, headers=HEADERS, timeout=15)
        except Exception as e:
            print(f"[{tid}] Error joining: {e}")
            return False

        if resp.status_code == 200:
            print(f"[{tid}] Joined successfully!")
            return True
        elif "tournament not open" in resp.text.lower():
            print(f"[{tid}] Not open yet, retry {attempt}/{MAX_RETRIES} in {RETRY_DELAY}s...")
            time.sleep(RETRY_DELAY)
            continue
        elif resp.status_code == 429:
            print(f"[{tid}] Rate limit hit – stopping retries.")
            return False
        else:
            print(f"[{tid}] Failed: {resp.status_code} | {resp.text}")
            return False
    print(f"[{tid}] Could not join after {MAX_RETRIES} retries.")
    return False


# --- Hauptfunktion ---
def join_team_tournaments():
    checked = load_checked()
    arena_url = f"https://lichess.org/api/team/{TEAM_ID}/arena?status=created"
    try:
        resp = requests.get(arena_url, headers=HEADERS, timeout=15)
    except Exception as e:
        print(f"Failed to fetch tournaments: {e}")
        return

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
        if tid in checked:
            continue
        checked.add(tid)

        if t.get("noBots") is True:
            print(f"[{tid}] Skipping: bots not allowed")
            continue

        if t.get("conditions"):
            print(f"[{tid}] Skipping: has restrictions")
            continue

        # Versuche sofort zu joinen
        try_join(tid)
        time.sleep(JOIN_DELAY)

    save_checked(checked)


if __name__ == "__main__":
    join_team_tournaments()
