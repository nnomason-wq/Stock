import os
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi
import pandas as pd

# ───────────────────────────────────────────────────────────────
# Load API keys
# ───────────────────────────────────────────────────────────────
load_dotenv()

api = tradeapi.REST(
    os.getenv("APCA_API_KEY_ID"),
    os.getenv("APCA_API_SECRET_KEY"),
    os.getenv("APCA_API_BASE_URL"),
    api_version="v2"
)

# ───────────────────────────────────────────────────────────────
# Settings
# ───────────────────────────────────────────────────────────────
SYMBOLS = ["SPY", "QQQ", "DIA", "TSLA", "NVDA"]
SHORT_WINDOW = 10
LONG_WINDOW = 50
QTY = 1


# ───────────────────────────────────────────────────────────────
# Get historical prices
# ───────────────────────────────────────────────────────────────
def get_prices(symbol, limit=200):
    bars = api.get_bars(symbol, "1Day", limit=limit).df
    return bars["close"]


# ───────────────────────────────────────────────────────────────
# Moving averages
# ───────────────────────────────────────────────────────────────
def get_moving_averages(prices):
    short_ma = prices.rolling(window=SHORT_WINDOW).mean()
    long_ma = prices.rolling(window=LONG_WINDOW).mean()
    return short_ma, long_ma


# ───────────────────────────────────────────────────────────────
# Check current position
# ───────────────────────────────────────────────────────────────
def get_position(symbol):
    try:
        position = api.get_position(symbol)
        return int(position.qty)
    except:
        return 0


# ───────────────────────────────────────────────────────────────
# Strategy logic
# ───────────────────────────────────────────────────────────────
def run_strategy():
    for symbol in SYMBOLS:
        print(f"\nRunning strategy for {symbol}...")

        prices = get_prices(symbol)
        short_ma, long_ma = get_moving_averages(prices)

        if len(short_ma.dropna()) < 2:
            print("  Not enough data yet. Skipping.")
            continue

        current_short = short_ma.iloc[-1]
        current_long = long_ma.iloc[-1]
        previous_short = short_ma.iloc[-2]
        previous_long = long_ma.iloc[-2]

        shares_owned = get_position(symbol)

        print(f"  Short MA: {current_short:.2f} | Long MA: {current_long:.2f}")
        print(f"  Shares owned: {shares_owned}")

        # BUY signal
        if previous_short <= previous_long and current_short > current_long:
            if shares_owned == 0:
                print(f"  BUY signal! Buying {QTY} share(s) of {symbol}")
                api.submit_order(
                    symbol=symbol,
                    qty=QTY,
                    side="buy",
                    type="market",
                    time_in_force="gtc"
                )
            else:
                print("  BUY signal, but already own shares.")

        # SELL signal
        elif previous_short >= previous_long and current_short < current_long:
            if shares_owned > 0:
                print(f"  SELL signal! Selling {QTY} share(s) of {symbol}")
                api.submit_order(
                    symbol=symbol,
                    qty=QTY,
                    side="sell",
                    type="market",
                    time_in_force="gtc"
                )
            else:
                print("  SELL signal, but no shares owned.")

        else:
            print("  No crossover. Holding.")


# ───────────────────────────────────────────────────────────────
# OPTIONAL: Immediate buy trigger (manual, safe)
# ───────────────────────────────────────────────────────────────
def buy_now():
    print("\nExecuting manual buy...")
    for symbol in SYMBOLS:
        api.submit_order(
            symbol=symbol,
            qty=1,
            side="buy",
            type="market",
            time_in_force="gtc"
        )
        print(f"  Bought 1 share of {symbol}")


# ───────────────────────────────────────────────────────────────
# Main
# ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Choose ONE of these:

    run_strategy()      # Normal strategy mode

    # buy_now()         # ← UNCOMMENT THIS LINE to buy immediately
