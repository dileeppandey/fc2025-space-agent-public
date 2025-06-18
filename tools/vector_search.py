import json
from typing import Dict, Any, List, Optional
import weave
from tools.return_type import ToolResult
import concurrent.futures
import boto3
import os
import numpy as np
from botocore.exceptions import ClientError  # Added for error handling

_BEDROCK_CLIENT: boto3.client = boto3.client('bedrock-runtime', region_name="us-east-1")
EMBEDDING_MODEL = "amazon.titan-embed-text-v2:0"  # Updated to Titan V2
EMBEDDING_DIMENSION = 1024  # Titan V2 default dimension (supports 1024, 512, 256)
    
# In-memory store for the vector database
# Each entry will be a dict: {"text": str, "chunk_id": int, "embedding": np.ndarray}
_VECTOR_DATABASE_STORE: List[Dict[str, Any]] = []

VECTOR_SEARCH_TOOLS = {
    "encyclopedia_search": {
        "type": "function",
        "function": {
            "name": "vector_search-encyclopedia_search",
            "description": """
            Performs semantic search over encyclopedia data using vector embeddings.
            This tool enables searching through knowledge using semantic similarity rather than just keyword matching.
            It uses Amazon Titan V2 embeddings to understand the meaning and context of queries.
            """,
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The search query to find semantically similar content in the encyclopedia"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "The number of top matching results to return.",
                        "default": 5,
                        "max": 5
                    }
                },
                "required": ["message"]
            }
        }
    }
}

# Vector database cache filepath
VECTOR_DB_CACHE_FILE = "objects/datasets/embeddings.json"

def _save_embeddings():
    """Save embeddings to JSON file."""
    os.makedirs("vector_cache", exist_ok=True)
    # Convert numpy arrays to lists for JSON serialization
    data = []
    for entry in _VECTOR_DATABASE_STORE:
        data.append({
            "text": entry["text"],
            "chunk_id": entry["chunk_id"], 
            "embedding": entry["embedding"].tolist()
        })
    
    with open(VECTOR_DB_CACHE_FILE, 'w') as f:
        json.dump(data, f)
    print(f"Saved {len(data)} embeddings to {VECTOR_DB_CACHE_FILE}")

def _load_embeddings():
    """Load embeddings from JSON file."""
    global _VECTOR_DATABASE_STORE
    if not os.path.exists(VECTOR_DB_CACHE_FILE):
        return False
    
    with open(VECTOR_DB_CACHE_FILE, 'r') as f:
        data = json.load(f)
    
    # Convert lists back to numpy arrays
    _VECTOR_DATABASE_STORE = []
    for entry in data:
        _VECTOR_DATABASE_STORE.append({
            "text": entry["text"],
            "chunk_id": entry["chunk_id"],
            "embedding": np.array(entry["embedding"], dtype=np.float32)
        })
    
    print(f"Loaded {len(_VECTOR_DATABASE_STORE)} embeddings from {VECTOR_DB_CACHE_FILE}")
    return True

def initialize_or_load_vector_db(markdown_filepath: str, max_workers: int = 4, force_regenerate: bool = False) -> Dict[str, Any]:
    """Load from cache or generate new embeddings."""
    if not force_regenerate and _load_embeddings():
        return {"status": "loaded_from_cache", "total_entries": len(_VECTOR_DATABASE_STORE)}
    
    # Generate new embeddings
    result = initialize_vector_db_from_markdown(markdown_filepath, max_workers)
    if result["status"] == "success":
        _save_embeddings()
    return result

def _get_embedding(text: str) -> np.ndarray:
    """
    Get the embedding for a given text using Amazon Bedrock Titan Text Embeddings V2.
    """
    if _BEDROCK_CLIENT is None:
        raise RuntimeError("AWS Bedrock client not initialized. Please configure AWS credentials.")
    
    try:
        request_body = json.dumps({
            "inputText": text.strip(),
            "dimensions": EMBEDDING_DIMENSION,
            "normalize": True,
            "embeddingTypes": ["float"]
        })
        
        # Invoke the Bedrock model
        response = _BEDROCK_CLIENT.invoke_model(
            body=request_body,
            modelId=EMBEDDING_MODEL,
            accept="application/json",
            contentType="application/json"
        )
        
        # Parse the response
        response_body = json.loads(response.get('body').read())
        
        # Extract embedding vector from the response
        if 'embeddingsByType' in response_body and 'float' in response_body['embeddingsByType']:
            embedding_vector = response_body['embeddingsByType']['float']
        elif 'embedding' in response_body:
            embedding_vector = response_body['embedding']
        else:
            raise ValueError("No embedding found in Bedrock response")
        
        # Convert to numpy array and validate dimension
        final_embedding = np.array(embedding_vector, dtype=np.float32)
        
        if final_embedding.shape[0] != EMBEDDING_DIMENSION:
            raise ValueError(f"Embedding dimension {final_embedding.shape[0]} does not match expected dimension {EMBEDDING_DIMENSION}")
        
        return final_embedding
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"AWS Bedrock ClientError ({error_code}): {error_message}")
        raise
    except Exception as e:
        print(f"Error getting embedding for text '{text[:50]}...': {e}")
        raise

