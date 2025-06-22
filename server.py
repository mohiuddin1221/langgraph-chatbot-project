from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

graph = None  

app = FastAPI(
    title="LangGraph Server",
    description="Minimal FastAPI LangGraph server",
    version="1.0"
)

@app.get("/")
async def root():
    return {"message": "Welcome to LangGraph server!"}

class MessageInput(BaseModel):
    messages: list

@app.post("/invoke")
async def invoke(data: MessageInput):
    if graph is None:
        return {"error": "Graph not initialized"}

    result = graph.invoke(data.dict())
    return result

def run_server(compiled_graph, config=None, port=8000):
    global graph
    graph = compiled_graph
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
