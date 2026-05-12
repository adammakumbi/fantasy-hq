"""
services/scheduler.py
Alert scheduling — waiver deadline, free agency, match day.
Sends alerts to a Discord or Slack webhook.
"""

import logging
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger   = logging.getLogger(__name__)
TIMEZONE = ZoneInfo(os.getenv("TIMEZONE", "Europe/London"))
WEBHOOK  = os.getenv("ALERT_WEBHOOK_URL", "")
WAIVER_DAY      = os.getenv("WAIVER_DAY", "tuesday")
FREE_AGENCY_DAY = os.getenv("FREE_AGENCY_DAY", "wednesday")

_scheduler = AsyncIOScheduler(timezone=str(TIMEZONE))

DAYS_FULL = ["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
DAYS_ABBR = ["mon","tue","wed","thu","fri","sat","sun"]


def _abbr(day: str) -> str:
    return DAYS_ABBR[DAYS_FULL.index(day.lower())]


def _abbr_before(day: str) -> str:
    return DAYS_ABBR[(DAYS_FULL.index(day.lower()) - 1) % 7]


async def start_scheduler():
    _scheduler.add_job(
        alert_waiver_deadline,
        CronTrigger(day_of_week=_abbr_before(WAIVER_DAY), hour=9, minute=0),
        id="waiver_alert", replace_existing=True,
    )
    _scheduler.add_job(
        alert_free_agency,
        CronTrigger(day_of_week=_abbr(FREE_AGENCY_DAY), hour=8, minute=0),
        id="fa_alert", replace_existing=True,
    )
    _scheduler.add_job(
        alert_match_day,
        CronTrigger(hour=7, minute=0),
        id="matchday_alert", replace_existing=True,
    )
    _scheduler.start()
    logger.info("⏰ Alert scheduler started")


async def stop_scheduler():
    _scheduler.shutdown(wait=False)


async def alert_waiver_deadline():
    tomorrow = (datetime.now(TIMEZONE) + timedelta(days=1)).strftime("%A %d %B")
    await _send(
        title="⚠️ Waiver wire deadline tomorrow",
        body=f"Waivers process tomorrow ({tomorrow}). Submit your claims now.",
        colour=0xFFC107,
    )


async def alert_free_agency():
    await _send(
        title="🟢 Free agency is open",
        body="Free agents available now — no waiver priority needed.",
        colour=0x00C853,
    )


async def alert_match_day():
    from services.fixture_manager import get_matchdays_this_week
    try:
        today_fixtures = [
            f for f in get_matchdays_this_week()
            if datetime.fromisoformat(f["kickoff"].replace("Z", "+00:00"))
               .astimezone(TIMEZONE).date() == datetime.now(TIMEZONE).date()
        ]
        if not today_fixtures:
            return
        lines = [f"• {f['home_team']} vs {f['away_team']} — {f['kickoff_local']}"
                 for f in today_fixtures]
        await _send(
            title=f"⚽ {len(today_fixtures)} match{'es' if len(today_fixtures)>1 else ''} today",
            body="\n".join(lines),
            colour=0x1565C0,
        )
    except Exception as e:
        logger.error(f"Match day alert error: {e}")


async def _send(title: str, body: str, colour: int = 0x00C853):
    logger.info(f"📣 Alert: {title}")
    if not WEBHOOK:
        logger.warning("No ALERT_WEBHOOK_URL configured")
        return
    payload = {
        "embeds": [{
            "title":       title,
            "description": body,
            "color":       colour,
            "timestamp":   datetime.utcnow().isoformat(),
            "footer":      {"text": "Fantasy HQ"},
        }]
    }
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(WEBHOOK, json=payload, timeout=10.0)
            r.raise_for_status()
            logger.info("✅ Alert sent")
    except Exception as e:
        logger.error(f"Alert send failed: {e}")
