import os
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import AzureChatOpenAI
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import  ToolNode, tools_condition
from langgraph.graph import MessagesState
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver

from server import run_server

# Step 1: Azure Chat Model Config
llm = AzureChatOpenAI(
    openai_api_key=os.environ["AZURE_OPENAI_API_KEY"],
    openai_api_version=os.environ["AZURE_OPENAI_API_VERSION"],
    azure_deployment=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    openai_api_type="azure",
    temperature=1,
)
memeory = MemorySaver()
def multiply(a: int, b: int) -> int:
    """Multiplies two integers."""
    return a * b

def add(a: int, b: int) -> int:
    """Adds two integers."""
    return a + b

def subtract(a: int, b: int) -> int:
    """Subtracts the second number from the first."""
    return a - b

def divide(a: int, b: int) -> float:
    """Divides the first number by the second. Raises error if second is zero."""
    if b == 0:
        raise ValueError("Cannot divide by zero.")
    return a / b

tools = [add, multiply, subtract, divide]

# Step 3: Bind tools to LLM
llm_with_tools = llm.bind_tools(tools, parallel_tool_calls=None)

# Step 4: System Prompt
sys_message = SystemMessage(content="You are a helpful assistant tasked with performing arithmetic on a set of inputs.")

# Step 5: Assistant Node Function
# def assistant_node(state: MessagesState):
#     return {"messages": [llm_with_tools.invoke([sys_message] + state["messages"])]}



def assistant_node(state: MessagesState):
    messages = [sys_message] + state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}

# Step 6: Build LangGraph
builder = StateGraph(MessagesState)
builder.add_node("assistant", assistant_node)
builder.add_node("tools", ToolNode(tools))  






# Define Graph Flow
builder.add_edge(START, "assistant")
builder.add_conditional_edges(
    "assistant",
    # If the latest message (result) from assistant is a tool call -> tools_condition routes to tools
    # If the latest message (result) from assistant is a not a tool call -> tools_condition routes to END
    tools_condition,
)
builder.add_edge("tools", "assistant")



# Run the agent with human-in-the-loop (breakpoint before tools)
# config = {"configurable": {"thread_id": "1"}}
graph = builder.compile(interrupt_before=["tools"], checkpointer=memeory)

###run server

if __name__ == "__main__":
    run_server(graph,  port=2024)  






























# messages = [HumanMessage(content="Add 3 and 4")]
# response = graph.invoke({"messages": messages}, config)

# if response is None:
#     print("Paused at breakpoint, waiting for approval...")

#     response = graph.resume(config)
    

# messages = response["messages"]

# first_response = None
# for msg in reversed(messages):
#     if hasattr(msg, "content") and msg.content.strip():
#         first_response = msg.content
#         break

# print("First response:", first_response)


# graph.update_state(
#     config,
#     {"messages": [HumanMessage(content="No actually multiply 3 and 3")]}
# )

# response = graph.invoke({}, config=config)

# if response is None:
#     print("Paused at breakpoint, waiting for approval...")
#     response = graph.resume(config)

# if response is not None:
#     messages = response["messages"]
#     second_response = None
#     for msg in reversed(messages):
#         if hasattr(msg, "content") and msg.content.strip():
#             second_response = msg.content
#             break
#     print("Second response:", second_response)
# else:
#     print("No response from the graph.")


