"""MCP client utilities for connecting to external services.

Each subdirectory is a self-contained MCP service:
  - tavily/: Tavily search + extract (FastMCP server as local subprocess)
  - google_calendar/: Google Calendar via @cocal/google-calendar-mcp (npx subprocess)
"""

from utils.mcp.tavily import (
    get_api_key,
    get_tavily_session,
    search_legislation,
    search_political_content,
    extract_search_results,
    extract_url_content,
)
from utils.mcp.google_calendar import (
    get_google_calendar_session,
    managed_google_calendar_session,
    create_event,
    is_calendar_configured,
)

__all__ = [
    # Tavily
    "get_api_key",
    "get_tavily_session",
    "search_legislation",
    "search_political_content",
    "extract_search_results",
    "extract_url_content",
    # Google Calendar
    "get_google_calendar_session",
    "managed_google_calendar_session",
    "create_event",
    "is_calendar_configured",
]
