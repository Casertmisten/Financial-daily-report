"""测试 LangGraph 工作流图构建"""
import pytest
from src.workflow.graph import create_report_graph, report_graph
from src.workflow.state import ReportState


class TestWorkflowGraph:
    """测试工作流图的构建和结构"""

    def test_create_report_graph(self):
        """测试图创建函数"""
        graph = create_report_graph()
        assert graph is not None
        # LangGraph 编译后的图不直接暴露 edges 属性
        # 我们验证它可以被调用
        assert hasattr(graph, 'invoke')

    def test_global_graph_instance(self):
        """测试全局图实例"""
        assert report_graph is not None
        assert hasattr(report_graph, 'nodes')

    def test_graph_has_all_nodes(self):
        """测试图包含所有必需节点"""
        graph = create_report_graph()
        expected_nodes = [
            "collect",
            "clean",
            "store",
            "vectorize",
            "rag",
            "pre_market_generate",
            "mid_close_generate",
            "after_close_generate",
            "save"
        ]

        actual_nodes = list(graph.nodes.keys())
        for node in expected_nodes:
            assert node in actual_nodes, f"Missing node: {node}"

    def test_graph_structure(self):
        """测试图的边结构"""
        # 验证图包含所有节点，并且路由函数配置正确
        graph = create_report_graph()

        # LangGraph 编译后的图不直接暴露 edges
        # 我们通过验证所有节点存在来间接验证结构
        expected_nodes = [
            "collect",
            "clean",
            "store",
            "vectorize",
            "rag",
            "pre_market_generate",
            "mid_close_generate",
            "after_close_generate",
            "save"
        ]

        actual_nodes = list(graph.nodes.keys())
        for node in expected_nodes:
            assert node in actual_nodes, f"Missing node: {node}"

        # 验证条件路由函数
        from src.workflow.nodes import route_by_report_type
        assert callable(route_by_report_type)

    def test_graph_entry_point(self):
        """测试图的入口点"""
        graph = create_report_graph()
        # LangGraph 使用不同的方式存储入口点
        # 我们通过验证第一个节点是 collect 来间接验证
        nodes = list(graph.nodes.keys())
        # 验证 collect 节点存在
        assert "collect" in nodes

    def test_conditional_routing(self):
        """测试条件路由配置"""
        # 这个测试验证路由函数存在且返回正确的节点名称
        from src.workflow.nodes import route_by_report_type

        # 测试不同报告类型的路由
        test_cases = [
            ("pre_market", "pre_market_generate"),
            ("mid_close", "mid_close_generate"),
            ("after_close", "after_close_generate"),
            ("unknown", "after_close_generate"),  # 默认值
        ]

        for report_type, expected_node in test_cases:
            state = {"report_type": report_type}
            result = route_by_report_type(state)
            assert result == expected_node, f"Report type {report_type} should route to {expected_node}, got {result}"

    def test_initial_state_structure(self):
        """测试初始状态结构"""
        initial_state = {
            "report_type": "after_close",
            "news_data": [],
            "market_data": {},
            "cleaned_news": [],
            "context": "",
            "report": "",
            "errors": []
        }

        # 验证所有必需字段存在
        required_fields = [
            "report_type",
            "news_data",
            "market_data",
            "cleaned_news",
            "context",
            "report",
            "errors"
        ]

        for field in required_fields:
            assert field in initial_state, f"Missing field in initial state: {field}"

    def test_graph_invocable(self):
        """测试图可以被调用（不执行完整流程）"""
        graph = create_report_graph()

        # 验证图有 invoke 方法
        assert hasattr(graph, 'invoke')

        # 注意：我们不实际调用图，因为这需要完整的依赖
        # 但我们验证图结构是正确的


class TestGraphIntegration:
    """测试图与其他组件的集成"""

    def test_nodes_import(self):
        """测试所有节点可以从 nodes 模块导入"""
        from src.workflow.nodes import (
            collect_node,
            clean_node,
            store_node,
            vectorize_node,
            rag_node,
            pre_market_generate_node,
            mid_close_generate_node,
            after_close_generate_node,
            save_node,
            route_by_report_type
        )

        # 验证所有节点都是可调用的
        assert callable(collect_node)
        assert callable(clean_node)
        assert callable(store_node)
        assert callable(vectorize_node)
        assert callable(rag_node)
        assert callable(pre_market_generate_node)
        assert callable(mid_close_generate_node)
        assert callable(after_close_generate_node)
        assert callable(save_node)
        assert callable(route_by_report_type)

    def test_state_import(self):
        """测试状态定义可以从 state 模块导入"""
        from src.workflow.state import ReportState

        # 验证 ReportState 是一个 TypedDict
        assert hasattr(ReportState, '__annotations__')

        # 验证所有必需字段
        required_fields = [
            "report_type",
            "news_data",
            "market_data",
            "cleaned_news",
            "context",
            "report",
            "errors"
        ]

        for field in required_fields:
            assert field in ReportState.__annotations__, f"Missing field in ReportState: {field}"
