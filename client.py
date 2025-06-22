import asyncio
from langgraph_sdk import get_client

async def main():
    client = get_client(url="http://127.0.0.1:2024")

    
    thread = await client.threads.create()
    thread_id = thread["thread_id"]
    print(f"Created thread with ID: {thread_id}")

    
    initial_input = {
        "messages": [
            {"type": "human", "content": "Multiply 2 and 3"}
        ]
    }

    
    print("Streaming first response...")
    async for chunk in client.runs.stream(
        thread_id,
        assistant_id="agent",
        input=initial_input,
        stream_mode="values",
        interrupt_before=["assistant"],
    ):
        print(f"Event: {chunk.event}")
        messages = chunk.data.get("messages", [])
        if messages:
            print("Assistant says:", messages[-1]["content"])
        print("-" * 40)

   
    current_state = await client.threads.get_state(thread_id)

    
    last_message = current_state["values"]["messages"][-1]
    last_message["content"] = "No, actually multiply 3 and 3!"

    await client.threads.update_state(
        thread_id,
        updates={"messages": [last_message]}
    )

    print("Streaming second response after update...")
    async for chunk in client.runs.stream(
        thread_id,
        assistant_id="agent",
        input=None,
        stream_mode="values",
        interrupt_before=["assistant"],
    ):
        print(f"Event: {chunk.event}")
        messages = chunk.data.get("messages", [])
        if messages:
            print("Assistant says:", messages[-1]["content"])
        print("-" * 40)


