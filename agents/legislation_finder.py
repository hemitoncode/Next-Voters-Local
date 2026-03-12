import os
import operator
from typing import TypedDict, Annotated, Sequence

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage
from langgraph.pre_built import create_react_agent

from mcp.server.fastmcp import FastMCP
from tavily import TavilyClient

load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini")


# ---------------------------------------------------------------------------
# Typed structures for web_search results
# ---------------------------------------------------------------------------
class SearchResult(TypedDict):
    title: str
    url: str
    content: str
    score: float


class SearchResponse(TypedDict):
    query: str
    results: list[SearchResult]


# ---------------------------------------------------------------------------
# MCP Server — exposes legislation-search tooling over the MCP protocol
# ---------------------------------------------------------------------------
mcp = FastMCP("legislation_finder")
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


@mcp.tool()
def web_search(query: str, max_results: int = 5) -> SearchResponse:
    """Search the web for legislation related to a specific municipality or topic.

    Uses the Tavily search API to find recent, relevant legislation pages.

    Args:
        query: The search query — e.g. "recent Brampton city council bylaws 2026".
        max_results: Maximum number of results to return (default 5).

    Returns:
        A SearchResponse with 'query' and 'results' (list of SearchResult).
    """
    response = tavily_client.search(
        query=query,
        max_results=max_results,
        search_depth="advanced",
        include_answer=False,
        include_raw_content=False,
    )

    results: list[SearchResult] = [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": r.get("content", ""),
            "score": r.get("score", 0.0),
        }
        for r in response.get("results", [])
    ]

    return {"query": query, "results": results}


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    results: list[SearchResult]


legislation_finder_agent = create_react_agent(
    model=llm,
    tools=[web_search],
    name="Legislation Finder"
)