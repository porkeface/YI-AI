# YI-AI 详细 AI 架构设计文档

> 本文档是 `yiai.md` 的 AI 层深化设计，聚焦多模型协同、RAG、Agent、长期记忆、Prompt、知识图谱、AI 解释引擎及评估策略。

---

## 目录

1. [多模型协同架构](#1-多模型协同架构)
2. [RAG 系统设计](#2-rag-系统设计)
3. [Agent 系统设计](#3-agent-系统设计)
4. [长期记忆系统](#4-长期记忆系统)
5. [Prompt 系统](#5-prompt-系统)
6. [知识图谱构建](#6-知识图谱构建)
7. [AI 解释引擎](#7-ai-解释引擎)
8. [评估和优化策略](#8-评估和优化策略)

---

## 1. 多模型协同架构

### 1.1 设计原则

核心原则：**不同任务分配不同模型，成本与能力匹配。**

规则计算不经过 LLM，由确定性引擎完成。LLM 只负责语义理解与自然语言生成。

### 1.2 模型分层

```
┌─────────────────────────────────────────────────────────────┐
│                    请求入口 (API Gateway)                     │
│                     ↓ 任务分类器 ↓                           │
├───────────┬───────────┬──────────────┬──────────────────────┤
│  Tier 1   │  Tier 2   │   Tier 3     │      Tier 4          │
│ 轻量推理  │ 标准解释  │  深度分析    │     推演规划          │
│           │           │              │                      │
│ DeepSeek  │ Qwen-Max  │ Claude       │ Claude / GPT-4o      │
│ Qwen-Turbo│ DeepSeek  │ Sonnet 4.6   │ + Extended Thinking  │
│           │           │              │                      │
│ 意图分类  │ 卦象解释  │  长期趋势    │  Agent 自动推演      │
│ 实体提取  │ 爻辞翻译  │  多卦关联    │  复杂决策树          │
│ 情感判断  │ 五行分析  │  用户画像    │  概率演化模拟        │
└───────────┴───────────┴──────────────┴──────────────────────┘
```

### 1.3 任务-模型映射表

| 任务类型 | 输入复杂度 | 推荐模型 | 理由 | 预估 token |
|---------|-----------|---------|------|-----------|
| 意图分类 | 低 | DeepSeek-V3 / Qwen-Turbo | 快速、低成本、分类准确 | 200-500 |
| 实体提取 | 低 | DeepSeek-V3 | 结构化输出能力强 | 300-800 |
| 卦象基础解释 | 中 | Qwen-Max / DeepSeek | 中文理解好、成本适中 | 1000-2000 |
| 爻辞古文翻译 | 中 | Qwen-Max | 古文能力最强 | 800-1500 |
| 五行关系分析 | 中 | DeepSeek-Reasoner | 推理链清晰 | 1500-3000 |
| 长期趋势报告 | 高 | Claude Sonnet 4.6 | 长上下文、分析深度 | 3000-6000 |
| 多卦关联分析 | 高 | Claude Sonnet 4.6 | 复杂关系推理 | 4000-8000 |
| Agent 自动推演 | 极高 | Claude Opus 4.5 / GPT-4o | 规划与多步推理 | 8000-16000 |
| 用户画像生成 | 高 | Claude Sonnet 4.6 | 综合分析能力 | 3000-5000 |

### 1.4 模型路由层

```python
# ai/router/model_router.py

from enum import Enum
from dataclasses import dataclass

class TaskTier(Enum):
    TIER_1_LIGHTWEIGHT = "lightweight"     # 意图分类、实体提取
    TIER_2_STANDARD = "standard"           # 卦象解释、爻辞翻译
    TIER_3_DEEP = "deep"                   # 长期趋势、多卦关联
    TIER_4_PLANNING = "planning"           # Agent推演、复杂决策

@dataclass
class ModelConfig:
    model_id: str
    provider: str              # openai / anthropic / deepseek / qwen
    max_tokens: int
    cost_per_1k_input: float
    cost_per_1k_output: float
    supports_streaming: bool
    supports_thinking: bool
    context_window: int

MODEL_REGISTRY: dict[TaskTier, list[ModelConfig]] = {
    TaskTier.TIER_1_LIGHTWEIGHT: [
        ModelConfig("deepseek-chat", "deepseek", 4096, 0.001, 0.002, True, False, 64000),
        ModelConfig("qwen-turbo", "qwen", 4096, 0.002, 0.006, True, False, 128000),
    ],
    TaskTier.TIER_2_STANDARD: [
        ModelConfig("qwen-max", "qwen", 8192, 0.02, 0.06, True, False, 32000),
        ModelConfig("deepseek-chat", "deepseek", 8192, 0.001, 0.002, True, False, 64000),
    ],
    TaskTier.TIER_3_DEEP: [
        ModelConfig("claude-sonnet-4-6", "anthropic", 8192, 0.003, 0.015, True, True, 200000),
        ModelConfig("deepseek-reasoner", "deepseek", 8192, 0.002, 0.008, True, True, 64000),
    ],
    TaskTier.TIER_4_PLANNING: [
        ModelConfig("claude-opus-4-5", "anthropic", 16384, 0.015, 0.075, True, True, 200000),
        ModelConfig("gpt-4o", "openai", 16384, 0.005, 0.015, True, False, 128000),
    ],
}

class ModelRouter:
    """根据任务类型、负载、成本选择最优模型。"""

    def __init__(self, cost_budget_per_request: float = 0.05):
        self.cost_budget = cost_budget_per_request
        self.model_health: dict[str, float] = {}  # model_id → health score

    async def select_model(
        self,
        tier: TaskTier,
        input_tokens: int,
        output_tokens: int,
        prefer_provider: str | None = None,
    ) -> ModelConfig:
        candidates = MODEL_REGISTRY[tier]

        if prefer_provider:
            candidates = [m for m in candidates if m.provider == prefer_provider] or candidates

        # 按成本过滤
        affordable = []
        for m in candidates:
            cost = (input_tokens * m.cost_per_1k_input + output_tokens * m.cost_per_1k_output) / 1000
            if cost <= self.cost_budget:
                affordable.append((m, cost))

        if not affordable:
            # 降级到更便宜的 tier
            return await self._fallback_select(tier, input_tokens, output_tokens)

        # 按健康度排序，选最优
        affordable.sort(key=lambda x: self.model_health.get(x[0].model_id, 1.0), reverse=True)
        return affordable[0][0]

    async def _fallback_select(self, tier, input_tokens, output_tokens):
        """降级策略：Tier 4 → Tier 3 → Tier 2 → Tier 1"""
        tier_order = [TaskTier.TIER_4_PLANNING, TaskTier.TIER_3_DEEP,
                      TaskTier.TIER_2_STANDARD, TaskTier.TIER_1_LIGHTWEIGHT]
        current_idx = tier_order.index(tier)
        for fallback_tier in tier_order[current_idx + 1:]:
            candidates = MODEL_REGISTRY[fallback_tier]
            for m in candidates:
                cost = (input_tokens * m.cost_per_1k_input + output_tokens * m.cost_per_1k_output) / 1000
                if cost <= self.cost_budget:
                    return m
        return MODEL_REGISTRY[TaskTier.TIER_1_LIGHTWEIGHT][0]
```

### 1.5 Fallback 与重试策略

```
请求 → 主模型 (超时 30s)
         │
         ├── 成功 → 返回
         │
         ├── 超时/限流 → 重试 1 次，切换同 Tier 备选模型
         │
         └── 连续失败 2 次 → 降级到下一 Tier → 记录告警
```

### 1.6 并行调用模式

当一个请求需要多个模型协作时（如"解释 + 情感分析 + 风险评估"），使用并行调用：

```python
import asyncio

async def parallel_interpretation(hexagram_data: dict, user_query: str):
    """并行调用多个模型完成不同子任务。"""
    results = await asyncio.gather(
        call_model(TaskTier.TIER_2_STANDARD, INTERPRET_PROMPT, hexagram_data),
        call_model(TaskTier.TIER_1_LIGHTWEIGHT, SENTIMENT_PROMPT, user_query),
        call_model(TaskTier.TIER_1_LIGHTWEIGHT, RISK_PROMPT, hexagram_data),
        call_model(TaskTier.TIER_3_DEEP, TREND_PROMPT, hexagram_data),
    )
    interpretation, sentiment, risk, trend = results
    return merge_results(interpretation, sentiment, risk, trend)
```

---

## 2. RAG 系统设计

### 2.1 三路检索融合架构

```
                    用户查询
                       │
           ┌───────────┼───────────┐
           ▼           ▼           ▼
     ┌──────────┐ ┌──────────┐ ┌──────────┐
     │ 向量检索  │ │ 图谱检索  │ │ 规则检索  │
     │ (Qdrant) │ │ (Neo4j)  │ │ (引擎)   │
     └────┬─────┘ └────┬─────┘ └────┬─────┘
          │            │            │
          ▼            ▼            ▼
     语义相关片段  结构化关系链  确定性规则结果
          │            │            │
          └─────────┬──┘────────────┘
                    ▼
            ┌──────────────┐
            │  融合排序器   │
            │ (RRF + 权重) │
            └──────┬───────┘
                   ▼
            上下文组装器 → LLM Prompt
```

### 2.2 向量检索（Qdrant）

#### 知识库文档分类

| Collection 名称 | 内容 | Embedding 模型 | 分块策略 |
|----------------|------|---------------|---------|
| `yijing_texts` | 易经原文、象辞、爻辞、彖传 | bge-m3 | 按卦分块，每卦一 chunk |
| `commentaries` | 历代注释（王弼、程颐、朱熹等） | bge-m3 | 按段落分块，overlap 50 |
| `modern_explanations` | 白话文解释、现代案例 | bge-m3 | 按语义段落分块 |
| `five_elements_rules` | 五行生克、旺衰、刑冲合害规则 | jina-embeddings-v3 | 按规则条目分块 |
| `divination_cases` | 历史卦例、解卦记录 | bge-m3 | 按完整卦例分块 |
| `user_history` | 用户历史卦记录（私有） | jina-embeddings-v3 | 按时间窗口分块 |

#### 检索流程

```python
# ai/rag/vector_retriever.py

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, SearchRequest

class VectorRetriever:
    def __init__(self, qdrant_url: str = "http://localhost:6333"):
        self.client = QdrantClient(url=qdrant_url)
        self.collections = [
            "yijing_texts",
            "commentaries",
            "modern_explanations",
            "five_elements_rules",
            "divination_cases",
        ]

    async def search(
        self,
        query_embedding: list[float],
        hexagram_context: dict | None = None,
        top_k: int = 10,
        score_threshold: float = 0.65,
    ) -> list[dict]:
        """跨多个 collection 检索，返回融合结果。"""
        all_results = []

        target_collections = self._select_collections(hexagram_context)

        for collection in target_collections:
            results = self.client.search(
                collection_name=collection,
                query_vector=query_embedding,
                limit=top_k,
                score_threshold=score_threshold,
                query_filter=self._build_filter(hexagram_context, collection),
            )
            for r in results:
                all_results.append({
                    "id": r.id,
                    "score": r.score,
                    "payload": r.payload,
                    "source": collection,
                })

        # 按 score 降序排列
        all_results.sort(key=lambda x: x["score"], reverse=True)
        return all_results[:top_k * 2]

    def _select_collections(self, hexagram_context: dict | None) -> list[str]:
        """根据卦象上下文动态选择检索目标 collection。"""
        if hexagram_context is None:
            return self.collections
        # 有卦象上下文时，优先检索相关 collection
        priority = ["yijing_texts", "commentaries", "five_elements_rules"]
        if hexagram_context.get("has_user_history"):
            priority.append("divination_cases")
        return priority

    def _build_filter(self, hexagram_context: dict | None, collection: str) -> Filter | None:
        """根据上下文构建过滤条件。"""
        if hexagram_context is None:
            return None
        conditions = []
        if hexagram_context.get("hexagram_name"):
            conditions.append(
                Filter(must=[{"key": "hexagram_name", "match": {"value": hexagram_context["hexagram_name"]}}])
            )
        return Filter(must=conditions) if conditions else None
```

### 2.3 图谱检索（Neo4j）

图谱检索用于获取结构化的易学关系链，如"乾卦 → 属金 → 生水 → 坎卦"。

```python
# ai/rag/graph_retriever.py

from neo4j import AsyncGraphDatabase

class GraphRetriever:
    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        self.driver = AsyncGraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

    async def search(
        self,
        hexagram_name: str,
        relation_depth: int = 2,
        relation_types: list[str] | None = None,
    ) -> dict:
        """以卦名为中心，检索 N 跳关系内的所有相关节点。"""
        if relation_types is None:
            relation_types = ["BELONGS_TO", "GENERATES", "RESTRAINS", "CLASHES",
                              "COMBINES", "TRANSFORMS_TO", "HAS_LINE", "HAS_ROLE"]

        rel_pattern = "|".join(relation_types)
        query = f"""
        MATCH path = (h:Hexagram {{name: $name}})-[:{rel_pattern}*1..{relation_depth}]-(related)
        RETURN
            [n IN nodes(path) | {{id: elementId(n), labels: labels(n), props: properties(n)}}] AS nodes,
            [r IN relationships(path) | {{type: type(r), props: properties(r)}}] AS relationships
        LIMIT 50
        """
        async with self.driver.session() as session:
            result = await session.run(query, name=hexagram_name)
            records = await result.data()

        return self._build_subgraph(records)

    async def find_element_chain(self, element: str) -> dict:
        """检索五行关系链：生我、我生、克我、我克。"""
        query = """
        MATCH (e:Element {name: $element})
        OPTIONAL MATCH (e)<-[:GENERATES]-(g:Element)
        OPTIONAL MATCH (e)-[:GENERATES]->(s:Element)
        OPTIONAL MATCH (e)<-[:RESTRAINS]-(r:Element)
        OPTIONAL MATCH (e)-[:RESTRAINS]->(rs:Element)
        RETURN
            e.name AS element,
            collect(DISTINCT g.name) AS generated_by,
            collect(DISTINCT s.name) AS generates,
            collect(DISTINCT r.name) AS restrained_by,
            collect(DISTINCT rs.name) AS restrains
        """
        async with self.driver.session() as session:
            result = await session.run(query, element=element)
            record = await result.single()
            return dict(record) if record else {}

    async def find_hexagram_transformation(self, hexagram_name: str) -> list[dict]:
        """检索卦变链：本卦 → 变卦的完整路径。"""
        query = """
        MATCH (h:Hexagram {name: $name})
        OPTIONAL MATCH (h)-[:TRANSFORMS_TO]->(changed:Hexagram)
        OPTIONAL MATCH (h)-[:ERRORS_TO]->(err:Hexagram)
        OPTIONAL MATCH (h)-[:COMBINES_WITH]->(mutual:Hexagram)
        RETURN
            h.name AS original,
            changed.name AS changed_to,
            err.name AS error_to,
            mutual.name AS mutual_with
        """
        async with self.driver.session() as session:
            result = await session.run(query, name=hexagram_name)
            return [dict(r) for r in await result.data()]

    def _build_subgraph(self, records: list[dict]) -> dict:
        """将 Neo4j 查询结果构建为统一子图结构。"""
        nodes = {}
        edges = []
        for record in records:
            for node in record["nodes"]:
                nid = node["id"]
                if nid not in nodes:
                    nodes[nid] = node
            for rel in record["relationships"]:
                edges.append(rel)
        return {"nodes": list(nodes.values()), "edges": edges}
```

### 2.4 规则检索（确定性引擎）

规则检索不经过 LLM，由确定性规则引擎直接输出结构化结果。

```python
# ai/rag/rule_retriever.py

from dataclasses import dataclass

@dataclass
class RuleResult:
    rule_name: str
    input_params: dict
    output: dict
    confidence: float  # 规则本身的确定性，确定性规则为 1.0
    explanation: str

class RuleRetriever:
    """确定性规则引擎，不经过 LLM。"""

    def retrieve(self, hexagram_data: dict, user_query: str) -> list[RuleResult]:
        results = []

        # 1. 五行生克关系
        results.extend(self._five_element_relations(hexagram_data))

        # 2. 六亲关系
        results.extend(self._six_relatives(hexagram_data))

        # 3. 动爻分析
        if hexagram_data.get("moving_lines"):
            results.extend(self._moving_line_analysis(hexagram_data))

        # 4. 世应关系
        results.extend(self._world_response(hexagram_data))

        # 5. 六神分析
        results.extend(self._six_spirits(hexagram_data))

        return results

    def _five_element_relations(self, data: dict) -> list[RuleResult]:
        """计算五行生克关系。"""
        results = []
        for line in data.get("lines", []):
            element = line["element"]
            yong_shen_element = data.get("yong_shen_element")

            if yong_shen_element:
                relation = self._get_element_relation(element, yong_shen_element)
                results.append(RuleResult(
                    rule_name="five_element_relation",
                    input_params={"line_element": element, "yong_shen": yong_shen_element},
                    output={"relation": relation, "line_position": line["position"]},
                    confidence=1.0,
                    explanation=f"爻之五行 {element} 与用神五行 {yong_shen_element} 为{relation}关系",
                ))
        return results

    def _get_element_relation(self, a: str, b: str) -> str:
        """确定性五行关系查询。"""
        SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
        KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

        if SHENG.get(a) == b:
            return "生（我生）"
        if SHENG.get(b) == a:
            return "生（生我）"
        if KE.get(a) == b:
            return "克（我克）"
        if KE.get(b) == a:
            return "克（克我）"
        if a == b:
            return "比和"
        return "无直接关系"

    def _six_relatives(self, data: dict) -> list[RuleResult]:
        """六亲关系推导。"""
        # 确定性规则：根据日辰、世爻、用神推导六亲
        # ... 完整实现
        return []

    def _moving_line_analysis(self, data: dict) -> list[RuleResult]:
        """动爻分析。"""
        return []

    def _world_response(self, data: dict) -> list[RuleResult]:
        """世应关系。"""
        return []

    def _six_spirits(self, data: dict) -> list[RuleResult]:
        """六神分析。"""
        return []
```

### 2.5 三路融合排序

```python
# ai/rag/fusion.py

from dataclasses import dataclass

@dataclass
class FusedResult:
    content: str
    source_type: str          # "vector" | "graph" | "rule"
    final_score: float
    metadata: dict

class ReciprocalRankFusion:
    """RRF + 加权融合排序器。"""

    def __init__(self, k: int = 60, weights: dict | None = None):
        self.k = k
        self.weights = weights or {
            "vector": 0.35,
            "graph": 0.30,
            "rule": 0.35,
        }

    def fuse(
        self,
        vector_results: list[dict],
        graph_results: list[dict],
        rule_results: list[dict],
        top_k: int = 15,
    ) -> list[FusedResult]:
        """三路结果融合排序。"""
        score_map: dict[str, FusedResult] = {}
        key_counter: dict[str, int] = {}

        # 向量检索结果
        for rank, result in enumerate(vector_results):
            key = self._make_key(result, "vector")
            rrf_score = 1.0 / (self.k + rank + 1)
            weighted = rrf_score * self.weights["vector"]
            if key in score_map:
                score_map[key].final_score += weighted
            else:
                score_map[key] = FusedResult(
                    content=result["payload"].get("text", ""),
                    source_type="vector",
                    final_score=weighted,
                    metadata=result,
                )

        # 图谱检索结果
        for rank, result in enumerate(graph_results):
            key = self._make_key(result, "graph")
            rrf_score = 1.0 / (self.k + rank + 1)
            weighted = rrf_score * self.weights["graph"]
            if key in score_map:
                score_map[key].final_score += weighted
            else:
                score_map[key] = FusedResult(
                    content=str(result),
                    source_type="graph",
                    final_score=weighted,
                    metadata=result,
                )

        # 规则检索结果
        for rank, result in enumerate(rule_results):
            key = self._make_key(result, "rule")
            rrf_score = 1.0 / (self.k + rank + 1)
            weighted = rrf_score * self.weights["rule"]
            score_map[key] = FusedResult(
                content=result.explanation,
                source_type="rule",
                final_score=weighted,
                metadata={"rule_name": result.rule_name, "output": result.output},
            )

        # 按融合分数排序
        sorted_results = sorted(score_map.values(), key=lambda x: x.final_score, reverse=True)
        return sorted_results[:top_k]

    def _make_key(self, result: dict, source: str) -> str:
        """生成唯一键用于去重。"""
        if source == "vector":
            return f"vec:{result.get('id', id(result))}"
        elif source == "graph":
            return f"graph:{result.get('nodes', [{}])[0].get('id', id(result))}"
        else:
            return f"rule:{result.rule_name}:{hash(str(result.output))}"
```

### 2.6 上下文组装器

```python
# ai/rag/context_assembler.py

class ContextAssembler:
    """将融合后的检索结果组装为 LLM 可消费的上下文。"""

    MAX_CONTEXT_TOKENS = 6000

    def assemble(
        self,
        fused_results: list[FusedResult],
        hexagram_data: dict,
        user_query: str,
        user_memory: dict | None = None,
    ) -> str:
        sections = []

        # Section 1: 确定性规则结果（置信度最高）
        rule_results = [r for r in fused_results if r.source_type == "rule"]
        if rule_results:
            sections.append(self._format_rule_section(rule_results))

        # Section 2: 图谱关系（结构化知识）
        graph_results = [r for r in fused_results if r.source_type == "graph"]
        if graph_results:
            sections.append(self._format_graph_section(graph_results))

        # Section 3: 向量检索（语义知识）
        vector_results = [r for r in fused_results if r.source_type == "vector"]
        if vector_results:
            sections.append(self._format_vector_section(vector_results))

        # Section 4: 用户长期记忆
        if user_memory:
            sections.append(self._format_memory_section(user_memory))

        return "\n\n---\n\n".join(sections)

    def _format_rule_section(self, results: list[FusedResult]) -> str:
        lines = ["## 确定性规则分析结果（高置信度）"]
        for r in results:
            lines.append(f"- {r.content}")
        return "\n".join(lines)

    def _format_graph_section(self, results: list[FusedResult]) -> str:
        lines = ["## 知识图谱关系"]
        for r in results:
            lines.append(f"- {r.content}")
        return "\n".join(lines)

    def _format_vector_section(self, results: list[FusedResult]) -> str:
        lines = ["## 相关易学文献参考"]
        for i, r in enumerate(results[:8], 1):
            source = r.metadata.get("source", "unknown")
            lines.append(f"### 参考 {i}（来源: {source}）\n{r.content}")
        return "\n".join(lines)

    def _format_memory_section(self, memory: dict) -> str:
        lines = ["## 用户历史变化轨迹"]
        if memory.get("recent_hexagrams"):
            lines.append(f"近期卦象: {memory['recent_hexagrams']}")
        if memory.get("recurring_themes"):
            lines.append(f"反复出现的主题: {memory['recurring_themes']}")
        if memory.get("emotional_trend"):
            lines.append(f"情绪趋势: {memory['emotional_trend']}")
        return "\n".join(lines)
```

---

## 3. Agent 系统设计

### 3.1 LangGraph 工作流总览

```
┌─────────────────────────────────────────────────────────────────┐
│                    YI-AI Agent Workflow (LangGraph)              │
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │  START   │───▶│  意图     │───▶│  路由     │───▶│  分支     │  │
│  │          │    │  分类器   │    │  决策器   │    │  执行     │  │
│  └──────────┘    └──────────┘    └──────────┘    └────┬─────┘  │
│                                                       │        │
│                  ┌────────────────────────────────────┼─────┐  │
│                  ▼              ▼              ▼       ▼     │  │
│            ┌──────────┐  ┌──────────┐  ┌──────────┐ ┌─────┐ │  │
│            │  卦象     │  │  趋势     │  │  推演     │ │记忆 │ │  │
│            │  解释     │  │  分析     │  │  模拟     │ │查询 │ │  │
│            └────┬─────┘  └────┬─────┘  └────┬─────┘ └──┬──┘ │  │
│                 │              │              │          │    │  │
│                 └──────────┬───┘──────────────┘──────────┘    │  │
│                            ▼                                  │  │
│                      ┌──────────┐                             │  │
│                      │  结果     │                             │  │
│                      │  合成器   │                             │  │
│                      └────┬─────┘                             │  │
│                           ▼                                   │  │
│                      ┌──────────┐                             │  │
│                      │  安全     │                             │  │
│                      │  检查器   │                             │  │
│                      └────┬─────┘                             │  │
│                           ▼                                   │  │
│                      ┌──────────┐                             │  │
│                      │   END    │                             │  │
│                      └──────────┘                             │  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 LangGraph 状态定义

```python
# ai/agent/state.py

from typing import TypedDict, Annotated
from langgraph.graph import add_messages

class YIAgentState(TypedDict):
    """LangGraph 状态定义。"""

    # 输入
    user_query: str                          # 用户原始问题
    hexagram_data: dict | None               # 卦象结构化数据
    session_id: str                          # 会话 ID
    user_id: str                             # 用户 ID

    # 意图分类结果
    intent: str                              # "divination" | "trend" | "learn" | "memory"
    entities: dict                           # 提取的实体
    confidence: float                        # 意图分类置信度

    # RAG 检索结果
    vector_results: list[dict]
    graph_results: dict
    rule_results: list[dict]
    fused_context: str                       # 融合后的上下文

    # 记忆
    user_memory: dict | None                 # 用户长期记忆
    conversation_history: Annotated[list, add_messages]

    # 中间结果
    interpretation_draft: str                # AI 解释草稿
    risk_flags: list[str]                    # 风险标记
    sentiment: str                           # 用户情绪判断

    # 输出
    final_response: str                      # 最终回复
    response_metadata: dict                  # 元数据

    # 控制流
    current_step: str                        # 当前执行步骤
    errors: list[str]                        # 错误记录
    retry_count: int                         # 重试计数
```

### 3.3 LangGraph 工作流实现

```python
# ai/agent/workflow.py

from langgraph.graph import StateGraph, END
from ai.agent.state import YIAgentState

class YIAgentWorkflow:
    def __init__(self):
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(YIAgentState)

        # 添加节点
        workflow.add_node("classify_intent", self.classify_intent)
        workflow.add_node("retrieve_memory", self.retrieve_memory)
        workflow.add_node("route_decision", self.route_decision)
        workflow.add_node("rag_retrieve", self.rag_retrieve)
        workflow.add_node("interpret_hexagram", self.interpret_hexagram)
        workflow.add_node("analyze_trend", self.analyze_trend)
        workflow.add_node("simulate_evolution", self.simulate_evolution)
        workflow.add_node("synthesize_result", self.synthesize_result)
        workflow.add_node("safety_check", self.safety_check)

        # 定义边
        workflow.set_entry_point("classify_intent")
        workflow.add_edge("classify_intent", "retrieve_memory")
        workflow.add_edge("retrieve_memory", "route_decision")

        # 条件路由
        workflow.add_conditional_edges(
            "route_decision",
            self._route_by_intent,
            {
                "divination": "rag_retrieve",
                "trend": "rag_retrieve",
                "learn": "rag_retrieve",
                "evolution": "rag_retrieve",
            },
        )

        workflow.add_edge("rag_retrieve", "interpret_hexagram")

        workflow.add_conditional_edges(
            "interpret_hexagram",
            self._needs_trend_analysis,
            {
                "trend_needed": "analyze_trend",
                "no_trend": "synthesize_result",
            },
        )

        workflow.add_conditional_edges(
            "analyze_trend",
            self._needs_evolution,
            {
                "evolution_needed": "simulate_evolution",
                "no_evolution": "synthesize_result",
            },
        )

        workflow.add_edge("simulate_evolution", "synthesize_result")
        workflow.add_edge("synthesize_result", "safety_check")
        workflow.add_edge("safety_check", END)

        return workflow.compile()

    # ---- 节点实现 ----

    async def classify_intent(self, state: YIAgentState) -> dict:
        """Tier 1 模型：意图分类。"""
        from ai.router.model_router import TaskTier
        intent_prompt = build_intent_prompt(state["user_query"])
        result = await call_model(TaskTier.TIER_1_LIGHTWEIGHT, intent_prompt, state["user_query"])
        return {
            "intent": result["intent"],
            "entities": result["entities"],
            "confidence": result["confidence"],
        }

    async def retrieve_memory(self, state: YIAgentState) -> dict:
        """查询用户长期记忆。"""
        memory = await self.memory_engine.get_user_memory(
            user_id=state["user_id"],
            context=state["user_query"],
        )
        return {"user_memory": memory}

    async def route_decision(self, state: YIAgentState) -> dict:
        """路由决策。"""
        return {"current_step": "route_decision"}

    async def rag_retrieve(self, state: YIAgentState) -> dict:
        """三路 RAG 检索。"""
        embedding = await get_embedding(state["user_query"])
        vector_results = await self.vector_retriever.search(embedding, state["hexagram_data"])
        graph_results = await self.graph_retriever.search(
            state["hexagram_data"]["hexagram_name"] if state["hexagram_data"] else "乾"
        )
        rule_results = self.rule_retriever.retrieve(state["hexagram_data"] or {}, state["user_query"])

        fused = self.fusion.fuse(vector_results, graph_results if isinstance(graph_results, list) else [graph_results], rule_results)
        context = self.context_assembler.assemble(fused, state["hexagram_data"] or {}, state["user_query"], state["user_memory"])

        return {
            "vector_results": vector_results,
            "graph_results": graph_results if isinstance(graph_results, dict) else {},
            "rule_results": [r.__dict__ for r in rule_results],
            "fused_context": context,
        }

    async def interpret_hexagram(self, state: YIAgentState) -> dict:
        """Tier 2-3 模型：卦象解释。"""
        tier = TaskTier.TIER_3_DEEP if state["confidence"] < 0.7 else TaskTier.TIER_2_STANDARD
        prompt = build_interpretation_prompt(
            hexagram_data=state["hexagram_data"],
            context=state["fused_context"],
            user_query=state["user_query"],
            user_memory=state["user_memory"],
        )
        result = await call_model(tier, prompt, "")
        return {"interpretation_draft": result}

    async def analyze_trend(self, state: YIAgentState) -> dict:
        """Tier 3 模型：趋势分析。"""
        prompt = build_trend_prompt(state)
        result = await call_model(TaskTier.TIER_3_DEEP, prompt, "")
        return {"interpretation_draft": state["interpretation_draft"] + "\n\n" + result}

    async def simulate_evolution(self, state: YIAgentState) -> dict:
        """Tier 4 模型：推演模拟。"""
        prompt = build_evolution_prompt(state)
        result = await call_model(TaskTier.TIER_4_PLANNING, prompt, "")
        return {"interpretation_draft": state["interpretation_draft"] + "\n\n" + result}

    async def synthesize_result(self, state: YIAgentState) -> dict:
        """合成最终结果。"""
        prompt = build_synthesis_prompt(state)
        result = await call_model(TaskTier.TIER_2_STANDARD, prompt, "")
        return {"final_response": result}

    async def safety_check(self, state: YIAgentState) -> dict:
        """安全检查：确保回复不含误导性承诺。"""
        issues = self._check_safety(state["final_response"])
        if issues:
            # 修正不安全内容
            fix_prompt = build_safety_fix_prompt(state["final_response"], issues)
            fixed = await call_model(TaskTier.TIER_1_LIGHTWEIGHT, fix_prompt, "")
            return {"final_response": fixed, "risk_flags": issues}
        return {"risk_flags": []}

    # ---- 条件边 ----

    def _route_by_intent(self, state: YIAgentState) -> str:
        intent = state.get("intent", "divination")
        route_map = {
            "divination": "divination",
            "hexagram_interpretation": "divination",
            "trend_analysis": "trend",
            "learning": "learn",
            "evolution_simulation": "evolution",
        }
        return route_map.get(intent, "divination")

    def _needs_trend_analysis(self, state: YIAgentState) -> str:
        if state.get("intent") in ("trend_analysis", "evolution_simulation"):
            return "trend_needed"
        if state.get("user_memory", {}).get("recurring_themes"):
            return "trend_needed"
        return "no_trend"

    def _needs_evolution(self, state: YIAgentState) -> str:
        if state.get("intent") == "evolution_simulation":
            return "evolution_needed"
        return "no_evolution"

    def _check_safety(self, response: str) -> list[str]:
        """检查回复安全性。"""
        issues = []
        dangerous_phrases = ["一定会", "必然", "保证", "绝对会", "百分之百"]
        for phrase in dangerous_phrases:
            if phrase in response:
                issues.append(f"包含确定性承诺: '{phrase}'")
        return issues
```

### 3.4 Agent 工具集

```python
# ai/agent/tools.py

from langchain_core.tools import tool

@tool
def query_hexagram(hexagram_name: str) -> dict:
    """查询卦象的完整信息，包括卦辞、爻辞、五行属性。"""
    # 确定性查询，不经过 LLM
    return hexagram_engine.get_hexagram(hexagram_name)

@tool
def calculate_five_elements(element_a: str, element_b: str) -> dict:
    """计算两个五行元素之间的生克关系。"""
    return five_element_engine.calculate_relation(element_a, element_b)

@tool
def get_hexagram_transformation(hexagram_name: str) -> dict:
    """获取卦变信息：错卦、综卦、互卦。"""
    return hexagram_engine.get_transformations(hexagram_name)

@tool
def query_user_history(user_id: str, limit: int = 10) -> list[dict]:
    """查询用户的历史卦记录。"""
    return memory_engine.get_recent_records(user_id, limit)

@tool
def search_knowledge(query: str, collection: str = "yijing_texts") -> list[dict]:
    """在易学知识库中搜索相关内容。"""
    embedding = get_embedding_sync(query)
    return vector_retriever.search_sync(embedding, top_k=5)

@tool
def analyze_pattern(user_id: str, time_range_days: int = 90) -> dict:
    """分析用户长期变化模式。"""
    return memory_engine.analyze_pattern(user_id, time_range_days)

@tool
def simulate_hexagram_chain(start_hexagram: str, steps: int = 3) -> list[dict]:
    """模拟从一个卦开始的演化链。"""
    return evolution_engine.simulate_chain(start_hexagram, steps)

@tool
def time_analysis(ganzhi: str, hexagram_name: str) -> dict:
    """分析特定时间干支对卦象的影响。"""
    return time_engine.analyze(ganzhi, hexagram_name)
```

### 3.5 决策树

```
用户输入
  │
  ├── 意图分类 (Tier 1)
  │     ├── "divination" (占卜/解卦)
  │     │     ├── 起卦 → 规则引擎排盘
  │     │     ├── RAG 检索相关卦辞
  │     │     ├── AI 解释 (Tier 2)
  │     │     └── 返回解释 + 风险提示
  │     │
  │     ├── "trend_analysis" (趋势分析)
  │     │     ├── 查询用户历史记忆
  │     │     ├── RAG 检索历史卦例
  │     │     ├── AI 趋势分析 (Tier 3)
  │     │     └── 返回趋势报告
  │     │
  │     ├── "learning" (学习咨询)
  │     │     ├── RAG 检索易学文献
  │     │     ├── AI 知识解释 (Tier 2)
  │     │     └── 返回教学内容
  │     │
  │     └── "evolution_simulation" (推演模拟)
  │           ├── 查询当前卦状态
  │           ├── 模拟演化链
  │           ├── AI 推演分析 (Tier 4)
  │           └── 返回推演报告
  │
  └── 安全检查 → 返回
```

---

## 4. 长期记忆系统

### 4.1 记忆层级架构

```
┌─────────────────────────────────────────────────────────┐
│                    长期记忆系统                           │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │ Layer 1: 工作记忆 (Working Memory)               │    │
│  │ 存储: Redis                                      │    │
│  │ 生命周期: 当前会话                                │    │
│  │ 内容: 对话上下文、当前卦数据、中间推理结果        │    │
│  └─────────────────────────────────────────────────┘    │
│                         │ 落盘                          │
│                         ▼                               │
│  ┌─────────────────────────────────────────────────┐    │
│  │ Layer 2: 情景记忆 (Episodic Memory)              │    │
│  │ 存储: PostgreSQL + Qdrant                        │    │
│  │ 生命周期: 永久                                   │    │
│  │ 内容: 每次卦记录、AI解释、用户反馈               │    │
│  └─────────────────────────────────────────────────┘    │
│                         │ 聚合                          │
│                         ▼                               │
│  ┌─────────────────────────────────────────────────┐    │
│  │ Layer 3: 语义记忆 (Semantic Memory)              │    │
│  │ 存储: Neo4j + Qdrant                             │    │
│  │ 生命周期: 永久，定期更新                          │    │
│  │ 内容: 用户画像、变化轨迹、行为模式、偏好          │    │
│  └─────────────────────────────────────────────────┘    │
│                         │ 抽象                          │
│                         ▼                               │
│  ┌─────────────────────────────────────────────────┐    │
│  │ Layer 4: 程序记忆 (Procedural Memory)            │    │
│  │ 存储: Neo4j                                      │    │
│  │ 生命周期: 永久，低频更新                          │    │
│  │ 内容: 用户习惯性提问模式、决策偏好、响应策略      │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### 4.2 数据模型

```python
# ai/memory/models.py

from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class DivinationRecord:
    """单次卦记录（情景记忆）。"""
    record_id: str
    user_id: str
    timestamp: datetime
    hexagram_name: str              # 本卦
    changed_hexagram: str | None    # 变卦
    moving_lines: list[int]         # 动爻位置
    question: str                   # 用户问题
    ai_interpretation: str          # AI 解释
    user_feedback: str | None       # 用户反馈
    sentiment: str                  # 情绪标签
    topic_tags: list[str]           # 主题标签
    time_ganzhi: str                # 时间干支

@dataclass
class UserProfile:
    """用户画像（语义记忆）。"""
    user_id: str
    created_at: datetime
    updated_at: datetime

    # 人口学
    age_range: str | None
    occupation: str | None
    interests: list[str] = field(default_factory=list)

    # 易学特征
    frequent_hexagrams: dict[str, int] = field(default_factory=dict)  # 卦名 → 出现次数
    dominant_elements: dict[str, float] = field(default_factory=dict) # 五行偏好
    question_topics: dict[str, int] = field(default_factory=dict)     # 问题主题分布

    # 行为模式
    active_time_pattern: str | None        # 活跃时间段
    question_frequency: float = 0.0        # 平均提问频率(次/周)
    avg_session_length: float = 0.0        # 平均会话长度

    # 情绪轨迹
    emotional_trajectory: list[dict] = field(default_factory=list)
    # [{"period": "2024-01", "dominant": "anxious", "intensity": 0.7}, ...]

@dataclass
class ChangeTrajectory:
    """变化轨迹（用户某个主题的长期变化）。"""
    trajectory_id: str
    user_id: str
    topic: str                          # 主题，如"事业"、"感情"
    start_date: datetime
    end_date: datetime
    records: list[str]                  # 关联的 record_id 列表
    pattern: str                        # 识别的模式："周期性" | "渐变" | "突变" | "稳定"
    dominant_hexagrams: list[str]       # 主导卦象
    trend_direction: str                # "上升" | "下降" | "波动" | "平稳"
    key_turning_points: list[dict]      # 关键转折点

@dataclass
class BehaviorPattern:
    """行为模式（程序记忆）。"""
    pattern_id: str
    user_id: str
    pattern_type: str                   # "question_style" | "decision_preference" | "response_preference"
    description: str
    frequency: float
    examples: list[str]
    last_observed: datetime
```

### 4.3 记忆引擎实现

```python
# ai/memory/engine.py

from datetime import datetime, timedelta

class MemoryEngine:
    def __init__(self, pg_pool, qdrant_client, neo4j_driver, redis_client):
        self.pg = pg_pool
        self.qdrant = qdrant_client
        self.neo4j = neo4j_driver
        self.redis = redis_client

    # ---- 工作记忆 (Layer 1) ----

    async def get_working_memory(self, session_id: str) -> dict:
        """获取当前会话的工作记忆。"""
        data = await self.redis.get(f"session:{session_id}:memory")
        return json.loads(data) if data else {}

    async def update_working_memory(self, session_id: str, updates: dict):
        """更新工作记忆。"""
        current = await self.get_working_memory(session_id)
        current.update(updates)
        current["last_updated"] = datetime.utcnow().isoformat()
        await self.redis.setex(
            f"session:{session_id}:memory",
            timedelta(hours=2),
            json.dumps(current, ensure_ascii=False),
        )

    # ---- 情景记忆 (Layer 2) ----

    async def save_divination_record(self, record: DivinationRecord):
        """保存卦记录到 PostgreSQL 和 Qdrant。"""
        # PostgreSQL 存储结构化数据
        async with self.pg.acquire() as conn:
            await conn.execute("""
                INSERT INTO divinations
                (id, user_id, timestamp, hexagram_name, changed_hexagram,
                 moving_lines, question, ai_interpretation, user_feedback,
                 sentiment, topic_tags, time_ganzhi)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            """, record.record_id, record.user_id, record.timestamp,
                record.hexagram_name, record.changed_hexagram,
                json.dumps(record.moving_lines), record.question,
                record.ai_interpretation, record.user_feedback,
                record.sentiment, json.dumps(record.topic_tags),
                record.time_ganzhi)

        # Qdrant 存储向量（用于语义检索历史记录）
        embedding = await get_embedding(record.ai_interpretation)
        self.qdrant.upsert(
            collection_name="user_history",
            points=[{
                "id": record.record_id,
                "vector": embedding,
                "payload": {
                    "user_id": record.user_id,
                    "hexagram_name": record.hexagram_name,
                    "question": record.question,
                    "timestamp": record.timestamp.isoformat(),
                    "topic_tags": record.topic_tags,
                },
            }],
        )

    async def get_recent_records(self, user_id: str, limit: int = 10) -> list[dict]:
        """获取用户最近的卦记录。"""
        async with self.pg.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM divinations
                WHERE user_id = $1
                ORDER BY timestamp DESC
                LIMIT $2
            """, user_id, limit)
            return [dict(r) for r in rows]

    # ---- 语义记忆 (Layer 3) ----

    async def get_user_profile(self, user_id: str) -> UserProfile:
        """获取用户画像。"""
        async with self.pg.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM user_profiles WHERE user_id = $1", user_id
            )
            if row:
                return UserProfile(**dict(row))
        return UserProfile(
            user_id=user_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

    async def update_user_profile(self, user_id: str, new_record: DivinationRecord):
        """根据新记录增量更新用户画像。"""
        profile = await self.get_user_profile(user_id)

        # 更新频繁卦象
        hex_name = new_record.hexagram_name
        profile.frequent_hexagrams[hex_name] = profile.frequent_hexagrams.get(hex_name, 0) + 1

        # 更新问题主题
        for tag in new_record.topic_tags:
            profile.question_topics[tag] = profile.question_topics.get(tag, 0) + 1

        # 更新情绪轨迹
        month_key = new_record.timestamp.strftime("%Y-%m")
        existing = [e for e in profile.emotional_trajectory if e.get("period") == month_key]
        if existing:
            existing[0]["count"] = existing[0].get("count", 0) + 1
        else:
            profile.emotional_trajectory.append({
                "period": month_key,
                "dominant": new_record.sentiment,
                "count": 1,
            })

        profile.updated_at = datetime.utcnow()

        # 持久化
        async with self.pg.acquire() as conn:
            await conn.execute("""
                INSERT INTO user_profiles (user_id, created_at, updated_at,
                    frequent_hexagrams, question_topics, emotional_trajectory)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (user_id) DO UPDATE SET
                    updated_at = $3,
                    frequent_hexagrams = $4,
                    question_topics = $5,
                    emotional_trajectory = $6
            """, profile.user_id, profile.created_at, profile.updated_at,
                json.dumps(profile.frequent_hexagrams),
                json.dumps(profile.question_topics),
                json.dumps(profile.emotional_trajectory))

        # 更新 Neo4j 中的用户节点
        await self._sync_user_to_graph(profile)

    async def _sync_user_to_graph(self, profile: UserProfile):
        """将用户画像同步到 Neo4j 图谱。"""
        query = """
        MERGE (u:User {user_id: $user_id})
        SET u.updated_at = datetime()

        WITH u
        UNWIND keys($hexagrams) AS hex_name
        MERGE (h:Hexagram {name: hex_name})
        MERGE (u)-[r:QUERIED]->(h)
        SET r.count = $hexagrams[hex_name]
        """
        async with self.neo4j.session() as session:
            await session.run(query,
                user_id=profile.user_id,
                hexagrams=profile.frequent_hexagrams,
            )

    # ---- 程序记忆 (Layer 4) ----

    async def detect_behavior_patterns(self, user_id: str) -> list[BehaviorPattern]:
        """检测用户行为模式。"""
        records = await self.get_recent_records(user_id, limit=50)
        patterns = []

        # 检测提问时间模式
        time_pattern = self._analyze_time_pattern(records)
        if time_pattern:
            patterns.append(time_pattern)

        # 检测问题风格模式
        style_pattern = self._analyze_question_style(records)
        if style_pattern:
            patterns.append(style_pattern)

        return patterns

    def _analyze_time_pattern(self, records: list[dict]) -> BehaviorPattern | None:
        """分析提问时间模式。"""
        if len(records) < 10:
            return None
        hours = [r["timestamp"].hour for r in records]
        from collections import Counter
        hour_counts = Counter(hours)
        peak_hour = hour_counts.most_common(1)[0][0]
        return BehaviorPattern(
            pattern_id=f"time_{records[0]['user_id']}",
            user_id=records[0]["user_id"],
            pattern_type="question_style",
            description=f"用户倾向于在 {peak_hour}:00 左右提问",
            frequency=len(records) / 30,
            examples=[],
            last_observed=records[0]["timestamp"],
        )

    def _analyze_question_style(self, records: list[dict]) -> BehaviorPattern | None:
        """分析问题风格。"""
        return None  # 由 LLM 辅助分析

    # ---- 综合记忆查询 ----

    async def get_user_memory(self, user_id: str, context: str) -> dict:
        """获取与当前上下文相关的用户综合记忆。"""
        profile = await self.get_user_profile(user_id)
        recent = await self.get_recent_records(user_id, limit=5)
        patterns = await self.detect_behavior_patterns(user_id)

        return {
            "profile": profile.__dict__,
            "recent_hexagrams": [r["hexagram_name"] for r in recent],
            "recurring_themes": self._extract_recurring_themes(profile),
            "emotional_trend": self._get_emotional_trend(profile),
            "behavior_patterns": [p.__dict__ for p in patterns],
        }

    def _extract_recurring_themes(self, profile: UserProfile) -> list[str]:
        """提取反复出现的主题。"""
        sorted_topics = sorted(profile.question_topics.items(), key=lambda x: x[1], reverse=True)
        return [t[0] for t in sorted_topics[:5]]

    def _get_emotional_trend(self, profile: UserProfile) -> str:
        """获取情绪趋势。"""
        if not profile.emotional_trajectory:
            return "数据不足"
        recent = profile.emotional_trajectory[-3:]
        if len(recent) < 2:
            return "数据不足"
        return " → ".join([f"{r['period']}: {r['dominant']}" for r in recent])
```

### 4.4 记忆衰减与压缩

```python
# ai/memory/decay.py

class MemoryDecay:
    """记忆衰减与压缩策略。"""

    # 衰减公式: relevance = base_score * decay_factor^(days_since / half_life)
    HALF_LIFE_DAYS = 90

    async def decay_old_records(self, user_id: str):
        """对超过半衰期的记录进行衰减评分。"""
        records = await self.get_all_records(user_id)
        for record in records:
            days_old = (datetime.utcnow() - record["timestamp"]).days
            decay_score = 0.5 ** (days_old / self.HALF_LIFE_DAYS)

            if decay_score < 0.1:
                # 极低相关性：压缩为摘要
                await self._compress_to_summary(record)
            elif decay_score < 0.3:
                # 低相关性：保留关键字段，丢弃细节
                await self._compress_to_essential(record)

    async def _compress_to_summary(self, record: dict):
        """将记录压缩为一句话摘要。"""
        summary_prompt = f"用一句话概括这次卦的核心信息：{record['ai_interpretation']}"
        summary = await call_model(TaskTier.TIER_1_LIGHTWEIGHT, summary_prompt, "")
        await self._update_record_summary(record["id"], summary)

    async def _compress_to_essential(self, record: dict):
        """保留关键字段。"""
        essential = {
            "hexagram_name": record["hexagram_name"],
            "question_summary": record["question"][:100],
            "sentiment": record["sentiment"],
            "timestamp": record["timestamp"],
        }
        await self._update_record_essential(record["id"], essential)
```

---

## 5. Prompt 系统

### 5.1 Prompt 模板管理

```
ai/prompts/
├── registry.py              # Prompt 注册中心
├── version_control.py       # 版本管理
├── templates/
│   ├── intent/
│   │   ├── classify_v3.yaml
│   │   └── extract_entities_v2.yaml
│   ├── interpretation/
│   │   ├── hexagram_base_v5.yaml
│   │   ├── line_detail_v4.yaml
│   │   ├── five_element_analysis_v3.yaml
│   │   └── modern_translation_v2.yaml
│   ├── trend/
│   │   ├── long_term_trend_v3.yaml
│   │   └── multi_hexagram_v2.yaml
│   ├── evolution/
│   │   ├── chain_simulation_v2.yaml
│   │   └── probability_tree_v1.yaml
│   ├── memory/
│   │   ├── profile_generation_v2.yaml
│   │   └── pattern_analysis_v1.yaml
│   ├── safety/
│   │   ├── disclaimer_v3.yaml
│   │   └── risk_flag_v2.yaml
│   └── system/
│       ├── base_system_v4.yaml
│       └── role_definition_v3.yaml
└── evaluations/
    ├── test_cases/
    └── scores/
```

### 5.2 Prompt 模板格式

```yaml
# ai/prompts/templates/interpretation/hexagram_base_v5.yaml

metadata:
  id: hexagram_base_v5
  version: "5.0.0"
  author: "yiai-team"
  created: "2025-01-15"
  updated: "2025-05-20"
  description: "基础卦象解释 Prompt，用于将规则引擎结果翻译为自然语言"
  tier: standard
  model_preference: ["qwen-max", "deepseek-chat"]
  max_tokens: 2000
  temperature: 0.7
  tags: ["interpretation", "core"]

variables:
  - name: hexagram_name
    type: string
    required: true
    description: "卦名"
  - name: hexagram_data
    type: object
    required: true
    description: "卦的结构化数据（卦辞、爻辞、五行等）"
  - name: rule_results
    type: array
    required: true
    description: "规则引擎的确定性结果"
  - name: rag_context
    type: string
    required: false
    description: "RAG 检索的相关文献"
  - name: user_query
    type: string
    required: true
    description: "用户的原始问题"
  - name: user_memory
    type: object
    required: false
    description: "用户历史记忆"

system_prompt: |
  你是 YI-AI 易学解释系统。你的职责是将规则引擎的确定性分析结果翻译为用户可理解的自然语言解释。

  ## 核心原则

  1. **规则优先**：所有分析必须基于规则引擎的结果，不得自行推导卦象含义
  2. **不确定性标记**：当规则结果不充分时，必须明确说明"信息有限，仅供参考"
  3. **禁止确定性承诺**：不得使用"一定"、"必然"、"保证"等词语
  4. **现代语义**：用现代人可理解的语言解释，保留专业术语但需附带解释
  5. **变化视角**：强调"状态变化"而非"结果预测"

  ## 输出结构

  1. 卦象概述（3-5 句）
  2. 核心规则分析（基于规则引擎结果）
  3. 变化趋势（基于动爻和变卦）
  4. 现代启示（如何理解这个状态）
  5. 注意事项（风险提示）

user_prompt: |
  ## 用户问题
  {user_query}

  ## 卦象数据
  卦名: {hexagram_name}
  卦辞: {hexagram_data.judgement}
  象辞: {hexagram_data.image}
  爻辞:
  {%- for line in hexagram_data.lines %}
  - 第{line.position}爻 ({line.yin_yang}): {line.text}
  {%- endfor %}

  ## 规则引擎分析结果
  {%- for result in rule_results %}
  - [{result.rule_name}] {result.explanation}（置信度: {result.confidence}）
  {%- endfor %}

  {% if rag_context %}
  ## 相关文献参考
  {rag_context}
  {% endif %}

  {% if user_memory %}
  ## 用户历史背景
  近期卦象: {user_memory.recent_hexagrams}
  关注主题: {user_memory.recurring_themes}
  {% endif %}

  请基于以上规则引擎的结果，为用户提供易懂的解释。强调这是对当前状态的分析，而非对未来的预测。
```

### 5.3 Prompt 版本控制

```python
# ai/prompts/version_control.py

import hashlib
import json
from datetime import datetime

class PromptVersionControl:
    """Prompt 版本管理。"""

    def __init__(self, storage_path: str = "ai/prompts/"):
        self.storage_path = storage_path

    def register_version(self, prompt_id: str, template: dict) -> str:
        """注册新版本。"""
        version = template["metadata"]["version"]
        content_hash = hashlib.sha256(
            json.dumps(template, sort_keys=True).encode()
        ).hexdigest()[:12]

        # 保存版本快照
        snapshot = {
            "prompt_id": prompt_id,
            "version": version,
            "hash": content_hash,
            "registered_at": datetime.utcnow().isoformat(),
            "template": template,
        }

        self._save_snapshot(prompt_id, version, snapshot)
        return f"{prompt_id}@{version}+{content_hash}"

    def get_active_version(self, prompt_id: str) -> dict:
        """获取当前活跃版本。"""
        return self._load_active(prompt_id)

    def rollback(self, prompt_id: str, target_version: str) -> dict:
        """回滚到指定版本。"""
        snapshot = self._load_snapshot(prompt_id, target_version)
        self._set_active(prompt_id, snapshot["template"])
        return snapshot["template"]

    def compare_versions(self, prompt_id: str, v1: str, v2: str) -> dict:
        """对比两个版本的差异。"""
        s1 = self._load_snapshot(prompt_id, v1)
        s2 = self._load_snapshot(prompt_id, v2)
        return {
            "system_prompt_diff": self._diff_text(
                s1["template"]["system_prompt"],
                s2["template"]["system_prompt"],
            ),
            "user_prompt_diff": self._diff_text(
                s1["template"]["user_prompt"],
                s2["template"]["user_prompt"],
            ),
        }

    def _diff_text(self, text1: str, text2: str) -> dict:
        """简单文本差异对比。"""
        lines1 = text1.splitlines()
        lines2 = text2.splitlines()
        added = [l for l in lines2 if l not in lines1]
        removed = [l for l in lines1 if l not in lines2]
        return {"added": added, "removed": removed}
```

### 5.4 Prompt 评估框架

```python
# ai/prompts/evaluation.py

from dataclasses import dataclass

@dataclass
class PromptEvalCase:
    """Prompt 评估用例。"""
    case_id: str
    prompt_id: str
    input_variables: dict
    expected_qualities: list[str]  # 期望的质量特征
    forbidden_patterns: list[str]  # 禁止出现的模式

class PromptEvaluator:
    """评估 Prompt 输出质量。"""

    def __init__(self):
        self.eval_cases: dict[str, list[PromptEvalCase]] = {}

    async def evaluate(self, prompt_id: str, output: str, case: PromptEvalCase) -> dict:
        """评估单个输出。"""
        scores = {}

        # 1. 禁止模式检查
        forbidden_found = []
        for pattern in case.forbidden_patterns:
            if pattern in output:
                forbidden_found.append(pattern)
        scores["forbidden_check"] = 0.0 if forbidden_found else 1.0

        # 2. 结构完整性
        scores["structure"] = self._check_structure(output)

        # 3. 长度合理性
        scores["length"] = self._check_length(output)

        # 4. 质量特征匹配（由 LLM 辅助评分）
        scores["quality"] = await self._llm_quality_check(output, case.expected_qualities)

        # 综合分
        weights = {"forbidden_check": 0.4, "structure": 0.2, "length": 0.1, "quality": 0.3}
        scores["overall"] = sum(scores[k] * weights[k] for k in weights)

        return scores

    def _check_structure(self, output: str) -> float:
        """检查输出结构是否符合预期。"""
        required_sections = ["卦象概述", "核心分析", "变化趋势", "注意事项"]
        found = sum(1 for s in required_sections if s in output)
        return found / len(required_sections)

    def _check_length(self, output: str) -> float:
        """检查长度是否在合理范围。"""
        length = len(output)
        if 300 <= length <= 3000:
            return 1.0
        elif 100 <= length < 300 or 3000 < length <= 5000:
            return 0.6
        return 0.2

    async def _llm_quality_check(self, output: str, expected: list[str]) -> float:
        """使用 LLM 评估输出质量。"""
        prompt = f"""
        评估以下易学解释的质量（0-1分）：
        期望特征: {', '.join(expected)}
        实际输出: {output[:1000]}
        仅返回数字评分。
        """
        score_str = await call_model(TaskTier.TIER_1_LIGHTWEIGHT, prompt, "")
        try:
            return float(score_str.strip())
        except ValueError:
            return 0.5
```

---

## 6. 知识图谱构建

### 6.1 节点定义

```cypher
// ============================================================
// 节点定义
// ============================================================

// 1. 卦 (Hexagram) - 64个
CREATE (h:Hexagram {
  name: "乾",                    // 卦名
  number: 1,                     // 卦序
  unicode: "䷀",                 // Unicode 符号
  upper_trigram: "乾",           // 上卦
  lower_trigram: "乾",           // 下卦
  judgement: "元亨利贞",         // 卦辞
  image: "天行健，君子以自强不息", // 象辞
  binary: "111111",              // 二进制表示
  element: "金"                  // 主属性
})

// 2. 爻 (Line) - 每卦6爻，共384个
CREATE (l:Line {
  position: 1,                   // 爻位 (1-6)
  yin_yang: "yang",              // 阴阳
  text: "潜龙勿用",              // 爻辞
  image: "潜龙勿用，阳在下也",   // 小象
  naijia_element: "甲子",        // 纳甲
  six_relative: "兄弟"           // 六亲
})

// 3. 五行 (Element) - 5个
CREATE (e:Element {
  name: "木",
  nature: "曲直",
  season: "春",
  direction: "东",
  color: "青",
  organ: "肝",
  emotion: "怒"
})

// 4. 八卦 (Trigram) - 8个
CREATE (t:Trigram {
  name: "乾",
  symbol: "☰",
  binary: "111",
  nature: "天",
  element: "金",
  family_role: "父",
  body_part: "首",
  animal: "马",
  direction: "西北"
})

// 5. 六亲 (Role) - 5个
CREATE (r:Role {
  name: "父母",
  description: "生我者",
  represents: "文书、长辈、庇护"
})

// 6. 六神 (Spirit) - 6个
CREATE (s:Spirit {
  name: "青龙",
  element: "木",
  nature: "吉",
  represents: "喜庆、文书、贵人"
})

// 7. 天干 (HeavenlyStem) - 10个
CREATE (hs:HeavenlyStem {
  name: "甲",
  element: "木",
  yin_yang: "阳",
  number: 1
})

// 8. 地支 (EarthlyBranch) - 12个
CREATE (eb:EarthlyBranch {
  name: "子",
  element: "水",
  yin_yang: "阳",
  animal: "鼠",
  month: 11,
  hours: "23:00-01:00"
})

// 9. 用户 (User)
CREATE (u:User {
  user_id: "uuid",
  created_at: datetime(),
  dominant_element: "木",
  question_frequency: 2.5
})

// 10. 占卜记录 (DivinationRecord)
CREATE (dr:DivinationRecord {
  record_id: "uuid",
  timestamp: datetime(),
  question: "事业方面最近如何？",
  sentiment: "anxious",
  topic_tags: ["事业", "焦虑"]
})
```

### 6.2 关系定义

```cypher
// ============================================================
// 关系定义
// ============================================================

// --- 五行关系 ---
// 相生
CREATE (wood)-[:GENERATES {cycle: "相生"}]->(fire)
CREATE (fire)-[:GENERATES {cycle: "相生"}]->(earth)
CREATE (earth)-[:GENERATES {cycle: "相生"}]->(metal)
CREATE (metal)-[:GENERATES {cycle: "相生"}]->(water)
CREATE (water)-[:GENERATES {cycle: "相生"}]->(wood)

// 相克
CREATE (wood)-[:RESTRAINS {cycle: "相克"}]->(earth)
CREATE (earth)-[:RESTRAINS {cycle: "相克"}]->(water)
CREATE (water)-[:RESTRAINS {cycle: "相克"}]->(fire)
CREATE (fire)-[:RESTRAINS {cycle: "相克"}]->(metal)
CREATE (metal)-[:RESTRAINS {cycle: "相克"}]->(wood)

// --- 卦爻关系 ---
CREATE (hexagram)-[:HAS_LINE {position: 1}]->(line)
CREATE (hexagram)-[:HAS_UPPER]->(trigram)
CREATE (hexagram)-[:HAS_LOWER]->(trigram)

// --- 卦变关系 ---
CREATE (hexagram)-[:TRANSFORMS_TO {moving_lines: [3,5]}]->(changed_hexagram)
CREATE (hexagram)-[:ERRORS_TO]->(error_hexagram)       // 错卦
CREATE (hexagram)-[:REVERSES_TO]->(reverse_hexagram)   // 综卦
CREATE (hexagram)-[:MUTUAL_WITH]->(mutual_hexagram)    // 互卦

// --- 纳甲关系 ---
CREATE (line)-[:NAIJIA {stem: "甲", branch: "子"}]->(heavenly_stem)
CREATE (line)-[:NAIJIA]->(earthly_branch)
CREATE (line)-[:HAS_ROLE]->(role)
CREATE (line)-[:HAS_ELEMENT]->(element)

// --- 时间关系 ---
CREATE (hexagram)-[:APPEARS_AT]->(time_node)
CREATE (earthly_branch)-[:CLASHES_WITH]->(opposing_branch)
CREATE (earthly_branch)-[:COMBINES_WITH {type: "六合"}]->(partner_branch)

// --- 用户关系 ---
CREATE (user)-[:QUERIED {timestamp: datetime()}]->(divination_record)
CREATE (divination_record)-[:RESULTED_IN]->(hexagram)
CREATE (user)-[:HAS_PATTERN]->(behavior_pattern)
```

### 6.3 完整索引与约束

```cypher
// ============================================================
// 索引与约束
// ============================================================

// 唯一约束
CREATE CONSTRAINT hexagram_name IF NOT EXISTS FOR (h:Hexagram) REQUIRE h.name IS UNIQUE;
CREATE CONSTRAINT hexagram_number IF NOT EXISTS FOR (h:Hexagram) REQUIRE h.number IS UNIQUE;
CREATE CONSTRAINT element_name IF NOT EXISTS FOR (e:Element) REQUIRE e.name IS UNIQUE;
CREATE CONSTRAINT trigram_name IF NOT EXISTS FOR (t:Trigram) REQUIRE t.name IS UNIQUE;
CREATE CONSTRAINT role_name IF NOT EXISTS FOR (r:Role) REQUIRE r.name IS UNIQUE;
CREATE CONSTRAINT spirit_name IF NOT EXISTS FOR (s:Spirit) REQUIRE s.name IS UNIQUE;
CREATE CONSTRAINT stem_name IF NOT EXISTS FOR (hs:HeavenlyStem) REQUIRE hs.name IS UNIQUE;
CREATE CONSTRAINT branch_name IF NOT EXISTS FOR (eb:EarthlyBranch) REQUIRE eb.name IS UNIQUE;
CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE;
CREATE CONSTRAINT record_id IF NOT EXISTS FOR (dr:DivinationRecord) REQUIRE dr.record_id IS UNIQUE;

// 性能索引
CREATE INDEX hexagram_element IF NOT EXISTS FOR (h:Hexagram) ON (h.element);
CREATE INDEX line_position IF NOT EXISTS FOR (l:Line) ON (l.position);
CREATE INDEX record_timestamp IF NOT EXISTS FOR (dr:DivinationRecord) ON (dr.timestamp);
CREATE INDEX record_sentiment IF NOT EXISTS FOR (dr:DivinationRecord) ON (dr.sentiment);

// 全文索引
CREATE FULLTEXT INDEX hexagram_text IF NOT EXISTS FOR (h:Hexagram) ON EACH [h.judgement, h.image];
CREATE FULLTEXT INDEX line_text IF NOT EXISTS FOR (l:Line) ON EACH [l.text, l.image];
CREATE FULLTEXT INDEX record_question IF NOT EXISTS FOR (dr:DivinationRecord) ON EACH [dr.question];
```

### 6.4 常用 Cypher 查询示例

```cypher
// ============================================================
// 查询示例
// ============================================================

// Q1: 查询某卦的完整信息（包括六爻、五行、纳甲）
MATCH (h:Hexagram {name: "乾"})-[r:HAS_LINE]->(l:Line)-[:HAS_ELEMENT]->(e:Element)
OPTIONAL MATCH (l)-[:HAS_ROLE]->(role:Role)
OPTIONAL MATCH (l)-[:NAIJIA]->(hs:HeavenlyStem)
OPTIONAL MATCH (l)-[:NAIJIA]->(eb:EarthlyBranch)
RETURN h, collect({
  position: l.position,
  yin_yang: l.yin_yang,
  text: l.text,
  element: e.name,
  role: role.name,
  stem: hs.name,
  branch: eb.name
}) AS lines

// Q2: 五行生克关系网络（以"木"为中心，2跳）
MATCH path = (e:Element {name: "木"})-[:GENERATES|RESTRAINS*1..2]-(related:Element)
RETURN
  e.name AS center,
  [r IN relationships(path) | type(r)] AS relations,
  collect(DISTINCT related.name) AS connected_elements

// Q3: 查找某用户最近30天的卦象变化轨迹
MATCH (u:User {user_id: $user_id})-[:QUERIED]->(dr:DivinationRecord)-[:RESULTED_IN]->(h:Hexagram)
WHERE dr.timestamp > datetime() - duration({days: 30})
RETURN
  h.name AS hexagram,
  dr.timestamp AS time,
  dr.question AS question,
  dr.sentiment AS sentiment
ORDER BY dr.timestamp DESC

// Q4: 分析用户的五行偏好
MATCH (u:User {user_id: $user_id})-[:QUERIED]->(dr:DivinationRecord)-[:RESULTED_IN]->(h:Hexagram)
WITH u, h.element AS element, count(*) AS frequency
RETURN element, frequency
ORDER BY frequency DESC

// Q5: 查找与某卦相似的卦（共享上卦或下卦）
MATCH (h:Hexagram {name: "乾"})-[:HAS_UPPER]->(t:Trigram)<-[:HAS_UPPER]-(similar1:Hexagram)
WHERE similar1 <> h
OPTIONAL MATCH (h)-[:HAS_LOWER]->(t2:Trigram)<-[:HAS_LOWER]-(similar2:Hexagram)
WHERE similar2 <> h
RETURN
  collect(DISTINCT similar1.name) AS same_upper,
  collect(DISTINCT similar2.name) AS same_lower

// Q6: 某卦的完整变化网络（本卦→变卦→错卦→综卦→互卦）
MATCH (h:Hexagram {name: "乾"})
OPTIONAL MATCH (h)-[:TRANSFORMS_TO]->(changed:Hexagram)
OPTIONAL MATCH (h)-[:ERRORS_TO]->(err:Hexagram)
OPTIONAL MATCH (h)-[:REVERSES_TO]->(rev:Hexagram)
OPTIONAL MATCH (h)-[:MUTUAL_WITH]->(mut:Hexagram)
RETURN {
  original: h.name,
  transforms_to: changed.name,
  errors_to: err.name,
  reverses_to: rev.name,
  mutual_with: mut.name
}

// Q7: 发现反复出现"坎"卦且情绪为"焦虑"的用户
MATCH (u:User)-[:QUERIED]->(dr:DivinationRecord)-[:RESULTED_IN]->(h:Hexagram {name: "坎"})
WHERE dr.sentiment = "anxious"
WITH u, count(*) AS occurrences
WHERE occurrences >= 3
RETURN u.user_id, occurrences
ORDER BY occurrences DESC

// Q8: 时间维度的卦象分布（某用户按月统计）
MATCH (u:User {user_id: $user_id})-[:QUERIED]->(dr:DivinationRecord)-[:RESULTED_IN]->(h:Hexagram)
WITH
  dr.timestamp.year AS year,
  dr.timestamp.month AS month,
  h.name AS hexagram,
  count(*) AS freq
RETURN year, month, collect({hexagram: hexagram, count: freq}) AS distribution
ORDER BY year, month

// Q9: 六冲关系查询
MATCH (eb1:EarthlyBranch)-[r:CLASHES_WITH]->(eb2:EarthlyBranch)
RETURN eb1.name, eb2.name

// Q10: 用户情绪趋势与卦象关联
MATCH (u:User {user_id: $user_id})-[:QUERIED]->(dr:DivinationRecord)-[:RESULTED_IN]->(h:Hexagram)
WHERE dr.timestamp > datetime() - duration({days: 180})
RETURN
  dr.timestamp.month AS month,
  dr.sentiment AS sentiment,
  h.name AS hexagram,
  h.element AS element
ORDER BY dr.timestamp
```

### 6.5 图谱数据初始化脚本

```python
# ai/graph/init_graph.py

from neo4j import AsyncGraphDatabase

class GraphInitializer:
    """初始化易学知识图谱。"""

    def __init__(self, driver):
        self.driver = driver

    async def initialize_all(self):
        """完整的图谱初始化流程。"""
        async with self.driver.session() as session:
            await session.execute_write(self._create_elements)
            await session.execute_write(self._create_trigrams)
            await session.execute_write(self._create_hexagrams)
            await session.execute_write(self._create_element_relations)
            await session.execute_write(self._create_branch_relations)
            await session.execute_write(self._create_hexagram_transformations)

    async def _create_elements(self, tx):
        """创建五行节点及基本关系。"""
        elements = [
            ("木", "曲直", "春", "东", "青", "肝", "怒"),
            ("火", "炎上", "夏", "南", "赤", "心", "喜"),
            ("土", "稼穑", "长夏", "中", "黄", "脾", "思"),
            ("金", "从革", "秋", "西", "白", "肺", "悲"),
            ("水", "润下", "冬", "北", "黑", "肾", "恐"),
        ]
        for name, nature, season, direction, color, organ, emotion in elements:
            await tx.run("""
                MERGE (e:Element {name: $name})
                SET e.nature = $nature,
                    e.season = $season,
                    e.direction = $direction,
                    e.color = $color,
                    e.organ = $organ,
                    e.emotion = $emotion
            """, name=name, nature=nature, season=season,
                direction=direction, color=color, organ=organ, emotion=emotion)

    async def _create_trigrams(self, tx):
        """创建八卦节点。"""
        trigrams = [
            ("乾", "☰", "111", "天", "金", "父", "首", "马", "西北"),
            ("坤", "☷", "000", "地", "土", "母", "腹", "牛", "西南"),
            ("震", "☳", "100", "雷", "木", "长男", "足", "龙", "东"),
            ("巽", "☴", "011", "风", "木", "长女", "股", "鸡", "东南"),
            ("坎", "☵", "010", "水", "水", "中男", "耳", "猪", "北"),
            ("离", "☲", "101", "火", "火", "中女", "目", "雉", "南"),
            ("艮", "☶", "001", "山", "土", "少男", "手", "狗", "东北"),
            ("兑", "☱", "110", "泽", "金", "少女", "口", "羊", "西"),
        ]
        for name, symbol, binary, nature, element, role, body, animal, direction in trigrams:
            await tx.run("""
                MERGE (t:Trigram {name: $name})
                SET t.symbol = $symbol, t.binary = $binary,
                    t.nature = $nature, t.element = $element,
                    t.family_role = $role, t.body_part = $body,
                    t.animal = $animal, t.direction = $direction
            """, name=name, symbol=symbol, binary=binary, nature=nature,
                element=element, role=role, body=body, animal=animal, direction=direction)

    async def _create_element_relations(self, tx):
        """创建五行生克关系。"""
        generates = [("木","火"),("火","土"),("土","金"),("金","水"),("水","木")]
        restrains = [("木","土"),("土","水"),("水","火"),("火","金"),("金","木")]

        for src, dst in generates:
            await tx.run("""
                MATCH (a:Element {name: $src}), (b:Element {name: $dst})
                MERGE (a)-[:GENERATES]->(b)
            """, src=src, dst=dst)

        for src, dst in restrains:
            await tx.run("""
                MATCH (a:Element {name: $src}), (b:Element {name: $dst})
                MERGE (a)-[:RESTRAINS]->(b)
            """, src=src, dst=dst)

    async def _create_branch_relations(self, tx):
        """创建地支冲合关系。"""
        # 六冲
        clashes = [("子","午"),("丑","未"),("寅","申"),("卯","酉"),("辰","戌"),("巳","亥")]
        for a, b in clashes:
            await tx.run("""
                MATCH (eb1:EarthlyBranch {name: $a}), (eb2:EarthlyBranch {name: $b})
                MERGE (eb1)-[:CLASHES_WITH]->(eb2)
                MERGE (eb2)-[:CLASHES_WITH]->(eb1)
            """, a=a, b=b)

        # 六合
        combines = [("子","丑"),("寅","亥"),("卯","戌"),("辰","酉"),("巳","申"),("午","未")]
        for a, b in combines:
            await tx.run("""
                MATCH (eb1:EarthlyBranch {name: $a}), (eb2:EarthlyBranch {name: $b})
                MERGE (eb1)-[:COMBINES_WITH {type: '六合'}]->(eb2)
                MERGE (eb2)-[:COMBINES_WITH {type: '六合'}]->(eb1)
            """, a=a, b=b)

    async def _create_hexagrams(self, tx):
        """创建六十四卦节点。此为示意，完整数据需从数据文件加载。"""
        # 实际实现应从 JSON/YAML 数据文件加载全部64卦
        pass

    async def _create_hexagram_transformations(self, tx):
        """创建卦变关系。"""
        # 实际实现应根据动爻规则计算并创建所有变换关系
        pass
```

---

## 7. AI 解释引擎

### 7.1 Pipeline 总览

```
                    ┌──────────────────────────────────────────────┐
                    │          AI 解释引擎 Pipeline                │
                    │                                              │
用户问题 + 卦数据   │  ┌────────┐  ┌────────┐  ┌────────┐        │
──────────────────▶│  │ Stage1 │─▶│ Stage2 │─▶│ Stage3 │        │
                    │  │ 预处理 │  │ 规则   │  │ RAG    │        │
                    │  └────────┘  └────────┘  └────┬───┘        │
                    │                               │             │
                    │  ┌────────┐  ┌────────┐  ┌────▼───┐        │
                    │  │ Stage6 │◀─│ Stage5 │◀─│ Stage4 │        │
                    │  │ 输出   │  │ 安全   │  │ AI解释 │        │
                    │  └────────┘  └────────┘  └────────┘        │
                    │                                              │
                    └──────────────────────────────────────────────┘
```

### 7.2 各 Stage 详细设计

```python
# ai/explanation/pipeline.py

from dataclasses import dataclass

@dataclass
class PipelineContext:
    """Pipeline 上下文，各 Stage 共享。"""
    user_query: str
    hexagram_data: dict
    session_id: str
    user_id: str

    # Stage 1 输出
    parsed_query: dict | None = None
    entities: dict | None = None
    intent: str | None = None

    # Stage 2 输出
    rule_results: list | None = None

    # Stage 3 输出
    rag_context: str | None = None
    user_memory: dict | None = None

    # Stage 4 输出
    raw_interpretation: str | None = None

    # Stage 5 输出
    safety_issues: list[str] | None = None
    safe_interpretation: str | None = None

    # Stage 6 输出
    final_response: str | None = None
    response_format: str = "text"  # "text" | "structured" | "streaming"


class ExplanationPipeline:
    """AI 解释引擎的完整 Pipeline。"""

    def __init__(self, model_router, rule_engine, rag_system, memory_engine, safety_checker):
        self.model_router = model_router
        self.rule_engine = rule_engine
        self.rag_system = rag_system
        self.memory_engine = memory_engine
        self.safety_checker = safety_checker

    async def execute(self, ctx: PipelineContext) -> PipelineContext:
        """执行完整 Pipeline。"""
        ctx = await self.stage1_preprocess(ctx)
        ctx = await self.stage2_rule_analysis(ctx)
        ctx = await self.stage3_rag_retrieve(ctx)
        ctx = await self.stage4_ai_interpret(ctx)
        ctx = await self.stage5_safety_check(ctx)
        ctx = await self.stage6_format_output(ctx)
        return ctx

    # ---- Stage 1: 预处理 ----

    async def stage1_preprocess(self, ctx: PipelineContext) -> PipelineContext:
        """
        职责：
        - 意图分类
        - 实体提取（卦名、五行、时间段等）
        - 查询改写（如果用户问题模糊）
        模型：Tier 1（DeepSeek / Qwen-Turbo）
        """
        prompt = f"""
        分析以下用户查询，返回 JSON 格式：
        1. intent: divination | trend_analysis | learning | evolution_simulation
        2. entities: 提取的实体（卦名、五行、时间、人物等）
        3. rewritten_query: 改写后的清晰查询
        4. confidence: 分类置信度 (0-1)

        用户查询: {ctx.user_query}
        """

        result = await self.model_router.call(
            tier=TaskTier.TIER_1_LIGHTWEIGHT,
            prompt=prompt,
        )

        parsed = json.loads(result)
        ctx.parsed_query = parsed
        ctx.entities = parsed.get("entities", {})
        ctx.intent = parsed.get("intent", "divination")

        return ctx

    # ---- Stage 2: 规则分析 ----

    async def stage2_rule_analysis(self, ctx: PipelineContext) -> PipelineContext:
        """
        职责：
        - 调用确定性规则引擎
        - 生成结构化分析结果
        - 不经过 LLM
        """
        ctx.rule_results = self.rule_engine.analyze(ctx.hexagram_data)
        return ctx

    # ---- Stage 3: RAG 检索 ----

    async def stage3_rag_retrieve(self, ctx: PipelineContext) -> PipelineContext:
        """
        职责：
        - 三路 RAG 检索（向量 + 图谱 + 规则补充）
        - 获取用户长期记忆
        - 上下文组装
        """
        # 获取用户记忆
        ctx.user_memory = await self.memory_engine.get_user_memory(
            ctx.user_id, ctx.user_query
        )

        # RAG 检索
        query_embedding = await get_embedding(ctx.user_query)
        vector_results = await self.rag_system.vector_search(query_embedding, ctx.hexagram_data)
        graph_results = await self.rag_system.graph_search(ctx.hexagram_data.get("hexagram_name", ""))

        # 融合
        fused = self.rag_system.fuse(vector_results, graph_results, ctx.rule_results)
        ctx.rag_context = self.rag_system.assemble_context(
            fused, ctx.hexagram_data, ctx.user_query, ctx.user_memory
        )

        return ctx

    # ---- Stage 4: AI 解释 ----

    async def stage4_ai_interpret(self, ctx: PipelineContext) -> PipelineContext:
        """
        职责：
        - 根据规则结果 + RAG 上下文生成自然语言解释
        - 选择合适的 Tier
        模型：Tier 2-3（Qwen-Max / Claude Sonnet）
        """
        # 根据复杂度选择 Tier
        complexity = self._assess_complexity(ctx)
        tier = TaskTier.TIER_3_DEEP if complexity > 0.7 else TaskTier.TIER_2_STANDARD

        prompt = self._build_interpretation_prompt(ctx)

        ctx.raw_interpretation = await self.model_router.call(
            tier=tier,
            prompt=prompt,
            system_prompt=INTERPRETATION_SYSTEM_PROMPT,
        )

        return ctx

    def _assess_complexity(self, ctx: PipelineContext) -> float:
        """评估任务复杂度。"""
        score = 0.0
        if len(ctx.hexagram_data.get("moving_lines", [])) > 2:
            score += 0.2
        if ctx.intent == "trend_analysis":
            score += 0.3
        if ctx.user_memory and ctx.user_memory.get("recurring_themes"):
            score += 0.2
        if len(ctx.rule_results or []) > 5:
            score += 0.2
        if ctx.intent == "evolution_simulation":
            score += 0.3
        return min(score, 1.0)

    def _build_interpretation_prompt(self, ctx: PipelineContext) -> str:
        """构建解释 Prompt。"""
        sections = [
            f"## 用户问题\n{ctx.user_query}",
            f"## 卦象数据\n{json.dumps(ctx.hexagram_data, ensure_ascii=False, indent=2)}",
            f"## 规则引擎分析\n" + "\n".join(
                f"- [{r['rule_name']}] {r['explanation']}" for r in (ctx.rule_results or [])
            ),
        ]
        if ctx.rag_context:
            sections.append(f"## 参考知识\n{ctx.rag_context}")
        if ctx.user_memory:
            sections.append(f"## 用户历史背景\n{json.dumps(ctx.user_memory, ensure_ascii=False)}")

        return "\n\n".join(sections)

    # ---- Stage 5: 安全检查 ----

    async def stage5_safety_check(self, ctx: PipelineContext) -> PipelineContext:
        """
        职责：
        - 检查禁止性承诺（"一定"、"必然"等）
        - 检查有害建议
        - 检查误导性表述
        - 必要时修正输出
        """
        issues = self.safety_checker.check(ctx.raw_interpretation)
        ctx.safety_issues = issues

        if issues:
            fix_prompt = f"""
            以下解释存在安全问题，请修正后返回：
            问题: {issues}
            原始解释: {ctx.raw_interpretation}

            修正要求：
            1. 移除确定性承诺
            2. 添加不确定性标记
            3. 保留分析价值
            """
            ctx.safe_interpretation = await self.model_router.call(
                tier=TaskTier.TIER_1_LIGHTWEIGHT,
                prompt=fix_prompt,
            )
        else:
            ctx.safe_interpretation = ctx.raw_interpretation

        return ctx

    # ---- Stage 6: 输出格式化 ----

    async def stage6_format_output(self, ctx: PipelineContext) -> PipelineContext:
        """
        职责：
        - 根据用户场景选择输出格式
        - 添加免责声明
        - 添加元数据
        """
        disclaimer = "\n\n---\n*以上分析基于易学规则体系，仅供参考，不构成任何决策建议。*"

        if ctx.response_format == "structured":
            ctx.final_response = self._format_structured(ctx) + disclaimer
        elif ctx.response_format == "streaming":
            ctx.final_response = ctx.safe_interpretation + disclaimer
        else:
            ctx.final_response = ctx.safe_interpretation + disclaimer

        ctx.response_metadata = {
            "intent": ctx.intent,
            "hexagram": ctx.hexagram_data.get("hexagram_name"),
            "rule_count": len(ctx.rule_results or []),
            "safety_issues": ctx.safety_issues,
            "model_tier_used": ctx._tier_used if hasattr(ctx, '_tier_used') else "unknown",
        }

        return ctx

    def _format_structured(self, ctx: PipelineContext) -> str:
        """结构化输出格式。"""
        data = {
            "hexagram": ctx.hexagram_data.get("hexagram_name"),
            "interpretation": ctx.safe_interpretation,
            "rule_analysis": ctx.rule_results,
            "risk_flags": ctx.safety_issues,
        }
        return json.dumps(data, ensure_ascii=False, indent=2)


class SafetyChecker:
    """安全检查器。"""

    FORBIDDEN_PHRASES = [
        "一定会", "必然", "保证", "绝对", "百分之百",
        "肯定会", "毫无疑问", "命中注定",
    ]

    HARMFUL_ADVICE_PATTERNS = [
        "应该投资", "应该辞职", "应该分手", "应该离婚",
        "一定会发财", "一定会升职",
    ]

    def check(self, text: str) -> list[str]:
        issues = []
        for phrase in self.FORBIDDEN_PHRASES:
            if phrase in text:
                issues.append(f"禁止性承诺: '{phrase}'")
        for pattern in self.HARMFUL_ADVICE_PATTERNS:
            if pattern in text:
                issues.append(f"有害建议: '{pattern}'")
        return issues
```

### 7.3 流式输出支持

```python
# ai/explanation/streaming.py

class StreamingExplanationPipeline:
    """支持流式输出的解释 Pipeline。"""

    async def execute_streaming(self, ctx: PipelineContext):
        """以 SSE 形式流式输出。"""
        # Stage 1-3 同步执行（预处理、规则、RAG）
        ctx = await self.pipeline.stage1_preprocess(ctx)
        ctx = await self.pipeline.stage2_rule_analysis(ctx)
        ctx = await self.pipeline.stage3_rag_retrieve(ctx)

        # Stage 4 流式输出
        prompt = self.pipeline._build_interpretation_prompt(ctx)

        yield {"type": "status", "data": "正在生成解释..."}

        async for chunk in self.model_router.call_streaming(
            tier=TaskTier.TIER_2_STANDARD,
            prompt=prompt,
            system_prompt=INTERPRETATION_SYSTEM_PROMPT,
        ):
            yield {"type": "content", "data": chunk}

        # Stage 5 异步安全检查
        yield {"type": "status", "data": "安全检查中..."}
        # ... 安全检查逻辑

        yield {"type": "done", "data": {"metadata": ctx.response_metadata}}
```

---

## 8. 评估和优化策略

### 8.1 评估维度

```
┌──────────────────────────────────────────────────────┐
│                    评估体系                           │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │ 准确性   │  │ 质量     │  │ 性能     │           │
│  │ Accuracy │  │ Quality  │  │ Perf     │           │
│  └──────────┘  └──────────┘  └──────────┘           │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │ 安全性   │  │ 成本     │  │ 用户     │           │
│  │ Safety   │  │ Cost     │  │ Feedback │           │
│  └──────────┘  └──────────┘  └──────────┘           │
└──────────────────────────────────────────────────────┘
```

### 8.2 评估指标定义

| 维度 | 指标 | 计算方式 | 目标值 |
|------|------|---------|-------|
| 准确性 | 规则翻译准确率 | AI解释与规则引擎结果的一致性 | >= 95% |
| 准确性 | 意图分类准确率 | 分类正确数 / 总数 | >= 90% |
| 准确性 | 实体提取 F1 | 提取实体与标注的匹配度 | >= 85% |
| 质量 | 结构完整性 | 输出包含必要章节的比例 | >= 90% |
| 质量 | 语言流畅度 | LLM 辅助评分 (1-5) | >= 4.0 |
| 质量 | 古文翻译准确率 | 与标准翻译的语义相似度 | >= 85% |
| 性能 | 首 token 延迟 (TTFT) | 从请求到首个 token 的时间 | < 500ms |
| 性能 | 端到端延迟 | 完整响应时间 | < 5s (非推演) |
| 性能 | RAG 检索延迟 | 三路检索 + 融合时间 | < 1s |
| 安全 | 禁止性承诺检出率 | 检出数 / 实际存在数 | 100% |
| 安全 | 有害建议检出率 | 检出数 / 实际存在数 | 100% |
| 安全 | 误报率 | 误报数 / 总检查数 | < 5% |
| 成本 | 单次请求平均成本 | 总成本 / 请求数 | < $0.03 |
| 成本 | 每用户日均成本 | 用户日成本 | < $0.50 |
| 用户 | 用户满意度 | 用户评分均值 | >= 4.0/5 |
| 用户 | 解释采纳率 | 用户正面反馈 / 总反馈 | >= 70% |

### 8.3 自动化评估 Pipeline

```python
# ai/evaluation/evaluator.py

from dataclasses import dataclass

@dataclass
class EvalResult:
    metric: str
    score: float
    details: dict
    timestamp: str

class AutoEvaluator:
    """自动化评估系统。"""

    def __init__(self, model_router, test_cases: list[dict]):
        self.model_router = model_router
        self.test_cases = test_cases

    async def run_full_evaluation(self) -> dict[str, EvalResult]:
        """运行完整评估套件。"""
        results = {}

        # 1. 准确性评估
        results["rule_translation"] = await self.eval_rule_translation()
        results["intent_classification"] = await self.eval_intent_classification()
        results["entity_extraction"] = await self.eval_entity_extraction()

        # 2. 质量评估
        results["structural_completeness"] = await self.eval_structure()
        results["language_fluency"] = await self.eval_fluency()

        # 3. 安全性评估
        results["safety_forbidden"] = await self.eval_safety_forbidden()
        results["safety_harmful"] = await self.eval_safety_harmful()

        # 4. RAG 评估
        results["rag_relevance"] = await self.eval_rag_relevance()
        results["rag_grounding"] = await self.eval_rag_grounding()

        return results

    async def eval_rule_translation(self) -> EvalResult:
        """评估规则翻译准确率：AI 解释是否忠实于规则引擎结果。"""
        correct = 0
        total = 0

        for case in self.test_cases:
            if case.get("type") != "interpretation":
                continue

            # 运行 Pipeline
            ctx = PipelineContext(
                user_query=case["query"],
                hexagram_data=case["hexagram_data"],
                session_id="eval",
                user_id="eval",
            )
            result = await self.pipeline.execute(ctx)

            # 用 LLM 判断解释是否忠实于规则结果
            judge_prompt = f"""
            判断以下AI解释是否忠实于规则引擎的分析结果。
            规则结果: {json.dumps(case['rule_results'], ensure_ascii=False)}
            AI解释: {result.final_response}
            返回 "correct" 或 "incorrect" 及原因。
            """
            judgment = await self.model_router.call(
                tier=TaskTier.TIER_1_LIGHTWEIGHT,
                prompt=judge_prompt,
            )

            if "correct" in judgment.lower():
                correct += 1
            total += 1

        score = correct / total if total > 0 else 0
        return EvalResult(
            metric="rule_translation_accuracy",
            score=score,
            details={"correct": correct, "total": total},
            timestamp=datetime.utcnow().isoformat(),
        )

    async def eval_rag_relevance(self) -> EvalResult:
        """评估 RAG 检索的相关性。"""
        # 使用 nDCG@10 评估
        scores = []
        for case in self.test_cases:
            if not case.get("relevant_doc_ids"):
                continue

            retrieved = await self.rag_system.search(case["query"], top_k=10)
            retrieved_ids = [r["id"] for r in retrieved]
            relevant_ids = set(case["relevant_doc_ids"])

            # 计算 nDCG@10
            dcg = sum(
                1.0 / (i + 1)
                for i, doc_id in enumerate(retrieved_ids)
                if doc_id in relevant_ids
            )
            ideal_dcg = sum(1.0 / (i + 1) for i in range(min(len(relevant_ids), 10)))
            ndcg = dcg / ideal_dcg if ideal_dcg > 0 else 0
            scores.append(ndcg)

        avg_score = sum(scores) / len(scores) if scores else 0
        return EvalResult(
            metric="rag_relevance_ndcg@10",
            score=avg_score,
            details={"num_queries": len(scores)},
            timestamp=datetime.utcnow().isoformat(),
        )

    async def eval_fluency(self) -> EvalResult:
        """评估语言流畅度（LLM-as-Judge）。"""
        scores = []
        for case in self.test_cases[:20]:
            judge_prompt = f"""
            对以下易学解释的中文语言流畅度评分（1-5分）：
            {case.get('ai_output', '')[:1000]}
            仅返回数字。
            """
            score_str = await self.model_router.call(
                tier=TaskTier.TIER_1_LIGHTWEIGHT,
                prompt=judge_prompt,
            )
            try:
                scores.append(float(score_str.strip()))
            except ValueError:
                scores.append(3.0)

        return EvalResult(
            metric="language_fluency",
            score=sum(scores) / len(scores) if scores else 0,
            details={"num_samples": len(scores), "scores": scores},
            timestamp=datetime.utcnow().isoformat(),
        )
```

### 8.4 A/B 测试框架

```python
# ai/evaluation/ab_testing.py

class ABTestManager:
    """A/B 测试管理器，用于对比不同 Prompt 版本或模型配置。"""

    def __init__(self):
        self.experiments: dict[str, dict] = {}

    def create_experiment(
        self,
        name: str,
        variant_a: dict,
        variant_b: dict,
        traffic_split: float = 0.5,
        metrics: list[str] = None,
    ):
        """创建实验。"""
        self.experiments[name] = {
            "variant_a": variant_a,      # {"prompt_id": "...", "model": "..."}
            "variant_b": variant_b,
            "traffic_split": traffic_split,
            "metrics": metrics or ["user_safety_score", "fluency", "relevance"],
            "results_a": [],
            "results_b": [],
            "created_at": datetime.utcnow(),
        }

    def assign_variant(self, experiment_name: str, user_id: str) -> str:
        """根据用户 ID 确定性分配变体。"""
        hash_val = hashlib.md5(f"{experiment_name}:{user_id}".encode()).hexdigest()
        threshold = int(hash_val[:8], 16) / 0xFFFFFFFF
        exp = self.experiments[experiment_name]
        return "variant_a" if threshold < exp["traffic_split"] else "variant_b"

    async def record_result(self, experiment_name: str, variant: str, metrics: dict):
        """记录实验结果。"""
        key = f"results_{variant.split('_')[1]}"
        self.experiments[experiment_name][key].append({
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat(),
        })

    def get_results(self, experiment_name: str) -> dict:
        """获取实验结果对比。"""
        exp = self.experiments[experiment_name]
        a_scores = self._aggregate(exp["results_a"], exp["metrics"])
        b_scores = self._aggregate(exp["results_b"], exp["metrics"])
        return {
            "variant_a": a_scores,
            "variant_b": b_scores,
            "winner": self._determine_winner(a_scores, b_scores),
        }

    def _aggregate(self, results: list[dict], metrics: list[str]) -> dict:
        if not results:
            return {m: 0 for m in metrics}
        agg = {}
        for m in metrics:
            values = [r["metrics"].get(m, 0) for r in results]
            agg[m] = sum(values) / len(values)
        agg["sample_size"] = len(results)
        return agg

    def _determine_winner(self, a: dict, b: dict) -> str:
        a_score = sum(v for k, v in a.items() if k != "sample_size")
        b_score = sum(v for k, v in b.items() if k != "sample_size")
        if a_score > b_score * 1.05:
            return "variant_a"
        elif b_score > a_score * 1.05:
            return "variant_b"
        return "no_clear_winner"
```

### 8.5 持续优化策略

```
┌─────────────────────────────────────────────────────────────┐
│                    持续优化闭环                               │
│                                                             │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐            │
│  │ 用户反馈 │────▶│ 数据收集 │────▶│ 分析     │            │
│  │ (显式+   │     │ + 标注   │     │ 问题模式 │            │
│  │  隐式)   │     │          │     │          │            │
│  └──────────┘     └──────────┘     └────┬─────┘            │
│       ▲                                  │                  │
│       │                                  ▼                  │
│  ┌────┴─────┐     ┌──────────┐     ┌──────────┐            │
│  │ 部署     │◀────│ 评估     │◀────│ 优化     │            │
│  │ 灰度发布 │     │ A/B 测试 │     │ Prompt   │            │
│  │          │     │ 自动化   │     │ 模型/参数│            │
│  └──────────┘     └──────────┘     └──────────┘            │
└─────────────────────────────────────────────────────────────┘
```

**优化方向 1: Prompt 迭代**

- 收集低分案例 → 分析失败模式 → 修改 Prompt → A/B 测试 → 部署
- 版本控制确保可回滚

**优化方向 2: RAG 质量提升**

- 分析 RAG 检索的 nDCG 分数
- 补充缺失的知识源
- 调整融合权重
- 优化 Embedding 模型

**优化方向 3: 模型选择优化**

- 跟踪各 Tier 模型的实际表现
- 分析成本-质量拐点
- 评估新模型的替代价值

**优化方向 4: 规则引擎扩展**

- 收集 AI 需要"猜测"而非"解释"的案例
- 将可确定化的推理路径转化为规则
- 逐步减少 AI 的不确定性区域

**优化方向 5: 用户个性化**

- 分析用户对不同解释风格的偏好
- 调整输出的详细程度
- 根据用户历史调整解释角度

---

## 附录 A: 系统数据流全景图

```
用户提问
  │
  ▼
┌─────────────────────────────────────────────────────────────┐
│ API Gateway (FastAPI)                                       │
│   ├── 认证 / 频率限制                                        │
│   ├── 请求路由                                               │
│   └── WebSocket 流式连接                                     │
└─────────────────────┬───────────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ Agent Workflow (LangGraph)                                  │
│   ├── 意图分类 (Tier 1) ──────────────────────────┐         │
│   ├── 记忆查询 (Redis + PG + Neo4j)               │         │
│   ├── 路由决策 ◀──────────────────────────────────┘         │
│   ├── RAG 检索                                               │
│   │   ├── 向量检索 (Qdrant)                                  │
│   │   ├── 图谱检索 (Neo4j)                                   │
│   │   ├── 规则检索 (Python Engine)                            │
│   │   └── 融合排序 (RRF + Weight)                            │
│   ├── AI 解释 (Tier 2-4)                                    │
│   ├── 安全检查                                               │
│   └── 输出格式化                                             │
└─────────────────────┬───────────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ 持久化层                                                     │
│   ├── PostgreSQL (用户、卦记录、配置)                         │
│   ├── Redis (会话缓存、工作记忆、频率限制)                    │
│   ├── Qdrant (知识向量、用户历史向量)                         │
│   ├── Neo4j (易学图谱、用户图谱)                              │
│   └── ClickHouse (日志、分析、指标)                           │
└─────────────────────────────────────────────────────────────┘
```

## 附录 B: 关键配置

```yaml
# config/ai.yaml

models:
  default_provider: deepseek
  providers:
    deepseek:
      api_key: ${DEEPSEEK_API_KEY}
      base_url: https://api.deepseek.com
    anthropic:
      api_key: ${ANTHROPIC_API_KEY}
    openai:
      api_key: ${OPENAI_API_KEY}
    qwen:
      api_key: ${QWEN_API_KEY}
      base_url: https://dashscope.aliyuncs.com

rag:
  qdrant:
    url: http://localhost:6333
    collections:
      - name: yijing_texts
        embedding_model: bge-m3
        dimensions: 1024
      - name: commentaries
        embedding_model: bge-m3
        dimensions: 1024
      - name: user_history
        embedding_model: jina-embeddings-v3
        dimensions: 1024
  fusion:
    k: 60
    weights:
      vector: 0.35
      graph: 0.30
      rule: 0.35

graph:
  neo4j:
    uri: bolt://localhost:7687
    user: neo4j
    password: ${NEO4J_PASSWORD}

memory:
  redis:
    url: redis://localhost:6379
  decay:
    half_life_days: 90
    compression_threshold: 0.1
  working_memory_ttl: 2h

safety:
  forbidden_phrases:
    - "一定会"
    - "必然"
    - "保证"
    - "绝对"
    - "百分之百"
  max_retries: 2

evaluation:
  auto_eval_schedule: "0 3 * * *"  # 每天凌晨3点
  ab_test_min_samples: 100
  cost_alert_threshold: 0.05  # 单次请求成本上限(USD)
```

---

*本文档版本: 1.0.0*
*最后更新: 2025-05-29*
*关联文档: yiai.md (总体架构)*
