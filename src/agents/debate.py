import time
import json
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
from src.agents.schemas import TradeProposal
from src.agents.llm_client import generate_structured_analysis
from src.agents.sec_rag import query_sec_database
from src.agents.risk_manager import evaluate_risk
from src.agents.memory import retrieve_past_trades, save_trade_memory

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
MAX_ROUNDS = 2            # number of full bull/bear rounds
RATE_LIMIT_SLEEP = 8      # seconds to pause before each LLM call
LLM_RETRIES = 3

class AgentState(TypedDict):
    ticker: str
    technical_data: str
    news_data: str
    fundamental_data: str
    sec_data: str
    memory_context: str         # NEW FIELD: stores retrieved past trades
    bull_argument: str
    bear_argument: str
    history: List[str]          # full debate transcript across all rounds
    round_count: int
    final_proposal: dict
    risk_assessment: dict

class Argument(BaseModel):
    reasoning: str = Field(
        description="The argument based on the data, citing which input "
                    "(Tech, News, Fundamentals, SEC) supports each claim."
    )

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def safe_analysis(sys_prompt: str, user_prompt: str, schema, retries: int = LLM_RETRIES):
    """Call the LLM with simple linear backoff so one failure doesn't kill the run."""
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            time.sleep(RATE_LIMIT_SLEEP)
            return generate_structured_analysis(sys_prompt, user_prompt, schema)
        except Exception as e:
            last_error = e
            wait = 10 * attempt
            print(f"  LLM call failed (attempt {attempt}/{retries}): {e}")
            if attempt < retries:
                print(f"  Retrying in {wait}s...")
                time.sleep(wait)
    raise RuntimeError(f"LLM call failed after {retries} attempts: {last_error}")

def market_context(state: AgentState) -> str:
    return (
        f"Ticker: {state['ticker']}\n"
        f"Tech: {state['technical_data']}\n"
        f"News: {state['news_data']}\n"
        f"Fundamentals: {state['fundamental_data']}\n"
        f"SEC Filings: {state['sec_data']}\n"
    )

# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------
def sec_agent(state: AgentState):
    print("--- SEC Agent Searching Filings ---")
    question = (
        "What are the key regulatory risks, pending lawsuits, or forward-looking "
        f"statements in the recent 10-K and 10-Q filings for {state['ticker']}?"
    )
    sec_context = query_sec_database(state["ticker"], question)
    return {"sec_data": sec_context}

def memory_agent(state: AgentState):
    print("--- Memory Agent Consulting Journal ---")
    # Build a context string to find semantically similar past trades
    context_str = market_context(state)
    memories = retrieve_past_trades(state['ticker'], context_str)
    return {"memory_context": memories}

def bull_agent(state: AgentState):
    print(f"--- Bull Agent Thinking (Round {state['round_count']}) ---")
    sys_prompt = (
        "You are a bullish financial analyst. Build the strongest data-backed case "
        "that the stock will go UP. If the bear has made an argument, acknowledge "
        "their strongest point and rebut it with evidence. Cite which input "
        "(Tech, News, Fundamentals, SEC) supports each claim."
    )
    user_prompt = (
        market_context(state)
        + f"Bear's previous argument: {state['bear_argument'] or 'None yet.'}"
    )
    response = safe_analysis(sys_prompt, user_prompt, Argument)
    return {
        "bull_argument": response.reasoning,
        "history": state["history"]
        + [f"BULL (round {state['round_count']}): {response.reasoning}"],
    }

def bear_agent(state: AgentState):
    print(f"--- Bear Agent Thinking (Round {state['round_count']}) ---")
    sys_prompt = (
        "You are a bearish financial analyst. Build the strongest data-backed case "
        "that the stock will go DOWN. Acknowledge the bull's strongest point, then "
        "dismantle it with evidence. Cite which input "
        "(Tech, News, Fundamentals, SEC) supports each claim."
    )
    user_prompt = market_context(state) + f"Bull's previous argument: {state['bull_argument']}"
    response = safe_analysis(sys_prompt, user_prompt, Argument)
    return {
        "bear_argument": response.reasoning,
        "round_count": state["round_count"] + 1,
        "history": state["history"]
        + [f"BEAR (round {state['round_count']}): {response.reasoning}"],
    }

def trader_agent(state: AgentState):
    print("--- Head Trader Making Decision ---")
    sys_prompt = (
        "You are the Head Trader. Review the technicals, news, fundamentals, SEC "
        "filings, past trading memories, and the full Bull/Bear debate. Weigh both sides "
        "objectively and make a final trading decision (BUY, SELL, or HOLD)."
    )
    # Inject past memories into the prompt alongside the debate history
    user_prompt = (
        market_context(state) 
        + f"Past Memories:\n{state['memory_context']}\n\n"
        + "Full debate:\n" 
        + "\n\n".join(state["history"])
    )
    proposal = safe_analysis(sys_prompt, user_prompt, TradeProposal)
    return {"final_proposal": proposal.model_dump()}

def risk_agent(state: AgentState):
    print("--- Risk Manager Enforcing Portfolio Limits ---")
    assessment = evaluate_risk(state["final_proposal"])
    
    # Automatically log approved trades to the ChromaDB journal to learn for next time
    if assessment.get("status") == "APPROVED":
        save_trade_memory(
            ticker=state["final_proposal"]["ticker"],
            action=state["final_proposal"]["action"],
            reasoning=state["final_proposal"]["reasoning"]
        )
        
    return {"risk_assessment": assessment}

def should_continue(state: AgentState):
    if state["round_count"] > MAX_ROUNDS:
        return "trader"
    return "bull"

# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------
workflow = StateGraph(AgentState)

workflow.add_node("sec", sec_agent)
workflow.add_node("memory", memory_agent)
workflow.add_node("bull", bull_agent)
workflow.add_node("bear", bear_agent)
workflow.add_node("trader", trader_agent)
workflow.add_node("risk", risk_agent)

workflow.set_entry_point("sec")
workflow.add_edge("sec", "memory")
workflow.add_edge("memory", "bull")
workflow.add_edge("bull", "bear")
workflow.add_conditional_edges("bear", should_continue, {"bull": "bull", "trader": "trader"})
workflow.add_edge("trader", "risk")
workflow.add_edge("risk", END)

app = workflow.compile()

if __name__ == "__main__":
    initial_state = {
        "ticker": "AAPL",
        "technical_data": "Trend: NEUTRAL. Support: 170. Resistance: 185.",
        "news_data": "Sentiment: 0.0. Themes: new product launch delayed, but revenue stable.",
        "fundamental_data": "Net income rising 19.5% YoY to $112.0B. Gross margin expanded to 46.9%. Low debt risk with $54.7B in cash.",
        "sec_data": "",
        "memory_context": "",
        "bull_argument": "",
        "bear_argument": "",
        "history": [],
        "round_count": 1,
        "final_proposal": {},
        "risk_assessment": {},
    }
    
    print("Starting LangGraph Debate...")
    final_output = app.invoke(initial_state)
    
    print("\n=== FINAL TRADE PROPOSAL ===")
    print(json.dumps(final_output["final_proposal"], indent=2))
    
    print("\n=== RISK MANAGEMENT DECISION ===")
    print(json.dumps(final_output["risk_assessment"], indent=2))
    