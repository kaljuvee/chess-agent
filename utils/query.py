import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from datetime import datetime
import argparse
import os
from openai import OpenAI
from utils.embeddings_util import load_all_metadata, load_embeddings_and_index
from dotenv import load_dotenv
from typing import Union

# Load environment variables
load_dotenv()

def format_game_with_llm(game_text: str, client: OpenAI) -> str:
    """Use OpenAI to format and analyze a chess game"""
    model = os.getenv('MODEL', 'gpt-3.5-turbo')  # Fallback to gpt-3.5-turbo if not specified
    
    prompt = """
    Analyze and format this chess game. Extract key information and provide:
    1. Basic game details (Event, Date, Players, Result, ECO)
    2. A brief description of the game's key moments or strategic themes
    3. Format the output in a clear, readable way
    
    Chess game:
    {game_text}
    """.format(game_text=game_text)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a chess expert analyzing games."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=500
    )
    
    return response.choices[0].message.content

def search_games(query: str, client: OpenAI = None, num_results: int = 5, dataset_id: str = None, return_str: bool = False) -> Union[None, str]:
    """Search chess games using semantic search and analyze with OpenAI
    Args:
        query: Search query string
        client: OpenAI client (optional - will create new one if None)
        num_results: Number of results to return
        dataset_id: Specific dataset to search
        return_str: If True, returns formatted string for web UI, else prints to console
    """
    # Initialize OpenAI client if not provided (CLI usage)
    if client is None:
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        if not client.api_key:
            msg = "Error: OPENAI_API_KEY environment variable not set"
            return msg if return_str else print(msg)

    # Load metadata
    all_metadata = load_all_metadata()
    if not all_metadata:
        msg = "No embeddings found. Please run create_index.py first."
        return msg if return_str else print(msg)
    
    # Use specified dataset or first available
    metadata = next((m for m in all_metadata if m['dataset_id'] == dataset_id), all_metadata[0])
    
    # Load embeddings and index
    embeddings, index, processed_documents, model_name = load_embeddings_and_index(metadata)
    if not all([embeddings, index, processed_documents, model_name]):
        msg = "Failed to load embeddings. Please check the embeddings directory."
        return msg if return_str else print(msg)
    
    if not return_str:
        print(f"Using embedding model: {model_name}")
        print(f"Using LLM model: {os.getenv('MODEL', 'gpt-3.5-turbo')}")
    
    # Load model and encode query
    model = SentenceTransformer(model_name)
    query_embedding = model.encode([query])[0]
    
    # Search using Faiss
    D, I = index.search(query_embedding.reshape(1, -1), num_results)
    
    # Format results
    results = []
    for idx, (distance, doc_idx) in enumerate(zip(D[0], I[0]), 1):
        formatted_game = format_game_with_llm(processed_documents[doc_idx], client)
        results.append(f"Game {idx} (similarity: {1-distance:.2f})\n{formatted_game}")
    
    # For CLI output
    if not return_str:
        print(f"\nSearch Results:\n")
        print("\n".join(results))
        print("-" * 80 + "\n")
        return None
        
    # For web UI output - generate conversational summary
    combined_results = "\n\n".join(results)
    summary_prompt = f"""
    Based on these chess games:
    {combined_results}
    
    Provide a concise, conversational response that:
    1. Summarizes the key findings
    2. Highlights interesting patterns or insights
    3. Uses a friendly, engaging tone
    4. Keeps the response focused and relevant to the original query: "{query}"
    """
    
    response = client.chat.completions.create(
        model=os.getenv('MODEL', 'gpt-3.5-turbo'),
        messages=[
            {"role": "system", "content": "You are a helpful chess analysis assistant providing insights about games."},
            {"role": "user", "content": summary_prompt}
        ],
        temperature=0.7
    )
    
    return response.choices[0].message.content

def main():
    predefined_queries = [
        "Shabalov's victories as White in major tournaments",
        "Games from World Senior Championships with tactical combinations",
        "Interesting games from Jurmala tournament in 1985",
        "Games where Shabalov defeated higher-rated opponents",
        "Quick victories in less than 25 moves",
        "Notable games with the Sicilian Defense",
        "Tournament games that ended in dramatic draws",
        "Games featuring interesting endgame techniques",
        "Exit"
    ]
    
    while True:
        print("\nChess Game Search Menu:")
        print("----------------------")
        for i, query in enumerate(predefined_queries, 1):
            print(f"{i}. {query}")
        
        try:
            choice = input("\nEnter choice number or type your own search query: ").strip()
            
            if choice.lower() == 'exit' or choice == str(len(predefined_queries)):
                print("Goodbye!")
                break
                
            if choice.isdigit() and 1 <= int(choice) <= len(predefined_queries):
                query = predefined_queries[int(choice) - 1]
            else:
                query = choice
            
            num_results = 5  # Default number of results
            dataset_id = None  # Default dataset
            
            print(f"\nSearching for: {query}")
            search_games(query, num_results=num_results, dataset_id=dataset_id)
            
            continue_search = input("\nPress Enter to continue or 'exit' to quit: ")
            if continue_search.lower() == 'exit':
                print("Goodbye!")
                break
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            continue

if __name__ == "__main__":
    main()
