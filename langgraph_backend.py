import os
from typing import Annotated, TypedDict
from dotenv import load_dotenv

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages
# USE ChatOllama for better streaming support
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import BaseMessage

load_dotenv()

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# Initialize ChatOllama
# If you get a 'validation error', ensure you have langchain-community updated
llm = ChatOllama(model="mistral")

def chat_node(state: ChatState):
    response = llm.invoke(state['messages'])
    return {'messages': [response]}

workflow = StateGraph(ChatState)
workflow.add_node("chat_node", chat_node)
workflow.add_edge(START, "chat_node")
workflow.add_edge("chat_node", END)

checkpointer = MemorySaver()
chatbot = workflow.compile(checkpointer=checkpointer)