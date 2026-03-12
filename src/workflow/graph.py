"""LangGraph 工作流图"""
from langgraph.graph import StateGraph, END
from src.workflow.state import ReportState
from src.workflow.nodes import (
    collect_node, clean_node, store_node, vectorize_node, rag_node,
    pre_market_generate_node, mid_close_generate_node, after_close_generate_node,
    save_node, route_by_report_type, analyze_node  # 新增 analyze_node
)


def create_report_graph() -> StateGraph:
    """创建日报生成工作流图"""
    builder = StateGraph(ReportState)

    # 添加所有节点
    builder.add_node("collect", collect_node)
    builder.add_node("clean", clean_node)
    builder.add_node("analyze", analyze_node)
    builder.add_node("store", store_node)
    builder.add_node("vectorize", vectorize_node)
    builder.add_node("rag", rag_node)
    builder.add_node("pre_market_generate", pre_market_generate_node)
    builder.add_node("mid_close_generate", mid_close_generate_node)
    builder.add_node("after_close_generate", after_close_generate_node)
    builder.add_node("save", save_node)

    # 设置入口点
    builder.set_entry_point("collect")

    # 构建线性流程
    builder.add_edge("collect", "clean")
    builder.add_edge("clean", "analyze")
    builder.add_edge("analyze", "store")
    builder.add_edge("store", "vectorize")
    builder.add_edge("vectorize", "rag")

    # 条件路由
    builder.add_conditional_edges(
        "rag",
        route_by_report_type,
        {
            "pre_market_generate": "pre_market_generate",
            "mid_close_generate": "mid_close_generate",
            "after_close_generate": "after_close_generate"
        }
    )

    # 所有生成节点汇聚到 save
    builder.add_edge("pre_market_generate", "save")
    builder.add_edge("mid_close_generate", "save")
    builder.add_edge("after_close_generate", "save")

    builder.add_edge("save", END)

    return builder.compile()


# 全局图实例
report_graph = create_report_graph()
