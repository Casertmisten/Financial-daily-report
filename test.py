import adata

# 获取全市场最新行情（支持多源自动切换）
df_all = adata.stock.market.get_market_index(index_code="399001")


print(df_all)

# # 字段示例：代码、名称、最新价、涨跌幅、成交额、换手率、量比等
# print(df_all.columns)

# # 单只股票实时行情（5档深度）
# df_one = adata.stock.market.get_market_five(symbol="600519")
# print(df_one)

# # 分时行情（当天）
# df_min = adata.stock.market.get_market_min(symbol="600519")