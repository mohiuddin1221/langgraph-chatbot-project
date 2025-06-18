from pprint import pprint
import os
from dotenv import load_dotenv
load_dotenv()
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage
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


messages = [AIMessage(f"So you said you were researching ocean mammals?", name="Bot")]
messages.append(HumanMessage(f"Yes, I know about whales. But what others should I learn about?", name="Lance"))

# for m in messages:
#     print(m.content)



def chat_model_node(state: MessagesState):
    """A simple chat model state function that returns the messages."""
    return {"messages": llm.invoke(state["messages"])}


#build node
builder = StateGraph(MessagesState)
builder.add_node("chat_model", chat_model_node)

builder.add_edge(START, "chat_model")
builder.add_edge("chat_model", END)

#compile
graph = builder.compile()


response = graph.invoke({
    "messages": messages
})
messages = response["messages"]
for m in messages:
    print(m.content)
