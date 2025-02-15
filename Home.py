import streamlit as st

# Page title and main header
st.title("AI Chess Assistant Platform")

# Introduction section
st.header("Welcome to Our Chess AI Platform")
st.write("""
Our platform offers two main features to help chess players and enthusiasts interact with chess data 
in a more intuitive and accessible way:
""")

# Features section with two columns
col1, col2 = st.columns(2)

with col1:
    st.subheader("🎮 Chess Buddy")
    st.write("""
    An interactive AI chess partner that:
    - Plays chess with you while providing explanations
    - Makes the game fun with chess-related puns and jokes
    - Helps you understand different moves and strategies
    - Offers a casual, educational gaming experience
    """)

with col2:
    st.subheader("📊 Player Analysis")
    st.write("""
    A powerful analysis tool that:
    - Analyzes chess games and playing styles
    - Provides insights from chess databases
    - Helps identify patterns and improvements
    - Offers personalized recommendations
    """)

# Why we created this section
st.header("Why We Created AI Chess Agent")
st.write("""
### The Challenge
Traditional chess databases and analysis tools have several limitations:
- Expensive software requirements (like ChessBase)
- Complex manual command inputs
- Rigid search parameters
- Limited accessibility for casual users

### Our Solution
We're revolutionizing chess analysis by:
1. Making chess data accessible through natural language interaction
2. Eliminating the need for complex manual commands
3. Providing intuitive access to chess insights
4. Creating an AI-powered interface that understands chess context

### Who Can Benefit
- Chess players of all levels
- Chess teachers and coaches
- Students learning the game
- Anyone interested in chess analysis
""")

# Additional context about the technology
st.header("How It Works")
st.write("""
Our platform combines the power of:
- Advanced Language Models (ChatGPT)
- Traditional chess databases (PGN format)
- Custom AI agents trained for specific chess-related tasks

This creates an intuitive interface that understands chess context and can provide 
relevant insights without requiring technical expertise in database management.
""")

# Call to action
st.markdown("""
---
👈 Select a feature from the sidebar to get started!
""")
