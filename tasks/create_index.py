import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
import faiss
from typing import List, Dict
import pickle
import json
import os
import uuid
from datetime import datetime
import glob
import chess.pgn
import io

# Load environment variables and set up OpenAI client
load_dotenv()
client = OpenAI()

# Define constants
EMBEDDING_MODEL = "text-embedding-3-large"
MAX_TOKENS_PER_CHUNK = 6000  # text-embedding-3-large has 8k limit, leaving some headroom
WORDS_PER_TOKEN = 0.75  # approximate ratio for English text

def chunk_text(text: str) -> List[str]:
    """Chunk text dynamically based on length while maintaining context.
    Estimates token count using word count and adjusts chunk size accordingly."""
    words = text.split()
    total_words = len(words)
    
    # Estimate optimal chunk size (in words) based on text length
    estimated_tokens = total_words / WORDS_PER_TOKEN
    if estimated_tokens <= MAX_TOKENS_PER_CHUNK:
        return [text]  # No chunking needed
        
    # For longer texts, use chunks of about 4000 tokens (3000 words) with 100 word overlap
    chunk_size = 3000
    overlap = 100
    
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        chunks.append(chunk)
    return chunks

def load_pgn_files() -> List[Dict[str, str]]:
    documents = []
    pgn_files = glob.glob('data/*.pgn')
    total_games = 0
    
    for pgn_file in pgn_files:
        print(f"Processing {pgn_file}...")
        # Try different encodings
        for encoding in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
            try:
                with open(pgn_file, 'r', encoding=encoding) as f:
                    content = f.read()
                    games = content.split('\n\n[')  # Split into individual games
                    game_count = 0
                    batch_size = 100  # Process 100 games at a time
                    
                    for game in games:
                        if not game.strip():
                            continue
                            
                        game_count += 1
                        if game_count % batch_size == 0:
                            print(f"Processed {game_count} games from {pgn_file}")
                            
                        if not game.startswith('['):
                            game = '[' + game
                        
                        # Parse the PGN game
                        pgn = io.StringIO(game)
                        try:
                            chess_game = chess.pgn.read_game(pgn)
                            if chess_game is None:
                                continue
                            
                            # Extract relevant information
                            headers = dict(chess_game.headers)
                            moves = ' '.join(move.uci() for move in chess_game.mainline_moves())
                            
                            # Create a richer description combining headers and moves
                            description = (
                                f"Event: {headers.get('Event', 'Unknown')} "
                                f"Site: {headers.get('Site', 'Unknown')} "
                                f"Date: {headers.get('Date', 'Unknown')} "
                                f"White: {headers.get('White', 'Unknown')} "
                                f"Black: {headers.get('Black', 'Unknown')} "
                                f"Result: {headers.get('Result', 'Unknown')} "
                                f"ECO: {headers.get('ECO', 'Unknown')} "
                                f"Moves: {moves}"
                            )
                            
                            documents.append({
                                'description': description,
                                'source': os.path.basename(pgn_file)
                            })
                        except Exception as e:
                            print(f"Error parsing game in {pgn_file}: {str(e)}")
                            continue
                            
                    total_games += game_count
                    print(f"Successfully processed {game_count} games from {pgn_file} with {encoding} encoding")
                    break
                    
            except UnicodeDecodeError:
                if encoding == 'cp1252':  # Last encoding we try
                    print(f"Failed to read {pgn_file} with any encoding")
                continue
                    
    print(f"Total games processed across all files: {total_games}")
    print(f"Total documents created: {len(documents)}")
    return documents

def chunk_documents(documents: List[Dict[str, str]]) -> List[Dict[str, str]]:
    chunked_documents = []
    # Add deduplication to avoid nearly identical chunks
    seen_chunks = set()
    
    for doc in documents:
        chunks = chunk_text(doc['description'])
        for chunk in chunks:
            # Only add chunk if it's sufficiently different
            chunk_normalized = ' '.join(chunk.split())  # Remove extra whitespace
            if chunk_normalized not in seen_chunks:
                seen_chunks.add(chunk_normalized)
                chunked_documents.append({
                    'description': chunk,
                    'source': doc['source']
                })
    print(f"Reduced to {len(chunked_documents)} unique chunks from {len(documents)} documents")
    return chunked_documents

def create_embeddings(docs: List[Dict[str, str]]):
    embeddings = []
    total = len(docs)
    
    print(f"Creating embeddings for {total} documents...")
    for i, doc in enumerate(docs, 1):
        if i % 100 == 0:  # Show progress every 100 documents
            print(f"Processing document {i}/{total}")
            
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=doc['description']
        )
        embeddings.append(response.data[0].embedding)
    return np.array(embeddings)

def create_faiss_index(embeddings: np.ndarray):
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    return index

def save_metadata(embedding_model, index_id):
    """Save metadata with consistent filename format"""
    metadata = {
        "dataset_id": index_id,  # Add dataset_id field
        "embedding_model": embedding_model,
        "index_id": index_id,
        "creation_date": datetime.now().isoformat(),
        # Add file paths to help with loading
        "files": {
            "embeddings": f"embeddings/embeddings_{index_id}.pkl",
            "index": f"embeddings/index_{index_id}.bin",
            "documents": f"embeddings/processed_documents_{index_id}.pkl"
        }
    }
    
    # Use consistent metadata filename format
    metadata_path = f'embeddings/metadata_{index_id}.json'
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"Saved metadata to {metadata_path}")

def save_embeddings_and_index(embeddings, index, processed_documents, embedding_model):
    """Save embeddings, index, and documents with consistent naming"""
    os.makedirs('embeddings', exist_ok=True)
    index_id = str(uuid.uuid4())
    
    # Save embeddings
    embeddings_path = f'embeddings/embeddings_{index_id}.pkl'
    with open(embeddings_path, 'wb') as f:
        pickle.dump(embeddings, f)
    print(f"Saved embeddings to {embeddings_path}")
    
    # Save index
    index_path = f'embeddings/index_{index_id}.bin'
    faiss.write_index(index, index_path)
    print(f"Saved index to {index_path}")
    
    # Save processed documents
    documents_path = f'embeddings/processed_documents_{index_id}.pkl'
    with open(documents_path, 'wb') as f:
        pickle.dump(processed_documents, f)
    print(f"Saved processed documents to {documents_path}")
    
    # Save metadata
    save_metadata(embedding_model, index_id)
    
    print(f"All files saved successfully with index ID: {index_id}")
    return index_id

def main():
    # Load and process documents
    print("Loading PGN files...")
    documents = load_pgn_files()
    
    if not documents:
        print("No PGN files found in data directory!")
        return
    
    print(f"Loaded {len(documents)} games")
    
    # Process documents with chunking
    processed_documents = chunk_documents(documents)
    print(f"Created {len(processed_documents)} chunks")
    
    # Create embeddings
    print(f"Creating embeddings using {EMBEDDING_MODEL}...")
    embeddings = create_embeddings(processed_documents)
    print("Embeddings created successfully!")
    
    # Create FAISS index
    print("Creating index...")
    faiss_index = create_faiss_index(embeddings)
    print("Index created successfully!")
    
    # Save everything
    index_id = save_embeddings_and_index(
        embeddings,
        faiss_index,
        processed_documents,
        EMBEDDING_MODEL
    )
    
    return index_id

if __name__ == "__main__":
    main()
