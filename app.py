import streamlit as st
import pandas as pd
import json
from stock_data import get_stock_history, get_stock_name, normalize_symbol
from chart import make_price_chart, CHART_CONFIG
from indicators import add_indicators
from stock_names import display_name

st.set_page_config(page_title="台股小幫手 V3", page_icon="📈", layout="wide")

st.title("📈 台股小幫手 V3")
st.markdown("""
<div style="background:linear-gradient(100deg,#1e3a5f,#243b53);border:1px solid #5a8cbd;
            border-left:6px solid #f5c451;border-radius:12px;padding:18px 22px;
            margin:12px 0 18px 0;color:#ffffff;">
  <div style="font-size:13px;font-weight:700;letter-spacing:2px;color:#f5d47b;">專題作品展示</div>
  <div style="font-size:clamp(20px,2.2vw,30px);font-weight:800;line-height:1.5;">
    王聖凱 <span style="color:#d7e8f9;">｜</span> 寒假轉學書審作品
  </div>
</div>
""", unsafe_allow_html=True)
st.caption("使用 Yahoo Finance 日線資料 · 僅供學習研究與書審展示，不是即時報價或下單軟體")
with st.expander("🧭 作品功能導覽與使用提醒", expanded=False):
    st.markdown("""**第一部分｜台股查詢與技術分析**：K 線、成交量、均線、RSI、MACD、KD、自選股與圖片匯出。  
**第二部分｜股票比較與條件選股**：比較多檔股票的期間漲跌幅，篩選指定股票清單。  
**第三部分｜投資組合與歷史回測**：模擬持倉損益、均線交叉策略與 CSV 匯出。  
**資料說明**：價格取自 Yahoo Finance 最近可取得的日線資料，可能延遲、缺漏；所有模擬結果均非真實交易績效。""")

@st.cache_data(ttl=60)
def load_history(symbol: str, period: str):
    return get_stock_history(symbol, period)

@st.cache_data(ttl=3600)
def load_name(symbol: str):
    return get_stock_name(symbol)

if "watchlist" not in st.session_state:
    try:
        with open("watchlist.json", "r", encoding="utf-8") as f:
            st.session_state.watchlist = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        st.session_state.watchlist = ["2330.TW", "2317.TW", "0050.TW"]

with st.sidebar:
    st.header("🔎 股票查詢")
    raw_symbol = st.text_input("輸入台股代號", value="2330", placeholder="例如：2330 或 6488")
    period_label = st.selectbox("歷史資料範圍", ["1 個月", "3 個月", "6 個月", "1 年", "2 年", "5 年"], index=3)
    period_map = {"1 個月": "1mo", "3 個月": "3mo", "6 個月": "6mo", "1 年": "1y", "2 年": "2y", "5 年": "5y"}
    period = period_map[period_label]
    search_clicked = st.button("查詢股票", type="primary", use_container_width=True)
    st.divider()
    st.subheader("📊 技術分析")
    chosen_indicators = st.multiselect("顯示技術指標", ["相對強弱指標（RSI）", "指數平滑異同移動平均線（MACD）", "隨機指標（KD）"], default=["相對強弱指標（RSI）", "指數平滑異同移動平均線（MACD）", "隨機指標（KD）"], help="RSI：相對強弱指標；MACD：指數平滑異同移動平均線；KD：隨機指標")
    st.divider()
    st.subheader("⭐ 自選股")
    for item in list(st.session_state.watchlist):
        c1, c2 = st.columns([3, 1])
        if c1.button(item.replace(".TW", "").replace(".TWO", ""), key=f"pick_{item}", use_container_width=True):
            st.session_state.selected_symbol = item
            st.rerun()
        if c2.button("✕", key=f"remove_{item}"):
            st.session_state.watchlist.remove(item)
            with open("watchlist.json", "w", encoding="utf-8") as f:
                json.dump(st.session_state.watchlist, f, ensure_ascii=False, indent=2)
            st.rerun()

if search_clicked or "selected_symbol" not in st.session_state:
    st.session_state.selected_symbol = normalize_symbol(raw_symbol)
elif raw_symbol.strip():
    # 只有按下查詢才以輸入框內容切換，避免點選自選股後被預設值覆蓋
    pass

symbol = st.session_state.selected_symbol
if not symbol:
    st.info("請在左側輸入股票代號，例如 2330。")
    st.stop()

