# YI-AI 系统架构设计文档

> 东方变化学 AI 操作系统 | V2.0

---

## 一、分层架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          可视化层 (Visualization Layer)                       │
│         太极动态 │ 六爻排盘 │ 动爻动画 │ 图谱网络 │ 时间演化树                │
├─────────────────────────────────────────────────────────────────────────────┤
│                           Agent层 (Agent Layer)                              │
│           自动推演 │ 趋势报告 │ 周期发现 │ 主动观察 │ 智能问答                │
├─────────────────────────────────────────────────────────────────────────────┤
│                      推演模拟层 (Simulation Layer)                           │
│           卦象演化 │ 状态转移 │ 趋势模拟 │ 时间推演 │ 概率树                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                      长期记忆层 (Memory Layer)                               │
│           用户历史 │ 卦象变化 │ 长期趋势 │ 行为模式 │ 情绪轨迹                │
├─────────────────────────────────────────────────────────────────────────────┤
│                       AI语义层 (AI Semantic Layer)                           │
│           意图理解 │ 规则翻译 │ 趋势解释 │ 自然语言输出 │ 风险提示            │
├─────────────────────────────────────────────────────────────────────────────┤
│                      知识图谱层 (Knowledge Graph Layer)                      │
│           卦→五行→六亲→时间→关系 │ Neo4j │ GraphRAG                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                       规则推演层 (Rule Engine Layer)                         │
│           生克 │ 冲合 │ 旺衰 │ 用神 │ 动静 │ 变卦 │ 错综互                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                      基础易学层 (Foundation Layer)                           │
│           八卦 │ 六十四卦 │ 爻 │ 五行 │ 纳甲 │ 六亲 │ 六神 │ 世应 │ 动爻   │
└─────────────────────────────────────────────────────────────────────────────┘
         ↑                    ↑                    ↑                    ↑
    ┌────┴────┐          ┌────┴────┐          ┌────┴────┐          ┌────┴────┐
    │PostgreSQL│          │  Redis  │          │  Qdrant │          │  Neo4j  │
    └─────────┘          └─────────┘          └─────────┘          └─────────┘
```

---

## 二、各层职责与接口定义

### 2.1 基础易学层（Foundation Layer）

**职责**：系统根基，提供易学基础数据结构与计算

| 模块 | 职责 | 输入 | 输出 |
|------|------|------|------|
| 卦引擎 | 卦象生成与转换 | 阴阳序列/时间/数字 | 本卦、变卦、错卦、综卦、互卦 |
| 爻引擎 | 爻位计算与状态管理 | 卦象数据 | 六爻状态、动爻标记 |
| 五行引擎 | 五行关系计算 | 五行属性 | 生克关系、旺衰状态 |
| 纳甲引擎 | 干支纳甲映射 | 卦象、时间 | 纳甲结果、干支组合 |
| 六亲引擎 | 六亲关系推导 | 卦象、用神 | 六亲分布 |
| 六神引擎 | 六神排列 | 日干 | 六神配置 |
| 世应引擎 | 世应定位 | 卦象类型 | 世爻、应爻位置 |

**数据结构定义**：

```python
# 基础类型
YinYang = Literal["yin", "yang"]  # 阴阳
TrigramName = Literal["乾", "兑", "离", "震", "巽", "坎", "艮", "坤"]
Element = Literal["金", "木", "水", "火", "土"]
SixRelation = Literal["父母", "官鬼", "妻财", "子孙", "兄弟"]

@dataclass(frozen=True)
class Line:
    position: int          # 爻位 1-6
    yin_yang: YinYang      # 阴阳
    is_moving: bool        # 是否动爻
    element: Element       # 五行属性
    six_relation: SixRelation  # 六亲
    six_spirit: str        # 六神
    gan_zhi: str           # 干支
    is_shi: bool           # 是否世爻
    is_ying: bool          # 是否应爻

@dataclass(frozen=True)
class Hexagram:
    id: int                # 1-64
    name: str              # 卦名
    upper_trigram: TrigramName
    lower_trigram: TrigramName
    lines: tuple[Line, ...]  # 6个爻
    element: Element       # 卦的五行属性
