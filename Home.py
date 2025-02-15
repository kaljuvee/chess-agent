import streamlit as st
from stchess import board
import chess
import chess.engine
from openai import OpenAI
from streamlit_chat import message
import json
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize OpenAI client
def init_openai():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("Please set OPENAI_API_KEY in your .env file")
        st.stop()
    return OpenAI(api_key=api_key)

# AI personalities for commentary
AI_PERSONALITIES = {
    "Grandmaster": "You are a chess grandmaster providing deep strategic analysis. Focus on long-term plans and positional understanding.",
    "Coach": "You are a friendly chess coach. Explain ideas simply and point out learning opportunities.",
    "Aggressive Player": "You are an attacking player who loves sacrifices. Focus on tactical opportunities and attacking chances.",
    "Defensive Expert": "You are a defensive specialist. Focus on prophylaxis and maintaining solid positions."
}

def get_position_analysis(fen):
    """Generate a position analysis prompt for the AI"""
    return f"""Analyze this chess position (FEN: {fen}). Consider:
1. Material balance
2. Piece activity
3. Pawn structure
4. King safety
5. Potential plans for both sides
Provide a concise but insightful analysis."""

def get_chat_response(client, messages, personality="Grandmaster"):
    """Get response from OpenAI with selected personality"""
    system_message = {"role": "system", "content": AI_PERSONALITIES[personality]}
    full_messages = [system_message] + messages
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=full_messages,
        temperature=0.7,
        max_tokens=150
    )
    return response.choices[0].message.content

def save_game(board, messages):
    """Save the current game state to a file"""
    game_data = {
        "fen": board.fen(),
        "pgn": str(board),
        "messages": messages,
        "timestamp": datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    }
    return json.dumps(game_data)

def load_game(game_data):
    """Load a game from saved data"""
    data = json.loads(game_data)
    board = chess.Board(data["fen"])
    return board, data["messages"]

def get_move_history(board):
    """Generate a formatted move history"""
    moves = []
    for i, move in enumerate(board.move_stack):
        if i % 2 == 0:
            moves.append(f"{i//2 + 1}. {board.san(move)}")
        else:
            moves[-1] += f" {board.san(move)}"
    return " ".join(moves)

# Initialize the Streamlit interface
st.title("Enhanced Chess Assistant")

# Initialize session state
if 'board' not in st.session_state:
    st.session_state.board = chess.Board()
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'openai_client' not in st.session_state:
    st.session_state.openai_client = init_openai()
if 'fen' not in st.session_state:
    st.session_state.fen = st.session_state.board.fen()
if 'personality' not in st.session_state:
    st.session_state.personality = "Grandmaster"

# Sidebar for controls and info
with st.sidebar:
    st.subheader("Game Controls")
    
    # AI Personality selector
    st.session_state.personality = st.selectbox(
        "Select AI Personality",
        list(AI_PERSONALITIES.keys())
    )
    
    # Save/Load game
    if st.button("Save Game"):
        game_data = save_game(st.session_state.board, st.session_state.messages)
        st.download_button(
            "Download Game",
            game_data,
            file_name=f"chess_game_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    uploaded_file = st.file_uploader("Load Game", type="json")
    if uploaded_file is not None:
        game_data = uploaded_file.read().decode()
        st.session_state.board, st.session_state.messages = load_game(game_data)
        st.session_state.fen = st.session_state.board.fen()
        st.experimental_rerun()
    
    # Move history
    st.subheader("Move History")
    st.text(get_move_history(st.session_state.board))

# Main board and chat area
col1, col2 = st.columns([2, 1])

with col1:
    # Interactive chess board using stchess
    board_result = board(
        color="white",  # Default to white perspective
        fen=st.session_state.fen,
        key="board"
    )
    
    # Handle moves
    if board_result and 'move' in board_result:
        try:
            move = board_result['move']
            chess_move = chess.Move.from_uci(move)
            
            if chess_move in st.session_state.board.legal_moves:
                st.session_state.board.push(chess_move)
                st.session_state.fen = st.session_state.board.fen()
                
                # Get position analysis
                analysis_prompt = get_position_analysis(st.session_state.fen)
                st.session_state.messages.append(
                    {"role": "user", "content": f"I played {move}. {analysis_prompt}"}
                )
                
                # Get AI response with current personality
                response = get_chat_response(
                    st.session_state.openai_client,
                    st.session_state.messages,
                    st.session_state.personality
                )
                st.session_state.messages.append(
                    {"role": "assistant", "content": response}
                )
                
                st.experimental_rerun()
            else:
                st.error("Invalid move! Please try again.")
        except ValueError:
            st.error("Invalid move format! Please try again.")

with col2:
    # Game status
    if st.session_state.board.is_checkmate():
        st.success("Checkmate!")
    elif st.session_state.board.is_stalemate():
        st.info("Stalemate!")
    elif st.session_state.board.is_check():
        st.warning("Check!")
    
    # Position info
    st.subheader("Position Information")
    material_count = {
        'P': len(st.session_state.board.pieces(chess.PAWN, chess.WHITE)),
        'p': len(st.session_state.board.pieces(chess.PAWN, chess.BLACK)),
        'N': len(st.session_state.board.pieces(chess.KNIGHT, chess.WHITE)),
        'n': len(st.session_state.board.pieces(chess.KNIGHT, chess.BLACK)),
        'B': len(st.session_state.board.pieces(chess.BISHOP, chess.WHITE)),
        'b': len(st.session_state.board.pieces(chess.BISHOP, chess.BLACK)),
        'R': len(st.session_state.board.pieces(chess.ROOK, chess.WHITE)),
        'r': len(st.session_state.board.pieces(chess.ROOK, chess.BLACK)),
        'Q': len(st.session_state.board.pieces(chess.QUEEN, chess.WHITE)),
        'q': len(st.session_state.board.pieces(chess.QUEEN, chess.BLACK))
    }
    st.write("Material Balance:", material_count)
    
    # Reset button
    if st.button("Reset Game"):
        st.session_state.board = chess.Board()
        st.session_state.fen = st.session_state.board.fen()
        st.session_state.messages = []
        st.experimental_rerun()

# Chat history
st.subheader("Analysis & Commentary")
for i, msg in enumerate(st.session_state.messages):
    if msg["role"] == "user":
        message(msg["content"], is_user=True, key=f"msg_{i}")
    else:
        message(msg["content"], is_user=False, key=f"msg_{i}")
