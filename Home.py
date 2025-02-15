import streamlit as st
from openai import OpenAI
from streamlit_chat import message
from dotenv import load_dotenv
import os
import json
from datetime import datetime
import chess
import chess.svg

# Load environment variables and system prompt
load_dotenv()

try:
    with open('prompt/system.md', 'r', encoding='utf-8') as file:
        SYSTEM_PROMPT = file.read()
except Exception as e:
    st.error(f"Error loading system prompt: {e}")
    SYSTEM_PROMPT = """You are a witty chess assistant playing a game against the user. You are playing as White. You should:
    1. Make chess-related puns and jokes while playing
    2. Keep track of the game state and respond with valid moves
    3. Explain your moves in a fun and entertaining way
    4. Use casual language and occasional emojis
    5. Always format your move clearly at the start of your response"""

# Available models
MODELS = {
    "GPT-4 Optimized Mini": "gpt-4o-mini",
    "GPT-4 Optimized": "gpt-4o"
}

# Initialize OpenAI client
def init_openai():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("Please set OPENAI_API_KEY in your .env file")
        st.stop()
    return OpenAI(api_key=api_key)

def save_game_state(messages, board):
    """Save game state to a JSON file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    game_state = {
        "messages": messages,
        "board_fen": board.fen(),
        "timestamp": timestamp
    }
    
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    filename = f"data/session_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(game_state, f)
    return filename

def get_chat_response(client, messages, board):
    """Get response from OpenAI with game context"""
    system_message = {
        "role": "system", 
        "content": SYSTEM_PROMPT
    }
    
    # Create game history context
    game_history = {
        "board_state": board.fen(),
        "moves": [msg["content"] for msg in messages]
    }
    
    # Create context message
    context_message = {
        "role": "user",
        "content": f"This is the game history: {json.dumps(game_history, indent=2)}"
    }
    
    full_messages = [system_message, context_message] + messages
    
    response = client.chat.completions.create(
        model=st.session_state.selected_model,
        messages=full_messages,
        temperature=0.1
    )
    return response.choices[0].message.content

# Initialize the Streamlit interface
st.title("Chess AI Agent")

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
    # Add initial message
    init_message = "You have whites. What is your first move?"
    st.session_state.messages.append({"role": "user", "content": init_message})
if 'openai_client' not in st.session_state:
    st.session_state.openai_client = init_openai()
if 'board' not in st.session_state:
    st.session_state.board = chess.Board()
if 'selected_model' not in st.session_state:
    st.session_state.selected_model = MODELS["GPT-4 Optimized Mini"]  # Default model
    # Get initial AI response
    if len(st.session_state.messages) == 1:  # Only user's initial message exists
        response = get_chat_response(
            st.session_state.openai_client,
            st.session_state.messages,
            st.session_state.board
        )
        st.session_state.messages.append({"role": "assistant", "content": response})

# Sidebar
with st.sidebar:
    st.header("Settings")
    selected_model = st.selectbox(
        "Select Model",
        list(MODELS.keys()),
        index=0  # Default to first model (gpt-4o-mini)
    )
    st.session_state.selected_model = MODELS[selected_model]
    
    # Display game history
    st.header("Game History")
    if st.session_state.messages:
        game_history = {
            "board_state": st.session_state.board.fen(),
            "moves": [msg["content"] for msg in st.session_state.messages]
        }
        st.json(game_history)
    else:
        st.write("No moves yet")
    
    # Move reset button to sidebar
    if st.button("Reset Game"):
        st.session_state.board = chess.Board()
        st.session_state.messages = []
        st.rerun()

# Display current board state
board_svg = chess.svg.board(board=st.session_state.board)
st.write(f'<div style="width: 600px; margin: auto;">{board_svg}</div>', unsafe_allow_html=True)
st.caption(f"Current position: {st.session_state.board.fen()}")

# Chat interface
st.subheader("Game Progress")

# Display chat history
for i, msg in enumerate(st.session_state.messages):
    message(
        msg["content"],
        is_user=(msg["role"] == "user"),
        key=f"msg_{i}"
    )

# User input at the bottom
user_input = st.text_input("Your move:", key="user_input")

if user_input and user_input != st.session_state.get('last_input', ''):
    # Store current input to prevent duplicate processing
    st.session_state.last_input = user_input
    
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": f"I play: {user_input}"})
    
    # Get AI response
    response = get_chat_response(
        st.session_state.openai_client,
        st.session_state.messages,
        st.session_state.board
    )
    
    # Add AI response to chat
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    # Save game state
    save_game_state(st.session_state.messages, st.session_state.board)
    
    # Rerun to update the display
    st.rerun()
