import yfinance as yf
import pandas as pd


def normalize_symbol(raw_symbol: str) -> str:
    """將使用者輸入轉成 Yahoo Finance 可辨識的台股代號。"""
    symbol = raw_symbol.strip().upper()
    if not symbol:
        return ""
    if symbol.endswith(".TW") or symbol.endswith(".TWO"):
        return symbol
    return f"{symbol}.TW"


def get_stock_history(symbol: str, period: str = "1y") -> pd.DataFrame:
    """下載日線資料並計算移動平均線。"""
    candidates = [symbol]
    if symbol.endswith(".TW"):
        candidates.append(symbol[:-3] + ".TWO")
    elif symbol.endswith(".TWO"):
        candidates.append(symbol[:-4] + ".TW")

    for candidate in candidates:
        ticker = yf.Ticker(candidate)
        data = ticker.history(period=period, interval="1d", auto_adjust=True)
        if not data.empty:
            data = data.rename_axis("Date")
            data = data[["Open", "High", "Low", "Close", "Volume"]].dropna(subset=["Close"])
            data["MA5"] = data["Close"].rolling(5).mean()
            data["MA20"] = data["Close"].rolling(20).mean()
            data["MA60"] = data["Close"].rolling(60).mean()
            data.attrs["symbol"] = candidate
            return data

    return pd.DataFrame()


def get_stock_name(symbol: str) -> str:
    """盡力取得公司名稱；若查不到，就回傳股票代號。"""
    try:
        name = yf.Ticker(symbol).info.get("longName")
        if name:
            return name
    except Exception:
        pass
    return symbol
