from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import anthropic
import os

router = APIRouter()
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

class PlayerAnalysisRequest(BaseModel):
    player_name: str
    team: str
    position: str
    price: float
    total_points: int
    form: float
    xg: float
    xa: float
    minutes: int
    ownership_pct: float
    transfers_in: int
    transfers_out: int
    next_fixtures: list[str]
    captain_pick: bool = False

class TransferRequest(BaseModel):
    player_out: PlayerAnalysisRequest
    player_in: PlayerAnalysisRequest
    budget_remaining: float
    gameweek: int

@router.post("/explain")
async def explain_player(req: PlayerAnalysisRequest):
    try:
        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=100,
            messages=[{"role": "user", "content": "Say hello"}]
        )
        return {"analysis": message.content[0].text}
    except Exception as e:
        import logging
        logging.error(f"Anthropic error: {repr(e)}")
        raise HTTPException(status_code=500, detail=repr(e))

@router.post("/transfer")
async def explain_transfer(req: TransferRequest):
    prompt = f"""You are an elite FPL analyst. Assess this transfer decision for GW{req.gameweek}.

OUT: {req.player_out.player_name} ({req.player_out.team}) - £{req.player_out.price}m
Form: {req.player_out.form} | xG: {req.player_out.xg} | Fixtures: {", ".join(req.player_out.next_fixtures)}

IN: {req.player_in.player_name} ({req.player_in.team}) - £{req.player_in.price}m
Form: {req.player_in.form} | xG: {req.player_in.xg} | Fixtures: {", ".join(req.player_in.next_fixtures)}

Budget remaining after transfer: £{req.budget_remaining}m

Give a TRANSFER RATING out of 10 and explain in 3-4 punchy bullet points why this is or is not worth burning a transfer on. Flag if it is a panic sell or genuinely smart move."""
    try:
        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}]
        )
        return {"analysis": message.content[0].text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))