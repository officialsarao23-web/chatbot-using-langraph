import streamlit as st
from langgraph_backend import chatbot
from langchain_core.messages import HumanMessage
import requests

st.set_page_config(page_title="Mistral Streamer", page_icon="🤖")

# --- CONNECTION CHECK ---
def is_ollama_online():
    try:
        # Default Ollama port
        requests.get("http://localhost:11434", timeout=2)
        return True
    except:
        return False

if not is_ollama_online():
    st.error("❌ Ollama is not running! Please open your terminal and run 'ollama serve' or 'ollama run mistral'.")
    st.stop()
# ------------------------

st.title("Local Streaming AI")

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

user_input = st.chat_input('Type here...')

if user_input:
    st.session_state['message_history'].append({'role': "user", 'content': user_input})
    with st.chat_message('user'):
        st.markdown(user_input)

    with st.chat_message('assistant'):
        placeholder = st.empty()
        full_response = ""
        
        # 1. Use "messages" stream mode
        stream_gen = chatbot.stream(
            {"messages": [HumanMessage(content=user_input)]}, 
            config={"configurable": {"thread_id": "thread-1"}},
            stream_mode="messages"
        )

        try:
            for chunk, metadata in stream_gen:
                # 2. Filter for our chat_node output
                if metadata.get("langgraph_node") == "chat_node":
                    # ChatOllama chunks have a .content attribute
                    if hasattr(chunk, 'content'):
                        # Important: If text appears doubled, change += to =
                        # Most modern ChatOllama versions send 'deltas' (just the new word)
                        full_response += chunk.content
                        placeholder.markdown(full_response + "▌")
            
            # 3. Final render
            if not full_response:
                full_response = "Thinking... (No tokens received yet)"
            
            placeholder.markdown(full_response)
            st.session_state['message_history'].append({'role': 'assistant', 'content': full_response})

        except Exception as e:
            st.error(f"Error during streaming: {e}")