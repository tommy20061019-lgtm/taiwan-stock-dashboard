import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pandas as pd
from portfolio_backtest import validate_holdings, calculate_portfolio, backtest_ma

class PortfolioTests(unittest.TestCase):
    def test_valid_holdings(self):
        self.assertEqual(validate_holdings([{'股票代號':'2330','買入價格':1000,'股數':100}]), [('2330',1000.0,100)])
    def test_invalid_holdings(self):
        with self.assertRaises(ValueError):
            validate_holdings([{'股票代號':'2330','買入價格':-1,'股數':100}])
    def test_portfolio_arithmetic(self):
        idx = pd.to_datetime(['2026-11-06'])
        df = pd.DataFrame({'Close':[1100.]},index=idx)
        result, errors = calculate_portfolio([('2330',1000.,100)], lambda _: df)
        self.assertFalse(errors)
        self.assertAlmostEqual(result.iloc[0]['投入成本'], 100000.)
        self.assertAlmostEqual(result.iloc[0]['未實現損益'], 10000.)
        self.assertAlmostEqual(result.iloc[0]['報酬率（%）'], 10.)

class BacktestTests(unittest.TestCase):
    def setUp(self):
        idx = pd.bdate_range('2026-01-01',periods=80)
        prices = [100 + i*.5 for i in range(40)] + [120 - (i-40)*.7 for i in range(40,80)]
        self.data = pd.DataFrame({'Open':prices,'Close':prices},index=idx)
    def test_output_and_no_future_trades(self):
        curve,trades,stats=backtest_ma(self.data,5,20)
        self.assertEqual(len(curve),80)
        self.assertEqual(stats['交易次數'],len(trades))
        self.assertTrue((curve['策略淨值']>=0).all())
        self.assertLessEqual(stats['最大回撤（%）'],0)
    def test_invalid_window(self):
        with self.assertRaises(ValueError):
            backtest_ma(self.data,20,5)

if __name__=='__main__': unittest.main()
