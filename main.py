import httpx
from dotenv import load_dotenv
from typing import TypedDict, NotRequired
from pydantic import BaseModel, Field

from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI

from agents.legislation_finder import legislation_finder_agent
from utils.models import WriterOutput
from utils.prompts import writer_sys_prompt

load_dotenv()

model = ChatOpenAI(model="gpt-4o-mini")

class LegislationContent(TypedDict):
    source: str
    content: str
    error: NotRequired[str]

class AgentOrchestrationState(TypedDict):
    """State for the agent orchestration graph."""
    city: NotRequired[str]

    legislation_sources: NotRequired[list[str]]
    legislation_sources_content: NotRequired[list[LegislationContent]]

    final_output: NotRequired[list[WriterOutput]]

def run_legislation_finder(state: AgentOrchestrationState) -> AgentOrchestrationState:
    """Run the legislation finder agent as a subgraph node."""
    city = state.get("city", "Unknown")
    agent_result = legislation_finder_agent.invoke({"messages": [], "city": city})
    legislation_sources = agent_result.get("messages", [])
    return {"legislation_sources": legislation_sources}


def run_content_retrieval(state: AgentOrchestrationState) -> AgentOrchestrationState:
    legislation_sources_content = []

    for source in state.get("legislation_sources", []):
        try:
            markdown_url = f"https://markdown.new/{source}"
            response = httpx.get(markdown_url, timeout=30, follow_redirects=True)
            response.raise_for_status()
            legislation_sources_content.append({
                "source": source,
                "content": response.text
            })
        except httpx.HTTPError as e:
            legislation_sources_content.append({
                "source": source,
                "content": None,
                "error": str(e)
            })

    return {"legislation_sources_content": legislation_sources_content}

def writer(state: AgentOrchestrationState) -> AgentOrchestrationState:
    notes = state.get("agent_conversation", [])[-1]
    system_prompt = writer_sys_prompt.format("")

    structured_model = model.with_structured_output(WriterOutput)

    response: WriterOutput = structured_model.invoke(
        [{"role": "system", "content": system_prompt}] + notes,
    )

    return {"final_output": response}

graph_builder = StateGraph(AgentOrchestrationState)
graph_builder.add_node("legislation_finder", run_legislation_finder)
graph_builder.add_node("content_retrieval", run_content_retrieval)
graph_builder.add_node("writer", writer)

graph_builder.add_edge(START, "legislation_finder")
graph_builder.add_edge("legislation_finder", "content_retrieval")
graph_builder.add_edge("content_retrieval", "writer")
graph_builder.add_edge("writer", END)

graph = graph_builder.compile()

if __name__ == "__main__":
    city = str(input("What city would you like to find legislation in? "))

    result = graph.invoke(
        {
            "city": city,
        }
    )

    print("\n=== Legislation Finder Results ===\n")
    agent_output = result.get("final_output") if result.get("final_output") else None
    print(agent_output)