"""Google Calendar MCP client — the interface app code imports.

Connects to the @cocal/google-calendar-mcp npm package as a stdio subprocess
and exposes async functions for creating calendar events from legislative dates.
Do not run this file directly; import its functions from your application.

The npm package handles all Google OAuth2 authentication internally.
"""

from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv

load_dotenv()

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from utils.mcp.session import MCPSessionManager


def is_calendar_configured() -> bool:
    """Check if Google Calendar credentials file is configured.

    Returns True only if GOOGLE_OAUTH_CREDENTIALS is set and the file exists.
    Callers should check this before enabling calendar functionality.
    """
    creds_path = os.getenv("GOOGLE_OAUTH_CREDENTIALS", "")
    return bool(creds_path and os.path.exists(creds_path))


@asynccontextmanager
async def get_google_calendar_session():
    """Get MCP session connected to @cocal/google-calendar-mcp via stdio.

    Launches the npm package as a subprocess via npx and communicates via
    stdin/stdout. Session is properly cleaned up on exit.
    """
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@cocal/google-calendar-mcp"],
        env={
            **os.environ,
            "GOOGLE_OAUTH_CREDENTIALS": os.getenv("GOOGLE_OAUTH_CREDENTIALS", ""),
        },
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


_manager = MCPSessionManager("google_calendar_session", get_google_calendar_session)
managed_google_calendar_session = _manager.managed_session


async def create_event(
    summary: str,
    start_time: str,
    end_time: str,
    description: str | None = None,
    location: str | None = None,
    calendar_id: str | None = None,
) -> dict[str, Any]:
    """Create a Google Calendar event via the MCP server.

    Args:
        summary: Event title/summary.
        start_time: Start time in ISO 8601 format (YYYY-MM-DDTHH:MM:SS).
        end_time: End time in ISO 8601 format.
        description: Optional event description.
        location: Optional physical or virtual location.
        calendar_id: Optional calendar ID. Defaults to the primary calendar.

    Returns:
        Dict with created event details from the Google Calendar API.
    """
    args: dict[str, Any] = {
        "summary": summary,
        "start": {"dateTime": start_time},
        "end": {"dateTime": end_time},
    }
    if description:
        args["description"] = description
    if location:
        args["location"] = location
    if calendar_id:
        args["calendarId"] = calendar_id
    return await _manager.call_tool("create-event", args)
