import os
import pymysql
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey

load_dotenv(override=True)

DB_USER     = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD")          # no default: fail loudly if missing
DB_HOST     = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT     = int(os.getenv("DB_PORT", "3307"))  # trading_mysql is mapped to 3307
DB_NAME     = os.getenv("DB_NAME", "trading_state")

if not DB_PASSWORD:
    raise RuntimeError("DB_PASSWORD is not set. Add it to your .env file.")


# 1. Ensure the database exists
def ensure_database():
    conn = None
    try:
        conn = pymysql.connect(
            host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD,
            charset="utf8mb4",
        )
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        conn.commit()
    except Exception as e:
        print("DB init failed:", e)
        raise
    finally:
        if conn:
            conn.close()


ensure_database()


# 2. SQLAlchemy engine (URL.create handles special characters like '#')
engine = create_engine(
    URL.create(
        drivername="mysql+pymysql",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        query={"charset": "utf8mb4"},
    ),
    echo=False,
    pool_pre_ping=True,
    pool_recycle=3600,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# 3. Models
class Portfolio(Base):
    __tablename__ = 'portfolio'
    id            = Column(Integer, primary_key=True)
    cash_balance  = Column(Float, default=100000.0)
    total_equity  = Column(Float, default=100000.0)

class Position(Base):
    __tablename__ = 'positions'
    ticker           = Column(String(10), primary_key=True)
    allocation_value = Column(Float, default=0.0)

def setup_mock_portfolio():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        if not db.query(Portfolio).first():
            db.add(Portfolio(id=1, cash_balance=100000.0, total_equity=100000.0))
            db.commit()
            print("Mock portfolio initialized with $100,000.")

def evaluate_risk(proposal: dict) -> dict:
    setup_mock_portfolio()

    ticker     = proposal.get('ticker', '')
    action     = proposal.get('action', 'HOLD')
    confidence = proposal.get('confidence', 0.0)

    with SessionLocal() as db:
        portfolio = db.query(Portfolio).first()
        position  = db.query(Position).filter(Position.ticker == ticker).first()

        if portfolio is None:
            return {"status": "REJECTED", "reason": "Portfolio not initialized."}

        current_alloc = position.allocation_value if position else 0.0
        max_alloc     = portfolio.total_equity * 0.02

        if action in ["BUY", "SELL"] and confidence < 0.60:
            return {"status": "REJECTED", "reason": f"Confidence ({confidence:.2f}) too low."}

        if action == "BUY":
            if current_alloc >= max_alloc:
                return {"status": "REJECTED", "reason": f"2% limit reached for {ticker}."}
            return {"status": "APPROVED", "reason": "BUY approved. Under $2,000 limit."}

        if action == "SELL":
            if current_alloc <= 0:
                return {"status": "REJECTED", "reason": f"No open position for {ticker}."}
            return {"status": "APPROVED", "reason": "SELL approved."}

        return {"status": "APPROVED", "reason": "HOLD requires no capital action."}

if __name__ == "__main__":
    mock_proposal = {"ticker": "AAPL", "action": "BUY", "confidence": 0.85}
    print(evaluate_risk(mock_proposal))