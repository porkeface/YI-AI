# YI-AI 项目进度报告

> 最后更新：2026-05-30
> 版本：v0.4.0

---

## 一、总体进度

| 阶段 | 状态 | 完成度 | 说明 |
|------|------|--------|------|
| Phase 1 (MVP) | ✅ 已完成 | 100% | 六爻排盘、AI解释、前后端完整 |
| Phase 2 | ✅ 已完成 | 100% | 知识图谱、RAG、模型路由、记忆系统 |
| Phase 2.5 | ✅ 已完成 | 100% | 评估框架、A/B测试、Prompt管理、缓存 |
| Phase 3 | ✅ 已完成 | 100% | Agent工作流、深度推理、多模型协作、观察Agent |
| Phase 3.5 | ✅ 已完成 | 100% | 插件系统、API平台、企业版、i18n、分析平台 |
| **Phase 3.6** | **✅ 已完成** | **100%** | **向量检索(Qdrant)、知识图谱(Neo4j)、Embedding** |
| Phase 4 | ⏳ 未开始 | 0% | 完整东方变化学AI平台 |

---

## 二、Phase 1 - MVP（已完成）

### 里程碑

| 里程碑 | 状态 | 交付物 |
|--------|------|--------|
| M1.1 技术栈确认 | ✅ | FastAPI + Nuxt 3 + Vue 3 + TailwindCSS + Pinia |
| M1.2 卦引擎v1 | ✅ | 64卦全覆盖，105个单元测试 |
| M1.3 五行引擎v1 | ✅ | 五行生克、纳甲、六亲、六神、世应 |
| M1.4 起卦系统 | ✅ | 时间起卦、数字起卦、手动排盘 |
| M1.5 排盘系统 | ✅ | 六爻排盘含世应、六神、干支、变卦 |
| M1.6 AI解释v1 | ✅ | AIInterpreter + SafetyChecker + RAG知识库(104条) |
| M1.7 MVP发布 | ✅ | 核心功能完整可用 |

### 后端模块
- `foundation/` - hexagram_engine, element_engine, six_relation_engine, gan_zhi_engine, six_spirit_engine, shi_ying_engine
- `rule_engine/` - analyzer, sheng_ke, wang_shuai, yong_shen
- `ai/` - interpreter, prompt_builder, safety_checker, knowledge_base, llm_client
- `api/` - app, divination, history, hexagram, auth

### 前端页面
- 起卦页（三种方式）、排盘可视化、分析面板、AI解读、历史记录、图谱、登录/注册

---

## 三、Phase 2 - 基础设施（已完成）

### 里程碑

| 里程碑 | 状态 | 交付物 |
|--------|------|--------|
| M2.1 知识图谱 | ✅ | KnowledgeGraph + KnowledgeGraphBuilder（64卦自动构建） |
| M2.2 三路RAG | ✅ | RAGFusion（向量+图谱+规则，RRF融合算法） |
| M2.3 多模型路由 | ✅ | ModelRouter 4-Tier路由 + Fallback |
| M2.4 长期记忆 | ✅ | 4层记忆架构（Working/Episodic/Semantic/Procedural） |
| M2.5 梅花易数 | ✅ | PlumBlossomEngine（数字起卦、外应起卦） |
| M2.6 推演引擎v1 | ✅ | InferenceEngine（状态转移、3步推演） |
| M2.7 v1.0发布 | ✅ | 集成测试通过 |

---

## 四、Phase 2.5 - 工程化（已完成）

| 模块 | 状态 | 说明 |
|------|------|------|
| 评估框架 | ✅ | AutoEvaluator（多维评估）、ABTestManager |
| Prompt管理 | ✅ | PromptVersionControl（版本/回滚/对比）、PromptRegistry |
| 缓存系统 | ✅ | LRUCache + MultiLevelCache（L1内存 + L2 Redis可选） |
| 设计Token | ✅ | CSS设计系统、主题切换 |

---

## 五、Phase 3 - Agent系统（已完成）

### 里程碑

| 里程碑 | 状态 | 交付物 |
|--------|------|--------|
| M3.1 LangGraph Agent | ✅ | AgentWorkflow（8节点状态图、条件路由、20步上限） |
| M3.2 自动观察Agent | ✅ | PatternDetector、AnomalyDetector、TrendReporter |
| M3.3 深度推理 | ✅ | DeepReasoningEngine（10步推理链）、ProbabilityTreeEngine |
| M3.4 多模型协作 | ✅ | ParallelCaller、ResultFuser、ModelHealthMonitor、DynamicWeightBalancer |
| M3.5 奇门遁甲 | ✅ | QiMenEngine（九宫、八门、九星、八神、多主题分析） |
| M3.6 紫微斗数 | ✅ | ZiWeiEngine（十二宫、主星、辅星、四化、多主题分析） |
| M3.7 v2.0发布 | ✅ | Agent驱动产品 |

