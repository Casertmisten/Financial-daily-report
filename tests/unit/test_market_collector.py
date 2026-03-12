from src.collectors.market_collector import MarketCollector

def test_market_collector_collect_returns_dict():
    collector = MarketCollector()
    result = collector.collect()
    assert isinstance(result, dict)

def test_market_collector_has_stocks_data():
    collector = MarketCollector()
    result = collector.collect()
    assert 'stocks' in result
    assert 'industry_flow' in result
