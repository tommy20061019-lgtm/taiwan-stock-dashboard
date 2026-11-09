"""台股小幫手：技術指標計算。"""
import pandas as pd


def add_indicators(data: pd.DataFrame) -> pd.DataFrame:
    result = data.copy()
    close = result['Close'].astype(float)
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    rs = gain / loss.replace(0, float('nan'))
    result['RSI14'] = (100 - 100 / (1 + rs)).where(loss.ne(0), 100).where(gain.ne(0) | loss.ne(0), 50)
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    result['DIF'] = ema12 - ema26
    result['DEA'] = result['DIF'].ewm(span=9, adjust=False).mean()
    result['MACD'] = result['DIF'] - result['DEA']
    low9 = result['Low'].rolling(9, min_periods=9).min()
    high9 = result['High'].rolling(9, min_periods=9).max()
    rsv = ((close - low9) / (high9 - low9).replace(0, float('nan')) * 100).fillna(50)
    k_values, d_values = [], []
    k, d = 50., 50.
    for value in rsv:
        k = (2*k + value) / 3
        d = (2*d + k) / 3
        k_values.append(k)
        d_values.append(d)
    result['K'] = k_values
    result['D'] = d_values
    return result
