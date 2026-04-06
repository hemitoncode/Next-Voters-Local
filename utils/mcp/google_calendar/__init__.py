"""Google Calendar MCP service — create events for legislative dates.

Import from here (or from client.py) for app code.
Uses @cocal/google-calendar-mcp (npm) as a stdio subprocess via npx.
"""

from utils.mcp.google_calendar.client import (
    get_google_calendar_session,
    managed_google_calendar_session,
    create_event,
    is_calendar_configured,
)

__all__ = [
    "get_google_calendar_session",
    "managed_google_calendar_session",
    "create_event",
    "is_calendar_configured",
]
