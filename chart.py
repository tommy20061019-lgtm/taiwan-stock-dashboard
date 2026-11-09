"""Plotly 圖表，所有可設定的文字均採繁體中文。"""
import plotly.graph_objects as go
from plotly.subplots import make_subplots

CHART_CONFIG = {
    'displaylogo': False,
    'displayModeBar': False,  # 隱藏無法完整中文化的 Plotly 內建英文工具列
    'scrollZoom': True,  # 滑鼠滾輪縮放；雙擊圖表可重設視野
    'locale': 'zh-TW',
    'toImageButtonOptions': {'format': 'png', 'filename': '台股小幫手_股價圖', 'scale': 2},
    'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
}


def make_price_chart(data, title: str, indicators=None):
    indicators = indicators or []
    rows = 2 + len(indicators)
    heights = [0.53, 0.17] + [0.30 / max(len(indicators), 1)] * len(indicators) if indicators else [0.75, 0.25]
    fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.035, row_heights=heights)
    fig.add_trace(go.Candlestick(
        x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'],
        name='K 線圖',
        hovertemplate='開盤價：%{open:,.2f} 元<br>最高價：%{high:,.2f} 元<br>最低價：%{low:,.2f} 元<br>收盤價：%{close:,.2f} 元<extra></extra>'
    ), row=1, col=1)
    for key, name in [('MA5','5 日均線'), ('MA20','20 日均線'), ('MA60','60 日均線')]:
        fig.add_trace(go.Scatter(x=data.index, y=data[key], mode='lines', name=name, hovertemplate=f'{name}：%{{y:,.2f}} 元<extra></extra>', line={'width':1.4}), row=1, col=1)
    fig.add_trace(go.Bar(x=data.index, y=data['Volume'], name='成交量', hovertemplate='成交量：%{y:,.0f} 股<extra></extra>', marker={'opacity':0.6}), row=2, col=1)
    for row, indicator in enumerate(indicators, start=3):
        if indicator == 'RSI':
            fig.add_trace(go.Scatter(x=data.index, y=data['RSI14'], name='相對強弱指標（RSI 14）', hovertemplate='相對強弱指標：%{y:.2f}<extra></extra>'), row=row, col=1)
            fig.add_hline(y=70, line_dash='dot', line_color='gray', row=row, col=1)
            fig.add_hline(y=30, line_dash='dot', line_color='gray', row=row, col=1)
            fig.update_yaxes(range=[0, 100], title_text='RSI', row=row, col=1)
        elif indicator == 'MACD':
            fig.add_trace(go.Bar(x=data.index, y=data['MACD'], name='指數平滑異同移動平均線（MACD 柱狀圖）', hovertemplate='柱狀值：%{y:.3f}<extra></extra>'), row=row, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=data['DIF'], name='快線（DIF）', hovertemplate='快線：%{y:.3f}<extra></extra>'), row=row, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=data['DEA'], name='慢線（DEA）', hovertemplate='慢線：%{y:.3f}<extra></extra>'), row=row, col=1)
            fig.update_yaxes(title_text='MACD', row=row, col=1)
        elif indicator == 'KD':
            fig.add_trace(go.Scatter(x=data.index, y=data['K'], name='隨機指標 K 值', hovertemplate='K 值：%{y:.2f}<extra></extra>'), row=row, col=1)
            fig.add_trace(go.Scatter(x=data.index, y=data['D'], name='隨機指標 D 值', hovertemplate='D 值：%{y:.2f}<extra></extra>'), row=row, col=1)
            fig.update_yaxes(range=[0, 100], title_text='KD', row=row, col=1)
    fig.update_layout(title=f'{title}｜股價走勢與技術分析', height=700+180*len(indicators), xaxis_rangeslider_visible=False,
                      hovermode='x unified', legend={'orientation':'h','y':1.02,'x':0},
                      margin={'l':15,'r':15,'t':80,'b':15})
    fig.update_yaxes(title_text='股價（元）', row=1, col=1)
    fig.update_yaxes(title_text='成交量（股）', row=2, col=1)
    fig.update_xaxes(title_text='日期', row=rows, col=1)
    fig.update_xaxes(hoverformat='%Y年%m月%d日')
    fig.update_layout(xaxis={'unifiedhovertitle': {'text': '%{x|%Y年%m月%d日}'}})
    return fig
