import streamlit as st
import requests
import json
import uuid
from src.core.config import settings
from src.core.logging_config import get_logger

logger = get_logger(__name__)

st.set_page_config(page_title="AI Chat Assistant", page_icon="💬", layout="centered")

st.title("AI Chat Assistant")

# Initialize session state for chat history and session ID
if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

st.sidebar.info(f"Session: {st.session_state.session_id}")
if st.sidebar.button("Clear Chat"):
    st.session_state.messages = []
    st.session_state.session_id = str(uuid.uuid4())
    st.rerun()

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("What is on your mind?"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Call the API and stream the response
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            # We use the /api/chat/stream endpoint directly
            # For simplicity in this dev environment, we assume the FastAPI server is running on localhost:8000
            # In a unified production Docker container, this would point to the internal service name or 127.0.0.1
            url = "http://localhost:8000/api/chat/stream"
            payload = {
                "session_id": st.session_state.session_id,
                "message": prompt
            }
            
            with requests.post(url, json=payload, stream=True) as r:
                for line in r.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith('data: '):
                            data_str = decoded_line.replace('data: ', '').strip()
                            if data_str == '[DONE]':
                                break
                            
                            try:
                                data = json.loads(data_str)
                                full_response += data.get("chunk", "")
                                response_placeholder.markdown(full_response + "▌")
                            except json.JSONDecodeError:
                                pass
            
            response_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            logger.error(f"UI Error: {e}")
            st.error("Could not reach the backend server. Make sure FastAPI is running on port 8000.")

