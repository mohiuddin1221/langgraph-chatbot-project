import os
from dotenv import load_dotenv
load_dotenv()
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import MessagesState
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, RemoveMessage
from langgraph.graph import StateGraph, START, END


llm = AzureChatOpenAI(
    openai_api_key=os.environ["AZURE_OPENAI_API_KEY"],
    openai_api_version=os.environ["AZURE_OPENAI_API_VERSION"],
    azure_deployment=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    openai_api_type="azure",
    temperature=1,
)


class State(MessagesState):
    summary: str



def call_model(state: State):
    summary = state.get("summary", "")

    if not summary:
        messages = state["messages"]

    else:
        system_message = f"Summarize the following conversation:\n\n{summary}\n\n"

        messages = state["messages"] + [SystemMessage(content = system_message)]

    response = llm.invoke(messages)
    return {"messages":response}


def summarize_conversation(state:State):

    #First we get any existing summary

    summary = state.get("summary", "")

    # Create our summarization prompt 
    if summary:
        summary_message = (
            f"Summarize the following conversation:\n\n{summary}\n\n"
            "Extend the summary with the latest messages, but do not repeat any information.\n"
            "If the summary is already complete, return it unchanged.\n"
        )
    else:
        summary_message = "craete a summary of the conversation above.\n"

    messages = state["messages"] + [SystemMessage(content=summary_message)]
    response = llm.invoke(messages)

    #Delete all but  the 2 most recent messages
    delete_messages = state["messages"][-2:] + [RemoveMessage(id=m.id) for m in state["messages"][:-2]]
    return {"summary": response.content, "messages": delete_messages}


def should_continue(state: State):
    messages = state["messages"]

    if len(messages) < 6:
        return "summarize_conversation"
    return END




#define a new grpah

builder = StateGraph(State)
builder.add_node("conversation", call_model)
builder.add_node("summarize_conversation", summarize_conversation)


#define the edges
builder.add_edge(START, "conversation")
builder.add_conditional_edges("conversation", should_continue )
builder.add_edge("summarize_conversation", END)


# Compile the graph
memeory = MemorySaver()
graph = builder.compile(checkpointer = memeory)

config = {"configurable": {"thread_id": "1"}}


#start the conversation

input_messages = HumanMessage(content="Hi, I'm Lance.")
response = graph.invoke({ "messages": [input_messages]},config)

messages = response["messages"]
# Print the conversation
for msg in reversed(messages):
    if hasattr(msg, "content") and msg.content.strip():
        final_response = msg.content
        break
print(final_response)



##########

input_messages = HumanMessage(content="what's my name?")
response = graph.invoke({ "messages": [input_messages]},config)

messages = response["messages"]
# Print the conversation
for msg in reversed(messages):
    if hasattr(msg, "content") and msg.content.strip():
        final_response = msg.content
        break
print(final_response)


####

input_messages = HumanMessage(content="i like the 49ers!")
response = graph.invoke({ "messages": [input_messages]},config)

messages = response["messages"]
# Print the conversation
for msg in reversed(messages):
    if hasattr(msg, "content") and msg.content.strip():
        final_response = msg.content
        break
print(final_response)