### Agent工作流节点
```
start → classify_intent → [retrieve_memory] → rule_analyze → rag_retrieve
→ interpret → [evolution_simulate] → safety_check → [store_memory] → end
```

- `_classify_intent` - 关键词匹配意图分类（divination/evolution/trend/learn）
- `_retrieve_memory` - 从4层记忆系统召回相关记忆
- `_rule_analyze` - 调用规则引擎进行确定性分析
- `_rag_retrieve` - 调用RAGFusion三路融合检索（向量+图谱+规则）
- `_interpret` - 调用LLM生成AI解释（DeepSeek/Qwen，含降级方案）
- `_evolution_simulate` - 调用推演引擎执行卦象演化
- `_safety_check` - 检查禁止性承诺（"一定会"、"必然"等）
- `_store_memory` - 将交互结果存入长期记忆

---

## 六、Phase 3.5 - 平台化（已完成）

### 里程碑

| 里程碑 | 状态 | 交付物 |
|--------|------|--------|
| M3.5.1 开放API | ✅ | APIKeyManager、APIRateLimiter、/api/api-platform/* |
| M3.5.2 插件系统 | ✅ | PluginRegistry、PluginManager、/api/plugins/* |
| M3.5.3 企业版 | ✅ | TenantManager（RBAC、配额管理）、/api/enterprise/* |
| M3.5.4 多语言i18n | ✅ | Translator（zh-CN/en/ja/ko）、PromptTemplateManager |
| M3.5.5 数据分析 | ✅ | EventTracker（事件追踪、仪表盘、漏斗分析）、/api/analytics/* |
| M3.5.6 v3.0发布 | ✅ | 平台版本 |

---

## 七、Phase 3.6 - 向量检索与知识图谱（已完成）

> 完成时间：2026-05-30

### 实现内容

| 模块 | 文件 | 说明 |
|------|------|------|
| Embedding服务 | `ai/embedding.py` | fastembed本地向量生成（BAAI/bge-small-en-v1.5，384维） |
| VectorBackend协议 | `ai/adapters/__init__.py` | 向量存储后端协议定义 |
| Qdrant适配器 | `ai/adapters/qdrant_adapter.py` | Qdrant向量数据库适配器（UUID点ID、超时配置） |
| Neo4j适配器 | `ai/adapters/neo4j_adapter.py` | Neo4j图数据库适配器（完整GraphBackend实现） |
| 知识库改造 | `ai/knowledge_base.py` | 支持向量检索 + 自动降级到关键词匹配 |
| 知识图谱改造 | `ai/knowledge_graph.py` | 支持Neo4j后端自动检测 + InMemoryGraph降级 |
| RAG融合改造 | `ai/rag_fusion.py` | 真实向量检索接入 + RRF融合 |
| 工作流改造 | `ai/agent/workflow.py` | 使用RAGFusion公共API，图谱上下文注入 |
| 索引脚本 | `scripts/index_knowledge.py` | 批量索引104条知识到Qdrant |
| 依赖 | `pyproject.toml` | 添加qdrant-client、fastembed、neo4j可选依赖 |

### 架构设计

```
用户查询
    ↓
[_rag_retrieve] 工作流节点
    ↓
[RAGFusion] 三路融合检索
    ├─ 向量检索路：EmbeddingService → QdrantVectorBackend.search()
    ├─ 图谱检索路：KnowledgeGraph.get_hexagram_context()
    └─ 规则检索路：KnowledgeBase.retrieve()（关键词匹配）
    ↓
[RRF融合] Reciprocal Rank Fusion (k=60)
    ↓
返回 top-N 知识上下文
```

### 降级机制

```
有 Qdrant + fastembed → 向量语义检索（最佳质量）
有 KnowledgeGraph     → 图谱关系检索
无外部服务            → 关键词匹配（MVP兜底）
```

### 环境变量配置

```bash
# Qdrant 向量数据库
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=yiai_knowledge

# Neo4j 图数据库
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

### 安装可选依赖

```bash
# 向量检索
pip install qdrant-client fastembed

# 知识图谱
pip install neo4j

# 全部安装
pip install yiai[all]
```

### 索引知识库

```bash
# 启动 Qdrant 后运行
python backend/scripts/index_knowledge.py
```

---

## 八、API端点总览

| 路由前缀 | 模块 | 功能 |
|----------|------|------|
| `/api/health` | health | 健康检查 |
| `/api/auth` | auth | JWT认证（登录/注册） |
| `/api/divination` | divination | 六爻起卦（时间/数字/手动） |
| `/api/hexagram` | hexagram | 卦象查询（错卦/综卦/互卦） |
| `/api/history` | history | 历史记录CRUD |
| `/api/inference` | inference | 推演引擎 |
| `/api/graph` | graph | 知识图谱查询 |
| `/api/agent` | agent | Agent对话（普通/流式） |
| `/api/ws` | ws_divination | WebSocket流式起卦 |
| `/api/qimen` | qimen | 奇门遁甲（排盘/分析） |
| `/api/ziwei` | ziwei | 紫微斗数（排盘/分析） |
| `/api/reasoning` | reasoning | 深度推理（推理链/概率树） |
| `/api/observation` | observation | 观察报告（模式/异常/趋势） |
| `/api/plugins` | plugins | 插件管理（注册/启用/禁用） |
| `/api/api-platform` | api_platform | API密钥管理 |
| `/api/enterprise` | enterprise | 企业租户管理 |
| `/api/analytics` | analytics | 数据分析（事件/仪表盘/漏斗） |

---

## 九、前端页面总览

| 页面 | 路径 | 功能 | 认证 |
|------|------|------|------|
| 首页 | `/` | 项目介绍 | ❌ |
| 起卦 | `/divination` | 三种起卦方式 + 排盘可视化 | ✅ |
| 历史 | `/history` | 历史记录列表/详情 | ✅ |
| 图谱 | `/graph` | 64卦图谱浏览 | ✅ |
| Agent | `/agent` | AI对话 + 推演 | ✅ |
| 推理 | `/reasoning` | 深度推理链 + 概率树 | ✅ |
| 奇门 | `/qimen` | 奇门遁甲排盘（九宫格） | ✅ |
| 紫微 | `/ziwei` | 紫微斗数命盘（十二宫） | ✅ |
| 观察 | `/observation` | 行为模式/异常检测/趋势报告 | ✅ |
| 插件 | `/plugins` | 插件注册/管理 | ✅ |
| API管理 | `/api-management` | API密钥管理 | ✅ |
| 企业 | `/enterprise` | 租户/用户管理 | ✅ |
| 分析 | `/analytics` | 事件追踪/仪表盘/漏斗 | ✅ |
| 登录 | `/login` | JWT登录 | ❌ |
| 注册 | `/register` | 用户注册 | ❌ |

---

## 十、测试状态

| 指标 | 数值 |
|------|------|
| 后端测试总数 | **409** |
| 通过率 | **100%** |
| 测试文件数 | 14 |
| 覆盖模块 | foundation, rule_engine, ai, api, memory, observation, plugins, api_platform, i18n, analytics, enterprise, phase25, phase3, phase3_batch2 |

---

## 十一、代码统计

### 后端（Python）
- 总文件数：~100个
- 核心模块：foundation(13), rule_engine(6), ai(45+), api(17), adapters(3), db(3)
- 测试文件：14个
- 脚本：scripts/index_knowledge.py

### 前端（Vue/TypeScript）
- 总文件数：~75个
- 页面：15个
- 组件：43个（5 hexagram + 38 ui）
- Composable：14个
- Store：2个

---

## 十二、待办事项（Phase 4 方向）

### 基础设施迁移
- [x] ~~内存list → Qdrant（向量检索）~~ → ✅ 已完成（Phase 3.6）
- [x] ~~内存dict → Neo4j（知识图谱）~~ → ✅ 已完成（Phase 3.6）
- [ ] SQLite → PostgreSQL（用户数据持久化）
- [ ] 内存dict → Redis（会话缓存、限流）

### 功能增强
- [ ] WebSocket流式输出（前端实时显示）
- [ ] 前端视觉优化（动画、3D场景）
- [ ] 前端测试（Vitest配置 + 组件测试）
- [ ] 用户认证增强（OAuth2、社交登录）

### 生产化
- [ ] CI/CD流水线完善
- [ ] Docker容器化（含Qdrant、Neo4j服务）
- [ ] Kubernetes部署
- [ ] 监控告警（Prometheus + Grafana）
- [ ] 日志收集（Loki + OpenTelemetry）

---

## 十三、技术债务

| 项目 | 优先级 | 说明 |
|------|--------|------|
| CORS硬编码 | P1 | 当前仅允许localhost:3000/3001 |
| on_event deprecated | P2 | FastAPI 0.103+已弃用，需迁移到lifespan |
| 管理端点无认证 | P1 | enterprise/plugins/api_platform端点未加认证 |
| 前端无测试 | P2 | 需配置Vitest |
| Embedding维度硬编码 | P2 | embedding.py硬编码384维，应从模型动态获取 |
| Neo4j连接超时 | P2 | is_available()阻塞数秒，需配置超时参数 |

---

*文档生成时间：2026-05-30*
