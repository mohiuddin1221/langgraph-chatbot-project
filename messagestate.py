from langgraph.prebuilt import MessagesState

class MessagesState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
