import time
import random
import openai
from overmind_sdk import init, tool, workflow, entry_point

init(service_name="example-tracer", environment="development")


class WebSearchTool:
    @tool(name="search")
    def search(self, query: str):
        time.sleep(random.random())
        return [
            f"News 1 for '{query}': Company achieves record profits.",
            f"News 2 for '{query}': {query} announces new product."
        ]


class YahooFinanceTool:
    @tool(name="get_stock_price")
    def get_stock_price(self, symbol: str):
        time.sleep(random.random())
        fake_prices = {"AAPL": 186.12, "GOOGL": 2734.00}
        return fake_prices.get(symbol.upper(), 100.00)


openai_client = openai.OpenAI()
websearch_tool = WebSearchTool()
yahoo_finance_tool = YahooFinanceTool()


@workflow(name="stock_agent_aggregate")
def stock_agent(stock_symbol: str):
    """Agent which aggregates stock price, latest news, and OpenAI analysis for a stock."""

    price = yahoo_finance_tool.get_stock_price(stock_symbol)
    news = websearch_tool.search(stock_symbol)

    prompt = (
        f"Stock symbol: {stock_symbol}\n"
        f"Latest price: ${price}\n"
        f"News headlines:\n"
        + "\n".join(f"- {item}" for item in news)
        + "\n\nSummarize the current state of this stock and recent news in plain English."
    )

    openai_response = openai_client.chat.completions.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    summary = openai_response.choices[0].message.content

    return {
        "symbol": stock_symbol,
        "price": price,
        "news": news,
        "summary": summary
    }


@entry_point(name="main")
def main():
    while True:
        stock_symbol = input("Enter stock symbol (or 'quit' to exit): ")
        if stock_symbol.strip().lower() in ["quit", "exit"]:
            break
        result = stock_agent(stock_symbol)
        print("Stock Agent Result:\n", result)


if __name__ == "__main__":
    main()
