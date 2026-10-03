import re
import time
import warnings
import requests
import chromadb
from bs4 import BeautifulSoup
from functools import lru_cache
from sentence_transformers import SentenceTransformer

warnings.filterwarnings("ignore")

HEADERS = {"User-Agent": "TradingAgents Research Pipeline (your_real_email@example.com)"}
COLLECTION = "sec_filings"
CHUNK_SIZE = 800      # chars; stays under MiniLM's ~256 token limit
CHUNK_OVERLAP = 100

chroma_client = chromadb.HttpClient(host="localhost", port=8000)

print("Loading embedding model (this may take a moment on first run)...")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


def _get(url: str) -> requests.Response:
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    time.sleep(0.2)  # SEC allows max ~10 requests/second
    return resp


@lru_cache(maxsize=1)
def _ticker_map() -> dict:
    data = _get("https://www.sec.gov/files/company_tickers.json").json()
    return {v["ticker"].upper(): str(v["cik_str"]).zfill(10) for v in data.values()}


def get_cik(ticker: str):
    return _ticker_map().get(ticker.upper())


def _chunk(text: str) -> list[str]:
    step = CHUNK_SIZE - CHUNK_OVERLAP
    return [text[i:i + CHUNK_SIZE] for i in range(0, len(text), step) if text[i:i + CHUNK_SIZE].strip()]


def _filing_text(cik: str, accession: str, primary_doc: str) -> str:
    url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}/{primary_doc}"
    soup = BeautifulSoup(_get(url).text, "lxml")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return re.sub(r"\s+", " ", soup.get_text(" ")).strip()


def build_sec_vector_db(ticker: str, max_filings: int = 2):
    """Ingest the latest 10-K/10-Q filings (full text) plus a filing-history summary."""
    ticker = ticker.upper()
    print(f"\nFetching SEC EDGAR data for {ticker}...")
    cik = get_cik(ticker)
    if not cik:
        print(f"Could not find SEC CIK for {ticker}.")
        return

    recent = _get(f"https://data.sec.gov/submissions/CIK{cik}.json").json()["filings"]["recent"]
    collection = chroma_client.get_or_create_collection(name=COLLECTION)

    docs, ids, metas = [], [], []

    # (a) Filing-history chunks (what you had before), now with metadata
    for i in range(min(25, len(recent["accessionNumber"]))):
        docs.append(
            f"On {recent['filingDate'][i]}, {ticker} filed a {recent['form'][i]} document."
        )
        ids.append(f"{ticker}_{recent['accessionNumber'][i]}_meta")
        metas.append({"ticker": ticker, "form": recent["form"][i],
                      "date": recent["filingDate"][i], "type": "history"})

    # (b) Full text of the most recent 10-K / 10-Q filings
    taken = 0
    for i, form in enumerate(recent["form"]):
        if form not in ("10-K", "10-Q") or taken >= max_filings:
            continue
        acc, doc, date = recent["accessionNumber"][i], recent["primaryDocument"][i], recent["filingDate"][i]
        print(f"  Downloading {form} filed {date}...")
        try:
            chunks = _chunk(_filing_text(cik, acc, doc))
        except Exception as e:
            print(f"  Skipped {acc}: {e}")
            continue
        for n, c in enumerate(chunks):
            docs.append(f"[{ticker} {form} filed {date}] {c}")
            ids.append(f"{ticker}_{acc}_{n}")
            metas.append({"ticker": ticker, "form": form, "date": date, "type": "text"})
        taken += 1

    print(f"Embedding {len(docs)} chunks into ChromaDB...")
    for s in range(0, len(docs), 100):  # batch to stay within Chroma limits
        batch = docs[s:s + 100]
        collection.upsert(
            documents=batch,
            embeddings=embedding_model.encode(batch).tolist(),
            ids=ids[s:s + 100],
            metadatas=metas[s:s + 100],
        )
    print("SEC Vector Database built successfully!")


def query_sec_database(ticker: str, query: str, n_results: int = 4) -> str:
    try:
        collection = chroma_client.get_collection(name=COLLECTION)
    except Exception:
        return f"SEC database not built yet. Run build_sec_vector_db('{ticker}') first."

    results = collection.query(
        query_embeddings=embedding_model.encode([query]).tolist(),
        n_results=n_results,
        where={"ticker": ticker.upper()},   # only this company's filings
    )
    if results["documents"] and results["documents"][0]:
        return "\n\n".join(results["documents"][0])
    return f"No relevant SEC filings found for {ticker}."


if __name__ == "__main__":
    build_sec_vector_db("AAPL")
    q = "What risks does Apple highlight in its most recent annual report?"
    print(f"\nQuery: {q}\n")
    print(query_sec_database("AAPL", q))