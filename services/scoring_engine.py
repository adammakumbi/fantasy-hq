"""
services/scoring_engine.py
Applies the exact Fantrax scoring system for GK and outfield players.
All scores are calculated per 90 minutes played.

GK scoring:
  Aerials Won +1, Assists +8, Clean Sheets +8, Effective Clearances +0.25
  Goals Against -2, Goals +10, Interceptions +1, Key Passes +6
  Penalty Saves +8, Red Cards -7, Saves +2, Second Yellow -4, Yellow Cards -3

OF scoring:
  Accurate Crosses +1, Aerials Won +0.5, Assists +6, Clean Sheets +6
  Dispossessed -0.5, Goals +9, Interceptions +1, Own Goals -9
  Red Cards -7, Shots on Target +2, Successful Dribbles +1, Key Passes +2
  Second Yellow -4, Tackles Won +1, Yellow Cards -3
"""

GK_SCORING = {
    "aerials_won":            1.00,
    "assists":                8.00,
    "clean_sheets":           8.00,
    "effective_clearances":   0.25,
    "goals_against":         -2.00,
    "goals":                 10.00,
    "interceptions":          1.00,
    "key_passes":             6.00,
    "penalty_saves":          8.00,
    "red_cards":             -7.00,
    "saves":                  2.00,
    "second_yellow":         -4.00,
    "yellow_cards":          -3.00,
}

OF_SCORING = {
    "accurate_crosses":       1.00,
    "aerials_won":            0.50,
    "assists":                6.00,
    "clean_sheets":           6.00,
    "dispossessed":          -0.50,
    "goals":                  9.00,
    "interceptions":          1.00,
    "own_goals":             -9.00,
    "red_cards":             -7.00,
    "shots_on_target":        2.00,
    "successful_dribbles":    1.00,
    "key_passes":             2.00,
    "second_yellow":         -4.00,
    "tackles_won":            1.00,
    "yellow_cards":          -3.00,
}


def calculate_score(stats: dict, is_gk: bool = False, minutes: float = 90) -> float:
    """Calculate fantasy points per 90 from a stats dict."""
    if minutes <= 0:
        return 0.0
    scale = 90 / minutes
    rules = GK_SCORING if is_gk else OF_SCORING
    score = sum(
        (stats.get(key) or 0) * points * scale
        for key, points in rules.items()
    )
    return round(score, 2)


def score_player(player: dict) -> float:
    """Auto-detect GK vs outfield and return per-90 score."""
    pos     = (player.get("position") or "").upper()
    minutes = float(player.get("minutes") or 90)
    is_gk   = pos in ("GK", "G", "GOALKEEPER")
    return calculate_score(player, is_gk=is_gk, minutes=minutes)


def score_all_players(players: list) -> list:
    """Add fantrax_score_per90 to each player and sort descending."""
    for p in players:
        p["fantrax_score_per90"] = score_player(p)
    players.sort(key=lambda p: p["fantrax_score_per90"], reverse=True)
    return players


def get_scoring_breakdown(player: dict) -> dict:
    """Itemised breakdown showing how each stat contributes to the score."""
    pos     = (player.get("position") or "").upper()
    minutes = float(player.get("minutes") or 90)
    is_gk   = pos in ("GK", "G", "GOALKEEPER")
    rules   = GK_SCORING if is_gk else OF_SCORING
    scale   = 90 / minutes if minutes > 0 else 1

    breakdown = {}
    total = 0.0
    for key, points in rules.items():
        val          = float(player.get(key) or 0)
        contribution = round(val * points * scale, 2)
        if contribution != 0:
            breakdown[key] = {
                "value":        round(val, 2),
                "points_each":  points,
                "contribution": contribution,
            }
        total += contribution

    return {
        "total_per90": round(total, 2),
        "breakdown":   breakdown,
        "is_gk":       is_gk,
    }
