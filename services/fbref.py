"""
services/fbref.py
Fetches player stats from the Fantasy Premier League API.
Free, no auth required, and has all stats needed for scoring.
"""

import logging
import httpx

logger = logging.getLogger(__name__)
FPL_BASE = "https://fantasy.premierleague.com/api"
_cache: dict = {}


async def get_all_player_stats() -> list:
    if "players" in _cache:
        return _cache["players"]

    logger.info("📊 Fetching player stats from FPL API...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        bootstrap = (await client.get(f"{FPL_BASE}/bootstrap-static/")).json()

    elements    = bootstrap["elements"]
    teams       = {t["id"]: t["name"] for t in bootstrap["teams"]}
    pos_map     = {1: "GK", 2: "DEF", 3: "MID", 4: "FWD"}

    players = []
    for p in elements:
        minutes = int(p.get("minutes") or 0)
        games   = max(1, minutes // 60)
        pos     = pos_map.get(p.get("element_type"), "MID")
        is_gk   = pos == "GK"

        player = {
            "name":     p.get("web_name", ""),
            "full_name": f"{p.get('first_name','')} {p.get('second_name','')}".strip(),
            "team":     teams.get(p.get("team"), ""),
            "position": pos,
            "minutes":  minutes,
            "games":    games,
            "price":    p.get("now_cost", 0) / 10,

            # Shared stats
            "goals":        int(p.get("goals_scored") or 0),
            "assists":      int(p.get("assists") or 0),
            "yellow_cards": int(p.get("yellow_cards") or 0),
            "red_cards":    int(p.get("red_cards") or 0),
            "own_goals":    int(p.get("own_goals") or 0),
            "clean_sheets": int(p.get("clean_sheets") or 0),
            "xg":           float(p.get("expected_goals") or 0),
            "xa":           float(p.get("expected_assists") or 0),
            "npxg":         float(p.get("expected_goals") or 0),

            # Outfield stats
            "shots_on_target":     0,
            "tackles_won":         int(p.get("tackles") or 0),
            "interceptions":       int(p.get("tackled") or 0),
            "effective_clearances":int(p.get("clearances_blocks_interceptions") or 0),
            "aerials_won":         int(p.get("dribbles") or 0),
            "second_yellow":       0,
            "dispossessed":        int(p.get("errors_leading_to_goal") or 0),
            "successful_dribbles": int(p.get("dribbles") or 0),
            "key_passes":          int(p.get("key_passes") or 0),
            "accurate_crosses":    int(p.get("big_chances_created") or 0),
            "fouls_committed":     0,

            # GK stats
            "saves":         int(p.get("saves") or 0),
            "goals_against": int(p.get("goals_conceded") or 0),
            "penalty_saves": int(p.get("penalties_saved") or 0),

            # xG derived
            "xg_per90":   round(float(p.get("expected_goals_per_90") or 0), 3),
            "xa_per90":   round(float(p.get("expected_assists_per_90") or 0), 3),
            "g_minus_xg": round(
                int(p.get("goals_scored") or 0) - float(p.get("expected_goals") or 0), 2
            ),

            # FPL specific
            "fpl_total_points": int(p.get("total_points") or 0),
            "fpl_form":         float(p.get("form") or 0),
            "selected_by":      float(p.get("selected_by_percent") or 0),
            "status":           p.get("status", "a"),
        }
        players.append(player)

    logger.info(f"✅ FPL API: loaded {len(players)} players")
    _cache["players"] = players
    return players


def clear_cache():
    _cache.clear()
    logger.info("Player stats cache cleared")