try:
    data = load_history(symbol, period)
except Exception as exc:
    st.error(f"讀取股票資料時發生問題：{exc}")
    st.info("請確認網路連線、股票代號，或稍後再試。")
    st.stop()

if data.empty or len(data) < 2:
    st.error("找不到足夠的股價資料。請確認代號是否正確，例如上市 2330、上櫃股票可嘗試代號。")
    st.stop()

symbol = data.attrs.get("symbol", symbol)
name = display_name(symbol, load_name(symbol))
data = add_indicators(data)
latest = data.iloc[-1]
previous = data.iloc[-2]
price = float(latest["Close"])
change = price - float(previous["Close"])
change_pct = change / float(previous["Close"]) * 100 if float(previous["Close"]) else 0
volume = int(latest["Volume"]) if pd.notna(latest["Volume"]) else 0

header_col, button_col = st.columns([4, 1])
with header_col:
    st.subheader(f"{name}（{symbol.replace('.TW', '').replace('.TWO', '')}）")
with button_col:
    if symbol not in st.session_state.watchlist:
        if st.button("＋ 加入自選股", use_container_width=True):
            st.session_state.watchlist.append(symbol)
            with open("watchlist.json", "w", encoding="utf-8") as f:
                json.dump(st.session_state.watchlist, f, ensure_ascii=False, indent=2)
            st.rerun()
    else:
        st.button("⭐ 已加入自選股", disabled=True, use_container_width=True)

m1, m2, m3, m4 = st.columns(4)
m1.metric("最近收盤價", f"{price:,.2f} 元", f"{change:+,.2f} ({change_pct:+.2f}%)")
m2.metric("成交量", f"{volume:,} 股")
m3.metric("當日最高", f"{float(latest['High']):,.2f} 元")
m4.metric("當日最低", f"{float(latest['Low']):,.2f} 元")

st.caption(f"資料日期：{data.index[-1].strftime('%Y-%m-%d')} · 這是最近可取得的日線資料，不保證即時。")
chart = make_price_chart(data, name, [{"相對強弱指標（RSI）":"RSI", "指數平滑異同移動平均線（MACD）":"MACD", "隨機指標（KD）":"KD"}[item] for item in chosen_indicators])
st.plotly_chart(chart, use_container_width=True, config=CHART_CONFIG)
st.caption("圖表操作：拖曳可選取放大範圍、滑鼠滾輪可縮放、雙擊圖表可重設視野。")
# 下載 PNG 使用 Kaleido 產生圖片，不再顯示 Plotly 內建英文下載提示。
# 只有使用者按下按鈕時才嘗試轉圖，避免每次查詢都額外耗時。
if st.button("📷 準備下載圖表圖片（PNG）", key="prepare_chart_png"):
    with st.spinner("正在產生圖表圖片…"):
        try:
            import plotly.io as pio
            st.session_state["v3_chart_png"] = pio.to_image(chart, format="png", scale=2)
            st.session_state["v3_chart_png_name"] = symbol.replace(".", "_")
        except Exception as exc:
            st.session_state.pop("v3_chart_png", None)
            st.error("無法產生 PNG 圖片。請先安裝 Kaleido（python -m pip install kaleido），並確認電腦已安裝 Chrome 瀏覽器。")
            st.caption(f"技術資訊：{exc}")
if st.session_state.get("v3_chart_png") and st.session_state.get("v3_chart_png_name") == symbol.replace(".", "_"):
    st.download_button("⬇️ 下載圖表圖片（PNG）", data=st.session_state["v3_chart_png"],
                       file_name=f"台股小幫手_{st.session_state.get('v3_chart_png_name', '股價')}.png",
                       mime="image/png", key="download_chart_png")

with st.expander("查看最近 20 個交易日資料"):
    view = data.tail(20).copy()
    view.index = view.index.strftime("%Y-%m-%d")
    st.dataframe(view.rename(columns={
        "Open": "開盤", "High": "最高", "Low": "最低",
        "Close": "收盤", "Volume": "成交量",
        "MA5": "5 日均線", "MA20": "20 日均線", "MA60": "60 日均線",
        "RSI14": "相對強弱指標 RSI", "DIF": "MACD 快線", "DEA": "MACD 慢線",
        "MACD": "MACD 柱狀值", "K": "KD 的 K 值", "D": "KD 的 D 值"
    }).sort_index(ascending=False), use_container_width=True)

