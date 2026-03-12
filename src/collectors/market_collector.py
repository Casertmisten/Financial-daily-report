import adata
import akshare as ak
from loguru import logger
from src.collectors.base import BaseCollector
from typing import Dict

class MarketCollector(BaseCollector):
    def __init__(self):
        super().__init__("MarketCollector")

    def collect(self) -> Dict:
        result = {
            'indices': [],
            'industry_flow': [],
            'concept_flow': [],
            'main_flow': [],
            'lhb': []
        }

        # 获取三大指数行情（上证、深证、创业板）
        index_codes = {
            '000001': '上证指数',
            '399001': '深证成指',
            '399006': '创业板指'
        }
        for code, name in index_codes.items():
            try:
                df = adata.stock.market.get_market_index(index_code=code)
                if df is not None and not df.empty:
                    # 添加指数名称
                    df['index_name'] = name
                    result['indices'].append(df.to_dict('records')[0])
                    logger.info(f"{name}({code}): 获取成功")
            except Exception as e:
                logger.warning(f"{name}({code}) 采集失败: {e}")

        # 行业资金流
        try:
            df = ak.stock_fund_flow_industry(symbol="即时")
            result['industry_flow'] = df.to_dict('records')
            logger.info(f"行业资金流: 获取 {len(df)} 条")
        except Exception as e:
            logger.warning(f"行业资金流采集失败: {e}")

        # 概念资金流
        try:
            df = ak.stock_fund_flow_concept(symbol="即时")
            result['concept_flow'] = df.to_dict('records')
            logger.info(f"概念资金流: 获取 {len(df)} 条")
        except Exception as e:
            logger.warning(f"概念资金流采集失败: {e}")

        # 主力资金流
        # try:
        #     df = ak.stock_main_fund_flow(symbol="全部股票")
        #     result['main_flow'] = df.to_dict('records')[:50]  # 限制前50条
        #     logger.info(f"主力资金流: 获取 {len(df)} 条")
        # except Exception as e:
        #     logger.warning(f"主力资金流采集失败: {e}")

        # 龙虎榜（获取最近一天）
        try:
            from datetime import datetime, timedelta
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=3)).strftime("%Y%m%d")
            df = ak.stock_lhb_detail_em(start_date=start_date, end_date=end_date)
            result['lhb'] = df.to_dict('records')
            logger.info(f"龙虎榜: 获取 {len(df)} 条")
        except Exception as e:
            logger.warning(f"龙虎榜采集失败: {e}")

        # 统计成功采集的数据
        success_count = sum(1 for v in result.values() if v)
        logger.success(f"市场数据采集完成 (成功: {success_count}/5)")

        return result
