import httpx
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/fpl", tags=["fpl"])

FPL_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"

@router.get("/bootstrap")
async def get_bootstrap():
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(FPL_URL, headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json"
            })
            r.raise_for_status()
            return r.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"FPL API error: {str(e)}")