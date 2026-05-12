"""
services/fixture_manager.py
Stores and manages fixtures locally across seasons.
Run POST /api/fixtures/fetch now for 2025-26.
Run it again next summer for 2026-27 when announced.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import httpx

logger   = logging.getLogger(__name__)
TIMEZONE = ZoneInfo(os.getenv("TIMEZONE", "Europe/London"))
FPL_BASE = "https://fantasy.premierleague.com/api"
FIXTURES_DIR   = os.path.join(os.path.dirname(__file__), "..", "fixtures_data")
CURRENT_SEASON = os.getenv("CURRENT_SEASON", "2025-26")

os.makedirs(FIXTURES_DIR, exist_ok=True)


def _path(season: str) -> str:
    return os.path.join(FIXTURES_DIR, f"{season.replace('/', '-')}.json")


def get_available_seasons() -> list:
    seasons = []
    for f in os.listdir(FIXTURES_DIR):
        if f.endswith(".json"):
            seasons.append(f.replace(".json", "").replace("-", "/", 1))
    return sorted(seasons)


async def fetch_and_store_fixtures(season: str = None) -> dict:
    """Fetch from FPL API and store locally."""
    target = season or CURRENT_SEASON
    logger.info(f"Fetching fixtures for {target} from FPL API...")

    async with httpx.AsyncClient(timeout=20.0) as client:
        bootstrap    = (await client.get(f"{FPL_BASE}/bootstrap-static/")).json()
        fixtures_raw = (await client.get(f"{FPL_BASE}/fixtures/")).json()

    teams  = {t["id"]: t for t in bootstrap["teams"]}
    events = {e["id"]: e for e in bootstrap["events"]}

    fixtures = []
    for f in fixtures_raw:
        if not f.get("event"):
            continue
        home  = teams.get(f["team_h"], {})
        away  = teams.get(f["team_a"], {})
        event = events.get(f["event"], {})
        fixtures.append({
            "id":         f["id"],
            "gameweek":   f["event"],
            "gw_name":    event.get("name", f"GW{f['event']}"),
            "deadline":   event.get("deadline_time"),
            "kickoff":    f.get("kickoff_time"),
            "finished":   f.get("finished", False),
            "home_team":  home.get("name", ""),
            "home_short": home.get("short_name", ""),
            "away_team":  away.get("name", ""),
            "away_short": away.get("short_name", ""),
            "home_fdr":   f.get("team_h_difficulty", 3),
            "away_fdr":   f.get("team_a_difficulty", 3),
            "home_score": f.get("team_h_score"),
            "away_score": f.get("team_a_score"),
        })

    data = {
        "season":     target,
        "updated_at": datetime.now(TIMEZONE).isoformat(),
        "total":      len(fixtures),
        "fixtures":   fixtures,
    }
    with open(_path(target), "w") as f:
        json.dump(data, f, indent=2)

    logger.info(f"✅ Stored {len(fixtures)} fixtures for {target}")
    return {"season": target, "stored": len(fixtures), "updated_at": data["updated_at"]}


def load_fixtures(season: str = None) -> list:
    path = _path(season or CURRENT_SEASON)
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f).get("fixtures", [])


def get_current_gameweek_from_storage(season: str = None) -> dict:
    fixtures = load_fixtures(season)
    if not fixtures:
        return {}
    today = datetime.now(TIMEZONE)
    upcoming_gws = sorted(set(
        f["gameweek"] for f in fixtures
        if not f.get("finished") and f.get("kickoff") and
        datetime.fromisoformat(f["kickoff"].replace("Z", "+00:00")).astimezone(TIMEZONE) > today
    ))
    if not upcoming_gws:
        return {}
    gw  = upcoming_gws[0]
    gws = [f for f in fixtures if f["gameweek"] == gw]
    return {
        "gameweek": gw,
        "name":     f"Gameweek {gw}",
        "deadline": gws[0].get("deadline") if gws else None,
        "season":   season or CURRENT_SEASON,
    }


def get_next5_fdr_from_storage(team_names: list = None, season: str = None) -> list:
    fixtures = load_fixtures(season)
    if not fixtures:
        return []
    today = datetime.now(TIMEZONE)
    upcoming = [
        f for f in fixtures
        if not f.get("finished") and f.get("kickoff") and
        datetime.fromisoformat(f["kickoff"].replace("Z", "+00:00")).astimezone(TIMEZONE) > today
    ]
    all_teams = set()
    for f in upcoming:
        all_teams.add(f["home_team"])
        all_teams.add(f["away_team"])

    result = []
    for team in sorted(all_teams):
        if team_names and team not in team_names:
            continue
        team_fixtures = []
        for f in upcoming:
            if f["home_team"] == team:
                team_fixtures.append({
                    "gameweek": f["gameweek"],
                    "opponent": f["away_short"],
                    "is_home":  True,
                    "fdr":      f["home_fdr"],
                    "kickoff":  f["kickoff"],
                })
            elif f["away_team"] == team:
                team_fixtures.append({
                    "gameweek": f["gameweek"],
                    "opponent": f["home_short"],
                    "is_home":  False,
                    "fdr":      f["away_fdr"],
                    "kickoff":  f["kickoff"],
                })
        team_fixtures.sort(key=lambda x: x["gameweek"])
        next5 = team_fixtures[:5]
        if not next5:
            continue
        avg = round(sum(x["fdr"] for x in next5) / len(next5), 2)
        result.append({
            "team":     team,
            "fixtures": next5,
            "avg_fdr":  avg,
        })
    result.sort(key=lambda t: t["avg_fdr"])
    return result


def get_matchdays_this_week(season: str = None) -> list:
    """Fixtures in the next 7 days — used for match day alerts."""
    fixtures = load_fixtures(season)
    today     = datetime.now(TIMEZONE)
    week_end  = today + timedelta(days=7)
    result    = []
    for f in fixtures:
        if not f.get("kickoff"):
            continue
        ko = datetime.fromisoformat(f["kickoff"].replace("Z", "+00:00")).astimezone(TIMEZONE)
        if today <= ko <= week_end:
            result.append({**f, "kickoff_local": ko.strftime("%A %d %B %H:%M %Z")})
    return sorted(result, key=lambda x: x["kickoff"])
