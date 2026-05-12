"""
routers/players.py
Player endpoints — FBref stats + Fantrax scoring engine + xG + FDR.
Powers draft board, waiver wire, and player analysis.
"""

from fastapi import APIRouter, Query
from typing import Optional
from services import fbref, understat
from services.scoring_engine import score_all_players, get_scoring_breakdown
from services.fixture_manager import get_next5_fdr_from_storage

router = APIRouter()


async def _get_enriched_players(position=None, min_games=3, season=None):
    """Fetch, score, and enrich all players — shared by multiple endpoints."""
    players = await fbref.get_all_player_stats()

    if position:
        players = [p for p in players if p.get("position", "").upper() == position.upper()]

    players = [p for p in players if (p.get("games") or 0) >= min_games]
    players = score_all_players(players)

    # Merge xG from Understat
    try:
        xg_data   = await understat.get_league_players_xg(season=season or "2024")
        xg_lookup = {p["name"].lower(): p for p in xg_data}
        for p in players:
            xg = xg_lookup.get(p["name"].lower(), {})
            p["xg_per90"]   = xg.get("xg_per90",   p.get("xg_per90",   0))
            p["xa_per90"]   = xg.get("xa_per90",   p.get("xa_per90",   0))
            p["g_minus_xg"] = xg.get("g_minus_xg", p.get("g_minus_xg", 0))
    except Exception:
        pass

    # Merge FDR
    try:
        fdr_data   = get_next5_fdr_from_storage()
        fdr_lookup = {t["team"].lower(): t["avg_fdr"] for t in fdr_data}
        for p in players:
            p["fdr_avg5"] = fdr_lookup.get(p.get("team", "").lower(), 3.0)
    except Exception:
        for p in players:
            p.setdefault("fdr_avg5", 3.0)

    return players


@router.get("/")
async def all_players(
    position:  Optional[str] = None,
    sort_by:   str = "fantrax_score_per90",
    min_games: int = 3,
    season:    Optional[str] = None,
):
    """All players ranked by Fantrax score per 90."""
    players = await _get_enriched_players(position, min_games, season)

    sort_options = {
        "fantrax_score_per90": lambda p: -(p.get("fantrax_score_per90") or 0),
        "xg_per90":   lambda p: -(p.get("xg_per90") or 0),
        "xa_per90":   lambda p: -(p.get("xa_per90") or 0),
        "goals":      lambda p: -(p.get("goals") or 0),
        "fdr":        lambda p:  (p.get("fdr_avg5") or 3),
        "g_minus_xg": lambda p: -(p.get("g_minus_xg") or 0),
    }
    players.sort(key=sort_options.get(sort_by, sort_options["fantrax_score_per90"]))
    return players


@router.get("/draft-board")
async def draft_board(
    draft_position: int   = Query(1, ge=1, le=20, description="Your draft pick position"),
    league_size:    int   = Query(12, ge=6, le=20, description="Number of teams in league"),
    position:       Optional[str] = None,
    min_games:      int   = 3,
    season:         Optional[str] = None,
):
    """
    Draft board ranked by Fantrax points per game.
    Highlights your picks in snake draft order.
    Returns players with overall_pick, round, and is_your_pick fields.
    """
    players = await _get_enriched_players(position, min_games, season)
    players.sort(key=lambda p: -(p.get("fantrax_score_per90") or 0))

    # Calculate your snake draft picks
    your_picks = set()
    for rnd in range(20):
        if rnd % 2 == 0:
            pick = rnd * league_size + draft_position
        else:
            pick = rnd * league_size + (league_size + 1 - draft_position)
        your_picks.add(pick)

    for i, p in enumerate(players):
        pick_num = i + 1
        p["overall_pick"] = pick_num
        p["round"]        = ((pick_num - 1) // league_size) + 1
        p["is_your_pick"] = pick_num in your_picks

    return {
        "draft_position": draft_position,
        "league_size":    league_size,
        "total_players":  len(players),
        "your_picks":     sorted(your_picks),
        "players":        players,
    }


@router.get("/waiver-wire")
async def waiver_wire(
    position:  Optional[str] = None,
    sort_by:   str = "fantrax_score_per90",
    min_games: int = 3,
    season:    Optional[str] = None,
):
    """Waiver wire players ranked by Fantrax score per 90."""
    return await all_players(
        position=position,
        sort_by=sort_by,
        min_games=min_games,
        season=season,
    )


@router.get("/top")
async def top_players(
    n:        int = Query(20, ge=5, le=100),
    position: Optional[str] = None,
    season:   Optional[str] = None,
):
    """Top N players by Fantrax score per 90."""
    players = await _get_enriched_players(position, min_games=3, season=season)
    return players[:n]


@router.get("/{player_name}/breakdown")
async def player_breakdown(player_name: str):
    """
    Itemised scoring breakdown for a player.
    Shows exactly how each stat contributes to their Fantrax score.
    """
    players = await fbref.get_all_player_stats()

    match = next(
        (p for p in players if p["name"].lower() == player_name.lower()), None
    ) or next(
        (p for p in players if player_name.lower() in p["name"].lower()), None
    )

    if not match:
        return {"error": f"Player '{player_name}' not found"}

    breakdown = get_scoring_breakdown(match)
    return {
        "player":   match["name"],
        "team":     match.get("team"),
        "position": match.get("position"),
        "minutes":  match.get("minutes"),
        "games":    match.get("games"),
        **breakdown,
    }


@router.get("/{player_id}/shots")
async def player_shots(player_id: str, season: str = "2024"):
    """Shot-level xG data for a player from Understat."""
    return await understat.get_player_shots(player_id, season)


@router.post("/refresh")
async def refresh_stats():
    """Force refresh of FBref player stats cache."""
    fbref.clear_cache()
    return {"status": "cache cleared — next request fetches fresh data"}
