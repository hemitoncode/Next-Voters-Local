from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool

llm = ChatOpenAI(model="gpt-4o-mini")

@tool
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together."""
    return a + b

tools = [add_numbers]

worker_agent_1 = create_react_agent(
    llm=llm,
    tools=tools,
    name="worker_agent_a",
    prompt="You solve problems and use tools when needed."
)

worker_agent_2 = create_react_agent(
    llm=llm,
    tools=tools,
    name="worker_agent_b",
    prompt="You solve problems and use tools when needed."
)

# ---- Supervisor ----
supervisor = create_supervisor(
    llm=llm,
    agents=[worker_agent_1, worker_agent_2],
    prompt="You decide which agent should handle the task."
)


graph = supervisor.compile()

result = graph.invoke({
    "messages": [
        {"role": "user", "content": "What is 5 + 7?"}
    ]
})

print(result)