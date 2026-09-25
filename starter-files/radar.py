#!/usr/bin/env python3
"""
GitHub profile search starter script.

This file is a STARTER TEMPLATE. It is not meant to run as-is.

Before using it:

1. Copy this file, along with the other starter files, into a new PRIVATE
   repository.
2. Paste this file's contents into Claude or another LLM along with your search
   requirements.
3. Ask the LLM to customize the search logic, filters, CSV columns, and
   workflow for your specific use case.
4. If your search does not use every filter shown here, ask the LLM to remove
   the unused filter from all relevant parts of the file.
5. Use the customized version in your private repository.

Important:

- Not every search needs a location filter.
- Not every search needs a programming-language filter.
- The CSV columns must match the data written by this script.
- If the LLM changes the search criteria, it must update the search query,
  evaluation logic, CSV_COLUMNS, and profiles.csv together.
- Do not run this script from the public template repository.
"""

import csv
import json
import os
import sys
import time
from datetime import date, datetime, timedelta, timezone

import requests


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

# Replace these placeholder values with your own search criteria.

# Not every search needs every filter below.
#
# For example, if your search does not use location:
#
# - remove LOCATIONS
# - remove NOT_LOCATION_HINTS
# - remove the location clause from search_window()
# - remove the is_location_match() function
# - remove its call from evaluate()
# - remove "location" from CSV_COLUMNS
# - remove "location" from the row written by evaluate()
#
# Do not simply leave LOCATIONS empty while keeping the location checks.
# An empty LOCATIONS list would cause every profile to be rejected.

LOCATIONS = [
    "REPLACE_WITH_LOCATION_1",
    "REPLACE_WITH_LOCATION_2",
]

# Replace this with the selected programming language or technology.
#
# If the search does not use a programming-language filter, ask the LLM to
# remove SEARCH_LANGUAGE and the language-related logic from the file.
SEARCH_LANGUAGE = "REPLACE_WITH_LANGUAGE"

# Minimum age of a GitHub account in years.
MIN_ACCOUNT_AGE_YEARS = 3

# Minimum number of public repositories.
MIN_PUBLIC_REPOS = 5

# Require general repository activity within this number of days.
ACTIVE_WITHIN_DAYS = 183

# Require activity in the selected programming language within this number
# of days.
LANGUAGE_WITHIN_DAYS = 730

# Recheck previously processed profiles after this number of days.
RECHECK_AFTER_DAYS = 30

# Stop processing before the API rate limit is completely exhausted.
MIN_CORE_REMAINING = 30

# Add terms here to exclude ambiguous or unrelated locations.
#
# For example, if searching for "Cambridge", exclusions could include other
# regions or cities that should not be included.
NOT_LOCATION_HINTS = []

CSV_FILE = "profiles.csv"
STATE_FILE = "state.json"

# The CSV header must exactly match the fields written by evaluate().
#
# If the search requirements change, ask Claude or another LLM to update:
#
# - this CSV_COLUMNS list
# - the profiles.csv header
# - the row dictionary in evaluate()
# - any supporting API or search logic
CSV_COLUMNS = [
    "login",
    "full_name",
    "github_url",
    "location",
    "company",
    "blog",
    "followers",
    "public_repos",
    "created_at",
    "last_push",
    "language_repos",
    "date_added",
    "last_checked",
    "contacted",
    "notes",
]

# These fields are intended for manual recruiter tracking.
MANUAL_COLUMNS = [
    "contacted",
    "notes",
]


# ---------------------------------------------------------------------------
# GitHub API setup
# ---------------------------------------------------------------------------

TOKEN = os.environ.get("GH_TOKEN", "")

SESSION = requests.Session()
SESSION.headers.update(
    {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "github-search-template",
    }
)

if TOKEN:
    SESSION.headers["Authorization"] = f"Bearer {TOKEN}"

core_remaining = None


class OutOfBudget(Exception):
    """Raised when the available GitHub API request budget is too low."""


