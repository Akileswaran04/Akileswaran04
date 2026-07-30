#!/usr/bin/env python3
"""
Fetch real daily contribution counts from GitHub's official GraphQL API and
write data/contributions.json with the raw days plus derived stats
(current streak, longest streak, best day, monthly totals).

Primary data source: GitHub GraphQL API v4 (requires GH_PAT token env var).
Fallback:           HTML scraping of the public contributions endpoint
                    (unauthenticated, less reliable).

Set GH_PAT to a classic personal access token with read:user scope for
accurate, stable data. Without it, the script falls back to HTML scraping
which may produce incomplete or approximate results.

Run daily by .github/workflows/snake.yml.
"""
import datetime
import json
import os
import re
import sys

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

USERNAME = os.environ.get("GH_PROFILE_USER", "YOUR_GITHUB_USERNAME")
GH_PAT = os.environ.get("GH_PAT", "")
GRAPHQL_URL = "https://api.github.com/graphql"
HTML_URL = f"https://github.com/users/{USERNAME}/contributions"
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "contributions.json")

START_YEAR = 2020  # earliest year to check for contributions

USE_GRAPHQL = bool(GH_PAT)


# ── GraphQL query helpers ─────────────────────────────────────────────

CONTRIBUTIONS_QUERY = """
query($username: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $username) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""


def _make_session():
    """Create a requests session with retry logic for transient failures."""
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.headers.update({"User-Agent": "profile-readme-bot/1.0"})
    return session


# ── GraphQL fetch ─────────────────────────────────────────────────────

def fetch_year_range_graphql(from_date, to_date, session=None):
    """Fetch contributions via GitHub GraphQL API for a date range.

    Returns list of {"date": ..., "count": ...} dicts.
    """
    if session is None:
        session = _make_session()
    session.headers.update({"Authorization": f"Bearer {GH_PAT}"})

    variables = {
        "username": USERNAME,
        "from": f"{from_date}T00:00:00Z",
        "to": f"{to_date}T23:59:59Z",
    }
    payload = {"query": CONTRIBUTIONS_QUERY, "variables": variables}

    resp = session.post(GRAPHQL_URL, json=payload, timeout=30)
    resp.raise_for_status()
    body = resp.json()

    if "errors" in body:
        err_msg = body["errors"][0].get("message", str(body["errors"]))
        raise RuntimeError(f"GraphQL API error: {err_msg}")

    try:
        weeks = body["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    except (KeyError, TypeError) as exc:
        raise RuntimeError(f"Unexpected GraphQL response structure: {exc}") from exc

    days = []
    for week in weeks:
        for day in week.get("contributionDays", []):
            date = day.get("date")
            count = day.get("contributionCount", 0)
            if date:
                days.append({"date": date, "count": count})

    days.sort(key=lambda d: d["date"])
    return days


# ── HTML fallback fetch (unchanged scraping logic) ────────────────────

def _parse_count(td, soup):
    """Extract contribution count from a calendar cell.

    Checks multiple data sources in order of reliability:
    1. aria-label on the <td> itself (most stable)
    2. <tool-tip> element referenced by the cell's id
    3. data-level attribute (gives a range estimate)
    4. Falls back to 0
    """
    label = td.get("aria-label", "")
    if label:
        m = re.search(r"(\d+)\s+contribution", label, re.I)
        if m:
            return int(m.group(1))
        if re.search(r"no contributions?", label, re.I):
            return 0
        return 0

    td_id = td.get("id")
    tooltip_el = soup.find("tool-tip", attrs={"for": td_id}) if td_id else None
    text = tooltip_el.get_text(strip=True) if tooltip_el else ""

    if re.search(r"no contributions?", text, re.I):
        return 0

    m = re.search(r"(\d+)\s+contribution", text, re.I)
    if m:
        return int(m.group(1))

    level = td.get("data-level")
    if level is not None:
        try:
            level = int(level)
            if level == 0:
                return 0
            estimates = {1: 3, 2: 8, 3: 15, 4: 25}
            return estimates.get(level, 1)
        except (ValueError, TypeError):
            pass

    return 0


def fetch_year_range_html(from_date, to_date, session=None):
    """Fetch contributions via HTML scraping (fallback method)."""
    if session is None:
        session = _make_session()
    url = f"{HTML_URL}?from={from_date}&to={to_date}"
    resp = session.get(url, timeout=30)
    resp.raise_for_status()

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(resp.text, "html.parser")

    cells = soup.select("td.ContributionCalendar-day")
    if not cells:
        cells = soup.select("td[data-date]")
    if not cells:
        cells = soup.select("[data-date]")
    if not cells:
        return []

    days = []
    for td in cells:
        date = td.get("data-date")
        if not date:
            continue
        count = _parse_count(td, soup)
        days.append({"date": date, "count": count})

    days.sort(key=lambda d: d["date"])
    return days


# ── Fetch orchestrator ────────────────────────────────────────────────

def fetch_year_range(from_date, to_date, session=None):
    """Fetch contributions for a specific date range.

    Uses GraphQL API if GH_PAT is set, otherwise falls back to HTML scraping.
    """
    if USE_GRAPHQL:
        return fetch_year_range_graphql(from_date, to_date, session)
    else:
        print("  ⚠️  WARNING: GH_PAT not set — falling back to HTML scraping. Data may be INACCURATE (missing days, estimated counts).", file=sys.stderr)
        return fetch_year_range_html(from_date, to_date, session)


def fetch_all_days():
    """Fetch ALL contributions by iterating year by year from START_YEAR."""
    if USERNAME == "YOUR_GITHUB_USERNAME":
        raise ValueError(
            "GH_PROFILE_USER environment variable not set. "
            "Set it to your GitHub username before running this script."
        )

    if USE_GRAPHQL:
        print(f"fetching ALL contributions for {USERNAME} via GraphQL API...")
    else:
        print(f"fetching ALL contributions for {USERNAME} via HTML scraping (no GH_PAT set)...")
        print("  ℹ️  Set GH_PAT env var (classic PAT with read:user scope) for accurate GraphQL data.", file=sys.stderr)

    now = datetime.datetime.now(datetime.timezone.utc)
    today_str = now.strftime("%Y-%m-%d")
    current_year = now.year
    session = _make_session()
    all_days = []

    for year in range(START_YEAR, current_year + 1):
        if year == current_year:
            from_date = f"{year}-01-01"
            to_date = today_str
        else:
            from_date = f"{year}-01-01"
            to_date = f"{year}-12-31"

        days = fetch_year_range(from_date, to_date, session=session)
        if not days:
            print(f"  {year}: no calendar data returned", file=sys.stderr)
            continue

        total = sum(d["count"] for d in days)
        print(f"  {year}: {total} contributions over {len(days)} days "
              f"({days[0]['date']} to {days[-1]['date']})")
        all_days.extend(days)

    if not all_days:
        print("NO contribution data returned from any source", file=sys.stderr)
        sys.exit(1)

    # Deduplicate by date (keep the last occurrence)
    all_days = sorted(
        {d["date"]: d for d in all_days}.values(),
        key=lambda x: x["date"]
    )

    # Filter out future dates
    all_days = [d for d in all_days if d["date"] <= today_str]

    # Sanity check: warn if a year has significantly fewer days than expected
    for year in set(d["date"][:4] for d in all_days):
        year_days = [d for d in all_days if d["date"].startswith(year)]
        expected = 366 if int(year) % 4 == 0 and (int(year) % 100 != 0 or int(year) % 400 == 0) else 365
        now_doy = int(now.strftime("%j"))
        if int(year) == current_year:
            expected = now_doy
        if len(year_days) < expected * 0.85:
            print(f"  [warning] {year}: only {len(year_days)} days (expected ~{expected}) "
                  f"— data may be incomplete", file=sys.stderr)

    return all_days


# ── Streak & stats computation (unchanged) ────────────────────────────

def compute_current_streak(days):
    """Compute the current (ongoing) contribution streak.

    Skips today's entry if it has 0 contributions and today hasn't finished
    yet in UTC, to avoid breaking the streak prematurely.
    """
    if not days:
        return 0, None, None

    today_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    idx = len(days) - 1

    if idx >= 0 and days[idx]["date"] == today_str and days[idx]["count"] == 0:
        idx -= 1

    if idx < 0:
        return 0, None, None

    streak = 0
    end_idx = idx

    while idx >= 0 and days[idx]["count"] > 0:
        streak += 1
        idx -= 1

    if streak == 0:
        return 0, None, None

    start_idx = idx + 1
    return streak, days[start_idx]["date"], days[end_idx]["date"]


def compute_longest_streak(days):
    """Compute the longest contribution streak ever recorded."""
    longest = run = 0
    longest_start = longest_end = None
    run_start_idx = None
    for i, d in enumerate(days):
        if d["count"] > 0:
            if run == 0:
                run_start_idx = i
            run += 1
            if run > longest:
                longest = run
                longest_start = days[run_start_idx]["date"]
                longest_end = days[i]["date"]
        else:
            run = 0
    return longest, longest_start, longest_end


def build_data(days):
    """Assemble the full data structure from a list of day dicts."""
    total = sum(d["count"] for d in days)
    active_days = sum(1 for d in days if d["count"] > 0)
    best = max(days, key=lambda d: d["count"])
    cur_len, cur_start, cur_end = compute_current_streak(days)
    long_len, long_start, long_end = compute_longest_streak(days)

    monthly = {}
    for d in days:
        key = d["date"][:7]
        monthly[key] = monthly.get(key, 0) + d["count"]
    monthly_list = [{"month": k, "total": v} for k, v in sorted(monthly.items())]

    return {
        "username": USERNAME,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "graphql" if USE_GRAPHQL else "html_scrape",
        "range": {"start": days[0]["date"], "end": days[-1]["date"]},
        "total_contributions": total,
        "active_days": active_days,
        "avg_per_active_day": round(total / active_days, 1) if active_days else 0,
        "current_streak": {"length": cur_len, "start": cur_start, "end": cur_end},
        "longest_streak": {"length": long_len, "start": long_start, "end": long_end},
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly": monthly_list,
        "days": days,
    }


if __name__ == "__main__":
    print(f"fetching ALL contributions for {USERNAME} from {START_YEAR} to present...")
    days = fetch_all_days()
    data = build_data(days)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(data, f, indent=2)
    rng = data["range"]
    source_label = "GraphQL API" if USE_GRAPHQL else "HTML scrape"
    print(f"wrote {OUT_PATH}: {data['total_contributions']} contributions, "
          f"{rng['start']} to {rng['end']}, "
          f"current streak {data['current_streak']['length']}, "
          f"longest streak {data['longest_streak']['length']} "
          f"[source: {source_label}]")
