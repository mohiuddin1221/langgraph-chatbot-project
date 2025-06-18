from langchain.chat_models import AzureChatOpenAI
import os

from langgraph.graph import StateGraph, START, END
from langgraph.graph import MessagesState
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import tools_condition




llm = AzureChatOpenAI(
    openai_api_key=os.environ["AZURE_OPENAI_API_KEY"],
    openai_api_version=os.environ["AZURE_OPENAI_API_VERSION"],
    azure_deployment=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    openai_api_type="azure",
    temperature=1,
)


def multiply(x: int, y: int) -> int:
    """Multiply two integers."""
    return x * y

llm_with_tools = llm.bind_tools([multiply])

#node
def tool_calling_llm(state: MessagesState):
    return {"messages": llm_with_tools.invoke(state["messages"])}


#build graph

builder = StateGraph(MessagesState)
builder.add_node("tool_calling_llm", tool_calling_llm)
builder.add_node("tools", ToolNode([multiply]))



#edge
builder.add_edge(START, "tool_calling_llm")
builder.add_edge("tool_calling_llm", "tools", tools_condition)  
builder.add_edge("tools", END)

graph = builder.compile()

