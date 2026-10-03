# Multi-Agent Trading Firm

[![Project Image](project-image-url)](project-image-url)

> A multi-agent system that mimics a trading firm: specialised agents gather market data and news, store knowledge in a vector database, and keep their records in MySQL.

---

### Table of Contents

- [Description](#description)
- [How To Use](#how-to-use)
- [References](#references)
- [License](#license)
- [Author Info](#author-info)

---

## Description

Multi-Agent Trading Firm is a Python project that models how a trading firm works by splitting the job across cooperating agents. Market prices come from Yahoo Finance and headlines from NewsAPI. Agent memory and embeddings live in ChromaDB, and structured data is persisted in a MySQL database. Both databases run in Docker, so the supporting infrastructure starts with a single command.

#### Key Features

- Market data collection with `yfinance` and `pandas`
- News ingestion through the NewsAPI client
- Vector memory for agents using ChromaDB
- Relational storage in MySQL through SQLAlchemy and PyMySQL
- Resilient API calls with automatic retries (`tenacity`) and response caching (`requests-cache`)
- One-command local infrastructure with Docker Compose

#### Technologies

- Python
- pandas
- yfinance
- newsapi-python
- ChromaDB
- SQLAlchemy and PyMySQL
- MySQL 8.0
- Docker and Docker Compose
- tenacity and requests-cache

[Back To The Top](#multi-agent-trading-firm)

---

## How To Use

#### Prerequisites

- Python 3.9 or higher
- [Docker](https://www.docker.com/) and Docker Compose
- A free [NewsAPI](https://newsapi.org/) key

#### Installation

1. Clone the repository

```bash
git clone https://github.com/ankitabehera777/Multi-Agent-Trading-Firm.git
cd Multi-Agent-Trading-Firm
```

2. Create and activate a virtual environment (optional but recommended)

```bash
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate
```

3. Install the dependencies

```bash
pip install -r requirements.txt
pip install python-dotenv     # used to load the .env file
```

4. Create a `.env` file in the project root

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=trading_firm
NEWS_API_KEY=your_newsapi_key
```

5. Start MySQL and ChromaDB

```bash
docker-compose up -d
```

This starts two containers:

| Service     | Container       | Port                      |
| ----------- | --------------- | ------------------------- |
| `mysql-db`  | `trading_mysql` | `DB_PORT` (maps to 3306)  |
| `chroma-db` | `trading_chroma`| `8000`                    |

Data is stored in the `mysql_data` and `chroma_data` Docker volumes, so it survives restarts.

6. Check the database connection

```bash
python test_dp.py
```

You should see `Login worked!` if the credentials in `.env` are correct.

#### Project Structure

```
Multi-Agent-Trading-Firm/
├── src/                 # Agent and application source code
├── docker-compose.yml   # MySQL and ChromaDB services
├── requirements.txt     # Python dependencies
├── test_dp.py           # Database connection check
└── .gitignore
```

#### API Reference

Stopping the infrastructure:

```bash
docker-compose down          # stop containers, keep data
docker-compose down -v       # stop containers and delete data
```

[Back To The Top](#multi-agent-trading-firm)

---

## References

- [yfinance](https://github.com/ranaroussi/yfinance)
- [NewsAPI](https://newsapi.org/docs)
- [ChromaDB](https://docs.trychroma.com/)
- [SQLAlchemy](https://docs.sqlalchemy.org/)
- [Docker Compose](https://docs.docker.com/compose/)


[Back To The Top](#multi-agent-trading-firm)

