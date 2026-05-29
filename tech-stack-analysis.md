# YI-AI 技术栈深度分析文档

> 版本: 1.0.0 | 日期: 2026-05-29 | 基于 yiai.md + ai-architecture.md 现有架构

---

## 目录

1. [前端技术栈](#1-前端技术栈)
2. [后端技术栈](#2-后端技术栈)
3. [数据层技术栈](#3-数据层技术栈)
4. [AI/ML 技术栈](#4-aiml-技术栈)
5. [DevOps 部署技术栈](#5-devops-部署技术栈)
6. [监控方案](#6-监控方案)
7. [版本锁定建议](#7-版本锁定建议)
8. [技术风险与备选方案](#8-技术风险与备选方案)
9. [开发工具链](#9-开发工具链)

---

## 1. 前端技术栈

### 1.1 框架层

#### Nuxt 4 + Vue 3

| 维度 | 说明 |
|------|------|
| **作用** | 应用框架，提供 SSR/SSG/ISR 渲染模式、文件路由、自动导入、SEO 友好 |
| **为什么选** | YI-AI 需要 SSR 做 SEO（易学内容有大量搜索流量），Vue 3 的 Composition API 适合复杂状态管理，Nuxt 4 基于 Nitro 引擎支持多平台部署 |
| **优点** | SSR 开箱即用；Nitro server engine 支持 edge 部署；自动导入 composables 减少样板代码；Vue 3 响应式系统（Proxy-based）性能优于 Vue 2；TypeScript 一等公民支持 |
| **缺点** | Nuxt 4 生态不如 Next.js 成熟（插件/模板少约 30%）；SSR 调试复杂度高于 SPA；服务端 hydration 闪烁问题需要额外处理 |
| **替代方案对比** | |

| 替代方案 | 优势 | 劣势 | 适用场景 |
|----------|------|------|----------|
| Next.js 15 (React) | 生态最成熟，Vercel 部署便捷，RSC 创新 | React 生态动画库不如 Vue+GSAP 组合；团队若熟悉 Vue 则迁移成本高 | 团队有 React 经验时首选 |
| Astro + Vue Islands | 极致静态性能，岛屿架构按需加载 JS | 交互密集型页面（太极动画、图谱）需要大量 islands，复杂度上升 | 内容为主的页面 |
| SvelteKit | 编译时框架，bundle 极小，动画原生支持好 | 生态最小，第三方组件库少，招人难度大 | 追求极致性能的小团队 |

**结论**: 保持 Nuxt 4 + Vue 3。YI-AI 的可视化需求（太极动画、六爻排盘、图谱 3D）与 Vue 3 的响应式系统 + GSAP 组合最契合，SSR 对 SEO 是刚需。

#### TailwindCSS v4

| 维度 | 说明 |
|------|------|
| **作用** | 原子化 CSS 框架，提供设计系统基础 |
| **为什么选** | v4 引入 CSS-first 配置（不再需要 tailwind.config.js），性能提升 10x，与 Nuxt 4 集成良好 |
| **优点** | 开发速度快；bundle 体积小（按需 purge）；与 shadcn-vue 配合无缝；v4 原生支持 CSS 变量和 @theme |
| **缺点** | HTML 类名可读性差（长字符串）；复杂组件需要 @apply 或组件封装；v4 刚发布，部分插件未适配 |
| **替代方案** | UnoCSS（更快、可兼容 Tailwind 语法）、Panda CSS（类型安全）、vanilla-extract（零运行时） |

#### shadcn-vue

| 维度 | 说明 |
|------|------|
| **作用** | 无头 UI 组件库，提供可定制的基础组件（Button、Dialog、Sheet 等） |
| **为什么选** | 组件代码直接复制到项目中（非 npm 依赖），完全可控；基于 Radix Vue 无障碍性好 |
| **优点** | 代码所有权完全在项目内；TailwindCSS 深度集成；无障碍（a11y）内置；社区活跃 |
| **缺点** | 组件数量不如 PrimeVue / Element Plus 丰富；需要手动更新；图表类组件缺失 |
| **替代方案** | PrimeVue（企业级组件 90+）、Naive UI（Vue 3 原生，动画好）、Element Plus（中文生态最大） |

### 1.2 可视化与动画层

#### GSAP (GreenSock Animation Platform)

| 维度 | 说明 |
|------|------|
| **作用** | 高性能动画引擎，驱动太极旋转、爻变翻转、卦象过渡等关键动画 |
| **为什么选** | 业界动画性能天花板；ScrollTrigger 插件支持滚动驱动动画；Timeline 支持复杂序列编排；SVG 动画一等公民 |
| **优点** | 性能远优于 CSS animation（requestAnimationFrame 调度）；Timeline 编排复杂动画序列极其方便；SVG 路径动画、morphing 开箱即用；Cross-browser 一致性好 |
| **缺点** | 商业用途需付费（Business License $150/年）；bundle 体积 ~30kb gzip；与 Vue 响应式系统需要桥接（useGSAP） |
| **替代方案** | Motion Vue（Vue 原生，轻量）、Anime.js（免费，API 简洁）、Framer Motion（React 生态） |
| **许可说明** | 免费许可适用于非商业/个人项目；商业项目需 Business GreenSock License |

#### Cytoscape.js

| 维度 | 说明 |
|------|------|
| **作用** | 图谱关系网络可视化，渲染易学知识图谱（卦-五行-六亲关系网络） |
| **为什么选** | 专业图论可视化库；支持复杂布局算法（force-directed、dagre、cola）；事件系统完善；支持自定义样式 |
| **优点** | 专为图论设计，节点/边操作 API 完善；内置 20+ 布局算法；Canvas 和 WebGL 渲染可选；支持 compound nodes（嵌套节点） |
| **缺点** | 不支持 3D 渲染（纯 2D）；大数据量（1000+ 节点）需手动优化；自定义渲染需要深入了解 Canvas API |
| **替代方案** | Sigma.js（WebGL 渲染，大图性能更好）、vis-network（快速原型）、G6（蚂蚁集团，中文生态好） |
| **组合建议** | Cytoscape.js 做 2D 图谱 + Three.js 做 3D 节点装饰，分层渲染 |

#### D3.js

| 维度 | 说明 |
|------|------|
| **作用** | 数据驱动的底层可视化引擎，用于时间演化轴、五行雷达图、情绪趋势图等自定义图表 |
| **为什么选** | 最灵活的数据可视化库；SVG/Canvas 操作底层能力；与 Vue 3 可通过 ref 桥接 |
| **优点** | 无与伦比的灵活性和定制能力；数据绑定 + DOM 操作范式强大；社区示例极其丰富 |
| **缺点** | 学习曲线陡峭；与 Vue 响应式系统有范式冲突（D3 直接操作 DOM）；开发效率低于 ECharts |
| **替代方案** | ECharts（开箱即用图表丰富，Apache 项目）、Chart.js（轻量简单）、Observable Plot（D3 团队新作，声明式） |
| **组合建议** | D3 用于高度定制的可视化（演化树、五行关系图）；ECharts 用于标准图表（趋势图、饼图） |

#### Three.js

| 维度 | 说明 |
|------|------|
| **作用** | 3D 可视化引擎，用于太极 3D 模型、空间卦象展示、沉浸式体验 |
| **为什么选** | Web 3D 事实标准；社区庞大；与 Vue 集成有 TresJS 桥接层 |
| **优点** | 功能全面（PBR、粒子系统、后处理）；社区资源海量；WebGPU 支持在推进中 |
| **缺点** | bundle 大（~150kb gzip）；3D 场景调试困难；性能优化需要深入了解渲染管线 |
| **替代方案** | Babylon.js（更完整的引擎，TypeScript 原生）、TresJS（Vue 3 声明式 3D）、model-viewer（简单 3D 展示） |
| **使用策略** | 仅在需要 3D 的页面动态加载 `const THREE = await import('three')`，避免主 bundle 膨胀 |

### 1.3 状态管理与工具

#### Pinia

| 维度 | 说明 |
|------|------|
| **作用** | Vue 3 官方状态管理，管理用户会话、卦象数据、UI 状态 |
| **为什么选** | Vue 3 官方推荐；TypeScript 类型推导优秀；DevTools 支持；支持 SSR 状态水合 |
| **优点** | API 简洁（无 mutations）；模块化 store 设计；支持插件扩展；Nuxt 集成模块 `@pinia/nuxt` |
| **缺点** | 复杂异步流程不如 Zustand/XState 直观；大型应用需要严格分层 |
| **替代方案** | Vuex 4（Vue 2 遗产，不推荐）、Zustand-like 的 `vue-zustand`、XState（状态机，适合复杂流程） |

#### 其他前端依赖

| 库 | 作用 | 必要性 |
|----|------|--------|
| `@vueuse/core` | 组合式工具函数（useStorage、useIntersectionObserver 等） | 必要 |
| `axios` 或 `ofetch` | HTTP 客户端（Nuxt 内置 ofetch） | 必要 |
| `floating-vue` | Tooltip/Popover（图谱节点悬停信息） | 推荐 |
| `vue-echarts` | ECharts Vue 封装（标准图表） | 推荐 |
| `@vue-flow/core` | 流程图/节点编辑器（Agent 工作流可视化） | 可选 |
| `lottie-web` | AE 动画导出播放（太极 Lottie 动画） | 可选 |
| `mathjax` 或 `katex` | 数学公式渲染（易经数学结构展示） | 可选 |

### 1.4 前端架构总结

```
Nuxt 4 (SSR 框架)
  ├── Vue 3 (Composition API + <script setup>)
  ├── TailwindCSS v4 (原子化样式)
  ├── shadcn-vue (基础 UI 组件)
  ├── Pinia (状态管理)
  ├── GSAP (动画引擎 - 太极/爻变/过渡)
  ├── Cytoscape.js (图谱网络 - 2D)
  ├── D3.js (自定义数据可视化)
  ├── Three.js (3D 沉浸式场景)
  ├── ECharts (标准图表)
  └── VueUse (工具函数)
```

---

## 2. 后端技术栈

### 2.1 核心框架

#### Python + FastAPI

| 维度 | 说明 |
|------|------|
| **作用** | HTTP/WebSocket API 服务，承载所有业务逻辑和 AI Pipeline |
| **为什么选** | Python 是 AI/ML 生态第一语言（LangChain/LangGraph/PyTorch 全在 Python）；FastAPI 性能接近 Node.js（基于 Starlette + uvicorn）；类型注解 + 自动生成 OpenAPI 文档 |
| **优点** | async/await 原生支持高并发；Pydantic 数据校验零成本；自动 API 文档（Swagger）；依赖注入系统清晰 |
| **缺点** | GIL 限制 CPU 密集型任务（规则引擎计算）；部署比 Go/Rust 复杂；Python 运行时内存占用较高 |
| **替代方案** | |

| 替代方案 | 优势 | 劣势 |
|----------|------|------|
| Go + Gin/Echo | 性能极高，并发模型优秀，部署简单 | AI 生态弱，LangChain 无 Go 版本 |
| Rust + Axum | 极致性能，内存安全 | 开发速度慢，AI 生态几乎为零 |
| Node.js + Hono | 前后端同语言，Edge 部署友好 | AI/ML 库生态不如 Python |

**结论**: 保持 Python + FastAPI。AI 密集型项目 Python 是唯一合理选择。

#### asyncio 异步框架

| 维度 | 说明 |
|------|------|
| **作用** | 处理并发请求、异步 AI 模型调用、数据库连接池 |
| **关键用法** | `asyncio.gather` 并行调用多个 LLM；`asyncio.Semaphore` 控制并发数；`asyncio.Queue` 任务队列 |
| **配合库** | `httpx`（异步 HTTP 客户端调 LLM API）、`asyncpg`（异步 PostgreSQL）、`aioredis`（异步 Redis）、`motor`（异步 MongoDB，备选） |

#### Celery + Redis Broker

| 维度 | 说明 |
|------|------|
| **作用** | 后台任务队列，处理长耗时任务（Embedding 生成、知识图谱构建、记忆压缩、批量分析） |
| **为什么选** | 成熟稳定；Redis 作为 broker 与现有缓存层复用；支持定时任务（celery beat） |
| **优点** | 任务重试、优先级、结果后端、监控（Flower）一应俱成 |
| **缺点** | 配置复杂；不支持原生 async（需要 `celery[async]` 或 loop 嵌入）；监控工具 Flower 较老 |
| **替代方案** | |

| 替代方案 | 优势 | 劣势 |
|----------|------|------|
| Dramatiq | 更简洁的 API，Redis/RabbitMQ 支持好 | 生态不如 Celery |
| ARQ | 原生 asyncio，轻量 | 功能少，无定时任务 |
| BullMQ (Node.js) | 如果前后端同语言 | 需要 Node.js 运行时 |
| Temporal.io | 可靠性极高，复杂工作流编排 | 部署复杂，学习成本高 |

**建议**: 第一阶段用 Celery；第三阶段引入 LangGraph 做 AI 工作流编排后，Celery 退化为纯基础设施任务队列。

### 2.2 API 设计

| 模式 | 用途 | 协议 |
|------|------|------|
| REST API | 用户管理、卦记录 CRUD、配置管理 | HTTP/JSON |
| WebSocket | AI 解释流式输出、实时推演、Agent 状态推送 | WS |
| SSE (Server-Sent Events) | 单向流式输出（AI 生成文本流） | HTTP/EventStream |
| gRPC (未来) | 微服务间通信（如果拆分服务） | HTTP/2 + Protobuf |

### 2.3 后端分层架构

```
FastAPI Application
  ├── API Layer (路由、请求校验、响应格式化)
  │     ├── /api/v1/users          (用户管理)
  │     ├── /api/v1/divinations    (卦记录)
  │     ├── /api/v1/hexagrams      (卦象查询)
  │     ├── /api/v1/ai/explain     (AI 解释)
  │     ├── /api/v1/ai/analyze     (趋势分析)
  │     ├── /api/v1/ai/stream      (WebSocket 流式)
  │     └── /api/v1/graph          (图谱查询)
  │
  ├── Service Layer (业务逻辑)
  │     ├── UserService
  │     ├── DivinationService
  │     ├── HexagramEngine (确定性规则)
  │     ├── FiveElementEngine (五行计算)
  │     ├── TimeEngine (干支/节气)
  │     └── EvolutionEngine (推演)
  │
  ├── AI Layer (AI Pipeline)
  │     ├── ModelRouter (模型路由)
  │     ├── RAGSystem (三路检索)
  │     ├── AgentWorkflow (LangGraph)
  │     ├── MemoryEngine (长期记忆)
  │     ├── SafetyChecker (安全检查)
  │     └── PromptRegistry (Prompt 管理)
  │
  ├── Infrastructure Layer
  │     ├── Database Repositories
  │     ├── Cache Manager
  │     ├── Message Queue
  │     └── External API Clients
  │
  └── Cross-cutting
        ├── Authentication (JWT + OAuth2)
        ├── Rate Limiting
        ├── Logging
        ├── Error Handling
        └── Metrics Collection
```

### 2.4 关键 Python 依赖

| 库 | 版本建议 | 作用 |
|----|---------|------|
| `fastapi` | >=0.115 | Web 框架 |
| `uvicorn[standard]` | >=0.34 | ASGI 服务器 |
| `pydantic` | >=2.10 | 数据校验与序列化 |
| `sqlalchemy[asyncio]` | >=2.0 | ORM（async 模式） |
| `asyncpg` | >=0.30 | PostgreSQL 异步驱动 |
| `redis[hiredis]` | >=5.2 | Redis 客户端 |
| `httpx` | >=0.28 | 异步 HTTP 客户端（调 LLM API） |
| `celery[redis]` | >=5.4 | 任务队列 |
| `langchain` | >=0.3 | LLM 编排基础 |
| `langgraph` | >=0.3 | Agent 工作流 |
| `qdrant-client` | >=1.12 | Qdrant 向量数据库客户端 |
| `neo4j` | >=5.25 | Neo4j 图数据库驱动 |
| `sentence-transformers` | >=3.3 | Embedding 模型加载 |
| `python-jose[cryptography]` | >=3.3 | JWT 认证 |
| `prometheus-client` | >=0.21 | 指标暴露 |

---

## 3. 数据层技术栈

### 3.1 数据库全景

```
┌─────────────────────────────────────────────────────────────────┐
│                        YI-AI 数据架构                            │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ PostgreSQL   │  │ Redis        │  │ Qdrant               │  │
│  │ (主数据库)    │  │ (缓存/会话)   │  │ (向量数据库)          │  │
│  │              │  │              │  │                      │  │
│  │ - 用户数据    │  │ - 会话缓存    │  │ - 知识库 Embedding   │  │
│  │ - 卦记录     │  │ - 工作记忆    │  │ - 用户历史向量       │  │
│  │ - 配置数据    │  │ - 频率限制    │  │ - 语义检索           │  │
│  │ - Prompt 版本 │  │ - 任务队列    │  │                      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Neo4j        │  │ ClickHouse   │  │ MinIO                │  │
│  │ (图数据库)    │  │ (分析数据库)   │  │ (对象存储)           │  │
│  │              │  │              │  │                      │  │
│  │ - 知识图谱    │  │ - 用户行为    │  │ - 静态资源           │  │
│  │ - 用户图谱    │  │ - AI 调用日志 │  │ - 历史快照           │  │
│  │ - 关系推理    │  │ - 性能指标    │  │ - 导出文件           │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 PostgreSQL -- 主数据库

**用途**: 存储结构化业务数据，是系统的单一数据真相源（Single Source of Truth）。

**数据模型**:

```sql
-- 核心表设计

-- 用户表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(20) UNIQUE,
    nickname VARCHAR(50),
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_active_at TIMESTAMPTZ,
    settings JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE
);

-- 用户画像表（与 users 分离，更新频率不同）
CREATE TABLE user_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    frequent_hexagrams JSONB DEFAULT '{}',     -- {"乾": 5, "坎": 3}
    dominant_elements JSONB DEFAULT '{}',       -- {"木": 0.3, "水": 0.5}
    question_topics JSONB DEFAULT '{}',         -- {"事业": 10, "感情": 5}
    emotional_trajectory JSONB DEFAULT '[]',    -- [{period, dominant, count}]
    active_time_pattern VARCHAR(50),
    question_frequency FLOAT DEFAULT 0,
    behavior_patterns JSONB DEFAULT '[]'
);

-- 卦记录表（高频写入，分区表）
CREATE TABLE divinations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- 卦象数据
    hexagram_name VARCHAR(10) NOT NULL,
    hexagram_number SMALLINT,
    changed_hexagram VARCHAR(10),
    moving_lines SMALLINT[] DEFAULT '{}',
    binary_representation VARCHAR(6),

    -- 上下文
    question TEXT NOT NULL,
    question_intent VARCHAR(50),
    time_ganzhi VARCHAR(20),
    time_solar DATE,

    -- AI 结果
    ai_interpretation TEXT,
    ai_model_used VARCHAR(50),
    ai_tier VARCHAR(20),
    ai_tokens_used INT DEFAULT 0,
    ai_cost_usd DECIMAL(10,6) DEFAULT 0,

    -- 用户反馈
    user_feedback VARCHAR(20),      -- 'helpful' | 'neutral' | 'unhelpful'
    user_feedback_text TEXT,
    sentiment VARCHAR(20),
    topic_tags TEXT[] DEFAULT '{}',

    -- 安全
    safety_issues TEXT[] DEFAULT '{}',
    risk_flags TEXT[] DEFAULT '{}'
) PARTITION BY RANGE (created_at);

-- 按月分区
CREATE TABLE divinations_2026_01 PARTITION OF divinations
    FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');

-- 索引
CREATE INDEX idx_divinations_user_id ON divinations(user_id);
CREATE INDEX idx_divinations_created_at ON divinations(created_at DESC);
CREATE INDEX idx_divinations_hexagram ON divinations(hexagram_name);
CREATE INDEX idx_divinations_intent ON divinations(question_intent);
CREATE INDEX idx_divinations_tags ON divinations USING GIN(topic_tags);

-- 六十四卦基础数据表
CREATE TABLE hexagrams (
    number SMALLINT PRIMARY KEY,
    name VARCHAR(10) NOT NULL UNIQUE,
    unicode CHAR(1),
    upper_trigram VARCHAR(5),
    lower_trigram VARCHAR(5),
    judgement TEXT,             -- 卦辞
    image TEXT,                 -- 象辞
    binary_repr VARCHAR(6),
    element VARCHAR(5),
    JSONB lines_data DEFAULT '[]'   -- 六爻完整数据
);

-- Prompt 版本管理表
CREATE TABLE prompt_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_id VARCHAR(100) NOT NULL,
    version VARCHAR(20) NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    template JSONB NOT NULL,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(50),
    evaluation_score DECIMAL(5,4),
    UNIQUE(prompt_id, version)
);

-- AI 调用日志表（写入密集，考虑异步写入）
CREATE TABLE ai_call_logs (
    id BIGSERIAL,
    user_id UUID,
    request_id UUID,
    model_id VARCHAR(50),
    tier VARCHAR(20),
    input_tokens INT,
    output_tokens INT,
    cost_usd DECIMAL(10,6),
    latency_ms INT,
    status VARCHAR(20),         -- 'success' | 'error' | 'timeout' | 'fallback'
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
) PARTITION BY RANGE (created_at);
```

**为什么选 PostgreSQL**:
- JSONB 支持灵活的半结构化数据（卦象数据、用户配置）
- 数组类型原生支持（动爻位置、标签）
- GIN 索引支持 JSONB 和数组高效查询
- 表分区支持海量历史数据
- 生态成熟，asyncpg 性能极佳

### 3.3 Redis -- 缓存与会话

**用途**: 工作记忆缓存、会话管理、频率限制、任务队列 broker。

**数据模型**:

```
# 会话工作记忆 (TTL: 2小时)
session:{session_id}:memory → JSON {
    "current_hexagram": {...},
    "conversation_history": [...],
    "user_intent": "...",
    "last_updated": "ISO timestamp"
}

# 用户频率限制 (滑动窗口)
rate_limit:user:{user_id}:minute → counter (TTL: 60s)
rate_limit:user:{user_id}:hour → counter (TTL: 3600s)
rate_limit:user:{user_id}:day → counter (TTL: 86400s)

# 热门卦象缓存
cache:hexagram:{hexagram_name} → JSON (卦的完整结构化数据)

# AI 模型健康状态
model_health:{model_id} → float (0.0-1.0)

# A/B 测试变体分配
ab_test:{experiment_name}:user:{user_id} → "variant_a" | "variant_b"

# Celery Broker
# celery 使用 db 0
# 缓存使用 db 1
# 会话使用 db 2
```

**为什么选 Redis**:
- 亚毫秒级延迟，适合工作记忆频繁读写
- 丰富的数据结构（String/Hash/Sorted Set/Stream）
- 原子操作支持频率限制
- Pub/Sub 支持实时通知（备选方案）
- 与 Celery 复用，减少基础设施

**替代方案对比**:

| 替代方案 | 优势 | 劣势 |
|----------|------|------|
| Dragonfly | Redis 兼容，多线程，内存效率更高 | 相对新，稳定性待验证 |
| KeyDB | Redis 多线程 fork | 社区小 |
| Valkey | Redis 开源 fork（Linux Foundation） | 生态尚在建设 |

### 3.4 Qdrant -- 向量数据库

**用途**: 存储知识库文档 Embedding、用户历史卦记录向量，支持语义检索。

**Collections 设计**:

| Collection | 维度 | Embedding 模型 | 分块策略 | 预估数据量 |
|-----------|------|---------------|---------|-----------|
| `yijing_texts` | 1024 | bge-m3 | 按卦分块 | 64-200 条 |
| `commentaries` | 1024 | bge-m3 | 按段落，overlap 50 | 5000-20000 条 |
| `modern_explanations` | 1024 | bge-m3 | 语义段落 | 2000-5000 条 |
| `five_elements_rules` | 1024 | jina-embeddings-v3 | 规则条目 | 500-1000 条 |
| `divination_cases` | 1024 | bge-m3 | 完整卦例 | 1000-5000 条 |
| `user_history` | 1024 | jina-embeddings-v3 | 时间窗口 | 按用户增长 |

**Payload 索引**:

```json
{
    "hexagram_name": "keyword",
    "dynasty": "keyword",
    "author": "keyword",
    "topic_tags": "keyword[]",
    "created_at": "datetime",
    "user_id": "keyword"  // user_history collection
}
```

**为什么选 Qdrant**:
- Rust 实现，单机性能优于 Milvus/Weaviate
- 支持 Payload 过滤 + 向量搜索联合查询
- 支持多向量（multi-vector）和稀疏向量（sparse）
- 内置量化（scalar/product/binary），减少内存占用
- 有 Qdrant Cloud 托管选项

**替代方案对比**:

| 替代方案 | 优势 | 劣势 |
|----------|------|------|
| Milvus | 分布式原生，大数据量 | 部署复杂（依赖 etcd/MinIO/Pulsar） |
| Weaviate | GraphQL API，多模态支持 | 性能不如 Qdrant |
| Pinecone | 全托管，零运维 | 闭源，成本高，数据在境外 |
| pgvector | 与 PostgreSQL 复用 | 性能差距大（10x-100x） |
| ChromaDB | 简单易用 | 不适合生产环境 |

### 3.5 Neo4j -- 图数据库

**用途**: 存储易学知识图谱（64卦-五行-六亲-时间关系网络）和用户行为图谱。

**图谱规模估算**:

| 节点类型 | 数量 | 说明 |
|---------|------|------|
| Hexagram | 64 | 六十四卦 |
| Line | 384 | 64卦 x 6爻 |
| Element | 5 | 五行 |
| Trigram | 8 | 八卦 |
| Role | 6 | 六亲（含比和） |
| Spirit | 6 | 六神 |
| HeavenlyStem | 10 | 十天干 |
| EarthlyBranch | 12 | 十二地支 |
| User | N | 按用户增长 |
| DivinationRecord | N | 按使用增长 |
| **总计（静态）** | **~500** | 知识图谱基础节点 |
| **总计（含用户）** | **500 + 用户数 x 平均记录数** | |

**关系类型**:

| 关系 | 含义 | 数量级 |
|------|------|--------|
| GENERATES | 相生 | 5 |
| RESTRAINS | 相克 | 5 |
| HAS_LINE | 包含爻 | 384 |
| HAS_UPPER / HAS_LOWER | 上下卦 | 128 |
| TRANSFORMS_TO | 变卦 | ~200 |
| ERRORS_TO | 错卦 | 64 |
| REVERSES_TO | 综卦 | 64 |
| MUTUAL_WITH | 互卦 | 64 |
| CLASHES_WITH | 六冲 | 6 (双向=12) |
| COMBINES_WITH | 六合 | 6 (双向=12) |
| NAIJIA | 纳甲 | 384 |
| QUERIED | 用户查询 | N |

**为什么选 Neo4j**:
- Cypher 查询语言直观（关系模式匹配）
- 知识图谱场景下查询性能远优于关系数据库 JOIN
- 内置图算法库（路径查找、社区发现、中心性）
- 可视化浏览器方便调试
- 支持全文索引

**替代方案对比**:

| 替代方案 | 优势 | 劣势 |
|----------|------|------|
| Amazon Neptune | 托管服务，免运维 | 价格高，数据在境外 |
| ArangoDB | 多模型（文档+图+KV） | 社区小于 Neo4j |
| Nebula Graph | 国产，分布式 | 生态不如 Neo4j |
| PostgreSQL + Apache AGE | 复用 PG | 性能和功能不如原生图数据库 |

### 3.6 ClickHouse -- 分析数据库

**用途**: 存储海量时序分析数据（AI 调用日志、用户行为轨迹、性能指标）。

**核心表设计**:

```sql
-- AI 调用日志（写入密集，列式存储）
CREATE TABLE ai_call_logs (
    timestamp DateTime64(3),
    user_id UUID,
    request_id UUID,
    model_id LowCardinality(String),
    tier LowCardinality(String),
    intent LowCardinality(String),
    input_tokens UInt32,
    output_tokens UInt32,
    cost_usd Decimal(10, 6),
    latency_ms UInt32,
    ttft_ms UInt32,             -- Time to first token
    status LowCardinality(String),
    error_code String,
    hexagram_name LowCardinality(String),
    safety_issues_count UInt8
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (user_id, timestamp)
TTL timestamp + INTERVAL 180 DAY;

-- 用户行为轨迹
CREATE TABLE user_events (
    timestamp DateTime64(3),
    user_id UUID,
    event_type LowCardinality(String),  -- 'page_view', 'divination', 'feedback', 'share'
    page_path String,
    session_id UUID,
    device_type LowCardinality(String),
    country LowCardinality(String),
    properties JSON
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (user_id, event_type, timestamp)
TTL timestamp + INTERVAL 365 DAY;

-- 系统性能指标
CREATE TABLE system_metrics (
    timestamp DateTime,
    service LowCardinality(String),
    metric_name LowCardinality(String),
    value Float64,
    labels Map(String, String)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (service, metric_name, timestamp)
TTL timestamp + INTERVAL 90 DAY;
```

**为什么选 ClickHouse**:
- 列式存储，聚合查询性能碾压 PostgreSQL（100x-1000x）
- 内置时间序列函数（window functions、time series interpolation）
- 高压缩比（10x-20x），存储成本低
- 与 Grafana 原生集成

**替代方案对比**:

| 替代方案 | 优势 | 劣劣 |
|----------|------|------|
| TimescaleDB | PG 扩展，SQL 兼容 | 分析查询性能不如 CH |
| Apache Doris | 国产，兼容 MySQL 协议 | 生态不如 CH |
| QuestDB | 时序专精，写入快 | 社区小 |

### 3.7 MinIO -- 对象存储

**用途**: 存储静态资源、历史快照、导出文件、用户上传头像。

**Bucket 规划**:

| Bucket | 内容 | 访问策略 |
|--------|------|---------|
| `yiai-static` | 前端静态资源（图片、字体、Lottie 动画） | 公读 |
| `yiai-snapshots` | 卦象历史快照（JSON 格式） | 私有 |
| `yiai-exports` | 用户导出文件（PDF 报告、分析结果） | 私有，签名 URL |
| `yiai-uploads` | 用户上传（头像、自定义图片） | 私有，签名 URL |
| `yiai-models` | AI 模型文件（Embedding 模型权重） | 私有 |

**为什么选 MinIO**:
- S3 兼容 API，可无缝切换到 AWS S3/阿里云 OSS
- 自托管，数据完全在掌控
- 轻量级，单节点即可启动

### 3.8 数据库交互模式

```
读写分离策略:

写入路径:
  用户请求 → FastAPI → PostgreSQL (主库)
                     → Qdrant (向量写入)
                     → Redis (缓存失效)
                     → Celery → Neo4j (异步图谱更新)
                     → Celery → ClickHouse (异步日志)

读取路径:
  用户请求 → FastAPI → Redis (缓存命中?) → 返回
                     → PostgreSQL (缓存未命中) → 写入 Redis → 返回
  AI 请求  → FastAPI → Redis (工作记忆)
                     → Qdrant (向量检索) ─┐
                     → Neo4j (图谱检索)  ├→ RRF 融合 → LLM
                     → 规则引擎(本地)   ─┘
```

---

## 4. AI/ML 技术栈

### 4.1 LLM 模型层

| 模型 | 提供商 | 用途 | 成本 ($/1M tokens) | 上下文窗口 |
|------|--------|------|---------------------|-----------|
| DeepSeek-V3 | DeepSeek | 意图分类、实体提取 | 输入 $0.27 / 输出 $1.10 | 64K |
| Qwen-Turbo | 阿里云 | 轻量推理、备选 | 输入 $0.05 / 输出 $0.20 | 128K |
| Qwen-Max | 阿里云 | 卦象解释、古文翻译 | 输入 $2.40 / 输出 $9.60 | 32K |
| DeepSeek-Reasoner | DeepSeek | 五行推理、推理链 | 输入 $0.55 / 输出 $2.19 | 64K |
| Claude Sonnet 4.6 | Anthropic | 长期趋势、多卦关联 | 输入 $3.00 / 输出 $15.00 | 200K |
| Claude Opus 4.5 | Anthropic | Agent 推演、复杂决策 | 输入 $15.00 / 输出 $75.00 | 200K |
| GPT-4o | OpenAI | 备选推演模型 | 输入 $2.50 / 输出 $10.00 | 128K |

**模型选择原则**:
1. 能用规则引擎解决的，绝不调 LLM
2. 能用 Tier 1 解决的，绝不用 Tier 2
3. 每次请求必须有成本上限（$0.05/请求）
4. 必须有 fallback 链

### 4.2 Embedding 模型

| 模型 | 维度 | 用途 | 部署方式 |
|------|------|------|---------|
| bge-m3 (BAAI) | 1024 | 知识库文档 Embedding（古文+现代文混合） | 自部署 (sentence-transformers) |
| jina-embeddings-v3 | 1024 | 用户历史、规则条目 Embedding | API 调用 / 自部署 |

**为什么选 bge-m3**:
- 中文 Embedding 排行榜前列
- 支持稠密+稀疏+多向量三种检索模式
- 最大 8192 token 输入，适合长文本
- 开源免费，可自部署

**替代方案**: `text-embedding-3-large` (OpenAI)、`Cohere embed-v3`、`m3e-large` (中文)

### 4.3 Agent 框架

#### LangGraph

| 维度 | 说明 |
|------|------|
| **作用** | 构建有状态的多步骤 AI Agent 工作流 |
| **为什么选** | LangChain 团队出品，与 LangChain 生态无缝集成；支持条件路由、循环、并行节点；内置状态管理和持久化 |
| **核心能力** | StateGraph 定义工作流；条件边实现动态路由；checkpoint 支持会话恢复；Human-in-the-loop 支持人工介入 |
| **缺点** | API 变化频繁（v0.1→v0.3 有 breaking changes）；调试困难；状态序列化有坑 |

#### LangChain

| 维度 | 说明 |
|------|------|
| **作用** | LLM 调用抽象层、Prompt 模板、Output Parser、Tool 调用 |
| **为什么选** | 最大的 LLM 应用生态；抽象了不同提供商的 API 差异；Chain/Agent/Tool 标准化 |
| **关键模块** | `langchain-core`（基础抽象）、`langchain-anthropic`、`langchain-openai`、`langchain-deepseek` |
| **缺点** | 过度抽象导致调试困难；版本更新频繁；部分模块质量参差不齐 |
| **替代方案** | 直接使用 httpx 调用 API（更可控但工作量大）、Haystack (deepset)、Semantic Kernel (Microsoft) |

**建议**: 使用 `langchain-core` 的基础抽象（Prompt、OutputParser、Tool），避免过度依赖高层 Chain。核心的模型路由和 RAG 逻辑自研，保持对关键路径的控制。

### 4.4 RAG 技术栈

```
Hybrid RAG Architecture:

Query → [Rewrite] → ┌── Dense Retrieval (bge-m3 + Qdrant)
                     ├── Graph Retrieval (Neo4j Cypher)
                     └── Rule Retrieval (确定性引擎)
                              │
                              ▼
                     RRF Fusion (k=60, weights configurable)
                              │
                              ▼
                     Context Assembly (Token Budget: 6000)
                              │
                              ▼
                     LLM Generation (Temperature: 0.7)
```

**GraphRAG 集成策略**:
- Microsoft GraphRAG 的社区检测 + 层次化摘要可补充知识图谱的自动构建
- 但 YI-AI 的领域知识高度结构化（64卦体系确定），不需要 GraphRAG 的自动图谱构建
- 借鉴 GraphRAG 的 local search / global search 模式，但自研检索融合

### 4.5 AI 技术栈依赖图

```
┌──────────────────────────────────────────────────────────────────┐
│                    AI Layer Dependencies                          │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │ LangGraph    │───▶│ LangChain    │───▶│ LLM Providers    │   │
│  │ (Workflow)   │    │ (Core/Tools) │    │ (DeepSeek/Qwen/  │   │
│  └──────────────┘    └──────────────┘    │  Claude/GPT)     │   │
│         │                                  └──────────────────┘   │
│         ▼                                                        │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │ RAG System   │───▶│ Qdrant       │    │ bge-m3           │   │
│  │ (Fusion)     │───▶│ Neo4j        │    │ jina-embeddings  │   │
│  └──────────────┘    └──────────────┘    └──────────────────┘   │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │ Memory       │───▶│ Redis        │    │ sentence-        │   │
│  │ Engine       │    │ PostgreSQL   │    │ transformers     │   │
│  └──────────────┘    └──────────────┘    └──────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 5. DevOps 部署技术栈

### 5.1 容器化

#### Docker + Docker Compose (开发环境)

```yaml
# docker-compose.dev.yml
version: "3.9"

services:
  # --- 应用服务 ---
  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    env_file: .env
    depends_on:
      - postgres
      - redis
      - qdrant
      - neo4j
    command: uvicorn main:app --reload --host 0.0.0.0 --port 8000

  web:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
    command: npx nuxi dev --host 0.0.0.0

  celery-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A tasks worker --loglevel=info --concurrency=4
    depends_on:
      - redis
      - postgres

  celery-beat:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A tasks beat --loglevel=info

  # --- 数据库服务 ---
  postgres:
    image: postgres:17-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: yiai
      POSTGRES_USER: yiai
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru

  qdrant:
    image: qdrant/qdrant:v1.12
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage

  neo4j:
    image: neo4j:5-community
    ports:
      - "7474:7474"  # Browser
      - "7687:7687"  # Bolt
    environment:
      NEO4J_AUTH: neo4j/${NEO4J_PASSWORD}
      NEO4J_PLUGINS: '["apoc", "graph-data-science"]'
    volumes:
      - neo4j_data:/data

  clickhouse:
    image: clickhouse/clickhouse-server:24-alpine
    ports:
      - "8123:8123"  # HTTP
      - "9000:9000"  # Native
    volumes:
      - clickhouse_data:/var/lib/clickhouse

  minio:
    image: minio/minio:latest
    ports:
      - "9001:9001"  # Console
      - "9000:9000"  # API
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: ${MINIO_PASSWORD}
    volumes:
      - minio_data:/data

volumes:
  postgres_data:
  qdrant_data:
  neo4j_data:
  clickhouse_data:
  minio_data:
```

### 5.2 Kubernetes 部署 (生产环境)

**集群规划**:

| 命名空间 | 服务 | 副本数 | 资源限制 |
|---------|------|--------|---------|
| `yiai-prod` | FastAPI API | 2-6 (HPA) | 2C/4G |
| `yiai-prod` | Nuxt SSR | 2-4 (HPA) | 1C/2G |
| `yiai-prod` | Celery Worker | 2-4 | 2C/4G |
| `yiai-prod` | Celery Beat | 1 | 0.5C/1G |
| `yiai-infra` | PostgreSQL (StatefulSet) | 1 主 + 1 只读副本 | 4C/16G |
| `yiai-infra` | Redis (StatefulSet) | 3 (哨兵模式) | 2C/4G |
| `yiai-infra` | Qdrant (StatefulSet) | 3 (集群模式) | 4C/16G |
| `yiai-infra` | Neo4j (StatefulSet) | 1 (单实例) | 4C/16G |
| `yiai-infra` | ClickHouse (StatefulSet) | 2 (分片) | 4C/16G |
| `yiai-infra` | MinIO (StatefulSet) | 4 (分布式) | 2C/4G |
| `monitoring` | Prometheus + Grafana | 各 1 | 2C/4G |
| `monitoring` | Loki + Promtail | 各 1 | 2C/4G |

**关键 K8s 资源**:

```yaml
# HPA for API
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: yiai-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: yiai-api
  minReplicas: 2
  maxReplicas: 6
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80

# PDB (Pod Disruption Budget)
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: yiai-api-pdb
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: yiai-api
```

### 5.3 CI/CD Pipeline

**GitHub Actions Workflow**:

```yaml
# .github/workflows/deploy.yml
name: YI-AI CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  # --- 前端 ---
  frontend-lint-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: pnpm
      - run: pnpm install --frozen-lockfile
      - run: pnpm run lint
      - run: pnpm run type-check
      - run: pnpm run test --coverage
      - run: pnpm run build

  # --- 后端 ---
  backend-lint-test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:17-alpine
        env:
          POSTGRES_DB: yiai_test
          POSTGRES_PASSWORD: test
        ports: ["5432:5432"]
      redis:
        image: redis:7-alpine
        ports: ["6379:6379"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install uv && uv sync
      - run: uv run ruff check .
      - run: uv run mypy .
      - run: uv run pytest --cov --cov-report=xml

  # --- 安全扫描 ---
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: trivy fs --exit-code 1 --severity HIGH,CRITICAL .

  # --- 部署 (仅 main) ---
  deploy:
    if: github.ref == 'refs/heads/main'
    needs: [frontend-lint-test, backend-lint-test, security-scan]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build and push Docker images
        run: |
          docker build -t yiai-api:${{ github.sha }} ./backend
          docker build -t yiai-web:${{ github.sha }} ./frontend
          # push to registry...
      - name: Deploy to K8s
        run: |
          kubectl set image deployment/yiai-api api=registry/yiai-api:${{ github.sha }}
          kubectl set image deployment/yiai-web web=registry/yiai-web:${{ github.sha }}
```

### 5.4 基础设施即代码

| 工具 | 用途 |
|------|------|
| Terraform | 云资源管理（K8s 集群、数据库、CDN、DNS） |
| Helm Charts | K8s 应用打包和部署 |
| ArgoCD | GitOps 持续部署 |
| Sealed Secrets / External Secrets | K8s 密钥管理 |

---

## 6. 监控方案

### 6.1 可观测性三支柱

```
┌─────────────────────────────────────────────────────────────┐
│                   YI-AI 可观测性架构                          │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Metrics      │  │ Logging      │  │ Tracing          │  │
│  │ (指标)       │  │ (日志)       │  │ (链路追踪)        │  │
│  │              │  │              │  │                  │  │
│  │ Prometheus   │  │ Loki +       │  │ OpenTelemetry    │  │
│  │ + Grafana    │  │ Promtail     │  │ + Jaeger/Tempo   │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│         │                  │                  │             │
│         └──────────────────┼──────────────────┘             │
│                            ▼                                │
│                    ┌──────────────┐                          │
│                    │ Grafana      │                          │
│                    │ (统一仪表板)  │                          │
│                    └──────────────┘                          │
│                            │                                │
│                    ┌──────────────┐                          │
│                    │ AlertManager │                          │
│                    │ (告警路由)    │                          │
│                    └──────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Prometheus + Grafana (指标)

**关键指标**:

| 指标名称 | 类型 | 标签 | 说明 |
|---------|------|------|------|
| `http_requests_total` | Counter | method, path, status | HTTP 请求计数 |
| `http_request_duration_seconds` | Histogram | method, path | 请求延迟分布 |
| `ai_model_call_total` | Counter | model, tier, status | AI 模型调用计数 |
| `ai_model_latency_seconds` | Histogram | model, tier | AI 模型响应延迟 |
| `ai_model_cost_usd_total` | Counter | model, tier | AI 调用累计成本 |
| `rag_search_duration_seconds` | Histogram | source_type | RAG 检索延迟 |
| `rag_search_results_count` | Histogram | source_type | RAG 返回结果数 |
| `safety_issue_total` | Counter | issue_type | 安全问题检出计数 |
| `active_sessions_gauge` | Gauge | - | 当前活跃会话数 |
| `celery_task_total` | Counter | task_name, status | Celery 任务计数 |
| `celery_task_duration_seconds` | Histogram | task_name | Celery 任务耗时 |
| `db_query_duration_seconds` | Histogram | db, operation | 数据库查询延迟 |
| `redis_operation_duration_seconds` | Histogram | operation | Redis 操作延迟 |

**Grafana Dashboard 规划**:

| Dashboard | 内容 |
|-----------|------|
| `YI-AI Overview` | 总请求量、错误率、延迟 P50/P95/P99、活跃用户 |
| `AI Model Performance` | 各模型调用量、延迟、成本、fallback 频率 |
| `RAG Performance` | 检索延迟、命中率、融合权重效果 |
| `Database Health` | PG/Redis/Qdrant/Neo4j/CH 各自的连接数、查询延迟、存储使用 |
| `User Behavior` | 用户活跃度、卦象分布、意图分布、满意度 |
| `Cost Analysis` | AI 模型成本趋势、单用户成本、成本预测 |
| `Security & Safety` | 安全问题检出率、频率限制触发、异常请求 |

### 6.3 Loki + Promtail (日志)

**日志格式 (JSON)**:

```json
{
    "timestamp": "2026-05-29T10:30:00.123Z",
    "level": "info",
    "service": "yiai-api",
    "request_id": "uuid",
    "user_id": "uuid",
    "method": "POST",
    "path": "/api/v1/ai/explain",
    "status": 200,
    "duration_ms": 3500,
    "ai_model": "deepseek-chat",
    "ai_tier": "TIER_2_STANDARD",
    "ai_tokens_in": 1500,
    "ai_tokens_out": 800,
    "ai_cost_usd": 0.012,
    "hexagram": "乾",
    "safety_issues": 0,
    "message": "AI explanation completed"
}
```

**Loki 查询示例**:

```logql
# 查询所有 AI 模型调用错误
{service="yiai-api"} | json | status >= 500

# 查询高成本请求
{service="yiai-api"} | json | ai_cost_usd > 0.05

# 查询安全问题
{service="yiai-api"} | json | safety_issues > 0
```

### 6.4 OpenTelemetry + Jaeger/Tempo (链路追踪)

**追踪 Span 示例**:

```
[POST /api/v1/ai/explain] (总耗时: 3500ms)
  ├── authenticate (5ms)
  ├── validate_request (2ms)
  ├── classify_intent [DeepSeek-V3] (200ms)
  ├── retrieve_memory [Redis + PG] (50ms)
  │     ├── redis_get_working_memory (5ms)
  │     └── pg_get_user_profile (30ms)
  ├── rag_retrieve (800ms)
  │     ├── vector_search [Qdrant, 5 collections] (300ms)
  │     ├── graph_search [Neo4j, depth=2] (200ms)
  │     ├── rule_engine (10ms)
  │     └── fusion_ranking (5ms)
  ├── ai_interpret [Qwen-Max] (2000ms)
  ├── safety_check (100ms)
  ├── save_divination_record [PG + Qdrant] (100ms, async)
  └── format_response (5ms)
```

### 6.5 告警规则

| 告警名称 | 条件 | 严重级别 | 通知渠道 |
|---------|------|---------|---------|
| API 错误率 > 5% | `rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05` | Critical | PagerDuty + Slack |
| API 延迟 P99 > 10s | `histogram_quantile(0.99, http_request_duration_seconds) > 10` | Warning | Slack |
| AI 模型全部失败 | `rate(ai_model_call_total{status="error"}[5m]) > 0.8` | Critical | PagerDuty |
| AI 日成本超限 | `increase(ai_model_cost_usd_total[24h]) > 100` | Warning | Slack + Email |
| 数据库连接池耗尽 | `db_connection_pool_available < 2` | Critical | PagerDuty |
| 磁盘使用率 > 85% | `node_filesystem_avail_bytes / node_filesystem_size_bytes < 0.15` | Warning | Slack |
| Neo4j 查询超时 | `rate(neo4j_query_timeout_total[5m]) > 0` | Warning | Slack |

### 6.6 监控技术栈选型理由

| 组件 | 替代方案 | 选择理由 |
|------|---------|---------|
| Prometheus | InfluxDB, VictoriaMetrics | K8s 生态标准，PromQL 强大 |
| Grafana | Kibana, Datadog | 开源，数据源支持最广 |
| Loki | ELK Stack, Datadog Logs | 与 Grafana 原生集成，成本低于 ELK |
| Jaeger/Tempo | Zipkin, Datadog APM | OpenTelemetry 兼容，Tempo 与 Grafana 集成好 |
| AlertManager | Grafana Alerting | Prometheus 原生，路由规则灵活 |

---

## 7. 版本锁定建议

### 7.1 前端版本锁定

```json
// package.json (关键依赖)
{
    "engines": {
        "node": ">=22.0.0",
        "pnpm": ">=9.0.0"
    },
    "dependencies": {
        "nuxt": "^4.0.0",
        "vue": "^3.5.0",
        "pinia": "^2.3.0",
        "tailwindcss": "^4.0.0",
        "@gsap/business": "^3.12.0",
        "cytoscape": "^3.30.0",
        "d3": "^7.9.0",
        "three": "^0.170.0",
        "echarts": "^5.6.0",
        "vue-echarts": "^7.0.0",
        "@vueuse/core": "^12.0.0",
        "axios": "^1.7.0"
    },
    "devDependencies": {
        "typescript": "^5.7.0",
        "vitest": "^3.0.0",
        "playwright": "^1.50.0",
        "@nuxt/test-utils": "^3.15.0",
        "eslint": "^9.0.0",
        "prettier": "^3.4.0"
    }
}
```

**包管理器**: pnpm（磁盘效率最高，monorepo 支持好）

### 7.2 后端版本锁定

```toml
# pyproject.toml (uv 管理)
[project]
requires-python = ">=3.12,<3.14"

[tool.uv]
# uv.lock 自动锁定所有依赖

[project.dependencies]
fastapi = ">=0.115,<1.0"
uvicorn = {version = ">=0.34", extras = ["standard"]}
pydantic = ">=2.10,<3.0"
sqlalchemy = {version = ">=2.0,<3.0", extras = ["asyncio"]}
asyncpg = ">=0.30,<1.0"
redis = {version = ">=5.2,<6.0", extras = ["hiredis"]}
httpx = ">=0.28,<1.0"
celery = {version = ">=5.4,<6.0", extras = ["redis"]}
langchain = ">=0.3,<1.0"
langgraph = ">=0.3,<1.0"
qdrant-client = ">=1.12,<2.0"
neo4j = ">=5.25,<6.0"
sentence-transformers = ">=3.3,<4.0"
python-jose = {version = ">=3.3", extras = ["cryptography"]}
prometheus-client = ">=0.21,<1.0"
```

**包管理器**: uv（比 pip 快 10-100x，lockfile 支持好）

### 7.3 数据库版本锁定

| 数据库 | 推荐版本 | 锁定理由 |
|--------|---------|---------|
| PostgreSQL | 17.x | JSONB 性能优化，增量备份改进 |
| Redis | 7.x | Stream 增强，Functions 支持 |
| Qdrant | 1.12.x | 量化搜索、multi-vector 支持 |
| Neo4j | 5.x Community | GDS 库兼容，Cypher 性能优化 |
| ClickHouse | 24.x LTS | 稳定性，Join 性能改进 |
| MinIO | latest stable | S3 兼容性保持最新 |

### 7.4 Docker 基础镜像锁定

```dockerfile
# 后端 Dockerfile
FROM python:3.12-slim-bookworm AS base
# 使用 slim 减少攻击面，bookworm 为 Debian 12 稳定版

# 前端 Dockerfile
FROM node:22-alpine AS base
# Alpine 减少镜像体积
```

### 7.5 版本升级策略

- **补丁版本 (patch)**: 自动升级，CI 验证
- **次要版本 (minor)**: 每月评估一次，小范围灰度
- **主要版本 (major)**: 季度评估，完整测试后升级
- **数据库大版本**: 至少等待 .2 补丁后再升级

---

## 8. 技术风险与备选方案

### 8.1 风险矩阵

| 风险编号 | 风险描述 | 概率 | 影响 | 等级 | 缓解策略 |
|---------|---------|------|------|------|---------|
| R1 | GSAP 商业许可限制 | 中 | 高 | **高** | 评估 Motion Vue / Framer Motion 替代；非商业阶段免费使用 |
| R2 | Nuxt 4 生态不成熟 | 中 | 中 | **中** | 关键组件自研；保持 Vue 3 原生能力作为退路 |
| R3 | LLM API 价格波动 | 高 | 中 | **高** | 模型路由层抽象；本地小模型（Qwen2.5-7B）作为 Tier 1 fallback |
| R4 | LLM API 可用性 | 中 | 高 | **高** | 多提供商 fallback 链；本地模型兜底；请求队列缓冲 |
| R5 | Neo4j Community 限制 | 低 | 中 | **低** | 数据量在 Community 范围内；必要时迁移到 ArangoDB |
| R6 | Qdrant 单点故障 | 低 | 高 | **中** | 生产环境 Qdrant 集群模式（3 节点）；定期快照备份 |
| R7 | Python GIL 限制 | 低 | 低 | **低** | 规则引擎 CPU 密集任务用 `multiprocessing`；Python 3.13+ free-threading 实验性支持 |
| R8 | 知识图谱数据质量 | 中 | 高 | **高** | 专家审核知识库；版本控制数据变更；回滚机制 |
| R9 | AI 安全性（误导性输出） | 中 | 极高 | **极高** | SafetyChecker 强制检查；禁止确定性承诺；人工审核高风险输出 |
| R10 | 数据隐私合规 | 中 | 高 | **高** | 用户数据加密存储；GDPR 数据删除支持；审计日志 |
| R11 | Embedding 模型中文效果 | 低 | 中 | **低** | bge-m3 中文表现优秀；定期评估新模型（M3E、text2vec） |
| R12 | ClickHouse 运维复杂度 | 中 | 低 | **低** | ClickHouse Cloud 托管选项；Loki 可替代部分日志场景 |

### 8.2 关键备选方案

#### 前端备选方案

```
场景: Nuxt 4 生态问题严重到无法继续
  备选: Next.js 15 + React
  迁移成本: 高（Vue → React 全面重写）
  评估触发点: Nuxt 4 GA 后 6 个月内无稳定生态

场景: GSAP 许可问题
  备选: Motion Vue + CSS Animation + Web Animations API
  迁移成本: 中（动画逻辑重写，但核心效果可保留）
  评估触发点: 商业化时许可证审查

场景: Three.js 3D 需求减少
  备选: 移除 Three.js，用 CSS 3D transform + GSAP 实现简单 3D 效果
  迁移成本: 低（渐进增强，3D 页面独立）
  评估触发点: 3D 页面 PV < 5%
```

#### 后端备选方案

```
场景: Python 性能成为瓶颈
  备选: 规则引擎用 Rust (PyO3) 扩展；API 网关用 Go
  迁移成本: 中（核心规则引擎用 Rust 重写，Python 调用）
  评估触发点: P99 延迟持续 > 5s 且无法通过优化解决

场景: Celery 无法满足需求
  备选: Temporal.io (复杂工作流) 或 ARQ (轻量 async)
  迁移成本: 中
  评估触发点: Celery 任务丢失率 > 0.1%

场景: LangChain 过度抽象导致问题
  备选: 直接使用 httpx 调用 LLM API + 自研调用层
  迁移成本: 低-中（抽象层隔离）
  评估触发点: LangChain breaking changes 频率过高
```

#### 数据库备选方案

```
场景: Qdrant 不满足需求
  备选: Milvus (分布式) 或 pgvector (简化架构)
  迁移成本: 中
  评估触发点: Qdrant 集群稳定性问题

场景: Neo4j Community 功能限制
  备选: ArangoDB (多模型) 或 PostgreSQL + Apache AGE
  迁移成本: 高（Cypher → AQL 或 AGE 语法差异）
  评估触发点: 需要分布式图数据库

场景: ClickHouse 运维负担过重
  备选: ClickHouse Cloud 托管 或 TimescaleDB (PG 扩展)
  迁移成本: 低（ClickHouse Cloud）/ 中（TimescaleDB）
  评估触发点: 运维团队无法维护 CH 集群
```

#### AI 备选方案

```
场景: 主要 LLM 提供商 API 全面涨价
  备选: 本地部署 Qwen2.5-72B / DeepSeek-V3 (量化版)
  部署方式: vLLM / Ollama + 4xA100 GPU
  迁移成本: 低（API 兼容层隔离）
  评估触发点: 单次请求成本 > $0.10

场景: bge-m3 效果不理想
  备选: text-embedding-3-large (OpenAI) 或 m3e-large
  迁移成本: 低（重新 Embedding 全量数据）
  评估触发点: RAG nDCG@10 < 0.6
```

---

## 9. 开发工具链

### 9.1 语言与运行时

| 工具 | 版本 | 用途 |
|------|------|------|
| Node.js | 22 LTS | 前端运行时 |
| pnpm | 9.x | 前端包管理 |
| Python | 3.12 | 后端运行时 |
| uv | 0.5+ | Python 包管理（替代 pip/poetry） |
| TypeScript | 5.7+ | 前端类型系统 |

### 9.2 代码质量

| 工具 | 用途 | 适用范围 |
|------|------|---------|
| ESLint 9 (flat config) | JavaScript/TypeScript Lint | 前端 |
| Prettier | 代码格式化 | 前端 |
| Vue TSC | Vue TypeScript 类型检查 | 前端 |
| Ruff | Python Lint + Format (替代 flake8+black+isort) | 后端 |
| Mypy | Python 静态类型检查 | 后端 |
| Pre-commit hooks | 提交前自动检查 | 全栈 |

### 9.3 测试

| 工具 | 用途 | 适用范围 |
|------|------|---------|
| Vitest | 单元测试（Vue/Vite 原生） | 前端 |
| Playwright | E2E 测试 + 视觉回归 | 前端 |
| @vue/test-utils | Vue 组件测试 | 前端 |
| pytest | Python 测试框架 | 后端 |
| pytest-asyncio | 异步测试 | 后端 |
| pytest-cov | 覆盖率 | 后端 |
| httpx (TestClient) | API 集成测试 | 后端 |
| Faker | 测试数据生成 | 全栈 |
| factory_boy | Python 测试工厂 | 后端 |

### 9.4 开发环境

| 工具 | 用途 |
|------|------|
| VS Code / Cursor | IDE |
| Docker Desktop | 本地容器运行 |
| DBeaver / pgAdmin | 数据库管理 |
| Neo4j Browser | 图谱可视化调试 |
| Redis Insight | Redis 可视化 |
| Postman / Bruno | API 测试 |
| ngrok | 本地 webhook/回调调试 |

### 9.5 文档

| 工具 | 用途 |
|------|------|
| FastAPI 自动文档 | API 文档（Swagger/ReDoc） |
| Storybook | 前端组件文档 |
| MkDocs / VitePress | 项目文档站 |

### 9.6 版本控制

| 工具 | 用途 |
|------|------|
| Git | 版本控制 |
| GitHub | 代码托管 + CI/CD |
| Conventional Commits | 提交消息规范 |
| Changesets | 版本发布管理 |
| Branch Strategy | Git Flow (main + develop + feature/*) |

### 9.7 开发工具链全景

```
Code & Edit
  ├── VS Code / Cursor (IDE)
  ├── ESLint + Prettier (前端)
  ├── Ruff + Mypy (后端)
  └── Pre-commit hooks

Build & Test
  ├── pnpm build (前端)
  ├── uv build (后端)
  ├── Vitest + Playwright (前端测试)
  └── pytest (后端测试)

Container & Deploy
  ├── Docker (容器化)
  ├── Docker Compose (本地编排)
  ├── GitHub Actions (CI/CD)
  └── Helm + ArgoCD (K8s 部署)

Monitor & Observe
  ├── Prometheus + Grafana (指标)
  ├── Loki + Promtail (日志)
  ├── OpenTelemetry + Tempo (追踪)
  └── AlertManager (告警)
```

---

## 附录: 技术栈依赖关系总图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         YI-AI 技术栈全景                                │
│                                                                         │
│  ┌─── 前端 ──────────────────────────────────────────────────────────┐  │
│  │ Nuxt 4 · Vue 3 · TailwindCSS · shadcn-vue · Pinia               │  │
│  │ GSAP · Cytoscape.js · D3.js · Three.js · ECharts                │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                               │ REST / WebSocket / SSE                  │
│  ┌─── 后端 ──────────────────────────────────────────────────────────┐  │
│  │ Python 3.12 · FastAPI · asyncio · Celery                         │  │
│  │ LangGraph · LangChain · httpx                                    │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                               │                                         │
│  ┌─── AI/ML ─────────────────────────────────────────────────────────┐  │
│  │ DeepSeek · Qwen · Claude · GPT                                    │  │
│  │ bge-m3 · jina-embeddings · sentence-transformers                  │  │
│  │ ModelRouter · RAG (RRF Fusion) · SafetyChecker                   │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                               │                                         │
│  ┌─── 数据 ──────────────────────────────────────────────────────────┐  │
│  │ PostgreSQL 17 · Redis 7 · Qdrant 1.12                            │  │
│  │ Neo4j 5 · ClickHouse 24 · MinIO                                  │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                               │                                         │
│  ┌─── 基础设施 ──────────────────────────────────────────────────────┐  │
│  │ Docker · Kubernetes · Terraform · Helm                           │  │
│  │ GitHub Actions · ArgoCD · Sealed Secrets                        │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                               │                                         │
│  ┌─── 监控 ──────────────────────────────────────────────────────────┐  │
│  │ Prometheus · Grafana · Loki · Tempo · AlertManager               │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

*本文档版本: 1.0.0*
*最后更新: 2026-05-29*
*关联文档: yiai.md (总体架构) · ai-architecture.md (AI 架构)*
