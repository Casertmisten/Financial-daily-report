from src.processors.cleaner import RuleCleaner

def test_rule_cleaner_removes_duplicates():
    cleaner = RuleCleaner()
    news = [
        {'title': '新闻A', 'content': '内容A'},
        {'title': '新闻A', 'content': '内容A'},
        {'title': '新闻B', 'content': '内容B'},
    ]
    result = cleaner.clean(news)
    assert len(result) == 2

def test_rule_cleaner_normalizes_time():
    cleaner = RuleCleaner()
    news = [
        {'title': '新闻', 'content': '内容', 'time': '2024-03-11 08:30'},
    ]
    result = cleaner.clean(news)
    assert 'time' in result[0]
