"""Google Calendar MCP service — event management via the Google Calendar API v3.

server.py: FastMCP server registered in utils.mcp.registry (runs as subprocess)
  Tools: create_event, list_events, delete_event
  Auth: GOOGLE_OAUTH_CREDENTIALS env var → path to authorized-user JSON file
"""