def parse_dt(value):
    """Parse a GitHub ISO-8601 datetime string."""
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def api(path, params=None, search=False):
    """
    Make one GET request to the GitHub REST API.

    Search requests and standard API requests use separate GitHub rate limits.
    The remaining standard API request count is stored globally so processing
    can stop before the limit is exhausted.
    """
    global core_remaining

    url = "https://api.github.com" + path

    for attempt in range(4):
        try:
            response = SESSION.get(url, params=params, timeout=30)
        except requests.RequestException:
            time.sleep(3 * (attempt + 1))
            continue

        remaining = int(
            response.headers.get("x-ratelimit-remaining", "1")
        )
        reset = int(
            response.headers.get("x-ratelimit-reset", "0")
        )

        if not search:
            core_remaining = remaining

        if response.status_code == 200:
            return response.json()

        if response.status_code in (404, 422):
            return None

        if response.status_code in (403, 429):
            if remaining == 0:
                if search:
                    wait_seconds = max(1, reset - time.time()) + 1
                    time.sleep(min(70, wait_seconds))
                    continue

                raise OutOfBudget()

            retry_after = int(
                response.headers.get("retry-after", "30")
            )
            time.sleep(min(retry_after, 90))
            continue

        if response.status_code >= 500:
            time.sleep(5 * (attempt + 1))
            continue

        response.raise_for_status()

    raise RuntimeError(f"Request failed after retries: {path}")


# ---------------------------------------------------------------------------
# Candidate search
# ---------------------------------------------------------------------------

