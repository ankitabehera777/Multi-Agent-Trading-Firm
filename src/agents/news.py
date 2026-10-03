import chromadb
from chromadb.utils import embedding_functions
from src.agents.schemas import NewsReport
from src.agents.llm_client import generate_structured_analysis

class NewsAnalyst:
    def __init__(self):
        self.chroma_client = chromadb.HttpClient(host='localhost', port=8000)
        
        # Use the same robust model for querying that we used for ingestion
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        
        # Connect to our new v2 collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="financial_news_v2",
            embedding_function=self.embedding_fn
        )
        
        self.system_prompt = """
        You are an expert fundamental news analyst.
        Analyze the provided news context for a given asset.
        Determine the overall sentiment score (-1.0 to 1.0), extract key fundamental themes, and provide a concise summary.
        Do not hallucinate facts outside the provided context.
        """

    def analyze(self, ticker: str) -> NewsReport:
        # Query ChromaDB for the most relevant recent news on this ticker
        results = self.collection.query(
            query_texts=[f"Financial news and updates regarding {ticker}"],
            n_results=10
        )

        documents = results.get("documents", [[]])[0]
        
        if not documents:
            context = f"No recent news found in the database for {ticker}."
        else:
            context = "\n".join([f"- {doc}" for doc in documents])

        user_prompt = f"Analyze the following recent news context for {ticker}:\n\n{context}\n\nGenerate the news report."

        # The Groq LLM will strictly return a NewsReport Pydantic object
        report = generate_structured_analysis(self.system_prompt, user_prompt, NewsReport)
        return report

if __name__ == "__main__":
    print("Running News Analyst...")
    analyst = NewsAnalyst()
    try:
        report = analyst.analyze("AAPL")
        
        print("\n--- News Report Output ---")
        print(f"Sentiment Score: {report.sentiment_score}")
        print(f"Key Themes: {report.key_themes}")
        print(f"Summary: {report.summary}")
    except Exception as e:
        print(f"Error: {e}")