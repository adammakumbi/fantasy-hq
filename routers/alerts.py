"""routers/alerts.py"""
from fastapi import APIRouter
from pydantic import BaseModel
from services.scheduler import alert_waiver_deadline, alert_match_day, alert_free_agency

router = APIRouter()


class AlertPrefs(BaseModel):
    waiver_deadline: bool = True
    free_agency:     bool = True
    match_day:       bool = True
    value_alerts:    bool = False
    injury_alerts:   bool = True


_prefs = AlertPrefs()


@router.get("/preferences")
async def get_prefs():
    return _prefs


@router.put("/preferences")
async def update_prefs(prefs: AlertPrefs):
    global _prefs
    _prefs = prefs
    return {"status": "updated", "prefs": _prefs}


@router.post("/test/waiver")
async def test_waiver():
    await alert_waiver_deadline()
    return {"sent": True}


@router.post("/test/matchday")
async def test_matchday():
    await alert_match_day()
    return {"sent": True}


@router.post("/test/freeagency")
async def test_freeagency():
    await alert_free_agency()
    return {"sent": True}
