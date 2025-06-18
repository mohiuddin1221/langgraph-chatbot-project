from pprint import pprint
import os
from dotenv import load_dotenv
load_dotenv()
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.messages import RemoveMessage
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


def filter_messages(state: MessagesState):
    #Dellete all messages but the 2 most recent ones
    delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-2]]
    return{"messages": delete_messages}

def chat_model_node(state: MessagesState):    
    return {"messages": [llm.invoke(state["messages"])]}

#build node
builder = StateGraph(MessagesState)
builder.add_node("filter_messages", filter_messages)
builder.add_node("chat_model", chat_model_node)

# Add edges
builder.add_edge(START, "filter_messages")
builder.add_edge("filter_messages", "chat_model")
builder.add_edge("chat_model", END)

#compile
graph = builder.compile()


messages = [AIMessage("Hi.", name="Bot", id="1")]
messages.append(HumanMessage("Hi.", name="Lance", id="2"))
messages.append(AIMessage("So you said you were researching ocean mammals?", name="Bot", id="3"))
messages.append(HumanMessage("Yes, I know about whales. But what others should I learn about?", name="Lance", id="4"))
messages.append(HumanMessage("Hey I am Topu whatsup", name="Topu", id="5"))

response = graph.invoke({
    "messages": messages
})
messages = response["messages"]
for m in messages:
    print(m.content)




