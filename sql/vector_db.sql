-- 1. First, install the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Create a table to store your embeddings
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(1536)  -- Adjust dimension based on your embedding model
);

-- 3. Insert an example document with its embedding
INSERT INTO documents (content, embedding)
VALUES (
    'Example document text',
    '[0.1, 0.2, 0.3, ...]'::vector  -- Replace with actual embedding values
);

-- 4. Create an index for faster similarity search
-- Choose one based on your needs:

-- Option A: IVFFlat index (faster build, good for frequent updates)
CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);  -- Number of lists, adjust based on your data size

-- Option B: HNSW index (slower build, faster search)
CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);  -- Adjust parameters as needed

-- 5. Perform similarity search
-- Find the 5 most similar documents using cosine similarity
SELECT content, 
       1 - (embedding <=> query_embedding) as similarity
FROM documents
ORDER BY embedding <=> '[0.1, 0.2, 0.3, ...]'::vector
LIMIT 5;

-- 6. Alternative distance metrics
-- L2 distance (Euclidean)
SELECT * FROM documents ORDER BY embedding <-> query_embedding LIMIT 5;

-- Inner product
SELECT * FROM documents ORDER BY embedding <#> query_embedding LIMIT 5;

-- 7. Example with Python using psycopg2
import psycopg2
import numpy as np

def store_embedding(content: str, embedding: np.ndarray):
    conn = psycopg2.connect("dbname=your_db user=your_user password=your_password")
    cur = conn.cursor()
    
    # Convert numpy array to string representation
    embedding_str = '[' + ','.join(map(str, embedding)) + ']'
    
    cur.execute("""
        INSERT INTO documents (content, embedding)
        VALUES (%s, %s::vector)
    """, (content, embedding_str))
    
    conn.commit()
    cur.close()
    conn.close()

def find_similar(query_embedding: np.ndarray, limit: int = 5):
    conn = psycopg2.connect("dbname=your_db user=your_user password=your_password")
    cur = conn.cursor()
    
    embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
    
    cur.execute("""
        SELECT content, 1 - (embedding <=> %s::vector) as similarity
        FROM documents
        ORDER BY embedding <=> %s::vector
        LIMIT %s
    """, (embedding_str, embedding_str, limit))
    
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results