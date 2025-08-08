from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import requests
import numpy as np

app = FastAPI()

# Enable CORS for ChainOpera
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # (Use specific origin for production)
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_URL = "https://api.binance.com"
INTERVAL = "1d"

@app.get("/top-volatile")
def top_volatile(
    exchange: str = "binance",
    days: int = 7,
    top_n: int = 10,
    exclude_stable: bool = True
):
    if exchange.lower() != "binance":
        return {"error": "Only Binance supported for now."}

    pairs = fetch_usdt_pairs()
    if exclude_stable:
        pairs = [p for p in pairs if not any(s in p for s in ['USDC', 'BUSD', 'TUSD'])]

    results = []
    for pair in pairs:
        closes = fetch_ohlc(pair, days)
        if closes:
            vol = calculate_volatility(closes)
            if vol:
                results.append({"symbol": pair, "volatility": round(vol, 2)})

    top = sorted(results, key=lambda x: x["volatility"], reverse=True)[:top_n]
    return {"exchange": exchange, "days": days, "results": top}


def fetch_usdt_pairs():
    url = f"{BASE_URL}/api/v3/exchangeInfo"
    res = requests.get(url)
    data = res.json()
    return [s['symbol'] for s in data['symbols']
            if s['quoteAsset'] == 'USDT' and s['status'] == 'TRADING']


def fetch_ohlc(symbol, days):
    url = f"{BASE_URL}/api/v3/klines"
    params = {"symbol": symbol, "interval": INTERVAL, "limit": days}
    res = requests.get(url, params=params)
    data = res.json()
    return [float(c[4]) for c in data]  # Close prices


def calculate_volatility(prices):
    if len(prices) < 2:
        return None
    return (np.std(prices) / np.mean(prices)) * 100
