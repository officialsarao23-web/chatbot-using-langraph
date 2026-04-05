import os
from typing import Annotated, TypedDict
from dotenv import load_dotenv

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.message import add_messages
# USE ChatOllama for better streaming support
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import BaseMessage, HumanMessage
import sqlite3
load_dotenv()

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# Initialize ChatOllama
# If you get a 'validation error', ensure you have langchain-community updated
llm = ChatOllama(model="mistral")
conn = sqlite3.connect(database='chatbot.db', check_same_thread=False)
checkpointer = SqliteSaver(conn)

def chat_node(state: ChatState):
    response = llm.invoke(state['messages'])
    return {'messages': [response]}

workflow = StateGraph(ChatState)
workflow.add_node("chat_node", chat_node)
workflow.add_edge(START, "chat_node")
workflow.add_edge("chat_node", END)

chatbot = workflow.compile(checkpointer=checkpointer)

def retrieve_all_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])
    return list(all_threads)