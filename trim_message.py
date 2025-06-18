from pprint import pprint
import os
from dotenv import load_dotenv
load_dotenv()
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.messages import trim_messages
from langgraph.graph import MessagesState
from langgraph.graph import StateGraph, START, END


llm = AzureChatOpenAI(
    openai_api_key=os.environ["AZURE_OPENAI_API_KEY"],
    openai_api_version=os.environ["AZURE_OPENAI_API_VERSION"],
    azure_deployment=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    openai_api_type="azure",
    temperature=1,
)


def trim_messages_node(state: MessagesState):
    messages = trim_messages(
        state["messages"],
        max_tokens=1000,  # Adjust the max tokens as needed
        token_counter=AzureChatOpenAI(
            model=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
            api_version="Your-API-Version-Here",  # Replace with your API version
        ),
        strategy="last",
        allow_partial=False,
    )

    return {"messages": messages}

# Build node
builder = StateGraph(MessagesState)
builder.add_node("trim_messages", trim_messages_node)

# Add edges
builder.add_edge(START, "trim_messages")
builder.add_edge("trim_messages", END)

# Compile
graph = builder.compile()

messages = [AIMessage("Hi.", name="Bot", id="1")]
messages.append(HumanMessage("Hi.", name="Lance", id="2"))
messages.append(AIMessage("So you said you were researching ocean mammals?", name="Bot", id="3"))


response = graph.invoke({
    "messages": messages
})