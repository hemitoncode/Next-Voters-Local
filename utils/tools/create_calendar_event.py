"""Calendar event creation tool adapter for legislation discovery.

Thin adapter that calls the Google Calendar MCP server and wraps results
in LangGraph Commands for state updates. Gracefully skips the Google API
call if credentials are not configured, but always records the event in
agent state so it flows through to the pipeline and report.
"""

import logging
from datetime import datetime, timedelta
from typing import Annotated, Any

from langchain_core.tools import tool, InjectedToolCallId
from langgraph.prebuilt.tool_node import InjectedState
from langgraph.types import Command

from utils.mcp import registry as mcp
from utils.schemas import LegislativeEvent
from utils.tools._helpers import ok

logger = logging.getLogger(__name__)


def _default_end_time(start_date: str) -> str:
    """Return start_date + 1 hour as a fallback end time."""
    try:
        dt = datetime.fromisoformat(start_date)
        return (dt + timedelta(hours=1)).isoformat()
    except ValueError:
        return start_date


async def _event_exists(title: str, start_date: str, city: str) -> bool:
    """Return True if a matching event already exists in the calendar for this date.

    Queries the calendar for the same day as start_date and checks for a title
    match against the city-prefixed summary used when creating events.
    """
    try:
        date_part = start_date[:10]  # "YYYY-MM-DD"
        result = await mcp.call("google_calendar", "list_events", {
            "time_min": f"{date_part}T00:00:00Z",
            "time_max": f"{date_part}T23:59:59Z",
            "max_results": 50,
        })
        target = f"[{city}] {title}".lower()
        return any(
            ev.get("summary", "").lower() == target
            for ev in result.get("items", [])
        )
    except Exception:
        return False  # if the check fails, proceed with creation


@tool
async def create_calendar_event(
    title: str,
    start_date: str,
    tool_call_id: Annotated[str, InjectedToolCallId],
    city: Annotated[str, InjectedState("city")],
    end_date: str | None = None,
    description: str | None = None,
    location: str | None = None,
    source_url: str | None = None,
) -> Command:
    """Create a Google Calendar event for a legislative date.

    Use this tool when you find a specific upcoming date for a legislative event
    such as a city council meeting, public hearing, committee session, vote, or
    ordinance effective date.

    Args:
        title: Descriptive event title (e.g. "Austin City Council — Zoning Vote #2026-45").
        start_date: Start date/time in ISO 8601 format (YYYY-MM-DDTHH:MM:SS).
        tool_call_id: Injected by LangGraph — used to associate the ToolMessage.
        city: The city (injected from agent state).
        end_date: Optional end date/time in ISO 8601 format. Defaults to start + 1 hour.
        description: Optional description of what will happen at this event.
        location: Optional meeting venue or virtual link.
        source_url: URL where this event date was found.
    """
    resolved_end = end_date or _default_end_time(start_date)

    # Always record the event in state — calendar availability is a side effect.
    event = LegislativeEvent(
        title=title,
        description=description or f"Legislative event for {city}",
        start_date=start_date,
        end_date=resolved_end,
        location=location,
        source_url=source_url,
    )

    if not mcp.is_configured("google_calendar"):
        msg = (
            f"Event recorded (Google Calendar not configured): "
            f"'{title}' on {start_date}"
        )
        logger.info(msg)
        return ok(tool_call_id, msg, legislative_events=[event])

    if await _event_exists(title, start_date, city):
        msg = f"Calendar event already exists, skipping: '{title}' on {start_date}"
        logger.info(msg)
        return ok(tool_call_id, msg, legislative_events=[event])

    try:
        full_description = description or ""
        if source_url:
            full_description += f"\n\nSource: {source_url}"

        args: dict[str, Any] = {
            "summary": f"[{city}] {title}",
            "start_time": start_date,
            "end_time": resolved_end,
        }
        if full_description:
            args["description"] = full_description
        if location:
            args["location"] = location

        result = await mcp.call("google_calendar", "create_event", args)
        link = result.get("htmlLink") or result.get("id", "no link")
        msg = f"Calendar event created: '{title}' on {start_date} — {link}"
        logger.info(msg)

    except Exception as e:
        msg = f"Calendar event creation failed: {e}. Event recorded in state."
        logger.warning(msg)

    return ok(tool_call_id, msg, legislative_events=[event])
