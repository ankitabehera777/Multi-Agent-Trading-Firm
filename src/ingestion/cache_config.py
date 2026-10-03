import requests_cache
from tenacity import retry, stop_after_attempt, wait_exponential

# Create a persistent SQLite cache for all HTTP requests
session = requests_cache.CachedSession(
    'trading_api_cache', 
    backend='sqlite', 
    expire_after=86400 # 24 hours
)

# Reusable exponential backoff decorator for external API calls
def retry_with_backoff():
    return retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )