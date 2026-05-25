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
    prompt = f"""
You are an elite FPL analyst. Analyse this player and give a clear, punchy recommendation.

Player: {req.player_name} ({req.team}, {req.position}) — £{req.price}m
Season: {req.total_points} pts | xG: {req.xg} | xA: {req.xa} | Mins: {req.minutes}
Form (last 5 GW avg): {req.form}
Ownership: {req.ownership_pct}%
Next 3 fixtures: {", ".join(req.next_fixtures)}
GW transfers: +{req.transfers_in:,} in / -{req.transfers_out:,} out
Captain consideration: {"Yes" if req.captain_pick else "No"}

Respond in this exact structure:

VERDICT: [BUY / HOLD / SELL / CAPTAIN] — one line summary

FORM & OUTPUT:
- 2-3 bullet points on recent performance and underlying numbers

FIXTURES:
- 1-2 bullet points on upcoming fixture difficulty

OWNERSHIP ANGLE:
- One sentence on whether his ownership makes him a differential or template pick

RISK:
- One sentence on the main downside

Keep it sharp. No fluff. Analyst tone, not hype.
"""
    try:
        message = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}]
        )
        return {"analysis": message.content[0].text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/transfer")
async def explain_transfer(req: TransferRequest):
    prompt = f"""
You are an elite FPL analyst. Assess this transfer decision for GW{req.gameweek}.

OUT: {req.player_out.player_name} ({req.player_out.team}) — £{req.player_out.price}m
Form: {req.player_out.form} | xG: {req.player_out.xg} | Fixtures: {", ".join(req.player_out.next_fixtures)}

IN: {req.player_in.player_name} ({req.player_in.team}) — £{req.player_in.price}m
Form: {req.player_in.form} | xG: {req.player_in.xg} | Fixtures: {", ".join(req.player_in.next_fixtures)}

Budget remaining after transfer: £{req.budget_remaining}m

Give a TRANSFER RATING out of 10 and explain in 3-4 punchy bullet points why this is or isn't worth burning a transfer on. Flag if it's a panic sell or genuinely smart move.
"""
    try:
        message = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}]
        )
        return {"analysis": message.content[0].text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))