```

**依赖**：无（最底层）

---

### 2.2 规则推演层（Rule Engine Layer）

**职责**：易学规则计算引擎，处理所有逻辑推演

| 模块 | 职责 | 输入 | 输出 |
|------|------|------|------|
| 生克引擎 | 五行生克关系计算 | 两个五行属性 | 生/克/被生/被克关系 |
| 冲合引擎 | 地支冲合计算 | 地支组合 | 冲合关系列表 |
| 旺衰引擎 | 时令旺衰判断 | 五行、月令 | 旺/相/休/囚/死状态 |
| 用神引擎 | 用神选取 | 问题类型、卦象 | 用神爻 |
| 变卦引擎 | 动爻变卦计算 | 本卦、动爻 | 变卦 |
| 错综互引擎 | 错卦/综卦/互卦生成 | 本卦 | 错卦、综卦、互卦 |

**规则引擎架构**：

```python
class RuleEngine:
    """规则推演引擎 - 纯计算，无AI参与"""

    def analyze(self, hexagram: Hexagram, question_type: str) -> RuleAnalysisResult:
        """
        完整分析流程：
        1. 确定用神
        2. 分析动爻
        3. 计算生克关系
        4. 判断旺衰
        5. 综合推断
        """
        yong_shen = self._find_yong_shen(hexagram, question_type)
        moving_lines = self._get_moving_lines(hexagram)
        relationships = self._analyze_relationships(hexagram, yong_shen)
        prosperity = self._judge_prosperity(hexagram, yong_shen)

        return RuleAnalysisResult(
            yong_shen=yong_shen,
            moving_lines=moving_lines,
            relationships=relationships,
            prosperity=prosperity,
            verdict=self._synthesize(relationships, prosperity)
        )

@dataclass(frozen=True)
class RuleAnalysisResult:
    yong_shen: Line
    moving_lines: tuple[Line, ...]
    relationships: RelationshipGraph
    prosperity: ProsperityState
    verdict: Verdict
```

**依赖**：基础易学层

---

### 2.3 知识图谱层（Knowledge Graph Layer）

**职责**：构建易学知识关系网络，支持图谱查询与推理

**Neo4j 节点模型**：

```cypher
// 节点定义
CREATE (h:Hexagram {id: 1, name: "乾", binary: "111111"})
CREATE (t:Trigram {name: "乾", element: "金"})
CREATE (l:Line {position: 1, yin_yang: "yang"})
CREATE (e:Element {name: "金"})
CREATE (r:Role {name: "父母"})
CREATE (gz:GanZhi {name: "甲子"})
CREATE (t:Time {timestamp: datetime(), lunar: "四月初一"})

// 关系定义
(h)-[:HAS_UPPER]->(t)
(h)-[:HAS_LOWER]->(t)
(h)-[:CONTAINS]->(l)
(l)-[:HAS_ELEMENT]->(e)
(l)-[:HAS_ROLE]->(r)
(l)-[:HAS_GANZHI]->(gz)
(e)-[:GENERATES]->(e)  // 五行相生
(e)-[:OVERCOMES]->(e)  // 五行相克
(h)-[:TRANSFORMS_TO]->(h)  // 变卦关系
(h)-[:OPPOSITE_OF]->(h)   // 错卦
(h)-[:REVERSED_OF]->(h)   // 综卦
```

**图谱服务接口**：

```python
class KnowledgeGraphService:
    """知识图谱服务"""

    async def get_hexagram_relations(self, hexagram_id: int) -> GraphRelations:
        """获取卦象的所有关系"""

    async def find_pattern(self, pattern: GraphPattern) -> list[PatternMatch]:
        """模式匹配查询"""

    async def get_evolution_path(self, hexagram_id: int, depth: int) -> EvolutionTree:
        """获取演化路径"""

    async def search_by_similarity(self, embedding: Vector, top_k: int) -> list[Hexagram]:
        """向量相似度搜索"""
