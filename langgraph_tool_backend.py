from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_groq import ChatGroq
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_tavily import TavilySearch
from langchain_core.tools import tool

import os
import requests


os.environ.setdefault("GROQ_API_KEY", os.getenv("GROQ_API_KEY", ""))
os.environ.setdefault("TAVILY_API_KEY", os.getenv("TAVILY_API_KEY", ""))

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

search_tool = TavilySearch(max_results=3)


@tool
def calculator(first_num: float, second_num: float, operation: str) -> str:
    """
    Perform a basic arithmetic operation on two numbers.
    Supported operations: add, sub, mul, div
    """
    try:
        if operation == "add":
            result = first_num + second_num
        elif operation == "sub":
            result = first_num - second_num
        elif operation == "mul":
            result = first_num * second_num
        elif operation == "div":
            if second_num == 0:
                return "Error: Division by zero is not allowed"
            result = first_num / second_num
        else:
            return f"Error: Unsupported operation '{operation}'"
        
        return f"Result of {first_num} {operation} {second_num} = {result}"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_stock_price(symbol: str) -> str:
    """
    Fetch the latest stock price for a given symbol (e.g. 'AAPL', 'TSLA').
    Returns the stock quote information.
    """
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey=C9PE94QUEW9VWGFM"
    r = requests.get(url)
    data = r.json()
    if "Global Quote" in data and data["Global Quote"]:
        quote = data["Global Quote"]
        return f"{symbol}: ${quote.get('05. price', 'N/A')} (Change: {quote.get('10. change percent', 'N/A')})"
    return f"Could not fetch data for {symbol}"


tools = [search_tool, get_stock_price, calculator]
llm_with_tools = llm.bind_tools(tools)


class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def chat_node(state: ChatState):
    messages = state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


tool_node = ToolNode(tools)


checkpointer = MemorySaver()


graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_node("tools", tool_node)

graph.add_edge(START, "chat_node")

graph.add_conditional_edges("chat_node", tools_condition)
graph.add_edge('tools', 'chat_node')

chatbot = graph.compile(checkpointer=checkpointer)


def retrieve_all_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        all_threads.add(checkpoint.config["configurable"]["thread_id"])
    return list(all_threads)
