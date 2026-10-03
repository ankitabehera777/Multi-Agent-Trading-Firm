import chromadb
import json
from datetime import datetime
from sentence_transformers import SentenceTransformer
import warnings

warnings.filterwarnings("ignore")

# Connect to your existing ChromaDB Docker container
chroma_client = chromadb.HttpClient(host='localhost', port=8000)
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def save_trade_memory(ticker: str, action: str, reasoning: str):
    """Saves a completed trade decision into the vector database."""
    collection = chroma_client.get_or_create_collection(name="trade_journal")
    
    # Generate a unique ID using the ticker and current time
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    memory_id = f"{ticker}_{timestamp}"
    
    # The document is the semantic text the agent will search against
    document = f"Previous Decision: {action} on {ticker}. Context and Reasoning: {reasoning}"
    
    metadata = {
        "ticker": ticker,
        "action": action,
        "date": timestamp
    }
    
    embedding = embedding_model.encode([document]).tolist()
    
    collection.upsert(
        documents=[document],
        embeddings=embedding,
        metadatas=[metadata],
        ids=[memory_id]
    )
    print(f"--- Memory Logged: {action} on {ticker} saved to ChromaDB Journal ---")

def retrieve_past_trades(ticker: str, current_market_context: str) -> str:
    """Retrieves similar past trades to guide current decisions."""
    collection = chroma_client.get_or_create_collection(name="trade_journal")
    
    if collection.count() == 0:
        return "No past trading memories found in the journal."
        
    query_embedding = embedding_model.encode([current_market_context]).tolist()
    
    # Query ChromaDB for past trades, filtering strictly for the current ticker
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=2,
        where={"ticker": ticker} 
    )
    
    if results['documents'] and results['documents'][0]:
        memories = "\n".join(results['documents'][0])
        return f"Past Trading Memories for {ticker}:\n{memories}"
        
    return f"No relevant past trades found for {ticker}."

if __name__ == "__main__":
    # Test saving and retrieving a memory
    save_trade_memory(
        ticker="AAPL", 
        action="HOLD", 
        reasoning="Strong fundamentals are offset by a delayed product launch and antitrust regulatory risks."
    )
    
    print("\nRetrieving Memory:")
    print(retrieve_past_trades("AAPL", "Apple is facing antitrust lawsuits but has good margins."))