```

**依赖**：基础易学层、规则推演层

---

### 2.4 AI语义层（AI Semantic Layer）

**职责**：AI解释与自然语言处理，将规则结果翻译为现代语义

**核心原则**：AI不计算，只解释

| 模块 | 职责 | 输入 | 输出 |
|------|------|------|------|
| 意图理解 | 解析用户问题 | 用户自然语言 | 结构化意图 |
| 规则翻译 | 将规则结果转为可解释文本 | RuleAnalysisResult | 解释文本 |
| 趋势解释 | 长期趋势分析解读 | 历史数据、当前状态 | 趋势报告 |
| 风险提示 | 识别潜在风险点 | 分析结果 | 风险提示列表 |

**AI工作流**：

```python
class AISemanticEngine:
    """AI语义引擎 - 只解释，不计算"""

    async def interpret(self, user_query: str, rule_result: RuleAnalysisResult) -> Interpretation:
        """
        工作流：
        1. 理解用户意图
        2. 匹配规则结果
        3. 调用RAG获取参考
        4. 生成解释
        """
        intent = await self._understand_intent(user_query)
        context = await self._retrieve_context(rule_result, intent)
        interpretation = await self._generate_interpretation(
            user_query, rule_result, context
        )
        return interpretation

@dataclass(frozen=True)
class Interpretation:
    intent: UserIntent
    main_text: str           # 主要解释
    key_points: tuple[str, ...]  # 要点
    risk_warnings: tuple[str, ...]  # 风险提示
    suggestions: tuple[str, ...]    # 建议
    confidence: float        # 置信度
    references: tuple[str, ...]     # 参考来源
```

**RAG架构**：

```python
class HybridRAG:
    """混合检索增强生成"""

    async def retrieve(self, query: str, context: dict) -> RAGResult:
        """
        三路检索：
        1. 向量检索 - 语义相似的易学文本
        2. 图谱检索 - 结构化关系查询
        3. 规则检索 - 匹配的规则案例
        """
        vector_results = await self._vector_search(query)
        graph_results = await self._graph_search(query, context)
        rule_results = await self._rule_search(context)

        return self._merge_and_rank(vector_results, graph_results, rule_results)
```

**依赖**：规则推演层、知识图谱层、长期记忆层

---

### 2.5 长期记忆层（Memory Layer）

**职责**：构建用户变化轨迹模型

**记忆类型**：

```python
class MemoryType(Enum):
    EPISODIC = "episodic"      # 情景记忆 - 具体事件
    SEMANTIC = "semantic"      # 语义记忆 - 知识概念
    PROCEDURAL = "procedural"  # 程序记忆 - 行为模式
    EMOTIONAL = "emotional"    # 情绪记忆 - 情绪轨迹

@dataclass(frozen=True)
class UserMemory:
    user_id: str
    memory_type: MemoryType
    content: dict
    timestamp: datetime
    hexagram_snapshot: Hexagram
    emotional_state: EmotionalState
    context: dict
    importance: float  # 重要性权重

@dataclass(frozen=True)
class UserChangeModel:
    """用户变化模型"""
    user_id: str
    long_term_themes: tuple[str, ...]    # 长期主题
    recurring_patterns: tuple[Pattern, ...]  # 重复模式
    emotional_trajectory: EmotionalTrajectory
    hexagram_frequency: dict[str, float]  # 卦象频率
    risk_indicators: tuple[RiskIndicator, ...]
```

**记忆存储架构**：

```python
class MemoryEngine:
    """长期记忆引擎"""

    async def store(self, memory: UserMemory) -> None:
        """存储记忆"""
        # 1. 写入PostgreSQL（结构化）
        await self.pg_store(memory)
        # 2. 写入Qdrant（向量化）
        await self.vector_store(memory)
        # 3. 更新Neo4j（关系）
        await self.graph_store(memory)
        # 4. 更新用户变化模型
        await self.update_change_model(memory)

    async def recall(self, user_id: str, query: str, context: dict) -> MemoryRecall:
        """召回相关记忆"""
        # 混合召回：向量 + 图谱 + 时间衰减
        ...

    async def get_change_model(self, user_id: str) -> UserChangeModel:
        """获取用户变化模型"""
        ...
