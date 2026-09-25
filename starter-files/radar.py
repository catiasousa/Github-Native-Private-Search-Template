#!/usr/bin/env python3
"""
GitHub profile search starter script.

This file is a STARTER TEMPLATE. It is not meant to run as-is.

Before using it:
1. Copy this file, along with the other starter files, into a new PRIVATE repository.
2. Paste this file's contents into Claude along with your search requirements.
3. Ask Claude to update the configuration values below for your specific search.
4. Use Claude's updated version in your private repository.

Do NOT run this script from the public template repository.
"""

import csv
import json
import os
import sys
import time
from datetime import date, datetime, timedelta, timezone

import requests

# ------------------------------------------------------------------ settings
# Replace these placeholder values with your own search criteria.
LOCATIONS = ["REPLACE_WITH_LOCATION_1", "REPLACE_WITH_LOCATION_2"]
SEARCH_LANGUAGE = "REPLACE_WITH_LANGUAGE"

MIN_ACCOUNT_AGE_YEARS = 3
MIN_PUBLIC_REPOS = 5
ACTIVE_WITHIN_DAYS = 183
LANGUAGE_WITHIN_DAYS = 730
RECHECK_AFTER_DAYS = 30
MIN_CORE_REMAINING = 30

NOT_LOCATION_HINTS = [
    # Add terms here to exclude ambiguous places with the same name.
]

CSV_FILE = "profiles.csv"
STATE_FILE = "state.json"
CSV_COLUMNS = [
    "login", "full_name", "github_url", "location", "company", "blog",
    "followers", "public_repos", "created_at", "last_push",
    "language_repos", "date_added", "last_checked", "contacted", "notes",
]
MANUAL_COLUMNS = ["contacted", "notes"]
# ---------------------------------------------------------------------------

TOKEN = os.environ.get("GH_TOKEN", "")
SESSION = requests.Session()
SESSION.headers.update({
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "github-search-template",
})
if TOKEN:
    SESSION.headers["Authorization"] = f"Bearer {TOKEN}"

core_remaining = None


class OutOfBudget(Exception):
    """The hourly API limit is used up."""


