import time
import random
from overmind.clients import openai
from overmind import trace_function

# Placeholder for web search tool
class WebSearchTool:
    @trace_function(span_name="search")
    def search(self, query: str):
        time.sleep(random.random())
        # In production, integrate with real web search, e.g., SerpAPI or Bing
        return [
            f"News 1 for '{query}': Company achieves record profits.",
            f"News 2 for '{query}': {query} announces new product."
        ]

# Placeholder for Yahoo Finance tool
class YahooFinanceTool:
    @trace_function(span_name="get_stock_price")
    def get_stock_price(self, symbol: str):
        time.sleep(random.random())
        # In production, integrate with yfinance or Yahoo Finance API
        fake_prices = {"AAPL": 186.12, "GOOGL": 2734.00}
        return fake_prices.get(symbol.upper(), 100.00)

# Instantiate tool clients
openai_client = openai.OpenAI()
websearch_tool = WebSearchTool()
yahoo_finance_tool = YahooFinanceTool()


@trace_function(span_name="stock_agent_aggregate")
def stock_agent(stock_symbol: str):
    """Agent which aggregates stock price, latest news, and OpenAI analysis for a stock."""

    # Get latest stock price
    price = yahoo_finance_tool.get_stock_price(stock_symbol)

    # Fetch latest news headlines
    news = websearch_tool.search(stock_symbol)

    # Prepare prompt for OpenAI to summarize findings
    prompt = (
        f"Stock symbol: {stock_symbol}\n"
        f"Latest price: ${price}\n"
        f"News headlines:\n"
        + "\n".join(f"- {item}" for item in news)
        + "\n\nSummarize the current state of this stock and recent news in plain English."
    )

    # Get OpenAI summary
    openai_response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
    )
    summary = openai_response.choices[0].message.content

    return {
        "symbol": stock_symbol,
        "price": price,
        "news": news,
        "summary": summary
    }

if __name__ == "__main__":
    # Example usage with tracing
    while True:
        stock_symbol = input("Enter stock symbol (or 'quit' to exit): ")
        if stock_symbol.strip().lower() in ["quit", "exit"]:
            break
        result = stock_agent(stock_symbol)
        print("Stock Agent Result:\n", result)
    print("Stock Agent Result:\n", result)
