# Interactive Chess Assistant

An interactive chess application built with Streamlit featuring AI-powered analysis, multiple AI personalities, and comprehensive game management features.

## Features

- 🎮 Interactive chess board with drag-and-drop functionality
- 🤖 AI analysis powered by GPT-4
- 👥 Multiple AI personalities (Grandmaster, Coach, Aggressive Player, Defensive Expert)
- 📊 Position analysis and material balance
- 💾 Save and load game functionality
- 📝 Move history tracking
- ⚡ Real-time game state indicators

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/chess-assistant.git
cd chess-assistant
```

2. Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Set up your OpenAI API key:
   - Create a `.streamlit` folder in your project directory
   - Create a `secrets.toml` file inside the `.streamlit` folder
   - Add your OpenAI API key:
     ```toml
     OPENAI_API_KEY = "your-api-key-here"
     ```

## Usage

1. Start the application:
```bash
streamlit run app.py
```

2. Open your web browser and navigate to `http://localhost:8501`

3. Play chess and get AI analysis:
   - Make moves by dragging and dropping pieces
   - View AI analysis in the chat window
   - Change AI personalities using the sidebar
   - Save/load games as needed

## Project Structure

```
chess-assistant/
├── app.py                 # Main application file
├── .streamlit/
│   ├── config.toml       # Streamlit configuration
│   └── secrets.toml      # API keys (not in version control)
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## AI Personalities

- **Grandmaster**: Provides deep strategic analysis and long-term plans
- **Coach**: Offers educational insights and learning opportunities
- **Aggressive Player**: Focuses on tactical opportunities and attacking chances
- **Defensive Expert**: Emphasizes prophylaxis and solid positioning

## Game Management

- Save games as JSON files with complete move history and analysis
- Load previously saved games to continue analysis
- Track material balance and position evaluation
- View complete move history in standard chess notation

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/improvement`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/improvement`)
5. Create a Pull Request

## References

- [PG Mentor](https://www.pgnmentor.com/files.html)
