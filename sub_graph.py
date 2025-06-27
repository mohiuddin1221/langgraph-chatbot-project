from operator import add
import os
from tkinter import END
from typing import Annotated, List, Optional, TypedDict
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import AzureChatOpenAI
from langgraph.graph import StateGraph, START, END
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


class Log(TypedDict):
    id: str
    question: str
    docs: Optional[list]
    answer: str
    grade: Optional[int]
    grader: Optional[str]
    feedback: Optional[str]


# Here is the failure analysis sub-graph, which uses FailureAnalysisState

# Failure Analysis Sub-graph
class FailureAnalysisState(TypedDict):
    cleaned_log: List[Log]
    failures: List[Log]
    fa_summary: str
    processed_logs: List[str]
    

class FailureAnalysisOutputState(TypedDict):
    fa_summary: str
    processed_logs: List[str]


def get_failures(state: FailureAnalysisState):
    cleaned_logs = state["cleaned_log"]
    failures = [log for log in cleaned_logs if "grade" in log]
    return {"failures": failures}

def generate_summary(state: FailureAnalysisState):
    failures = state["failures"]
    fa_summary = "Poor quality retrieval of Chroma documentation."
    return {
        "fa_summary": fa_summary,
        "processed_logs": [f"failure-analysis-on-log-{failure['id']}" for failure in failures]
        }


#build the graph

fa_builder = StateGraph(FailureAnalysisState, output_state=FailureAnalysisOutputState)
fa_builder.add_node("get_failures", get_failures)
fa_builder.add_node("generate_summary", generate_summary)

#edge the nodes
fa_builder.add_edge(START, "get_failures")
fa_builder.add_edge("get_failures", "generate_summary")
fa_builder.add_edge("generate_summary", END)



graph = fa_builder.compile()



###Here is the question summarization sub-grap, which uses QuestionSummarizationState.

class QuestionSummarizationState(TypedDict):
    cleaned_logs: List[Log]
    qs_summary: str
    report: str
    processed_logs: List[str]

class QuestionSummarizationOutputState(TypedDict):
    report: str
    processed_logs: List[str]



def generate_summary(state):
    cleaned_logs = state["cleaned_logs"]

    summary = "Questions focused on usage of ChatOllama and Chroma vector store."
    processed_logs = [f"question-summarization-on-log-{log['id']}" for log in cleaned_logs]

    return{
        "qs_summary": summary,
        "processed_logs": processed_logs
    }


def send_to_slack(state):
    qs_summary = state["qs_summary"]
    report = "foo bar baz"
    return {
        "report": report
    }


# Build the graph
q_builder = StateGraph(QuestionSummarizationState, output_state=QuestionSummarizationOutputState)
q_builder.add_node("generate_summary", generate_summary)
q_builder.add_node("send_to_slack", send_to_slack)


# Define the graph flow
q_builder.add_edge(START, "generate_summary")
q_builder.add_edge("generate_summary", "send_to_slack")
q_builder.add_edge("send_to_slack", END)

graph = q_builder.compile()


# Entry Graph
class EntryGraphState(TypedDict):
    raw_logs: List[Log]
    cleaned_logs: List[Log]
    fa_summary: str 
    report: str 
    processed_logs:  Annotated[List[int], add] 


def clean_logs(state: EntryGraphState):
    raw_logs = state["raw_logs"]
    cleaned_logs = raw_logs
    return {"cleaned_logs": cleaned_logs}



entry_builder = StateGraph(EntryGraphState)
entry_builder.add_node("clean_logs", clean_logs)
entry_builder.add_node("failure_analysis", fa_builder.compile())
entry_builder.add_node("question_summarization", q_builder.compile())

# Define the graph flow
entry_builder.add_edge(START, "clean_logs")
entry_builder.add_edge("clean_logs", "failure_analysis")
entry_builder.add_edge("clean_logs", "question_summarization")
entry_builder.add_edge("question_summarization", END)
entry_builder.add_edge("failure_analysis", END)


entry_graph = entry_builder.compile()

