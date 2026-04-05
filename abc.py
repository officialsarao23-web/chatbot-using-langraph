import streamlit as st
from langgraph_backend import chatbot
from langchain_core.messages import HumanMessage
import uuid
def generate_thread_id():
    return str(uuid.uuid4())


def reset_chat():
    st.session_state['message_history'] = []
    st.session_state['thread_id'] = generate_thread_id()
    add_thread(st.session_state['thread_id'])

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)


def load_conversation(thread_id):
    result = chatbot.get_state(config={"configurable":{"thread_id": thread_id}})
    return result.values.get('messages', []) if hasattr(result, 'values') else []


CONFIG = {"configurable":{"thread_id": generate_thread_id()}}
#session setup
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []
if 'thread_id' not in st.session_state:   
    st.session_state['thread_id'] = generate_thread_id()
if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = []
add_thread(st.session_state['thread_id'])



#side bar
st.sidebar.title('LangGraph chatbot')
if st.sidebar.button('new chat'):
    reset_chat() 
st.sidebar.header('conversation history')
for thread_id in st.session_state['chat_threads']:
    if st.sidebar.button('thread id: ' + thread_id[:8] + '...', key=thread_id):
        st.session_state['thread_id'] = thread_id
        messages = load_conversation(thread_id)
        temp_messages = []
        for message in messages:
            if isinstance(message, HumanMessage):
                role = 'user'
            else:
                role = 'assistant'
            temp_messages.append({'role': role, 'content': message.content})
        st.session_state['message_history'] = temp_messages

# Display chat messages (moved after sidebar to ensure loaded messages appear)
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

user_input = st.chat_input('type here...')

if user_input:
    #first add the message to message history
    st.session_state['message_history'].append({'role':"user", 'content': user_input})
    with st.chat_message('user'):
        st.text(user_input)



        
    # response =chatbot.invoke({"messages":[HumanMessage(content=user_input)]}, config = CONFIG)
    
   # st.session_state['message_history'].append({'role':'assistant', 'content': ai_message})
    with st.chat_message('assistant'):
        placeholder = st.empty()
        ai_message = ""
        for message_chunk, metadata in chatbot.stream(
            {"messages":[HumanMessage(content=user_input)]},
            config=CONFIG,
            stream_mode='messages'
        ):
            ai_message += message_chunk.content if hasattr(message_chunk, 'content') else str(message_chunk)
            placeholder.write(ai_message)
    st.session_state['message_history'].append({'role':'assistant', 'content': ai_message})    