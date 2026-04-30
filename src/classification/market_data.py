"""Fetch and display live market prices across asset classes."""

from __future__ import annotations

from datetime import datetime
import logging
import sys
from zoneinfo import ZoneInfo

import requests
import yfinance as yf

LOGGER = logging.getLogger(__name__)
COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"


def _now_ist() -> datetime:
    """Return current timestamp in IST timezone."""
    return datetime.now(ZoneInfo("Asia/Kolkata"))


def fetch_stock_price(symbol: str) -> dict:
    """Fetch one stock/index price using yfinance."""
    timestamp = _now_ist().strftime("%Y-%m-%d %H:%M:%S IST")
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        price = info.get("regularMarketPrice")
        if price is None:
            raise ValueError("regularMarketPrice missing from response")
        currency = str(info.get("currency", "INR")).upper()
        return {"name": symbol, "price": float(price), "currency": currency, "timestamp": timestamp}
    except Exception as exc:
        LOGGER.error("Stock fetch failed for %s: %s", symbol, exc)
        return {"name": symbol, "price": None, "currency": "-", "timestamp": timestamp}


def fetch_crypto_price(coin_id: str) -> dict:
    """Fetch one crypto price from CoinGecko in USD."""
    timestamp = _now_ist().strftime("%Y-%m-%d %H:%M:%S IST")
    params = {"ids": coin_id, "vs_currencies": "usd"}
    try:
        response = requests.get(COINGECKO_URL, params=params, timeout=10)
        response.raise_for_status()
        payload = response.json()
        price = payload.get(coin_id, {}).get("usd")
        if price is None:
            raise ValueError("usd price missing in CoinGecko response")
        return {"name": coin_id.upper(), "price": float(price), "currency": "USD", "timestamp": timestamp}
    except Exception as exc:
        LOGGER.error("Crypto fetch failed for %s: %s", coin_id, exc)
        return {"name": coin_id.upper(), "price": None, "currency": "-", "timestamp": timestamp}


def format_table(data: list[dict]) -> None:
    """Print aligned terminal table for fetched assets."""
    rows = [(d["name"], "N/A" if d["price"] is None else f"{d['price']:.2f}", d["currency"]) for d in data]
    headers = ("Asset", "Price", "Currency")
    w1 = max(len(headers[0]), *(len(r[0]) for r in rows))
    w2 = max(len(headers[1]), *(len(r[1]) for r in rows))
    w3 = max(len(headers[2]), *(len(r[2]) for r in rows))
    utf = (sys.stdout.encoding or "").lower().startswith("utf")
    h, v = ("─", "│") if utf else ("-", "|")
    tl, tc, tr = ("┌", "┬", "┐") if utf else ("+", "+", "+")
    ml, mc, mr = ("├", "┼", "┤") if utf else ("+", "+", "+")
    bl, bc, br = ("└", "┴", "┘") if utf else ("+", "+", "+")
    print(f"Asset Prices - fetched at {_now_ist().strftime('%Y-%m-%d %H:%M:%S IST')}\n")
    print(f"{tl}{h * (w1 + 2)}{tc}{h * (w2 + 2)}{tc}{h * (w3 + 2)}{tr}")
    print(f"{v} {'Asset':<{w1}} {v} {'Price':<{w2}} {v} {'Currency':<{w3}} {v}")
    print(f"{ml}{h * (w1 + 2)}{mc}{h * (w2 + 2)}{mc}{h * (w3 + 2)}{mr}")
    for asset, price, currency in rows:
        print(f"{v} {asset:<{w1}} {v} {price:<{w2}} {v} {currency:<{w3}} {v}")
    print(f"{bl}{h * (w1 + 2)}{bc}{h * (w2 + 2)}{bc}{h * (w3 + 2)}{br}")


def main() -> None:
    """Fetch stock/index, crypto, and one additional asset price."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    assets = [
        fetch_crypto_price("bitcoin"),
        fetch_stock_price("^NSEI"),
        fetch_stock_price("GC=F"),
    ]
    format_table(assets)


if __name__ == "__main__":
    main()
