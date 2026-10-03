from pydantic import BaseModel, Field
from typing import List

class TechnicalReport(BaseModel):
    trend: str = Field(description="Must be strictly BULLISH, BEARISH, or NEUTRAL.")
    support_levels: List[float] = Field(description="List of key price support levels.")
    resistance_levels: List[float] = Field(description="List of key price resistance levels.")
    analysis_summary: str = Field(description="A concise markdown summary of the technical context.")

class NewsReport(BaseModel):
    sentiment_score: float = Field(description="Sentiment score from -1.0 (extremely bearish) to 1.0 (extremely bullish).")
    key_themes: List[str] = Field(description="Main fundamental themes driving the news.")
    summary: str = Field(description="A brief paragraph summarizing the fundamental news context.")

class TradeProposal(BaseModel):
    ticker: str = Field(description="The asset ticker symbol.")
    action: str = Field(description="Strictly BUY, SELL, or HOLD.")
    confidence: float = Field(description="Confidence level from 0.0 to 1.0.")
    reasoning: str = Field(description="A brief paragraph explaining the final decision based on the debate.")

class FundamentalReport(BaseModel):
    profitability_trend: str = Field(description="Strictly IMPROVING, DETERIORATING, or STABLE.")
    debt_risk: str = Field(description="Assessment of debt levels: LOW, MEDIUM, or HIGH.")
    key_metrics_summary: str = Field(description="A brief paragraph summarizing revenue growth, margins, and debt-to-equity.")