"""
services/understat.py
Fetches xG, xA, and shot data from Understat.
No API key required — data is embedded in the page HTML.
"""

import json
import logging
import re
import httpx

logger = logging.getLogger(__name__)
UNDERSTAT_BASE = "https://understat.com"


async def _get_page_var(url: str, var_name: str):
    async with httpx.AsyncClient(
        timeout=20.0,
        headers={"User-Agent": "Mozilla/5.0"}
    ) as client:
        resp = await client.get(url)
        resp.raise_for_status()

    pattern = rf"var\s+{var_name}\s*=\s*JSON\.parse\('(.+?)'\)"
    match = re.search(pattern, resp.text)
    if not match:
        raise ValueError(f"Could not find {var_name} on {url}")

    raw = match.group(1).encode("utf-8").decode("unicode_escape")
    return json.loads(raw)


async def get_league_players_xg(league: str = "EPL", season: str = "2024") -> list:
    try:
        data = await _get_page_var(
            f"{UNDERSTAT_BASE}/league/{league}/{season}",
            "playersData"
        )
        return [
            {
                "name":       p.get("player_name", ""),
                "team":       p.get("team_title", ""),
                "position":   p.get("position", ""),
                "games":      int(p.get("games", 0)),
                "goals":      int(p.get("goals", 0)),
                "xg":         float(p.get("xG", 0)),
                "assists":    int(p.get("assists", 0)),
                "xa":         float(p.get("xA", 0)),
                "xg_per90":   _per90(float(p.get("xG", 0)), int(p.get("time", 0))),
                "xa_per90":   _per90(float(p.get("xA", 0)), int(p.get("time", 0))),
                "g_minus_xg": int(p.get("goals", 0)) - float(p.get("xG", 0)),
                "npxg":       float(p.get("npxG", 0)),
                "minutes":    int(p.get("time", 0)),
            }
            for p in data
        ]
    except Exception as e:
        logger.error(f"Understat fetch failed: {e}")
        return []


async def get_player_shots(player_id: str, season: str = "2024") -> list:
    try:
        data = await _get_page_var(
            f"{UNDERSTAT_BASE}/player/{player_id}",
            "shotsData"
        )
        return [
            {
                "date":     s.get("date", ""),
                "result":   s.get("result", ""),
                "xg":       float(s.get("xG", 0)),
                "situation":s.get("situation", ""),
                "match_id": s.get("match_id", ""),
            }
            for s in data
        ]
    except Exception as e:
        logger.error(f"Understat shots fetch failed: {e}")
        return []


def _per90(stat: float, minutes: int) -> float:
    if minutes < 1:
        return 0.0
    return round(stat / minutes * 90, 3)
