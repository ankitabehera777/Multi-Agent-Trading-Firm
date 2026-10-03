Multi-Agent Trading Firm

A multi-agent system that mimics the structure of a trading firm. Specialised agents gather market data and news, store and retrieve context from a vector database, and persist results in a relational database to support trading research and decisions.


Features
Multi-agent architecture: separate agents for roles such as market data, news/sentiment, analysis, and decision-making (edit to match your agents)
Market data via yfinance
News ingestion via NewsAPI (newsapi-python)
Vector memory with ChromaDB for semantic retrieval of news and past analyses
Relational storage with MySQL (via SQLAlchemy + PyMySQL)
Resilient API calls using tenacity retries and requests-cache caching
One-command infrastructure with Docker Compose (MySQL + ChromaDB)
Architecture 1:
            ┌──────────────────────────────┐
            │        Agent Orchestrator     │
            └──────────────┬───────────────┘
      ┌──────────┬─────────┴────┬───────────┐
      ▼          ▼              ▼           ▼
 Market Data   News         Analysis    Decision /
   Agent       Agent         Agent      Risk Agent
 (yfinance)  (NewsAPI)
      │          │              │           │
      └──────────┴───────┬──────┴───────────┘
                         ▼
          ┌──────────────┴──────────────┐
          ▼                             ▼
     MySQL (8.0)                  ChromaDB
  structured data & logs      embeddings / memory


Architecture 1:       ┌──────────────────────┐
                      │    Input Ticker      │
                      └──────────┬───────────┘
                                 │
                                 ▼
                      ┌──────────────────────┐
                      │   SEC RAG Agent      │  <── ChromaDB (10-K / 10-Q Filings)
                      └──────────┬───────────┘
                                 │
                                 ▼
                      ┌──────────────────────┐
                      │  Memory Agent        │  <── ChromaDB (Trade Journal)
                      └──────────┬───────────┘
                                 │
                   ┌─────────────┴─────────────┐
                   ▼                           ▲
        ┌─────────────────────┐     ┌─────────────────────┐
        │     Bull Agent      │ ──> │     Bear Agent      │  (Adversarial Debate:
        └─────────────────────┘     └─────────────────────┘   Up to MAX_ROUNDS)
                   │
                   ▼ (After Max Debate Rounds)
        ┌─────────────────────────────────────────────────┐
        │                Head Trader Node                 │  ──> Synthesizes Arguments &
        └────────────────────────┬────────────────────────┘      Generates Structured JSON
                                 │
                                 ▼
        ┌─────────────────────────────────────────────────┐
        │            Risk Management Node                 │  <── MySQL (Portfolio DB)
        └────────────────────────┬────────────────────────┘
                                 │
                     ┌───────────┴───────────┐
                     ▼                       ▼
           [Approved: Execute]     [Rejected: Discard]
                     │
                     ▼
          (Save to Memory Journal)



Project Structure
Multi-Agent-Trading-Firm/
├── src/                  # Agent and application source code
├── docker-compose.yml    # MySQL and ChromaDB services
├── requirements.txt      # Python dependencies
├── test_dp.py            # Quick script to verify your MySQL connection
└── .gitignore
Prerequisites
Python 3.10+
Docker and Docker Compose
A free NewsAPI key
Getting Started
1. Clone the repository
bash
git clone https://github.com/ankitabehera777/Multi-Agent-Trading-Firm.git
cd Multi-Agent-Trading-Firm
2. Create a virtual environment and install dependencies
bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install python-dotenv       # used by test_dp.py to load .env
3. Configure environment variables

Create a .env file in the project root. Docker Compose reads the DB_* values from it:

env
# MySQL
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_secure_password
DB_NAME=trading_firm

# APIs
NEWSAPI_KEY=your_newsapi_key

.env should be listed in .gitignore. Never commit secrets.

4. Start the databases
bash
docker compose up -d

This starts:

Service	Container	Port	Purpose
MySQL 8.0	trading_mysql	${DB_PORT} → 3306	Structured data
ChromaDB	trading_chroma	8000	Vector store

Data persists in the named Docker volumes mysql_data and chroma_data.

5. Verify the database connection
bash
python test_dp.py

You should see Login worked!. If it fails, check that the container is running and that your .env values match.

6. Run the application
bash
python -m src.main    
Tech Stack
Area	Tools
Language	Python
Market data	yfinance, pandas
News	newsapi-python
Vector DB	ChromaDB
Relational DB	MySQL 8.0, SQLAlchemy, PyMySQL
Reliability	tenacity, requests-cache
Infrastructure	Docker, Docker Compose
Troubleshooting
NewsAPI rate limits: the free tier is limited; requests-cache helps avoid repeat calls.
