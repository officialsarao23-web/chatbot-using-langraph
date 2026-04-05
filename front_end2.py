import streamlit as st
from langgraph_backend import chatbot
from langchain_core.messages import HumanMessage, AIMessage
import uuid
import json
import os
from datetime import datetime

HISTORY_DIR = "conversation_history"
os.makedirs(HISTORY_DIR, exist_ok=True)

def generate_thread_id():
    return str(uuid.uuid4())

def save_conversation(thread_id, messages, name=None):
    filepath = os.path.join(HISTORY_DIR, f"{thread_id}.json")
    if name is None:
        name = messages[0]['content'][:30] + "..." if messages and messages[0]['role'] == 'user' else f"Chat {thread_id[:8]}"
    data = {
        "thread_id": thread_id,
        "name": name,
        "messages": messages,
        "updated_at": datetime.now().isoformat()
    }
    with open(filepath, 'w') as f:
        json.dump(data, f)

def load_conversation(thread_id):
    filepath = os.path.join(HISTORY_DIR, f"{thread_id}.json")
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return None

def update_conversation_name(thread_id, new_name):
    filepath = os.path.join(HISTORY_DIR, f"{thread_id}.json")
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            data = json.load(f)
        data['name'] = new_name
        with open(filepath, 'w') as f:
            json.dump(data, f)

def list_conversations():
    conversations = []
    for filename in os.listdir(HISTORY_DIR):
        if filename.endswith('.json'):
            filepath = os.path.join(HISTORY_DIR, filename)
            with open(filepath, 'r') as f:
                data = json.load(f)
                conversations.append({
                    'thread_id': data['thread_id'],
                    'name': data.get('name', f"Chat {data['thread_id'][:8]}"),
                    'updated_at': data['updated_at']
                })
    return sorted(conversations, key=lambda x: x['updated_at'], reverse=True)

def delete_conversation(thread_id):
    filepath = os.path.join(HISTORY_DIR, f"{thread_id}.json")
    if os.path.exists(filepath):
        os.remove(filepath)

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    st.session_state['message_history'] = []
    st.session_state['streaming_complete'] = False
    st.session_state['editing_name'] = False
    st.session_state['current_chat_name'] = f"Chat {thread_id[:8]}"

def resume_chat(thread_id):
    conversation = load_conversation(thread_id)
    if conversation:
        st.session_state['thread_id'] = thread_id
        st.session_state['message_history'] = conversation['messages']
        st.session_state['streaming_complete'] = True
        st.session_state['editing_name'] = False
        st.session_state['current_chat_name'] = conversation.get('name', f"Chat {thread_id[:8]}")
        st.rerun()

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []
if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()
if 'streaming_complete' not in st.session_state:
    st.session_state['streaming_complete'] = False
if 'editing_name' not in st.session_state:
    st.session_state['editing_name'] = False
if 'current_chat_name' not in st.session_state:
    st.session_state['current_chat_name'] = f"Chat {st.session_state['thread_id'][:8]}"

st.set_page_config(page_title="LangGraph Chatbot", page_icon="💬")

st.sidebar.title("💬 LangGraph Chatbot")

if st.sidebar.button("➕ New Chat", use_container_width=True):
    reset_chat()
    st.rerun()

st.sidebar.divider()
st.sidebar.subheader("📋 Past Chats")

conversations = list_conversations()
for conv in conversations:
    is_current = conv['thread_id'] == st.session_state['thread_id']
    col1, col2 = st.sidebar.columns([3, 1])
    with col1:
        icon = "📌 " if is_current else "  "
        btn_label = f"{icon}{conv['name']}"
        if st.button(btn_label, key=f"conv_{conv['thread_id']}", use_container_width=True):
            resume_chat(conv['thread_id'])
    with col2:
        if st.button("🗑️", key=f"del_{conv['thread_id']}"):
            delete_conversation(conv['thread_id'])
            st.rerun()

st.sidebar.divider()

with st.sidebar.expander("✏️ Rename Current Chat", expanded=False):
    if st.session_state['editing_name']:
        new_name = st.text_input("New name", value=st.session_state['current_chat_name'], key="rename_input")
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("💾 Save", key="save_name"):
                st.session_state['current_chat_name'] = new_name
                update_conversation_name(st.session_state['thread_id'], new_name)
                st.session_state['editing_name'] = False
                st.rerun()
        with col2:
            if st.button("❌ Cancel", key="cancel_name"):
                st.session_state['editing_name'] = False
                st.rerun()
    else:
        if st.button("✏️ Rename", key="start_rename"):
            st.session_state['editing_name'] = True
            st.rerun()

st.sidebar.caption(f"ID: {st.session_state['thread_id'][:8]}...")

st.title("💬 " + st.session_state['current_chat_name'])

for message in st.session_state['message_history']:
    avatar = "👤" if message['role'] == "user" else "🤖"
    with st.chat_message(message['role'], avatar=avatar):
        st.text(message['content'])

CONFIG = {"configurable": {"thread_id": st.session_state['thread_id']}}

user_input = st.chat_input('Type your message here...')

if user_input and not st.session_state['streaming_complete']:
    if not st.session_state['message_history']:
        auto_name = user_input[:30] + "..." if len(user_input) > 30 else user_input
        st.session_state['current_chat_name'] = auto_name
    
    st.session_state['message_history'].append({'role': "user", 'content': user_input})
    with st.chat_message('user', avatar="👤"):
        st.text(user_input)

    with st.chat_message('assistant', avatar="🤖"):
        message_placeholder = st.empty()
        full_response = ""
        
        for message_chunk in chatbot.stream(
            {'messages': [HumanMessage(content=user_input)]}, 
            config=CONFIG,
            stream_mode='messages'
        ):
            msg = message_chunk[0]
            if hasattr(msg, 'content') and msg.content:
                full_response += msg.content
                message_placeholder.text(full_response)
        
        message_placeholder.text(full_response)
    
    st.session_state['message_history'].append({'role': 'assistant', 'content': full_response})
    save_conversation(st.session_state['thread_id'], st.session_state['message_history'], st.session_state['current_chat_name'])
    st.rerun()

if user_input:
    st.session_state['streaming_complete'] = False
