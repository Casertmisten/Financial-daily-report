"""LLM客户端模块，提供统一的LLM调用接口"""
from typing import List, Dict, Optional
from loguru import logger
import json
from openai import OpenAI
from config.settings import config


class LLMClient:
    """LLM客户端，支持聊天、清洗和向量化功能"""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        chat_model: Optional[str] = None,
        clean_model: Optional[str] = None,
        embedding_model: Optional[str] = None
    ):
        """
        初始化LLM客户端

        Args:
            base_url: API基础URL
            api_key: API密钥
            chat_model: 聊天模型名称
            clean_model: 清洗模型名称
            embedding_model: 向量化模型名称
        """
        self.base_url = base_url or config.llm.base_url
        self.api_key = api_key or config.llm.api_key
        self.chat_model = chat_model or config.llm.chat_model
        self.clean_model = clean_model or config.llm.clean_model
        self.embedding_model = embedding_model or config.embedding.embedding_model
        self.embedding_api_type = config.embedding.api_type  # "openai" 或 "ollama"

        # 初始化OpenAI客户端
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )
        self.embedding_client = OpenAI(
            base_url=config.embedding.base_url,
            api_key=config.embedding.api_key
        )

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        通用聊天接口

        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            model: 使用的模型，默认使用chat_model
            temperature: 温度参数，控制随机性
            max_tokens: 最大token数
            **kwargs: 其他参数

        Returns:
            模型回复的文本内容
        """
        model = model or self.chat_model

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            content = response.choices[0].message.content
            logger.debug(f"LLM chat成功，模型: {model}")
            return content
        except Exception as e:
            logger.error(f"LLM chat失败: {e}")
            raise

    def clean(
        self,
        text: str,
        model: Optional[str] = None,
        temperature: float = 0.3,
        **kwargs
    ) -> Dict:
        """
        数据清洗接口，返回结构化的清洗结果

        Args:
            text: 待清洗的文本
            model: 使用的模型，默认使用clean_model
            temperature: 温度参数，清洗任务使用较低温度
            **kwargs: 其他参数

        Returns:
            清洗结果字典，包含：
            - cleaned_content: 清洗后的内容
            - entities: 提取的实体列表
            - sentiment: 情感倾向
            - importance: 重要性评分(1-5)
            - tags: 标签列表
            - is_trash: 是否为垃圾信息
        """
        model = model or self.clean_model

        system_prompt = """你是一个专业的金融新闻数据清洗助手。请对输入的新闻内容进行清洗和结构化提取。

请严格按照以下JSON格式返回结果：
{
    "cleaned_content": "清洗后的新闻内容，去除HTML标签和冗余信息",
    "entities": ["提取的实体列表，如公司名、人名等"],
    "sentiment": "情感倾向，可选值: positive/neutral/negative",
    "importance": 1-5的整数，表示新闻重要性",
    "tags": ["相关标签，如行业、概念等"],
    "is_trash": false
}

