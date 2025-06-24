import operator
import os
from typing import Annotated, TypedDict
from dotenv import load_dotenv
load_dotenv()
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langchain_community.document_loaders import WikipediaLoader
from langchain_community.tools import TavilySearchResults
from langgraph.checkpoint.memory import MemorySaver
from fastapi import FastAPI
from langserve import add_routes



llm = AzureChatOpenAI(
    openai_api_key=os.environ["AZURE_OPENAI_API_KEY"],
    openai_api_version=os.environ["AZURE_OPENAI_API_VERSION"],
    azure_deployment=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    openai_api_type="azure",
    temperature=1,
)
memory = MemorySaver()


class State(TypedDict):
    question: str
    answer: str
    context: Annotated[list, operator.add]



def serch_web(state: State):

    """Retruve docs from web search"""

    tavily_search = TavilySearchResults(max_results=3)
    search_docs = tavily_search.invoke(state["question"])

    # Format
    formatted_search_docs = "\n\n---\n\n".join(
        [
            f'<Document href="{doc["url"]}">\n{doc["content"]}\n</Document>'
            for doc in search_docs
        ]
    )
    return {
        "context": [formatted_search_docs]
    }

def search_wikipedia(state: State):

    """Retrive docs from wikipedia"""

    search_docs = WikipediaLoader(query=state["question"], load_max_docs = 2).load()
    # Format
    formatted_search_docs = "\n\n---\n\n".join(
        [
            f'<Document source="{doc.metadata["source"]}" page="{doc.metadata.get("page", "")}">\n{doc.page_content}\n</Document>'
            for doc in search_docs
        ]
    )
    return {
        "context": [formatted_search_docs]
    }


def generate_answer(state: State):
    """Node the answer a question"""

    context = state["context"]
    question = state["question"]

    #Template for the answer

    answer_template = """Answer the question {question}  using the {context}"""
    
    answer_instructions = answer_template.format(question = question, context = context)

    #Answer
    response = llm.invoke([SystemMessage(content=answer_instructions), HumanMessage(content=question)])

    return{
        "answer": response
    }



#Add Nodes

builder = StateGraph(State)

builder.add_node("search_web", serch_web)
builder.add_node("search_wikipedia", search_wikipedia)
builder.add_node("generate_answer", generate_answer)

# Define Graph Flow
builder.add_edge(START, "search_web")
builder.add_edge(START, "search_wikipedia")
builder.add_edge("search_web", "generate_answer")
builder.add_edge("search_wikipedia", "generate_answer")
builder.add_edge("generate_answer", END)


# Compile the graph
graph = builder.compile(checkpointer=memory, name="parallelization")


#server setup

app = FastAPI()


add_routes(app, graph, path="/parallelization")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=2024)