def _clear_vector_database() -> None:
    """Clears all entries from the in-memory vector database."""
    global _VECTOR_DATABASE_STORE
    _VECTOR_DATABASE_STORE = []
    print("In-memory vector database cleared.")

def _save_entry_to_vector_database(entry: Dict[str, Any]) -> None:
    """Saves a new entry to the in-memory vector database."""
    _VECTOR_DATABASE_STORE.append(entry)

def _process_chunk_for_embedding(chunk_text: str, markdown_filepath: str, chunk_id: int) -> Dict[str, Any]:
    """
    Processes a single chunk: generates an embedding and prepares data for storage.
    This function is designed to be called in parallel.
    """
    embedding_vector = _get_embedding(chunk_text)
    return {
        "text": chunk_text,
        "chunk_id": chunk_id,
        "embedding": embedding_vector
    }

def initialize_vector_db_from_markdown(markdown_filepath: str, max_workers: int = 4) -> Dict[str, Any]:
    """
    Initializes the vector database by reading a markdown file,
    chunking its content, generating embeddings in parallel,
    and storing them in-memory.
    """
    _clear_vector_database()
    try:
        with open(markdown_filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # User changed to split by '\n'
        chunks = [chunk.strip() for chunk in content.split('\n') if chunk.strip()]
        
        if not chunks:
            return {"status": "error", "message": "No content chunks found in the file."}

        total_chunks = len(chunks)
        print(f"Starting processing of {total_chunks} chunks from {markdown_filepath} using {EMBEDDING_MODEL}...")
        processed_count = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_chunk_data = {
                executor.submit(_process_chunk_for_embedding, chunk, markdown_filepath, i): i
                for i, chunk in enumerate(chunks)
            }
            
            for i, future in enumerate(concurrent.futures.as_completed(future_to_chunk_data)):
                chunk_index_in_original_list = future_to_chunk_data[future]
                try:
                    entry_data = future.result()
                    _save_entry_to_vector_database(entry_data)
                    processed_count += 1
                    if (i + 1) % 1 == 0 or (i + 1) == total_chunks:
                        print(f"Processed and embedded chunk {i + 1}/{total_chunks} (Original index: {chunk_index_in_original_list}) from {markdown_filepath}")
                except Exception as exc:
                    print(f'Chunk {chunk_index_in_original_list} from {markdown_filepath} generated an exception during processing/embedding: {exc}')
        
        print(f"Finished processing. Added {processed_count}/{total_chunks} chunks to the in-memory database.")
        return {"status": "success", "chunks_added": processed_count, "total_chunks_in_db": len(_VECTOR_DATABASE_STORE)}

    except FileNotFoundError:
        return {"status": "error", "message": f"File not found: {markdown_filepath}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to initialize vector DB: {str(e)}"}

def _cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Calculates cosine similarity between two numpy vectors."""
    # Handle edge case: if either vector has zero norm, return 0.0
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    # For normalized vectors, dot product = cosine similarity
    # For non-normalized vectors, we need to divide by the product of norms
    return np.dot(vec1, vec2) / (norm1 * norm2)

@weave.op(name="vector_search-encyclopedia_search")
def encyclopedia_search(*, message: str, top_k: int = 5) -> ToolResult[List[Dict[str, Any]]]:
    """
    Performs a lookup in the in-memory vector database using embeddings.
    """
    if not message or not isinstance(message, str):
        return ToolResult.err("Input message must be a non-empty string.")

    if top_k > 25:
        return ToolResult.err("No more than 25 results may be returned for a single query.")

    if not _VECTOR_DATABASE_STORE:
        return ToolResult.ok("Vector database is empty. Initialize it first.")

    try:
        # Get embedding for the search query
        query_embedding = _get_embedding(message)
        
        results_with_scores = []
        for entry in _VECTOR_DATABASE_STORE:
            stored_embedding = entry.get("embedding")
            if isinstance(stored_embedding, np.ndarray):
                similarity = _cosine_similarity(query_embedding, stored_embedding)
                
                result_entry = {
                    "text": entry["text"],
                    "chunk_id": entry["chunk_id"],
                    "score": similarity
                }
                results_with_scores.append(result_entry)
            else:
                print(f"Warning: Skipping entry due to missing or invalid embedding: {entry.get('chunk_id')}")

        # Sort results by similarity score in descending order
        top_results = sorted(results_with_scores, key=lambda x: x["score"], reverse=True)[:top_k]
        
        if not top_results:
            return ToolResult.ok_empty(f"No relevant information found for: '{message}'")
            
        return ToolResult.ok(top_results)
        
    except Exception as e:
        return ToolResult.err(f"An error occurred during vector search: {str(e)}")
