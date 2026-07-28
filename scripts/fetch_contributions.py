"""
fetch_contributions.py — pull your real contribution calendar with no
GraphQL API and no personal access token, by scraping the same public HTML
fragment GitHub's own profile page uses.

Usage:
    python scripts/fetch_contributions.py

Output:
    data/contributions.json
"""

import json
import os
import sys
from datetime import datetime

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GITHUB_PROFILE_USERNAME", "stadlxr")
URL = f"https://github.com/users/{USERNAME}/contributions"

HEADERS = {
    # a normal browser UA avoids being served a stripped-down response
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    )
}


def fetch_html(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return resp.text


def parse_days(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")

    # GitHub renders each day as a <td> (or <rect> in some layouts) carrying
    # data-date and data-level attributes. Cover both shapes defensively.
    cells = soup.select("td.ContributionCalendar-day, td[data-date]") or soup.select(
        "rect[data-date]"
    )

    days = []
    for cell in cells:
        date_str = cell.get("data-date")
        level_str = cell.get("data-level")
        if not date_str:
            continue

        # GitHub links each day cell to a separate <tool-tip for="cell-id">
        # element that holds the human-readable count text.
        cell_id = cell.get("id")
        text_source = cell.get("title") or ""
        if not text_source and cell_id:
            tooltip_el = soup.find("tool-tip", attrs={"for": cell_id})
            if tooltip_el:
                text_source = tooltip_el.get_text()

        count = 0
        for token in text_source.replace(",", "").split():
            if token.isdigit():
                count = int(token)
                break

        days.append(
            {
                "date": date_str,
                "count": count,
                "level": int(level_str) if level_str is not None else 0,
            }
        )

    days.sort(key=lambda d: d["date"])
    return days


def compute_stats(days: list[dict]) -> dict:
    if not days:
        return {}

    total = sum(d["count"] for d in days)

    # current streak: consecutive days with count > 0, ending at the last day
    current_streak = 0
    for d in reversed(days):
        if d["count"] > 0:
            current_streak += 1
        else:
            break

    # longest streak anywhere in the window
    longest_streak = 0
    running = 0
    for d in days:
        if d["count"] > 0:
            running += 1
            longest_streak = max(longest_streak, running)
        else:
            running = 0

    best_day = max(days, key=lambda d: d["count"])

    monthly_totals: dict[str, int] = {}
    for d in days:
        month_key = d["date"][:7]  # YYYY-MM
        monthly_totals[month_key] = monthly_totals.get(month_key, 0) + d["count"]

    return {
        "total_contributions": total,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "best_day": best_day,
        "monthly_totals": monthly_totals,
    }


def main():
    print(f"Fetching {URL} ...")
    try:
        html = fetch_html(URL)
    except requests.RequestException as e:
        print(f"Failed to fetch contributions: {e}", file=sys.stderr)
        sys.exit(1)

    days = parse_days(html)
    if not days:
        print(
            "No contribution cells found — GitHub may have changed its markup, "
            "or the username has no public activity.",
            file=sys.stderr,
        )
        sys.exit(1)

    stats = compute_stats(days)

    output = {
        "username": USERNAME,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "days": days,
        "stats": stats,
    }

    os.makedirs("data", exist_ok=True)
    with open("data/contributions.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"Wrote data/contributions.json ({len(days)} days, {stats['total_contributions']} total)")


if __name__ == "__main__":
    main()