```

**依赖**：基础易学层、AI语义层

---

### 2.6 推演模拟层（Simulation Layer）

**职责**：模拟状态变化与趋势演化

**核心能力**：

```python
class SimulationEngine:
    """推演模拟引擎"""

    async def evolve(self, current: Hexagram, steps: int) -> EvolutionChain:
        """
        卦象演化
        乾 → 姤 → 遁 → 否 → 观 → 剥 → 晋 → 大有
        """
        chain = [current]
        for _ in range(steps):
            next_state = self._apply_transformation_rules(chain[-1])
            chain.append(next_state)
        return EvolutionChain(states=tuple(chain))

    async def simulate_probability_tree(
        self,
        current: Hexagram,
        depth: int
    ) -> ProbabilityTree:
        """
        概率演化树
        考虑所有可能的动爻组合
        """
        ...

    async def time_based_evolution(
        self,
        current: Hexagram,
        time_range: TimeRange
    ) -> TimeEvolution:
        """
        基于时间的演化
        考虑节气、月令等时间因素
        """
        ...
```

**状态转移模型**：

```python
@dataclass(frozen=True)
class StateTransition:
    from_state: Hexagram
    to_state: Hexagram
    trigger: str           # 触发条件
    probability: float     # 转移概率
    time_factor: TimeFactor
    conditions: tuple[Condition, ...]

@dataclass(frozen=True)
class EvolutionChain:
    states: tuple[Hexagram, ...]
    transitions: tuple[StateTransition, ...]
    probability: float
    time_span: TimeRange
```

**依赖**：基础易学层、规则推演层、知识图谱层

---

### 2.7 Agent层（Agent Layer）

**职责**：AI自动推演与主动分析

**Agent类型**：

```python
class AgentType(Enum):
    ANALYZER = "analyzer"        # 分析Agent
    OBSERVER = "observer"        # 观察Agent
    REPORTER = "reporter"        # 报告Agent
    ADVISOR = "advisor"          # 建议Agent

class BaseAgent(ABC):
    """Agent基类"""

    @abstractmethod
    async def run(self, context: AgentContext) -> AgentResult:
        ...

class AnalyzerAgent(BaseAgent):
    """分析Agent - 深度分析卦象"""

    async def run(self, context: AgentContext) -> AgentResult:
        # 1. 调用规则引擎
        rule_result = await self.rule_engine.analyze(context.hexagram)
        # 2. 调用AI语义层
        interpretation = await self.ai_engine.interpret(context.query, rule_result)
        # 3. 查询历史记忆
        memories = await self.memory_engine.recall(context.user_id, context.query)
        # 4. 生成综合分析
        return self._synthesize(rule_result, interpretation, memories)

class ObserverAgent(BaseAgent):
    """观察Agent - 持续监控变化"""

    async def run(self, context: AgentContext) -> AgentResult:
        # 1. 获取用户变化模型
        change_model = await self.memory_engine.get_change_model(context.user_id)
        # 2. 识别模式
        patterns = self._identify_patterns(change_model)
        # 3. 检测异常
        anomalies = self._detect_anomalies(change_model)
        # 4. 生成观察报告
        return self._generate_observation(patterns, anomalies)
```

**Agent编排**：

```python
class AgentOrchestrator:
    """Agent编排器"""

    async def execute_workflow(self, workflow: Workflow) -> WorkflowResult:
        """
        工作流执行：
        1. 分析阶段 - AnalyzerAgent
        2. 观察阶段 - ObserverAgent
        3. 报告阶段 - ReporterAgent
        4. 建议阶段 - AdvisorAgent
        """
        results = {}
        for step in workflow.steps:
            agent = self._get_agent(step.agent_type)
            result = await agent.run(step.context)
            results[step.name] = result
        return WorkflowResult(results=results)
