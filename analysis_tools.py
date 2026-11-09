"""第二階段：多檔股票比較與指定清單條件選股。"""
import pandas as pd
import plotly.graph_objects as go
from stock_data import normalize_symbol
from indicators import add_indicators


def parse_symbols(text: str, limit: int = 12) -> list[str]:
    """接受逗號、空白、換行與中文頓號；去重並限制查詢數量。"""
    for sep in ('，', '、', ';', '；', '\n', '\t'):
        text = text.replace(sep, ',')
    symbols = []
    for token in text.replace(' ', ',').split(','):
        value = normalize_symbol(token)
        if value and value not in symbols:
            symbols.append(value)
    return symbols[:limit]


def summarize(data: pd.DataFrame, symbol: str, name: str) -> dict:
    """計算最後一筆可用日線的摘要，不宣稱為即時報價。"""
    df = add_indicators(data.copy())
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    close = float(latest['Close'])
    prev_close = float(prev['Close'])
    ret = (close / prev_close - 1) * 100 if prev_close else None
    ma20 = latest['MA20']
    rsi = latest['RSI14']
    return {
        '股票代號': symbol.split('.')[0], '股票名稱': name,
        '資料日期': df.index[-1].strftime('%Y-%m-%d'),
        '收盤價（元）': round(close, 2),
        '單日漲跌幅（%）': round(ret, 2) if ret is not None else None,
        '成交量（股）': int(latest['Volume']) if pd.notna(latest['Volume']) else None,
        '20日均線（元）': round(float(ma20), 2) if pd.notna(ma20) else None,
        'RSI（14）': round(float(rsi), 2) if pd.notna(rsi) else None,
        '站上20日均線': bool(close > ma20) if pd.notna(ma20) else None,
    }


def make_comparison_chart(histories: dict[str, pd.DataFrame]) -> go.Figure:
    """以各股票第一個共同交易日收盤價為 0%，比較期間報酬走勢。"""
    close = pd.concat({name: df['Close'] for name, df in histories.items()}, axis=1).sort_index()
    close.index = pd.to_datetime(close.index).tz_localize(None) if close.index.tz is not None else pd.to_datetime(close.index)
    close = close.dropna(how='any')  # 只比較共同交易日，避免日期錯位
    fig = go.Figure()
    if close.empty:
        return fig
    for name in close.columns:
        base = float(close[name].iloc[0])
        if base <= 0:
            continue
        performance = (close[name] / base - 1) * 100
        fig.add_trace(go.Scatter(x=close.index, y=performance, name=name, mode='lines',
                                 hovertemplate='%{x|%Y年%m月%d日}<br>累積漲跌幅：%{y:+.2f}%<extra>%{fullData.name}</extra>'))
    fig.update_layout(title='股票期間漲跌幅比較（共同起始日＝0%）',
                      xaxis_title='日期', yaxis_title='累積漲跌幅（%）',
                      hovermode='x unified', template='plotly_dark',
                      height=480, legend_title_text='股票')
    return fig


def screen_rows(rows: list[dict], minimum_change: float | None = None,
                minimum_volume: int | None = None, above_ma20: bool = False,
                rsi_min: float | None = None, rsi_max: float | None = None) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    if minimum_change is not None:
        df = df[df['單日漲跌幅（%）'].notna() & (df['單日漲跌幅（%）'] >= minimum_change)]
    if minimum_volume is not None:
        df = df[df['成交量（股）'].notna() & (df['成交量（股）'] >= minimum_volume)]
    if above_ma20:
        df = df[df['站上20日均線'] == True]
    if rsi_min is not None:
        df = df[df['RSI（14）'].notna() & (df['RSI（14）'] >= rsi_min)]
    if rsi_max is not None:
        df = df[df['RSI（14）'].notna() & (df['RSI（14）'] <= rsi_max)]
    return df.reset_index(drop=True)