st.divider()
st.caption("提醒：本程式僅供學習與資訊整理，不構成投資建議。Yahoo Finance 資料可能延遲、缺漏或暫時無法取得；請勿將其視為交易下單依據。")

# ──────────────────────────────────────────────────────────────
# V3 第二階段：股票比較與指定清單條件選股
# ──────────────────────────────────────────────────────────────
from analysis_tools import parse_symbols, summarize, make_comparison_chart, screen_rows

st.divider()
st.header('🔍 V3 第二階段｜股票比較與條件選股')
st.caption('使用 Yahoo Finance 日線資料；僅供學習研究，非即時報價。')
comparison_tab, screener_tab = st.tabs(['📈 多檔股票比較', '🧮 條件選股'])

with comparison_tab:
    st.subheader('多檔股票走勢比較')
    st.write('輸入 2～5 檔台股代號，以共同交易日的第一天為基準，比較累積漲跌幅。')
    comparison_input = st.text_input('比較股票代號（逗號分隔）', value='2330,2317,0050', key='comparison_codes')
    comparison_period = st.selectbox('比較期間', ['3 個月', '6 個月', '1 年', '2 年'], index=2,
                                     key='comparison_period')
    compare_period_map = {'3 個月': '3mo', '6 個月': '6mo', '1 年': '1y', '2 年': '2y'}
    if st.button('開始比較', type='primary', key='run_comparison'):
        codes = parse_symbols(comparison_input, limit=6)
        if len(codes) < 2 or len(codes) > 5:
            st.warning('請輸入 2～5 檔不同的股票代號。')
        else:
            histories = {}
            summaries = []
            failures = []
            with st.spinner('正在取得股票歷史資料…'):
                for code in codes:
                    try:
                        df = load_history(code, compare_period_map[comparison_period])
                        if df.empty or len(df) < 2:
                            failures.append(code)
                            continue
                        actual = df.attrs.get('symbol', code)
                        name_cn = display_name(actual, load_name(actual))
                        label = f"{name_cn}（{actual.split('.')[0]}）"
                        histories[label] = df
                        summaries.append(summarize(df, actual, name_cn))
                    except Exception:
                        failures.append(code)
            if failures:
                st.warning('以下股票無法取得足夠資料：' + '、'.join(failures))
            if len(histories) >= 2:
                fig = make_comparison_chart(histories)
                if fig.data:
                    st.plotly_chart(fig, use_container_width=True, config=CHART_CONFIG)
                    st.dataframe(pd.DataFrame(summaries).drop(columns=['站上20日均線']),
                                 hide_index=True, use_container_width=True)
                    st.caption('比較圖只使用各股票共同有資料的交易日，基準日為 0%；未包含交易費用、稅與股利。')
                else:
                    st.warning('找不到共同交易日，無法比較。')
            else:
                st.info('至少需要兩檔有效股票資料才能繪製比較圖。')