```

**依赖**：所有下层

---

### 2.8 可视化层（Visualization Layer）

**职责**：东方科技感的可视化呈现

**可视化组件**：

```typescript
// 前端组件结构
interface VisualizationComponents {
  // 太极动态
  TaijiAnimation: {
    yinYangBalance: number;  // 阴阳平衡度
    rotationSpeed: number;
    colorScheme: 'gold' | 'jade' | 'ink';
  };

  // 六爻排盘
  HexagramChart: {
    hexagram: Hexagram;
    showMovingLines: boolean;
    showGanZhi: boolean;
    showSixRelations: boolean;
    animation: 'flip' | 'fade' | 'slide';
  };

  // 图谱网络
  KnowledgeGraph: {
    nodes: GraphNode[];
    edges: GraphEdge[];
    layout: 'force' | 'circular' | 'hierarchical';
    interactive: boolean;
  };

  // 演化时间轴
  EvolutionTimeline: {
    states: Hexagram[];
    currentIndex: number;
    autoPlay: boolean;
  };
}
```

**动画系统**：

```typescript
// GSAP动画配置
const hexagramFlipAnimation = {
  duration: 0.6,
  ease: "power2.inOut",
  stagger: 0.1,
  onComplete: () => {
    // 更新爻状态
  }
};

// Three.js 3D太极
class TaijiScene {
  constructor() {
    this.scene = new THREE.Scene();
    this.yinMesh = this.createYinMesh();
    this.yangMesh = this.createYangMesh();
  }

  animate() {
    requestAnimationFrame(() => this.animate());
    this.yinMesh.rotation.z += 0.01;
    this.yangMesh.rotation.z -= 0.01;
    this.renderer.render(this.scene, this.camera);
  }
}
```

**依赖**：所有下层（通过API）

---

## 三、层间通信机制

### 3.1 通信模式

```
┌─────────────────────────────────────────────────────────────────┐
│                        通信架构                                  │
├─────────────────────────────────────────────────────────────────┤
│  同步调用（HTTP/gRPC）                                          │
│  ├── 规则引擎调用                                               │
│  ├── 基础计算调用                                               │
│  └── 简单查询调用                                               │
├─────────────────────────────────────────────────────────────────┤
│  异步消息（Redis Pub/Sub / RabbitMQ）                           │
│  ├── Agent任务分发                                              │
│  ├── 记忆存储                                                   │
│  └── 推演任务                                                   │
├─────────────────────────────────────────────────────────────────┤
│  WebSocket                                                      │
│  ├── 实时推演结果                                               │
│  ├── 可视化数据流                                               │
│  └── Agent状态更新                                              │
├─────────────────────────────────────────────────────────────────┤
│  事件总线（Event Bus）                                          │
│  ├── 跨层事件通知                                               │
│  └── 解耦通信                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 接口定义

```python
# 层间接口协议
class LayerInterface:
    """层间通信接口"""

    # 同步调用
    async def call_sync(self, target_layer: str, method: str, params: dict) -> dict:
        ...

    # 异步消息
    async def publish_event(self, event_type: str, payload: dict) -> None:
        ...

    # 事件订阅
    async def subscribe_event(self, event_type: str, handler: Callable) -> None:
        ...

# 事件类型定义
class EventTypes:
    # 基础层事件
    HEXAGRAM_CREATED = "hexagram.created"
    LINE_CHANGED = "line.changed"

    # 规则层事件
    ANALYSIS_COMPLETED = "analysis.completed"
    RULE_TRIGGERED = "rule.triggered"

    # AI层事件
    INTERPRETATION_GENERATED = "interpretation.generated"
    INTENT_RECOGNIZED = "intent.recognized"

    # 记忆层事件
    MEMORY_STORED = "memory.stored"
    PATTERN_DETECTED = "pattern.detected"

    # Agent层事件
    AGENT_TASK_STARTED = "agent.task.started"
    AGENT_TASK_COMPLETED = "agent.task.completed"
```

### 3.3 数据流向图

