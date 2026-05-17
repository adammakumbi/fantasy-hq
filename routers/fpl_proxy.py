"""
FPL Proxy — forwards requests to the FPL API from the server side,
bypassing CORS restrictions that block direct browser requests.
"""

import httpx
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/fpl", tags=["FPL Proxy"])

FPL_BASE = "https://fantasy.premierleague.com/api"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}


@router.get("/bootstrap")
async def get_bootstrap():
    """Proxy the FPL bootstrap-static endpoint (players, teams, gameweeks)."""
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.get(f"{FPL_BASE}/bootstrap-static/", headers=HEADERS)
            r.raise_for_status()
            return r.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="FPL API timed out")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"FPL API error: {str(e)}")