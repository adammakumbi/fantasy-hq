"""routers/waiver.py — proxies to players waiver-wire endpoint"""
from fastapi import APIRouter
from typing import Optional
from routers.players import waiver_wire as _waiver

router = APIRouter()


@router.get("/")
async def waiver(
    position:  Optional[str] = None,
    sort_by:   str = "fantrax_score_per90",
    min_games: int = 3,
    season:    Optional[str] = None,
):
    """Waiver wire — all available players ranked by Fantrax score per 90."""
    return await _waiver(position=position, sort_by=sort_by, min_games=min_games, season=season)