```
用户输入
    │
    ▼
┌─────────────┐
│ 意图理解    │ ← AI语义层
└──────┬──────┘
       │ 结构化意图
       ▼
┌─────────────┐
│ 卦象生成    │ ← 基础易学层
└──────┬──────┘
       │ 卦象数据
       ▼
┌─────────────┐
│ 规则分析    │ ← 规则推演层
└──────┬──────┘
       │ 分析结果
       ├──────────────────┐
       ▼                  ▼
┌─────────────┐    ┌─────────────┐
│ 图谱查询    │    │ 记忆召回    │ ← 知识图谱层 + 长期记忆层
└──────┬──────┘    └──────┬──────┘
       │                  │
       └────────┬─────────┘
                │ 上下文
                ▼
         ┌─────────────┐
         │ AI解释生成  │ ← AI语义层
         └──────┬──────┘
                │ 解释结果
                ├──────────────────┐
                ▼                  ▼
         ┌─────────────┐    ┌─────────────┐
         │ 可视化渲染  │    │ 记忆存储    │ ← 可视化层 + 长期记忆层
         └─────────────┘    └─────────────┘
```

---

## 四、核心模块划分（模块化单体）

### 4.1 项目结构

```
yiai/
├── monolith/                      # 单体应用（可拆分）
│   ├── foundation/                # 基础易学层
│   │   ├── hexagram/             # 卦引擎
│   │   ├── line/                 # 爻引擎
│   │   ├── element/              # 五行引擎
│   │   ├── gan_zhi/              # 干支引擎
│   │   ├── six_relation/         # 六亲引擎
│   │   └── six_spirit/           # 六神引擎
│   │
│   ├── rule_engine/              # 规则推演层
│   │   ├── sheng_ke/             # 生克规则
│   │   ├── chong_he/             # 冲合规则
│   │   ├── wang_shuai/           # 旺衰规则
│   │   ├── yong_shen/            # 用神规则
│   │   └── bian_gua/             # 变卦规则
│   │
│   ├── knowledge_graph/          # 知识图谱层
│   │   ├── neo4j_client/
│   │   ├── graph_models/
│   │   └── graph_queries/
│   │
│   ├── ai_semantic/              # AI语义层
│   │   ├── intent/               # 意图理解
│   │   ├── interpreter/          # 规则翻译
│   │   ├── rag/                  # RAG系统
│   │   └── prompt/               # Prompt管理
│   │
│   ├── memory/                   # 长期记忆层
│   │   ├── episodic/             # 情景记忆
│   │   ├── semantic/             # 语义记忆
│   │   ├── change_model/         # 变化模型
│   │   └── vector_store/         # 向量存储
│   │
│   ├── simulation/               # 推演模拟层
│   │   ├── evolution/            # 演化引擎
│   │   ├── probability/          # 概率计算
│   │   └── time_series/          # 时间序列
│   │
│   ├── agent/                    # Agent层
│   │   ├── analyzer/
│   │   ├── observer/
│   │   ├── reporter/
│   │   └── orchestrator/
│   │
│   └── api/                      # API层
│       ├── rest/                 # REST API
│       ├── websocket/            # WebSocket
│       └── graphql/              # GraphQL（可选）
│
├── frontend/                     # 前端应用
│   ├── components/
│   │   ├── visualization/        # 可视化组件
│   │   ├── hexagram/             # 卦象组件
│   │   └── ui/                   # 通用UI
│   ├── composables/              # Vue组合式函数
│   ├── stores/                   # Pinia状态
│   └── pages/                    # 页面
│
└── shared/                       # 共享代码
    ├── types/                    # 类型定义
    ├── constants/                # 常量
    └── utils/                    # 工具函数
```

### 4.2 模块边界与依赖规则

```python
# 依赖规则（通过依赖注入实现）
DEPENDENCY_RULES = {
    "foundation": [],                    # 无依赖
    "rule_engine": ["foundation"],       # 依赖基础层
    "knowledge_graph": ["foundation", "rule_engine"],
    "ai_semantic": ["rule_engine", "knowledge_graph", "memory"],
    "memory": ["foundation"],
    "simulation": ["foundation", "rule_engine", "knowledge_graph"],
    "agent": ["ai_semantic", "memory", "simulation"],
    "api": ["agent"],                    # 最终依赖所有层
}
```

