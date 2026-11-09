"""模擬持倉計算與無前視偏差的均線策略回測。"""
import pandas as pd
import numpy as np

PORTFOLIO_COLUMNS = ['股票代號', '買入價格', '股數']


def validate_holdings(rows):
    clean = []
    for row in rows:
        code = str(row.get('股票代號', '')).strip().upper()
        if not code or code == 'NAN':
            continue
        try:
            cost = float(row.get('買入價格', 0))
            shares = float(row.get('股數', 0))
        except (TypeError, ValueError):
            raise ValueError(f'{code}：買入價格與股數必須是數字')
        if not np.isfinite(cost) or not np.isfinite(shares) or cost <= 0 or shares <= 0 or not shares.is_integer():
            raise ValueError(f'{code}：買入價格必須大於零，股數必須為正整數')
        clean.append((code, cost, int(shares)))
    if len(clean) > 20:
        raise ValueError('一次最多計算 20 筆持倉')
    return clean


def calculate_portfolio(holdings, fetch):
    results, failures = [], []
    for code, cost, shares in holdings:
        try:
            df = fetch(code)
            if df.empty:
                failures.append(code)
                continue
            last = df.iloc[-1]
            price = float(last['Close'])
            principal = cost * shares
            value = price * shares
            results.append({'股票代號': code, '買入價格': cost, '股數': shares,
                            '最近收盤價': price, '投入成本': principal, '目前估值': value,
                            '未實現損益': value - principal,
                            '報酬率（%）': (value / principal - 1) * 100,
                            '資料日期': df.index[-1].strftime('%Y-%m-%d')})
        except Exception:
            failures.append(code)
    return pd.DataFrame(results), failures


def backtest_ma(data, short=5, long=20, fee_rate=0.001425, sell_tax=0.003):
    """收盤產生訊號，下一交易日開盤執行；全額持倉或現金；不考慮股利與滑價。"""
    if short >= long:
        raise ValueError('短期均線天數必須小於長期均線天數')
    df = data[['Open', 'Close']].dropna().copy()
    if len(df) < long + 3:
        raise ValueError('歷史資料不足，請延長回測期間')
    df['短期均線'] = df['Close'].rolling(short).mean()
    df['長期均線'] = df['Close'].rolling(long).mean()
    signal = (df['短期均線'] > df['長期均線']).fillna(False)
    cash, shares, initial = 100000.0, 0.0, 100000.0
    records, transactions = [], []
    # 第 i 天開盤只依第 i-1 天收盤已知的訊號操作。
    for i, (date, row) in enumerate(df.iterrows()):
        op, close = float(row['Open']), float(row['Close'])
        if i > 0 and op > 0:
            want = bool(signal.iloc[i - 1])
            if want and shares == 0:
                qty = cash / (op * (1 + fee_rate))
                cash -= qty * op * (1 + fee_rate)
                shares = qty
                transactions.append({'日期': date.strftime('%Y-%m-%d'), '動作': '買入', '成交參考價': op})
            elif not want and shares > 0:
                cash += shares * op * (1 - fee_rate - sell_tax)
                shares = 0.0
                transactions.append({'日期': date.strftime('%Y-%m-%d'), '動作': '賣出', '成交參考價': op})
        records.append({'日期': date, '策略淨值': cash + shares * close})
    equity = pd.DataFrame(records).set_index('日期')
    equity['策略累積報酬（%）'] = (equity['策略淨值'] / initial - 1) * 100
    benchmark = df['Close'] / float(df['Close'].iloc[0]) * initial
    equity['買入持有累積報酬（%）'] = (benchmark / initial - 1) * 100
    drawdown = equity['策略淨值'] / equity['策略淨值'].cummax() - 1
    stats = {'策略報酬率（%）': float(equity['策略累積報酬（%）'].iloc[-1]),
             '買入持有報酬率（%）': float(equity['買入持有累積報酬（%）'].iloc[-1]),
             '最大回撤（%）': float(drawdown.min() * 100),
             '交易次數': len(transactions)}
    return equity, pd.DataFrame(transactions), stats