with screener_tab:
    st.subheader('指定清單條件選股')
    st.write('先設定要分析的股票代號，再設定條件；不會掃描整個台股市場。')
    default_codes = ','.join(s.split('.')[0] for s in st.session_state.watchlist)
    screen_input = st.text_area('候選股票代號（最多 12 檔）', value=default_codes,
                                key='screen_codes', height=90)
    f1, f2 = st.columns(2)
    with f1:
        filter_change = st.checkbox('篩選單日漲跌幅', key='filter_change')
        min_change = st.number_input('最低單日漲跌幅（%）', value=0.0, step=0.5,
                                     disabled=not filter_change)
        filter_volume = st.checkbox('篩選成交量', key='filter_volume')
        min_volume = st.number_input('最低成交量（股）', min_value=0, value=1000000, step=100000,
                                     disabled=not filter_volume)
    with f2:
        above_ma = st.checkbox('收盤價站上 20 日均線', key='filter_ma20')
        filter_rsi = st.checkbox('篩選 RSI（14）範圍', key='filter_rsi')
        rsi_range = st.slider('RSI 範圍', min_value=0, max_value=100, value=(30, 70),
                              disabled=not filter_rsi)
    if st.button('開始條件選股', type='primary', key='run_screener'):
        codes = parse_symbols(screen_input, limit=13)
        if not codes:
            st.warning('請至少輸入一檔股票代號。')
        elif len(codes) > 12:
            st.warning('一次最多分析 12 檔，請減少股票代號。')
        else:
            rows = []
            failures = []
            with st.spinner('正在逐檔讀取日線資料與計算技術指標…'):
                for code in codes:
                    try:
                        df = load_history(code, '6mo')
                        if df.empty or len(df) < 21:
                            failures.append(code)
                            continue
                        actual = df.attrs.get('symbol', code)
                        rows.append(summarize(df, actual, display_name(actual, load_name(actual))))
                    except Exception:
                        failures.append(code)
            if failures:
                st.warning('以下股票資料不足或取得失敗：' + '、'.join(failures))
            if rows:
                result = screen_rows(rows,
                                     minimum_change=float(min_change) if filter_change else None,
                                     minimum_volume=int(min_volume) if filter_volume else None,
                                     above_ma20=above_ma,
                                     rsi_min=float(rsi_range[0]) if filter_rsi else None,
                                     rsi_max=float(rsi_range[1]) if filter_rsi else None)
                st.success(f'已分析 {len(rows)} 檔，符合條件 {len(result)} 檔。')
                if result.empty:
                    st.info('目前沒有符合條件的股票，可放寬條件後重試。')
                else:
                    result_view = result.copy()
                    result_view['站上20日均線'] = result_view['站上20日均線'].map({True:'是', False:'否'})
                    st.dataframe(result_view, hide_index=True, use_container_width=True)
                    st.download_button('⬇️ 下載篩選結果（CSV）',
                                       data=result_view.to_csv(index=False).encode('utf-8-sig'),
                                       file_name='台股小幫手_條件選股結果.csv', mime='text/csv')
                st.caption('不同股票的最後資料日期可能不同，請查看表格的「資料日期」。')
            else:
                st.error('候選清單均無法取得足夠的日線資料。')

# ──────────────────────────────────────────────────────────────
# V3 第三階段：投資組合與均線策略回測（模擬用途）
# ──────────────────────────────────────────────────────────────
from portfolio_backtest import validate_holdings, calculate_portfolio, backtest_ma
import plotly.graph_objects as go

st.divider()
st.header('💼 V3 第三階段｜模擬投資組合與策略回測')
st.caption('所有計算僅供學習與書審展示，並非真實帳戶或投資建議。報價為最近可取得的日線收盤價。')
portfolio_tab, backtest_tab = st.tabs(['💰 投資組合與損益', '📉 歷史策略回測'])

with portfolio_tab:
    st.subheader('模擬投資組合')
    st.write('可修改下表股票代號、買入價格與股數；同一股票可分筆輸入。表格是模擬範例，重新整理或關閉瀏覽器後可能重設，請下載 CSV 留存結果。')
    if 'portfolio_input' not in st.session_state:
        st.session_state.portfolio_input = pd.DataFrame([
            {'股票代號': '2330', '買入價格': 1000.0, '股數': 100},
            {'股票代號': '2317', '買入價格': 200.0, '股數': 1000},
        ])
    edited = st.data_editor(st.session_state.portfolio_input, num_rows='dynamic', hide_index=True,
                            use_container_width=True, key='portfolio_editor',
                            column_config={
                                '股票代號': st.column_config.TextColumn('股票代號'),
                                '買入價格': st.column_config.NumberColumn('買入價格（元）', min_value=0.01, format='%.2f'),
                                '股數': st.column_config.NumberColumn('股數（股）', min_value=1, step=1, format='%d'),
                            })
    if st.button('計算模擬投資損益', type='primary', key='calc_portfolio'):
        try:
            positions = validate_holdings(edited.to_dict('records'))
            if not positions:
                st.warning('請至少輸入一筆有效的持倉。')
            else:
                with st.spinner('正在取得各檔股票的最近日線資料…'):
                    result, failed = calculate_portfolio(
                        positions, lambda code: load_history(normalize_symbol(code), '1mo'))
                if failed:
                    st.warning('以下股票資料取得失敗：' + '、'.join(failed))
                if not result.empty:
                    invested = float(result['投入成本'].sum())
                    current = float(result['目前估值'].sum())
                    gain = current - invested
                    a, b, c, d = st.columns(4)
                    a.metric('投入成本', f'{invested:,.2f} 元')
                    b.metric('目前估值', f'{current:,.2f} 元')
                    c.metric('未實現損益', f'{gain:+,.2f} 元')
                    d.metric('未實現報酬率', f'{gain/invested*100:+.2f}%')
                    st.dataframe(result, hide_index=True, use_container_width=True)
                    st.download_button('⬇️ 下載投資組合報告（CSV）',
                                       data=result.to_csv(index=False).encode('utf-8-sig'),
                                       file_name='模擬投資組合報告.csv', mime='text/csv')
                    st.caption('未計入買賣手續費、證交稅、股利、匯率或公司行動；不同股票資料日期可能不同。')
                else:
                    st.error('沒有成功取得任何持倉的股價資料。')
        except ValueError as exc:
            st.error(str(exc))

