# V3 第四階段｜安裝與測試

1. 用 VS Code 開啟**包含 app.py 的資料夾**。
2. 執行 `python -m pip install -r requirements.txt`。
3. 執行 `python -m streamlit run app.py`。
4. 驗證主畫面、中文署名、K 線與技術指標。
5. 在比較功能輸入 `2330,2317,0050`。
6. 使用模擬投資組合範例確認損益數值。
7. 回測 2330、2 年、短期 5 日／長期 20 日，確認交易紀錄可展開。
8. 執行 `python -m unittest discover -s tests -v` 進行離線計算測試。

注意：離線測試不代表網路資料、PNG 匯出與瀏覽器 UI 都已通過實機驗證。
