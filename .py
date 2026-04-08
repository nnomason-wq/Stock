import os
import time
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi
import pandas as pd

# ── Load your secret keys from .env ──────────────────────────────────────────
load_dotenv()

api = tradeapi.REST(
    os.getenv("APCA_API_KEY_ID"),
    os.getenv("APCA_API_SECRET_KEY"),
    os.getenv("APCA_API_BASE_URL"),
    api_version="v2"
)

# ── Settings — change these to experiment ────────────────────────────────────
SYMBOL      = "AAPL"   # Stock to trade
SHORT_WINDOW = 10      # Short moving average (10 days)
LONG_WINDOW  = 50      # Long moving average (50 days)
QTY          = 1       # How many shares to buy/sell at a time


# ── Step 1: Get historical price data ────────────────────────────────────────
def get_prices(symbol, limit=100):
    """Grab the last 100 daily closing prices for a stock."""
    bars = api.get_bars(symbol, "1Day", limit=limit).df
    return bars["close"]


# ── Step 2: Calculate the two moving averages ─────────────────────────────────
def get_moving_averages(prices):
    """Calculate short and long averages from price data."""
    short_ma = prices.rolling(window=SHORT_WINDOW).mean()
    long_ma  = prices.rolling(window=LONG_WINDOW).mean()
    return short_ma, long_ma


# ── Step 3: Check if we already own the stock ─────────────────────────────────
def get_position(symbol):
    """Returns how many shares we currently hold. 0 if none."""
    try:
        position = api.get_position(symbol)
        return int(position.qty)
    except:
        return 0


# ── Step 4: The actual trading logic ─────────────────────────────────────────
def run_strategy():
    print(f"Running strategy for {SYMBOL}...")

    prices = get_prices(SYMBOL)
    short_ma, long_ma = get_moving_averages(prices)

    # Get the most recent values
    current_short = short_ma.iloc[-1]
    current_long  = long_ma.iloc[-1]
    previous_short = short_ma.iloc[-2]
    previous_long  = long_ma.iloc[-2]

    shares_owned = get_position(SYMBOL)

    print(f"  Short MA: {current_short:.2f} | Long MA: {current_long:.2f}")
    print(f"  Shares owned: {shares_owned}")

    # BUY signal: short MA just crossed ABOVE long MA
    if previous_short <= previous_long and current_short > current_long:
        if shares_owned == 0:
            print(f"  BUY signal! Buying {QTY} share(s) of {SYMBOL}")
            api.submit_order(
                symbol=SYMBOL,
                qty=QTY,
                side="buy",
                type="market",
                time_in_force="gtc"
            )
        else:
            print("  BUY signal, but we already own shares. Holding.")

    # SELL signal: short MA just crossed BELOW long MA
    elif previous_short >= previous_long and current_short < current_long:
        if shares_owned > 0:
            print(f"  SELL signal! Selling {QTY} share(s) of {SYMBOL}")
            api.submit_order(
                symbol=SYMBOL,
                qty=QTY,
                side="sell",
                type="market",
                time_in_force="gtc"
            )
        else:
            print("  SELL signal, but we own nothing. Skipping.")

    # No crossover — do nothing
    else:
        print("  No crossover detected. Holding.")


# ── Step 5: Run it once a day in a loop ──────────────────────────────────────
if __name__ == "__main__":
    while True:
        run_strategy()
        print("  Waiting 24 hours...\n")
        time.sleep(86400)  # 86400 seconds = 1 day