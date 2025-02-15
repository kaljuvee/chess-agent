import streamlit as st
from openai import OpenAI
from streamlit_chat import message
from dotenv import load_dotenv
import os
from utils.query import search_games

# Load environment variables
load_dotenv()

# Initialize OpenAI client
def init_openai():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("Please set OPENAI_API_KEY in your .env file")
        st.stop()
    return OpenAI(api_key=api_key)

# Initialize Streamlit interface
st.title("Chess Player Analysis")
st.write("Ask questions about chess players and games in the database!")

# Initialize session state
if 'analysis_messages' not in st.session_state:
    st.session_state.analysis_messages = []
if 'openai_client' not in st.session_state:
    st.session_state.openai_client = init_openai()

# Sidebar with example queries
with st.sidebar:
    st.header("Example Queries")
    example_queries = [
        "Show me Shabalov's best games as White",
        "What are some interesting games from the World Senior Championships?",
        "Find games with brilliant tactical combinations",
        "Show games where underdogs defeated higher-rated players",
        "What are some notable games in the Sicilian Defense?",
    ]
    
    for query in example_queries:
        if st.button(query):
            st.session_state.analysis_messages.append({"role": "user", "content": query})
            response = search_games(query, client=st.session_state.openai_client, num_results=3, return_str=True)
            st.session_state.analysis_messages.append({"role": "assistant", "content": response})
            st.rerun()

# Chat interface
st.subheader("Analysis Chat")

# Display chat history
for i, msg in enumerate(st.session_state.analysis_messages):
    message(
        msg["content"],
        is_user=(msg["role"] == "user"),
        key=f"analysis_msg_{i}"
    )

# User input
user_input = st.text_input("Ask about chess players and games:", key="analysis_input")

if user_input and user_input != st.session_state.get('last_analysis_input', ''):
    # Store current input to prevent duplicate processing
    st.session_state.last_analysis_input = user_input
    
    # Add user message to chat
    st.session_state.analysis_messages.append({"role": "user", "content": user_input})
    
    # Get RAG response
    response = search_games(user_input, client=st.session_state.openai_client, num_results=3, return_str=True)
    
    # Add response to chat
    st.session_state.analysis_messages.append({"role": "assistant", "content": response})
    
    # Rerun to update the display
    st.rerun()

# Clear chat button
if st.button("Clear Chat"):
    st.session_state.analysis_messages = []
    st.rerun()
