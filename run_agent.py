from langgraph_sdk import get_client
import asyncio

async def main():
    client = get_client(url="http://127.0.0.1:2024/parallelization")

    thread = await client.threads.create()

    input_question = {"question": "How were Nvidia Q2 2024 earnings?"}

    async for event in client.runs.stream(
        thread["thread_id"],
        assistant_id="parallelization",
        input=input_question,
        stream_mode="values"
    ):
        answer = event.data.get("answer", None)
        if answer:
            print(answer["content"])

if __name__ == "__main__":
    asyncio.run(main())