判断标准：
- importance: 5=重大突发, 4=重要公告, 3=常规新闻, 2=轻微影响, 1=无实际内容
- is_trash: 广告、重复内容、无实际信息等应标记为true
- sentiment: 根据对公司/市场的影响判断"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ]

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                response_format={"type": "json_object"},
                **kwargs
            )
            content = response.choices[0].message.content
            result = json.loads(content)
            logger.debug(f"LLM clean成功，模型: {model}")
            return result
        except Exception as e:
            logger.error(f"LLM clean失败: {e}")
            # 返回默认值，确保不会中断流程
            return {
                "cleaned_content": text,
                "entities": [],
                "sentiment": "neutral",
                "importance": 3,
                "tags": [],
                "is_trash": False
            }

    def embed(
        self,
        texts: List[str],
        model: Optional[str] = None,
        **kwargs
    ) -> List[List[float]]:
        """
        向量化接口，将文本转换为向量

        Args:
            texts: 待向量化的文本列表
            model: 使用的模型，默认使用embedding_model
            **kwargs: 其他参数

        Returns:
            向量列表，每个向量是一个浮点数列表
        """
        model = model or self.embedding_model

        try:
            # 批量处理，每次最多处理100个文本
            all_embeddings = []
            batch_size = 100

            if self.embedding_api_type == "ollama":
                # Ollama API 格式：使用 prompt 参数，每次处理一个文本
                import requests
                for text in texts:
                    response = requests.post(
                        f"{config.embedding.base_url}/api/embeddings",
                        json={"model": model, "prompt": text},
                        **kwargs
                    ).json()
                    if "embedding" in response:
                        all_embeddings.append(response["embedding"])
            else:
                # OpenAI 兼容格式：使用 input 参数
                for i in range(0, len(texts), batch_size):
                    batch = texts[i:i + batch_size]
                    response = self.embedding_client.embeddings.create(
                        model=model,
                        input=batch,
                        **kwargs
                    )
                    embeddings = [item.embedding for item in response.data]
                    all_embeddings.extend(embeddings)

            logger.debug(f"LLM embed成功，处理 {len(texts)} 个文本，模型: {model}")
            return all_embeddings
        except Exception as e:
            logger.error(f"LLM embed失败: {e}")
            raise

    def test_connection(self) -> Dict[str, bool]:
        """
        测试LLM模型连通性

        在每次调用前验证两个模型是否可用：
        1. 生成模型 (chat_model)
        2. 嵌入模型 (embedding_model)

        Returns:
            测试结果字典:
            {
                "chat_model": True/False,  # 生成模型是否连通
                "embedding_model": True/False,  # 嵌入模型是否连通
                "all_ok": True/False  # 全部是否连通
            }
        """
        results = {
            "chat_model": False,
            "embedding_model": False,
            "all_ok": False
        }

        # 测试生成模型
        try:
            logger.info(f"测试生成模型连通性: {self.chat_model}")
            response = self.client.chat.completions.create(
                model=self.chat_model,
                messages=[{"role": "user", "content": "测试"}],
                max_tokens=10
            )
            if response.choices and response.choices[0].message.content:
                results["chat_model"] = True
                logger.success(f"✓ 生成模型连通: {self.chat_model}")
        except Exception as e:
            logger.error(f"✗ 生成模型连接失败: {self.chat_model} - {e}")

        # 测试嵌入模型
        try:
            logger.info(f"测试嵌入模型连通性: {self.embedding_model}")

            if self.embedding_api_type == "ollama":
                # Ollama API 测试
                import requests
                response = requests.post(
                    f"{config.embedding.base_url}/api/embeddings",
                    json={"model": self.embedding_model, "prompt": "测试"},
                    timeout=10
                )
                if response.status_code == 200 and "embedding" in response.json():
                    results["embedding_model"] = True
                    logger.success(f"✓ 嵌入模型连通: {self.embedding_model}")
            else:
                # OpenAI 兼容 API 测试
                response = self.embedding_client.embeddings.create(
                    model=self.embedding_model,
                    input=["测试"]
                )
                if response.data and len(response.data) > 0:
                    results["embedding_model"] = True
                    logger.success(f"✓ 嵌入模型连通: {self.embedding_model}")
        except Exception as e:
            logger.error(f"✗ 嵌入模型连接失败: {self.embedding_model} - {e}")

        results["all_ok"] = results["chat_model"] and results["embedding_model"]

        return results

    def analyze(
        self,
        text: str,
        model: Optional[str] = None,
        temperature: float = 0.3,
        **kwargs
    ) -> Dict:
        """
        深度分析接口，提取事件类型和标的关联

        Args:
            text: 待分析的文本，格式：标题 + 内容
            model: 使用的模型，默认使用 clean_model
            temperature: 温度参数，使用较低温度保证稳定性

        Returns:
            分析结果字典：
            {
                "event_type": "事件类型（从预定义列表选择）",
                "event_subtype": "具体子类型",
                "related_stocks": {
                    "direct": ["代码:名称", ...],
                    "indirect": ["行业", ...],
                    "concepts": ["概念", ...]
                }
            }
        """
        model = model or self.clean_model

        system_prompt = """你是专业的金融新闻分析助手。请分析以下新闻，提取事件类型和关联标的。

## 预定义事件类型
- 财报类：业绩预告、财报发布、业绩修正、分红预案、送转方案
- 重组并购类：收购、兼并、资产重组、股权转让、借壳上市
- 政策影响类：行业政策、监管变化、税收政策、产业规划、地方政策
- 经营类：重大合同、产品发布、产能扩张、战略合作、业务调整
- 风险类：诉讼、处罚、停产、退市风险、债务违约
- 其他：高管变更、股东变动、股份回购、其他

## 标的关联规则
- 直接标的：新闻明确提到的股票代码或公司名称，格式：代码:名称
- 间接标的：通过公司所属行业推断
- 概念标的：相关的概念板块

请严格按照 JSON 格式返回：
{
    "event_type": "事件类型（从预定义列表中选择）",
    "event_subtype": "具体子类型",
    "related_stocks": {
        "direct": ["股票代码:公司名称"],
        "indirect": ["相关行业"],
        "concepts": ["相关概念板块"]
    }
}"""

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=temperature,
                response_format={"type": "json_object"}
            )
            result = json.loads(response.choices[0].message.content)

            # 验证和修正结果
            result = self._validate_analysis_result(result)
            logger.debug(f"LLM analyze 成功")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"LLM analyze JSON 解析失败: {e}")
            return self._get_default_analysis_result()
        except Exception as e:
            logger.error(f"LLM analyze 失败: {e}")
            return self._get_default_analysis_result()

    def _validate_analysis_result(self, result: Dict) -> Dict:
        """验证和修正分析结果"""
        valid_event_types = [
            '财报类', '重组并购类', '政策影响类',
            '经营类', '风险类', '其他'
        ]

        # 验证事件类型
        if result.get('event_type') not in valid_event_types:
            logger.warning(f"无效事件类型 '{result.get('event_type')}'，使用默认值 '其他'")
            result['event_type'] = '其他'

        # 验证 related_stocks 结构
        if 'related_stocks' not in result:
            result['related_stocks'] = {}

        stocks = result['related_stocks']
        for key in ['direct', 'indirect', 'concepts']:
            if key not in stocks:
                stocks[key] = []
            if not isinstance(stocks[key], list):
                logger.warning(f"related_stocks.{key} 应为列表，已修正")
                stocks[key] = []

        return result

    def _get_default_analysis_result(self) -> Dict:
        """返回默认的分析结果"""
        return {
            "event_type": "其他",
            "event_subtype": "",
            "related_stocks": {
                "direct": [],
                "indirect": [],
                "concepts": []
            }
        }


# 全局LLM客户端实例
llm_client = LLMClient()