with backtest_tab:
    st.subheader('均線交叉策略回測')
    st.write('短期均線高於長期均線時持有股票，否則持有現金。以前一交易日收盤訊號，在下一交易日開盤模擬交易，避免使用未來資料。')
    t1, t2 = st.columns(2)
    with t1:
        test_code = st.text_input('回測股票代號', value='2330', key='bt_code')
        test_period = st.selectbox('回測資料期間', ['1 年', '2 年', '5 年'], index=1, key='bt_period')
        short_ma = st.number_input('短期均線天數', min_value=2, max_value=100, value=5, step=1)
    with t2:
        long_ma = st.number_input('長期均線天數', min_value=3, max_value=200, value=20, step=1)
        fee_pct = st.number_input('單邊手續費率（%）', min_value=0.0, max_value=2.0, value=0.1425, step=0.01, format='%.4f')
        tax_pct = st.number_input('賣出交易稅率（%）', min_value=0.0, max_value=2.0, value=0.3, step=0.01, format='%.4f')
    if st.button('開始策略回測', type='primary', key='run_backtest'):
        if short_ma >= long_ma:
            st.warning('短期均線天數必須小於長期均線天數。')
        elif not test_code.strip():
            st.warning('請輸入股票代號。')
        else:
            try:
                df_bt = load_history(normalize_symbol(test_code), {'1 年': '1y', '2 年': '2y', '5 年': '5y'}[test_period])
                if df_bt.empty:
                    st.warning('無法取得該股票的歷史資料。')
                else:
                    curve, trades, metrics = backtest_ma(df_bt, int(short_ma), int(long_ma),
                                                         float(fee_pct)/100, float(tax_pct)/100)
                    cols = st.columns(4)
                    for col, (label, val) in zip(cols, metrics.items()):
                        col.metric(label, f'{val:,}' if label == '交易次數' else f'{val:+.2f}%')
                    fig_bt = go.Figure()
                    fig_bt.add_scatter(x=curve.index, y=curve['策略累積報酬（%）'], name='均線策略')
                    fig_bt.add_scatter(x=curve.index, y=curve['買入持有累積報酬（%）'], name='買入並持有')
                    fig_bt.update_layout(title='模擬累積報酬比較', xaxis_title='日期', yaxis_title='累積報酬（%）',
                                         template='plotly_dark', hovermode='x unified')
                    st.plotly_chart(fig_bt, use_container_width=True, config=CHART_CONFIG)
                    with st.expander('查看模擬交易紀錄'):
                        if trades.empty:
                            st.info('這段期間沒有觸發交易。')
                        else:
                            st.dataframe(trades, hide_index=True, use_container_width=True)
                    st.download_button('⬇️ 下載回測淨值資料（CSV）',
                                       data=curve.to_csv().encode('utf-8-sig'),
                                       file_name='均線策略回測淨值.csv', mime='text/csv')
                    st.caption('假設初始資金 100,000 元，允許零股及小數股數模擬；收盤訊號於次日開盤成交。未計滑價、股利、最低手續費、流動性與市場衝擊。交易費稅為可調假設，結果不能代表實際交易績效。')
            except (ValueError, KeyError) as exc:
                st.error(f'無法完成回測：{exc}')
            except Exception as exc:
                st.error(f'讀取或計算回測資料時發生問題：{exc}')


st.divider()
st.subheader('📚 專題說明與版本資訊')
st.caption('台股小幫手 V3｜第四階段：作品展示與品質檢查版 · 製作者：王聖凱 · 寒假轉學書審作品')
st.info('本系統使用第三方歷史日線資料；技術指標、條件選股與策略回測僅供教學與研究，不提供即時交易訊號。')
