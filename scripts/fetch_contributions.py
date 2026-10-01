"""Scrape the public GitHub contribution calendar (no token required)."""
import json
import os
import re
import sys
from datetime import date, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GH_USER", "YunTaeng")
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "contributions.json"
COUNT_RE = re.compile(r"^(\d+)\s+contribution")


def fetch_days(username):
    url = f"https://github.com/users/{username}/contributions"
    resp = requests.get(url, timeout=30, headers={"User-Agent": "profile-readme-bot"})
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    counts = {}
    for tip in soup.find_all("tool-tip"):
        match = COUNT_RE.match(tip.get_text(strip=True))
        counts[tip.get("for")] = int(match.group(1)) if match else 0

    days = []
    for cell in soup.select("td.ContributionCalendar-day"):
        if not cell.get("data-date"):
            continue
        days.append(
            {
                "date": cell["data-date"],
                "level": int(cell.get("data-level", 0)),
                "count": counts.get(cell.get("id"), 0),
            }
        )
    days.sort(key=lambda d: d["date"])
    if not days:
        raise RuntimeError("No contribution cells found - GitHub markup may have changed")
    return days


def compute_streaks(days):
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)

    today = date.today()
    by_date = {d["date"]: d["count"] for d in days}
    cursor = today if by_date.get(today.isoformat(), 0) > 0 else today - timedelta(days=1)
    current = 0
    while by_date.get(cursor.isoformat(), 0) > 0:
        current += 1
        cursor -= timedelta(days=1)
    return current, longest


def main():
    days = fetch_days(USERNAME)
    current, longest = compute_streaks(days)
    data = {
        "username": USERNAME,
        "total": sum(d["count"] for d in days),
        "current_streak": current,
        "longest_streak": longest,
        "days": days,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"{USERNAME}: {data['total']} contributions, {len(days)} days -> {OUT_PATH}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