### 4.3 微服务拆分策略

当单体达到以下阈值时考虑拆分：

| 阈值 | 拆分目标 |
|------|----------|
| 团队 > 10人 | 按层拆分服务 |
| 请求量 > 10k/s | 拆分热路径 |
| 部署频率冲突 | 独立部署单元 |
| 技术栈差异 | AI服务独立 |

**拆分优先级**：
1. AI服务（独立扩缩容）
2. Agent服务（异步任务密集）
3. 推演服务（计算密集）
4. 图谱服务（特殊数据库）

---

## 五、扩展性设计

### 5.1 插件化架构

```python
# 规则插件系统
class RulePlugin(ABC):
    """规则插件接口"""

    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def version(self) -> str: ...

    @abstractmethod
    def execute(self, context: RuleContext) -> RuleResult: ...

# 插件注册
class RulePluginRegistry:
    def __init__(self):
        self._plugins: dict[str, RulePlugin] = {}

    def register(self, plugin: RulePlugin) -> None:
        self._plugins[plugin.name()] = plugin

    def get(self, name: str) -> RulePlugin:
        return self._plugins[name]

# 扩展点示例
class MeihuaPlugin(RulePlugin):
    """梅花易数插件"""
    def name(self) -> str:
        return "meihua"

    def execute(self, context: RuleContext) -> RuleResult:
        # 梅花易数逻辑
        ...

class QimenPlugin(RulePlugin):
    """奇门遁甲插件"""
    ...
```

### 5.2 事件驱动扩展

```python
# 事件系统支持扩展
class EventBus:
    def __init__(self):
        self._handlers: dict[str, list[Callable]] = defaultdict(list)

    def on(self, event_type: str, handler: Callable) -> None:
        self._handlers[event_type].append(handler)

    async def emit(self, event_type: str, data: dict) -> None:
        for handler in self._handlers[event_type]:
            await handler(data)

# 扩展示例：新增"紫微斗数"模块
event_bus.on("divination.requested", async (data):
    if data["type"] == "ziwei":
        result = await ziwei_engine.analyze(data)
        await event_bus.emit("divination.completed", result)
)
```

---

## 六、性能设计

### 6.1 缓存策略

```
┌─────────────────────────────────────────────────────────────┐
│                        缓存层级                              │
├─────────────────────────────────────────────────────────────┤
│  L1: 进程内缓存（LRU）                                      │
│  ├── 卦象数据（64卦固定）                                   │
│  ├── 五行关系表                                             │
│  └── 热门查询结果                                           │
├─────────────────────────────────────────────────────────────┤
│  L2: Redis缓存                                              │
│  ├── 用户会话                                               │
│  ├── 推演结果                                               │
│  ├── AI解释缓存                                             │
│  └── 频繁查询                                               │
├─────────────────────────────────────────────────────────────┤
│  L3: CDN                                                    │
│  ├── 静态资源                                               │
│  └── 可视化资源                                             │
└─────────────────────────────────────────────────────────────┘
```

**缓存实现**：

```python
class CacheManager:
    """多级缓存管理"""

    def __init__(self):
        self.l1 = LRUCache(maxsize=1000)
        self.l2 = RedisCache()

    async def get(self, key: str) -> Optional[Any]:
        result = self.l1.get(key)
        if result:
            return result
        result = await self.l2.get(key)
        if result:
            self.l1.set(key, result)
            return result
        return None

    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        self.l1.set(key, value)
        await self.l2.set(key, value, ttl)
```

### 6.2 异步处理

```python
# 使用Celery处理耗时任务
from celery import Celery

celery_app = Celery('yiai', broker='redis://localhost:6379/0')

@celery_app.task(bind=True, max_retries=3)
async def run_deep_analysis(self, user_id: str, hexagram_data: dict):
    """深度分析任务"""
    try:
        rule_result = await rule_engine.analyze(hexagram_data)
        graph_data = await knowledge_graph.query(hexagram_data)
        interpretation = await ai_engine.interpret(rule_result, graph_data)
        await memory.store(user_id, interpretation)
        await websocket.notify(user_id, interpretation)
    except Exception as exc:
        self.retry(exc=exc, countdown=60)
```