def parse_dt(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def api(path, params=None, search=False):
    global core_remaining
    url = "https://api.github.com" + path
    for attempt in range(4):
        try:
            r = SESSION.get(url, params=params, timeout=30)
        except requests.RequestException:
            time.sleep(3 * (attempt + 1))
            continue
        remaining = int(r.headers.get("x-ratelimit-remaining", "1"))
        reset = int(r.headers.get("x-ratelimit-reset", "0"))
        if not search:
            core_remaining = remaining
        if r.status_code == 200:
            if search and remaining == 0:
                time.sleep(max(1, reset - time.time()) + 1)
            return r.json()
        if r.status_code in (404, 422):
            return None
        if r.status_code in (403, 429):
            if remaining == 0:
                if search:
                    time.sleep(min(70, max(1, reset - time.time()) + 1))
                    continue
                raise OutOfBudget()
            time.sleep(min(int(r.headers.get("retry-after", "30")), 90))
            continue
        if r.status_code >= 500:
            time.sleep(5 * (attempt + 1))
            continue
        r.raise_for_status()
    raise RuntimeError(f"request failed: {path}")


def search_window(location, start, end, found):
    q = (
        f"location:{location} language:{SEARCH_LANGUAGE} type:user "
        f"repos:>={MIN_PUBLIC_REPOS} created:{start}..{end}"
    )
    params = {"q": q, "per_page": 100, "page": 1, "sort": "joined", "order": "asc"}
    first = api("/search/users", params, search=True)
    if not first:
        return
    total = first["total_count"]
    if total > 1000 and start < end:
        a, b = date.fromisoformat(start), date.fromisoformat(end)
        mid = a + (b - a) // 2
        search_window(location, start, mid.isoformat(), found)
        search_window(location, (mid + timedelta(days=1)).isoformat(), end, found)
        return
    for item in first["items"]:
        found.add(item["login"])
    for page in range(2, min(10, (total + 99) // 100) + 1):
        params["page"] = page
        data = api("/search/users", params, search=True)
        if not data or not data["items"]:
            break
        for item in data["items"]:
            found.add(item["login"])


def find_candidates():
    cutoff = date.today() - timedelta(days=int(365.25 * MIN_ACCOUNT_AGE_YEARS))
    found = set()
    for loc in LOCATIONS:
        try:
            search_window(loc, "2008-01-01", cutoff.isoformat(), found)
        except (OutOfBudget, RuntimeError) as e:
            print(f"search stopped early for {loc}: {e}")
    return found


def is_location_match(location):
    loc = (location or "").lower()
    if not any(town.lower() in loc for town in LOCATIONS):
        return False
    return not any(hint in loc for hint in NOT_LOCATION_HINTS)


def has_full_name(name):
    words = [w for w in (name or "").replace(",", " ").split() if len(w) >= 2]
    return len(words) >= 2


def evaluate(login, now):
    u = api(f"/users/{login}")
    if not u or u.get("type") != "User":
        return False, None
    if not has_full_name(u.get("name")):
        return False, None
    if not is_location_match(u.get("location")):
        return False, None
    created = parse_dt(u["created_at"])
    if created > now - timedelta(days=int(365.25 * MIN_ACCOUNT_AGE_YEARS)):
        return False, None
    if u.get("public_repos", 0) < MIN_PUBLIC_REPOS:
        return False, None

    repos = []
    for page in (1, 2):
        batch = api(
            f"/users/{login}/repos",
            {"per_page": 100, "sort": "pushed", "direction": "desc", "page": page},
        )
        if not batch:
            break
        repos += batch
        if len(batch) < 100:
            break

    epoch = datetime.min.replace(tzinfo=timezone.utc)

    def pushed(r):
        return parse_dt(r["pushed_at"]) if r.get("pushed_at") else epoch

    own = sorted((r for r in repos if not r.get("fork")), key=pushed, reverse=True)
    if not own:
        return False, None
    if pushed(own[0]) < now - timedelta(days=ACTIVE_WITHIN_DAYS):
        return False, None

    language_matches = [r for r in own if r.get("language") == SEARCH_LANGUAGE]
    if not language_matches:
        return False, None

    recent_language = [
        r for r in language_matches if pushed(r) >= now - timedelta(days=LANGUAGE_WITHIN_DAYS)
    ]
    if not recent_language:
        return False, None

    row = {
        "login": login,
        "full_name": u["name"].strip(),
        "github_url": u["html_url"],
        "location": u.get("location") or "",
        "company": u.get("company") or "",
        "blog": u.get("blog") or "",
        "followers": u.get("followers", 0),
        "public_repos": u.get("public_repos", 0),
        "created_at": u["created_at"][:10],
        "last_push": pushed(own[0]).date().isoformat(),
        "language_repos": "; ".join(r["name"] for r in recent_language[:3]),
    }
    return True, row


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"checked": {}}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=1, sort_keys=True)


def read_manual_columns():
    manual = {}
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                manual[r["login"]] = {c: r.get(c, "") for c in MANUAL_COLUMNS}
    return manual


def write_csv(state, manual):
    rows = []
    for login, rec in state["checked"].items():
        if not rec.get("passed"):
            continue
        row = dict(rec["row"])
        row["date_added"] = rec.get("added", rec["at"])[:10]
        row["last_checked"] = rec["at"][:10]
        for c in MANUAL_COLUMNS:
            row[c] = manual.get(login, {}).get(c, "")
        rows.append(row)
    rows.sort(key=lambda r: r["last_push"], reverse=True)
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        w.writeheader()
        w.writerows(rows)
    return len(rows)


def main():
    if not TOKEN:
        print("GH_TOKEN is missing. Run this inside GitHub Actions.")
        sys.exit(1)
    now = datetime.now(timezone.utc)
    state = load_state()
    checked = state["checked"]
    manual = read_manual_columns()

    logins = find_candidates()
    print(f"search found {len(logins)} profiles")

    stale_before = (now - timedelta(days=RECHECK_AFTER_DAYS)).isoformat()
    new = sorted(l for l in logins if l not in checked)
    stale = sorted(
        (l for l in logins if l in checked and checked[l]["at"] < stale_before),
        key=lambda l: checked[l]["at"],
    )
    todo = new + stale
    print(f"to check this run: {len(new)} new and {len(stale)} due for a recheck")

    done = passed = 0
    try:
        for login in todo:
            if core_remaining is not None and core_remaining < MIN_CORE_REMAINING:
                print("hourly limit nearly used, stopping. The next run continues.")
                break
            try:
                ok, row = evaluate(login, now)
            except OutOfBudget:
                print("hourly limit reached, stopping. The next run continues.")
                break
            except RuntimeError as e:
                print(f"skipped {login}: {e}")
                continue
            old = checked.get(login, {})
            checked[login] = {"at": now.isoformat(), "passed": ok, "row": row}
            if ok:
                checked[login]["added"] = old.get("added", now.isoformat())
                passed += 1
            done += 1
    finally:
        save_state(state)
        total = write_csv(state, manual)
        left = len([l for l in logins if l not in checked])
        print(f"checked {done} profiles, {passed} passed, {total} in profiles.csv, {left} not yet checked")


if __name__ == "__main__":
    main()
