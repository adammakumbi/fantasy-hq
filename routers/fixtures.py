"""routers/fixtures.py"""
from fastapi import APIRouter
from typing import Optional
from services.fixture_manager import (
    fetch_and_store_fixtures, load_fixtures,
    get_next5_fdr_from_storage, get_current_gameweek_from_storage,
    get_matchdays_this_week, get_available_seasons,
)

router = APIRouter()


@router.get("/")
async def fixtures(gameweek: Optional[int] = None, season: Optional[str] = None):
    """All fixtures, optionally filtered by gameweek."""
    stored = load_fixtures(season)
    if stored:
        return [f for f in stored if f["gameweek"] == gameweek] if gameweek else stored
    return []


@router.get("/fdr")
async def fdr(teams: Optional[str] = None, season: Optional[str] = None):
    """Next 5 fixture difficulty per team."""
    team_list = [t.strip() for t in teams.split(",")] if teams else None
    return get_next5_fdr_from_storage(team_list, season)


@router.get("/current-gameweek")
async def current_gameweek(season: Optional[str] = None):
    return get_current_gameweek_from_storage(season)


@router.get("/matchdays-this-week")
async def matchdays_this_week(season: Optional[str] = None):
    return get_matchdays_this_week(season)


@router.get("/seasons")
async def seasons():
    """All seasons with stored fixture data."""
    return {"seasons": get_available_seasons()}


@router.post("/fetch")
async def fetch_fixtures(season: Optional[str] = None):
    """
    Fetch and store fixtures from FPL API.
    Run now for 2025-26.
    Run again next summer for 2026-27 when fixtures are announced.
    Example: POST /api/fixtures/fetch?season=2026-27
    """
    return await fetch_and_store_fixtures(season)


@router.delete("/seasons/{season}")
async def delete_season(season: str):
    import os
    path = f"fixtures_data/{season.replace('/', '-')}.json"
    if os.path.exists(path):
        os.remove(path)
        return {"deleted": season}
    return {"error": f"Season {season} not found"}
