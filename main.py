from dotenv import load_dotenv
from typing import TypedDict, NotRequired
from langgraph.graph import StateGraph, START, END

load_dotenv()

class AgentOrchestrationState(TypedDict):
    agent_conversation: list[str]
    city: NotRequired[str]


agent_1 = legislation_finder_agent()
agent_2 = build_agent_2(llm)


def run_legislation_finder(state: AgentOrchestrationState) -> AgentOrchestrationState:
    agent_response = agent_1.invoke({"city": state["city"]})
    return {"agent_conversation": agent_response["messages"]}


def run_agent_2(state: AgentOrchestrationState) -> AgentOrchestrationState:
    agent_response = agent_2.invoke({"messages": state["agent_conversation"]})
    return {"agent_conversation": agent_response["messages"]}


graph_builder = StateGraph(AgentOrchestrationState)
graph_builder.add_node("legislation_finder", run_legislation_finder)
graph_builder.add_node("scraper_builder", run_agent_2)

graph_builder.add_edge(START, "legislation_finder")
graph_builder.add_edge("legislation_finder", "scraper_builder")
graph_builder.add_edge("scraper_builder", END)

graph = graph_builder.compile()

if __name__ == "__main__":
    city = str(input("What city would you like to find legislation in?"))

    result = graph.invoke(
        {
            "agent_conversation": [],
            "city": city,
        }
    )

    # Print final messages
    for msg in result["agent_conversation"]:
        print(f"\n[{msg.type}]: {msg.content[:200] if msg.content else '(tool call)'}")