def search_window(location, start, end, found):
    """
    Search for users in one location and account-creation date window.

    This function is intentionally simple so Claude or another LLM can adapt
    it for searches that use different filters, such as organization,
    followers, repository topics, or technology requirements.
    """
    query_parts = [
        f"location:{location}",
        f"language:{SEARCH_LANGUAGE}",
        "type:user",
        f"repos:>={MIN_PUBLIC_REPOS}",
        f"created:{start}..{end}",
    ]

    query = " ".join(query_parts)

    params = {
        "q": query,
        "per_page": 100,
        "page": 1,
        "sort": "joined",
        "order": "asc",
    }

    first = api("/search/users", params, search=True)

    if not first:
        return

    total = first["total_count"]

    # GitHub limits a single search query to the first 1,000 results.
    # Split large date windows to discover more results.
    if total > 1000 and start < end:
        start_date = date.fromisoformat(start)
        end_date = date.fromisoformat(end)
        midpoint = start_date + (end_date - start_date) // 2

        search_window(
            location,
            start,
            midpoint.isoformat(),
            found,
        )

        search_window(
            location,
            (midpoint + timedelta(days=1)).isoformat(),
            end,
            found,
        )

        return

    for item in first["items"]:
        found.add(item["login"])

    total_pages = min(10, (total + 99) // 100)

    for page in range(2, total_pages + 1):
        params["page"] = page

        data = api(
            "/search/users",
            params,
            search=True,
        )

        if not data or not data["items"]:
            break

        for item in data["items"]:
            found.add(item["login"])


def find_candidates():
    """
    Find candidate usernames using the configured search criteria.

    If the search is not location-based, ask Claude or another LLM to replace
    this function with logic appropriate for the desired search.
    """
    cutoff = date.today() - timedelta(
        days=int(365.25 * MIN_ACCOUNT_AGE_YEARS)
    )

    found = set()

    for location in LOCATIONS:
        try:
            search_window(
                location,
                "2008-01-01",
                cutoff.isoformat(),
                found,
            )
        except (OutOfBudget, RuntimeError) as error:
            print(
                f"Search stopped early for {location}: {error}"
            )

    return found


# ---------------------------------------------------------------------------
# Profile filters
# ---------------------------------------------------------------------------

def is_location_match(location):
    """
    Return True when the profile location matches the configured locations.

    If the search does not use location, remove this function and its call
    from evaluate(). Do not leave LOCATIONS empty while keeping this function,
    because an empty list will reject every profile.
    """
    profile_location = (location or "").lower()

    configured_locations = [
        location.lower()
        for location in LOCATIONS
    ]

    if not any(
        location in profile_location
        for location in configured_locations
    ):
        return False

    excluded_hints = [
        hint.lower()
        for hint in NOT_LOCATION_HINTS
    ]

    return not any(
        hint in profile_location
        for hint in excluded_hints
    )


def has_full_name(name):
    """Return True when the profile has at least two name-like words."""
    words = [
        word
        for word in (name or "").replace(",", " ").split()
        if len(word) >= 2
    ]

    return len(words) >= 2


def evaluate(login, now):
    """
    Evaluate one GitHub profile.

    Returns:
        (passed, row)

    If the profile fails the filters, returns:
        (False, None)

    If the profile passes the filters, returns:
        (True, row)
    """
    user = api(f"/users/{login}")

    if not user or user.get("type") != "User":
        return False, None

    if not has_full_name(user.get("name")):
        return False, None

    if not is_location_match(user.get("location")):
        return False, None

    created_at = parse_dt(user["created_at"])

    minimum_account_date = now - timedelta(
        days=int(365.25 * MIN_ACCOUNT_AGE_YEARS)
    )

    if created_at > minimum_account_date:
        return False, None

    if user.get("public_repos", 0) < MIN_PUBLIC_REPOS:
        return False, None

    repositories = []

    for page in (1, 2):
        batch = api(
            f"/users/{login}/repos",
            {
                "per_page": 100,
                "sort": "pushed",
                "direction": "desc",
                "page": page,
            },
        )

        if not batch:
            break

        repositories.extend(batch)

        if len(batch) < 100:
            break

    epoch = datetime.min.replace(tzinfo=timezone.utc)

    def pushed(repository):
        pushed_at = repository.get("pushed_at")

        if not pushed_at:
            return epoch

        return parse_dt(pushed_at)

    own_repositories = sorted(
        (
            repository
            for repository in repositories
            if not repository.get("fork")
        ),
        key=pushed,
        reverse=True,
    )

    if not own_repositories:
        return False, None

    most_recent_push = pushed(own_repositories[0])

    if most_recent_push < now - timedelta(days=ACTIVE_WITHIN_DAYS):
        return False, None

    language_matches = [
        repository
        for repository in own_repositories
        if repository.get("language") == SEARCH_LANGUAGE
    ]

    if not language_matches:
        return False, None

    recent_language_repositories = [
        repository
        for repository in language_matches
        if pushed(repository)
        >= now - timedelta(days=LANGUAGE_WITHIN_DAYS)
    ]

    if not recent_language_repositories:
        return False, None

    row = {
        "login": login,
        "full_name": (user.get("name") or "").strip(),
        "github_url": user["html_url"],
        "location": user.get("location") or "",
        "company": user.get("company") or "",
        "blog": user.get("blog") or "",
        "followers": user.get("followers", 0),
        "public_repos": user.get("public_repos", 0),
        "created_at": user["created_at"][:10],
        "last_push": most_recent_push.date().isoformat(),
        "language_repos": "; ".join(
            repository["name"]
            for repository in recent_language_repositories[:3]
        ),
    }

    return True, row


# ---------------------------------------------------------------------------
# State and CSV files
# ---------------------------------------------------------------------------

def load_state():
    """Load processing state from state.json."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as file:
            return json.load(file)

    return {"checked": {}}


def save_state(state):
    """Save processing state to state.json."""
    with open(STATE_FILE, "w", encoding="utf-8") as file:
        json.dump(
            state,
            file,
            ensure_ascii=False,
            indent=1,
            sort_keys=True,
        )


def read_manual_columns():
    """
    Preserve manually entered CSV fields.

    This prevents fields such as contacted and notes from being erased when
    the automated workflow rewrites profiles.csv.
    """
    manual = {}

    if not os.path.exists(CSV_FILE):
        return manual

    with open(CSV_FILE, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            login = row.get("login")

            if not login:
                continue

            manual[login] = {
                column: row.get(column, "")
                for column in MANUAL_COLUMNS
            }

    return manual


def write_csv(state, manual):
    """
    Write passed profiles to profiles.csv.

    CSV_COLUMNS must match the fields generated by evaluate(), plus the
    tracking fields added here.
    """
    rows = []

    for login, record in state["checked"].items():
        if not record.get("passed"):
            continue

        row = dict(record["row"])

        row["date_added"] = record.get(
            "added",
            record["at"],
        )[:10]

        row["last_checked"] = record["at"][:10]

        for column in MANUAL_COLUMNS:
            row[column] = manual.get(login, {}).get(column, "")

        rows.append(row)

    rows.sort(
        key=lambda row: row.get("last_push", ""),
        reverse=True,
    )

    with open(
        CSV_FILE,
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=CSV_COLUMNS,
        )

        writer.writeheader()
        writer.writerows(rows)

    return len(rows)


# ---------------------------------------------------------------------------
# Main workflow
# ---------------------------------------------------------------------------

def main():
    """Run the search, process profiles, and save progress."""
    if not TOKEN:
        print(
            "GH_TOKEN is missing. "
            "Run this inside GitHub Actions."
        )
        sys.exit(1)

    now = datetime.now(timezone.utc)

    state = load_state()
    checked = state.setdefault("checked", {})
    manual = read_manual_columns()

    logins = find_candidates()

    print(f"Search found {len(logins)} profiles")

    stale_before = (
        now - timedelta(days=RECHECK_AFTER_DAYS)
    ).isoformat()

    new_profiles = sorted(
        login
        for login in logins
        if login not in checked
    )

    stale_profiles = sorted(
        (
            login
            for login in logins
            if login in checked
            and checked[login].get("at", "") < stale_before
        ),
        key=lambda login: checked[login].get("at", ""),
    )

    todo = new_profiles + stale_profiles

    print(
        "To check this run: "
        f"{len(new_profiles)} new and "
        f"{len(stale_profiles)} due for a recheck"
    )

    checked_count = 0
    passed_count = 0

    try:
        for login in todo:
            if (
                core_remaining is not None
                and core_remaining < MIN_CORE_REMAINING
            ):
                print(
                    "Hourly API limit nearly used. "
                    "Stopping; the next run will continue."
                )
                break

            try:
                passed, row = evaluate(login, now)

            except OutOfBudget:
                print(
                    "Hourly API limit reached. "
                    "Stopping; the next run will continue."
                )
                break

            except RuntimeError as error:
                print(f"Skipped {login}: {error}")
                continue

            old_record = checked.get(login, {})

            checked[login] = {
                "at": now.isoformat(),
                "passed": passed,
                "row": row,
            }

            if passed:
                checked[login]["added"] = old_record.get(
                    "added",
                    now.isoformat(),
                )
                passed_count += 1

            checked_count += 1

    finally:
        save_state(state)

        total_profiles = write_csv(
            state,
            manual,
        )

        not_yet_checked = len(
            [
                login
                for login in logins
                if login not in checked
            ]
        )

        print(
            f"Checked {checked_count} profiles, "
            f"{passed_count} passed, "
            f"{total_profiles} in profiles.csv, "
            f"{not_yet_checked} not yet checked"
        )

        summary_file = os.environ.get(
            "GITHUB_STEP_SUMMARY"
        )

        if summary_file:
            with open(
                summary_file,
                "a",
                encoding="utf-8",
            ) as file:
                file.write(
                    "### Radar result\n\n"
                    f"Profiles found by the search: "
                    f"{len(logins)}\n\n"
                    f"Checked in this run: "
                    f"{checked_count}\n\n"
                    f"Passed the filters in this run: "
                    f"{passed_count}\n\n"
                    f"Total profiles in profiles.csv: "
                    f"{total_profiles}\n\n"
                    f"Not yet checked: "
                    f"{not_yet_checked}\n"
                )


if __name__ == "__main__":
    main()