---

## 七、部署架构

### 7.1 容器化部署

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: ./monolith
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/yiai
      - REDIS_URL=redis://redis:6379/0
      - NEO4J_URI=bolt://neo4j:7687
      - QDRANT_URL=http://qdrant:6333
    depends_on:
      - postgres
      - redis
      - neo4j
      - qdrant

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"

  postgres:
    image: postgres:16
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine

  neo4j:
    image: neo4j:5

  qdrant:
    image: qdrant/qdrant

volumes:
  postgres_data:
  redis_data:
  neo4j_data:
  qdrant_data:
```

### 7.2 网络架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        CDN / 边缘节点                           │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     负载均衡器 (Nginx/ALB)                       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              ▼                           ▼
┌─────────────────────┐       ┌─────────────────────┐
│    前端服务集群      │       │     API网关         │
│   (Nuxt SSR)       │       │   (Kong/Traefik)    │
└─────────────────────┘       └──────────┬──────────┘
                                         │
                           ┌─────────────┼─────────────┐
                           ▼             ▼             ▼
                    ┌──────────┐  ┌──────────┐  ┌──────────┐
                    │ API服务  │  │ AI服务   │  │ Agent服务│
                    │ 集群     │  │ 集群     │  │ 集群     │
                    └────┬─────┘  └────┬─────┘  └────┬─────┘
                         │             │             │
                         └─────────────┼─────────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    ▼                  ▼                  ▼
             ┌──────────┐       ┌──────────┐       ┌──────────┐
             │PostgreSQL│       │  Redis   │       │  Neo4j   │
             │ 集群     │       │  集群    │       │  集群    │
             └──────────┘       └──────────┘       └──────────┘
```

---

## 八、安全设计

### 8.1 认证与授权

```python
# JWT认证
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_current_user(token: str = Depends(security)) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user = await user_service.get_by_id(payload["sub"])
        if not user:
            raise HTTPException(status_code=401)
        return user
    except jwt.JWTError:
        raise HTTPException(status_code=401)

# RBAC权限
class Permission(Enum):
    READ_HEXAGRAM = "read:hexagram"
    CREATE_DIVINATION = "create:divination"
    ACCESS_AI = "access:ai"
    ADMIN = "admin"

ROLE_PERMISSIONS = {
    "user": [Permission.READ_HEXAGRAM, Permission.CREATE_DIVINATION],
    "premium": [Permission.READ_HEXAGRAM, Permission.CREATE_DIVINATION, Permission.ACCESS_AI],
    "admin": [Permission.ADMIN],
}
```

---

## 九、监控与可观测性

```python
# 性能指标收集
from prometheus_client import Counter, Histogram, Gauge

REQUEST_COUNT = Counter('yiai_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('yiai_request_duration_seconds', 'Request latency')
ACTIVE_USERS = Gauge('yiai_active_users', 'Active users')
AI_LATENCY = Histogram('yiai_ai_duration_seconds', 'AI processing latency')
```

---

## 十、总结

### 架构特点

1. **分层清晰**：八层架构各司其职，职责单一
2. **模块化单体**：初期开发效率高，后期可拆分
3. **插件化设计**：支持易学体系扩展（梅花、奇门、紫微）
4. **AI与规则分离**：AI只解释不计算，保证系统确定性
5. **事件驱动**：解耦各层，支持异步处理
6. **多级缓存**：优化性能，减少重复计算
7. **容器化部署**：支持弹性扩缩容

### 未来演进路径

```
Phase 1 (0-6月)        Phase 2 (6-12月)       Phase 3 (1-2年)
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│ 基础六爻    │  →    │ 图谱+记忆   │  →    │ Agent+推演  │
│ 规则引擎    │       │ RAG系统     │       │ 多模型协同  │
│ 基础AI解释  │       │ 长期分析    │       │ 完整平台    │
└─────────────┘       └─────────────┘       └─────────────┘
```

---

*文档版本：2.0*
*最后更新：2026-05-29*
