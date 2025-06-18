import random
from readline import redisplay
from typing_extensions import Literal, TypedDict
from langgraph.graph import START, END, StateGraph

class State(TypedDict):
    """
    A simple state representation for a state machine.
    """
    graph_state: str

def decide_mood(state) -> Literal["node_2", "node_3"]:

    user_input = state['graph_state']

    if random.random() > 0.5:
        return "node_2"
    else:
        return "node_3"


def node_1(state):
    print("Node 1 executed")
    return {"graph_state": state['graph_state'] + "I am"}


def node_2(state):
    print("Node 2 executed")
    return {"graph_state": state['graph_state'] + " a simple state machine"}    

def node_3(state):
    print("Node 3 executed")
    return {"graph_state": state['graph_state'] + " with LangGraph"}


#build graph

builder = StateGraph(State)
builder.add_node("node_1", node_1)
builder.add_node("node_2", node_2)
builder.add_node("node_3", node_3)

#logic
builder.add_edge(START, "node_1")
builder.add_conditional_edges("node_1", decide_mood)
builder.add_edge("node_2", END)
builder.add_edge("node_3", END)


#add
graph = builder.compile()

final_state = graph.invoke({"graph_state": "Hello, "})
print("Final Output:", final_state)







