import chromadb
from chromadb.utils import embedding_functions
from duckduckgo_search import DDGS
from src.ingestion.cache_config import retry_with_backoff
from sentence_transformers import SentenceTransformer

class NewsIngestionClient:
    def __init__(self):
        # 1. Pre-download the model safely using the robust library directly
        print("Checking AI model... (This will download safely if missing)")
        SentenceTransformer("all-MiniLM-L6-v2")
        print("Model is ready!")

        self.chroma_client = chromadb.HttpClient(host='localhost', port=8000)
        
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        
        # 2. Use a NEW collection name to completely bypass the old corrupted settings
        self.collection = self.chroma_client.get_or_create_collection(
            name="financial_news_v2",
            embedding_function=self.embedding_fn
        )
        self.ddgs = DDGS()

    @retry_with_backoff()
    def fetch_and_embed_news(self, ticker: str):
        """Fetches free news via DuckDuckGo and embeds them into ChromaDB."""
        
        query = f"{ticker} stock financial news"
        
        # Using .text() to completely avoid the 403 Rate Limit block
        results = self.ddgs.text(query, max_results=10)
        
        if not results:
            print(f"No news found for {ticker}.")
            return

        documents = []
        metadatas = []
        ids = []

        for i, article in enumerate(results):
            content = f"{article.get('title', '')}. {article.get('body', '')}"
            documents.append(content)
            metadatas.append({
                "source": "Web Search",
                "ticker": ticker
            })
            ids.append(f"{ticker}_ddg_text_{i}")

        if documents:
            self.collection.upsert(documents=documents, metadatas=metadatas, ids=ids)
            print(f"Successfully embedded {len(documents)} free articles for {ticker}.")

if __name__ == "__main__":
    client = NewsIngestionClient()
    client.fetch_and_embed_news("AAPL")