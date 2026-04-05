import streamlit as st
from langgraph_tool_backend import chatbot, retrieve_all_threads
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
import uuid
from datetime import datetime

# =========================== Utilities ===========================
def generate_thread_id():
    return str(uuid.uuid4())[:8]

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state["thread_id"] = thread_id
    add_thread(thread_id)
    st.session_state["message_history"] = []

def add_thread(thread_id):
    if thread_id not in st.session_state["chat_threads"]:
        st.session_state["chat_threads"].append(thread_id)

def load_conversation(thread_id):
    state = chatbot.get_state(config={"configurable": {"thread_id": thread_id}})
    return state.values.get("messages", [])

# ============================ Custom CSS ===========================
st.markdown("""
<style>
    /* Main chat container */
    .stMainBlockContainer {
        padding-top: 0rem;
    }
    
    /* Chat message styling */
    [data-testid="stChatMessageContent"] {
        padding: 12px 16px;
        border-radius: 16px;
        font-size: 15px;
        line-height: 1.5;
    }
    
    /* User messages */
    [data-testid="stChatMessageContent"]:has(+ [data-testid="stChatMessageAvatar"]) {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-bottom-right-radius: 4px;
    }
    
    /* Assistant messages */
    [data-testid="stChatMessageAvatar"]:has(+ *) + div [data-testid="stChatMessageContent"],
    div:has([data-testid="stChatMessageAvatar"]:nth-child(1)) [data-testid="stChatMessageContent"]:not(:has(+ [data-testid="stChatMessageAvatar"])) {
        background: #f0f2f6;
        color: #1a1a2e;
        border-bottom-left-radius: 4px;
    }
    
    /* Hide default avatars and use custom */
    [data-testid="stChatMessageAvatar"] {
        background: transparent !important;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }
    
    /* Sidebar title */
    .sidebar-title {
        color: #ffffff;
        font-size: 24px;
        font-weight: 700;
        padding: 20px 0;
        text-align: center;
        border-bottom: 1px solid rgba(255,255,255,0.1);
        margin-bottom: 20px;
    }
    
    /* Chat button styling */
    .stSidebar .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 12px 20px;
        border-radius: 12px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stSidebar .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    /* Conversation list items */
    .conversation-item {
        background: rgba(255,255,255,0.05);
        padding: 10px 15px;
        border-radius: 8px;
        margin: 5px 0;
        color: #e0e0e0;
        font-size: 13px;
        border-left: 3px solid #667eea;
        transition: all 0.2s ease;
    }
    
    .conversation-item:hover {
        background: rgba(255,255,255,0.1);
        border-left-color: #764ba2;
    }
    
    /* Chat input styling */
    .stChatInputContainer {
        background: white;
        border-radius: 25px;
        padding: 5px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    /* Header styling */
    header[data-testid="stHeader"] {
        background: transparent;
    }
    
    /* Tool status box */
    .st-emotion-cache-1vt4y50 {
        background: #f8f9fa;
        border-radius: 12px;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #667eea;
        border-radius: 3px;
    }
    
    /* New chat button in main area */
    .new-chat-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 12px 24px;
        border-radius: 25px;
        border: none;
        cursor: pointer;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* Timestamp styling */
    .timestamp {
        color: #888;
        font-size: 11px;
        margin-top: 4px;
    }
    
    /* Message container */
    .message-container {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ======================= Session Initialization ===================
if "message_history" not in st.session_state:
    st.session_state["message_history"] = []

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = generate_thread_id()

if "chat_threads" not in st.session_state:
    st.session_state["chat_threads"] = retrieve_all_threads()

add_thread(st.session_state["thread_id"])

# ============================ Sidebar ============================
with st.sidebar:
    st.markdown('<div class="sidebar-title">🤖 AI Assistant</div>', unsafe_allow_html=True)
    
    if st.button("➕ New Chat", use_container_width=True):
        reset_chat()
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 💬 Conversations")
    
    if st.session_state["chat_threads"]:
        for thread_id in st.session_state["chat_threads"][::-1][:10]:
            col1, col2 = st.columns([4, 1])
            with col1:
                if st.button(f"Chat {thread_id}", key=f"thread_{thread_id}", use_container_width=True):
                    st.session_state["thread_id"] = thread_id
                    messages = load_conversation(thread_id)
                    temp_messages = []
                    for msg in messages:
                        role = "user" if isinstance(msg, HumanMessage) else "assistant"
                        temp_messages.append({"role": role, "content": msg.content})
                    st.session_state["message_history"] = temp_messages
                    st.rerun()
    else:
        st.info("No conversations yet")
    
    st.markdown("---")
    st.markdown("##### Powered by Groq + LangGraph")

# ============================ Main UI ============================

# Header
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("""
        <div style="text-align: center; padding: 10px 0;">
            <h1 style="background: linear-gradient(135deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0;">
                ✨ AI Chat Assistant
            </h1>
            <p style="color: #666; margin-top: 5px;">Ask me anything - I can search the web, check stock prices, or do math!</p>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Render message history with better formatting
for idx, message in enumerate(st.session_state["message_history"]):
    avatar_icon = "👤" if message["role"] == "user" else "🤖"
    
    with st.chat_message(message["role"], avatar=avatar_icon):
        # Parse and format message content
        content = message["content"]
        if isinstance(content, str):
            # Handle tool results
            if content.startswith("[{"):
                try:
                    import json
                    data = json.loads(content)
                    for item in data:
                        if isinstance(item, dict) and 'url' in item and 'content' in item:
                            st.markdown(f"**🔗 {item.get('title', 'Result')}**")
                            st.markdown(item['content'][:500] + "..." if len(str(item['content'])) > 500 else item['content'])
                            st.markdown(f"<small>Source: {item.get('url', 'N/A')}</small>", unsafe_allow_html=True)
                            st.markdown("---")
                        else:
                            st.markdown(str(item))
                except:
                    st.markdown(content)
            else:
                st.markdown(content)

# Chat input with placeholder
user_input = st.chat_input(
    placeholder="💭 Ask me anything... (try: 'What's the weather?' or 'Stock price of AAPL')",
    key="chat_input"
)

if user_input:
    # Show user's message with animation
    st.session_state["message_history"].append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    CONFIG = {
        "configurable": {"thread_id": st.session_state["thread_id"]},
        "metadata": {"thread_id": st.session_state["thread_id"]},
        "run_name": "chat_turn",
    }

    # Assistant response with tool status
    with st.chat_message("assistant", avatar="🤖"):
        status_holder = {"box": None, "content": []}

        def ai_only_stream():
            for message_chunk, metadata in chatbot.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode="messages",
            ):
                if isinstance(message_chunk, ToolMessage):
                    tool_name = getattr(message_chunk, "name", "tool")
                    content = getattr(message_chunk, "content", "")
                    
                    if status_holder["box"] is None:
                        status_holder["box"] = st.status(
                            f"🔧 Calling `{tool_name}`", expanded=True
                        )
                    
                    # Show tool result preview
                    if content:
                        try:
                            import json
                            data = json.loads(content) if content.startswith('[') else [{"content": content}]
                            for item in data:
                                if isinstance(item, dict) and 'content' in item:
                                    preview = str(item['content'])[:200]
                                    status_holder["box"].write(f"📄 {preview}...")
                        except:
                            status_holder["box"].write(f"📄 {content[:200]}...")

                if isinstance(message_chunk, AIMessage):
                    yield message_chunk.content

        try:
            ai_message = st.write_stream(ai_only_stream())
            
            if status_holder["box"] is not None:
                status_holder["box"].update(
                    label="✅ Task completed", state="complete", expanded=False
                )
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            ai_message = "I encountered an error. Please try again."

    st.session_state["message_history"].append({"role": "assistant", "content": ai_message})
    st.rerun()

# Welcome message for empty state
if not st.session_state["message_history"]:
    st.markdown("""
        <div style="text-align: center; padding: 50px 20px; background: linear-gradient(135deg, #667eea10, #764ba210); border-radius: 20px; margin: 20px 0;">
            <h2 style="color: #1a1a2e;">👋 Welcome!</h2>
            <p style="color: #666; max-width: 500px; margin: 0 auto;">
                I'm your AI assistant powered by Groq and LangGraph. 
                I can help you with:
            </p>
            <div style="display: flex; justify-content: center; gap: 20px; margin-top: 20px; flex-wrap: wrap;">
                <div style="background: white; padding: 15px 25px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    🔍 <strong>Web Search</strong>
                </div>
                <div style="background: white; padding: 15px 25px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    📈 <strong>Stock Prices</strong>
                </div>
                <div style="background: white; padding: 15px 25px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    🧮 <strong>Calculations</strong>
                </div>
            </div>
            <p style="color: #888; margin-top: 30px;">Type a message below to get started!</p>
        </div>
    """, unsafe_allow_html=True)
