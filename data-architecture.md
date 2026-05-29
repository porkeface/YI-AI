# YI-AI 数据架构设计文档

> 本文档是 YI-AI 系统的完整数据架构设计，覆盖 PostgreSQL、Neo4j、Qdrant、Redis、ClickHouse、MinIO 六大数据存储，以及数据同步、备份、安全、容量规划。

---

## 目录

1. [数据架构总览](#1-数据架构总览)
2. [PostgreSQL 详细表设计](#2-postgresql-详细表设计)
3. [Neo4j 图谱设计](#3-neo4j-图谱设计)
4. [Qdrant 集合设计](#4-qdrant-集合设计)
5. [Redis 缓存策略](#5-redis-缓存策略)
6. [ClickHouse 日志设计](#6-clickhouse-日志设计)
7. [MinIO 对象存储设计](#7-minio-对象存储设计)
8. [数据同步策略](#8-数据同步策略)
9. [数据备份恢复方案](#9-数据备份恢复方案)
10. [数据安全和隐私保护](#10-数据安全和隐私保护)
11. [数据增长预测和容量规划](#11-数据增长预测和容量规划)

---

## 1. 数据架构总览

### 1.1 六库职责划分

```
┌─────────────────────────────────────────────────────────────────────┐
│                        YI-AI 数据架构全景                            │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ PostgreSQL   │  │   Neo4j      │  │   Qdrant     │              │
│  │              │  │              │  │              │              │
│  │ 用户数据     │  │ 易学关系图谱 │  │ 向量检索     │              │
│  │ 卦记录       │  │ 用户行为图谱 │  │ 语义搜索     │              │
│  │ 配置数据     │  │ 五行关系网   │  │ 知识库嵌入   │              │
│  │ 事务数据     │  │ 时间关系网   │  │ 用户历史嵌入 │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   Redis      │  │ ClickHouse   │  │   MinIO      │              │
│  │              │  │              │  │              │              │
│  │ 会话缓存     │  │ 操作日志     │  │ 原始文档     │              │
│  │ 热点数据     │  │ 分析指标     │  │ 用户附件     │              │
│  │ 频率限制     │  │ 时序数据     │  │ 生成报告     │              │
│  │ 工作记忆     │  │ A/B测试数据  │  │ 备份快照     │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 数据流向

```
用户请求
  │
  ▼
┌─────────────────────────────────────────────────────┐
│                  应用层 (FastAPI)                     │
│                                                     │
│  认证 ──▶ Redis (session/token)                     │
│  起卦 ──▶ PostgreSQL (写入) + ClickHouse (日志)     │
│  解卦 ──▶ 规则引擎 ──▶ Qdrant+Neo4j+规则 (RAG)    │
│  记忆 ──▶ PostgreSQL+Qdrant (持久化)                │
│         ──▶ Neo4j (图谱更新)                        │
│         ──▶ Redis (缓存失效)                        │
└─────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────┐
│                  数据层                              │
│                                                     │
│  写入路径: App → PG (主) → 异步同步 → Neo4j/Qdrant  │
│  读取路径: App → Redis (缓存) → PG/Neo4j/Qdrant    │
│  分析路径: App → ClickHouse (实时写入)              │
│  存储路径: App → MinIO (文件) + PG (元数据)         │
└─────────────────────────────────────────────────────┘
```

### 1.3 存储选型理由

| 存储 | 数据类型 | 选型理由 |
|------|---------|---------|
| PostgreSQL | 结构化事务数据 | ACID 事务、JSONB 灵活 schema、成熟生态 |
| Neo4j | 关系网络 | 原生图遍历、Cypher 查询、多跳关系高效 |
| Qdrant | 高维向量 | 专用向量索引、过滤检索、标量量化 |
| Redis | 热点缓存 | 亚毫秒延迟、丰富数据结构、TTL 支持 |
| ClickHouse | 时序分析 | 列式存储、高压缩比、聚合查询极快 |
| MinIO | 文件对象 | S3 兼容、自托管、版本控制 |

---

## 2. PostgreSQL 详细表设计

### 2.1 Schema 划分

```sql
-- 创建独立 Schema，按领域隔离
CREATE SCHEMA IF NOT EXISTS core;       -- 核心数据（用户、认证）
CREATE SCHEMA IF NOT EXISTS divination; -- 卦象数据
CREATE SCHEMA IF NOT EXISTS knowledge;  -- 知识库数据
CREATE SCHEMA IF NOT EXISTS config;     -- 配置数据
CREATE SCHEMA IF NOT EXISTS billing;    -- 计费数据
```

### 2.2 用户与认证

```sql
-- ============================================================
-- 用户表
-- ============================================================
CREATE TABLE core.users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone           VARCHAR(20) UNIQUE,
    email           VARCHAR(255) UNIQUE,
    wechat_open_id  VARCHAR(128) UNIQUE,
    nickname        VARCHAR(64) NOT NULL,
    avatar_url      VARCHAR(512),
    password_hash   VARCHAR(255),                -- bcrypt hash

    -- 用户画像（聚合字段，定期由离线任务更新）
    profile         JSONB DEFAULT '{}'::JSONB,
    -- {
    --   "age_range": "25-34",
    --   "occupation": "engineer",
    --   "interests": ["career", "relationship"],
    --   "dominant_element": "木",
    --   "question_frequency": 2.5,
    --   "emotional_trajectory": [...]
    -- }

    -- 偏好设置
    preferences     JSONB DEFAULT '{
        "language": "zh-CN",
        "theme": "dark",
        "notification_enabled": true,
        "detail_level": "standard",
        "interpretation_style": "modern"
    }'::JSONB,

    -- 状态
    status          VARCHAR(20) NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'suspended', 'deleted')),
    vip_level       SMALLINT NOT NULL DEFAULT 0
                    CHECK (vip_level BETWEEN 0 AND 5),
    vip_expires_at  TIMESTAMPTZ,

    -- 时间戳
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_login_at   TIMESTAMPTZ,
    deleted_at      TIMESTAMPTZ                    -- 软删除
);

-- 索引
CREATE INDEX idx_users_phone ON core.users (phone) WHERE phone IS NOT NULL;
CREATE INDEX idx_users_email ON core.users (email) WHERE email IS NOT NULL;
CREATE INDEX idx_users_wechat ON core.users (wechat_open_id) WHERE wechat_open_id IS NOT NULL;
CREATE INDEX idx_users_status ON core.users (status);
CREATE INDEX idx_users_vip ON core.users (vip_level) WHERE vip_level > 0;
CREATE INDEX idx_users_profile ON core.users USING GIN (profile);
CREATE INDEX idx_users_created ON core.users (created_at);

-- 自动更新 updated_at
CREATE OR REPLACE FUNCTION core.update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated
    BEFORE UPDATE ON core.users
    FOR EACH ROW EXECUTE FUNCTION core.update_timestamp();


-- ============================================================
-- 用户会话表（JWT refresh token 管理）
-- ============================================================
CREATE TABLE core.user_sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES core.users(id) ON DELETE CASCADE,
    refresh_token   VARCHAR(512) NOT NULL,
    device_info     JSONB DEFAULT '{}'::JSONB,
    -- {
    --   "platform": "ios",
    --   "device": "iPhone 15",
    --   "app_version": "1.2.0",
    --   "ip": "1.2.3.4"
    -- }

    expires_at      TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    revoked_at      TIMESTAMPTZ
);

CREATE INDEX idx_sessions_user ON core.user_sessions (user_id);
CREATE INDEX idx_sessions_token ON core.user_sessions (refresh_token);
CREATE INDEX idx_sessions_expires ON core.user_sessions (expires_at) WHERE revoked_at IS NULL;
```

### 2.3 易学核心数据（静态/半静态）

```sql
-- ============================================================
-- 六十四卦表
-- ============================================================
CREATE TABLE knowledge.hexagrams (
    id              SMALLINT PRIMARY KEY,          -- 卦序 1-64
    name            VARCHAR(8) NOT NULL UNIQUE,    -- 卦名：乾、坤...
    unicode_char    VARCHAR(4),                    -- Unicode 符号
    binary_code     CHAR(6) NOT NULL UNIQUE,       -- 二进制：111111
    upper_trigram   VARCHAR(4) NOT NULL,           -- 上卦
    lower_trigram   VARCHAR(4) NOT NULL,           -- 下卦

    -- 卦辞
    judgement       TEXT NOT NULL,                 -- 卦辞
    judgement_image TEXT,                          -- 象辞
    judgement_tuan  TEXT,                          -- 彖辞

    -- 五行属性
    element         VARCHAR(4) NOT NULL,           -- 主五行
    nature          VARCHAR(20),                   -- 卦象性质

    -- 元数据
    keywords        TEXT[],                        -- 关键词数组
    modern_summary  TEXT,                          -- 现代白话摘要
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE knowledge.hexagrams IS '六十四卦核心数据';
COMMENT ON COLUMN knowledge.hexagrams.binary_code IS '从初爻到上爻的二进制，1=阳 0=阴';


-- ============================================================
-- 爻辞表
-- ============================================================
CREATE TABLE knowledge.lines (
    id              SERIAL PRIMARY KEY,
    hexagram_id     SMALLINT NOT NULL REFERENCES knowledge.hexagrams(id),
    position        SMALLINT NOT NULL CHECK (position BETWEEN 1 AND 6),
    yin_yang        VARCHAR(4) NOT NULL CHECK (yin_yang IN ('yin', 'yang')),

    -- 爻辞
    text            TEXT NOT NULL,                 -- 爻辞
    image_text      TEXT,                          -- 小象

    -- 纳甲
    naijia_stem     VARCHAR(4),                   -- 天干
    naijia_branch   VARCHAR(4),                   -- 地支

    -- 六亲
    six_relative    VARCHAR(8),                   -- 六亲

    -- 元数据
    keywords        TEXT[],
    modern_explanation TEXT,

    UNIQUE (hexagram_id, position)
);

CREATE INDEX idx_lines_hexagram ON knowledge.lines (hexagram_id);
COMMENT ON TABLE knowledge.lines IS '每卦六爻，共 384 条爻辞';


-- ============================================================
-- 八卦表
-- ============================================================
CREATE TABLE knowledge.trigrams (
    id              SMALLINT PRIMARY KEY,
    name            VARCHAR(4) NOT NULL UNIQUE,
    symbol          VARCHAR(4),                    -- Unicode 卦符
    binary_code     CHAR(3) NOT NULL UNIQUE,
    nature          VARCHAR(8) NOT NULL,           -- 天地雷风水火山泽
    element         VARCHAR(4) NOT NULL,
    family_role     VARCHAR(8),                    -- 父母长中少
    body_part       VARCHAR(8),
    animal          VARCHAR(8),
    direction       VARCHAR(8)
);


-- ============================================================
-- 五行表
-- ============================================================
CREATE TABLE knowledge.elements (
    name            VARCHAR(4) PRIMARY KEY,        -- 木火土金水
    nature          VARCHAR(8) NOT NULL,           -- 曲直炎上稼穑从革润下
    season          VARCHAR(8),                    -- 春夏长夏秋冬
    direction       VARCHAR(8),                    -- 东南中西北
    color           VARCHAR(8),                    -- 青赤黄白黑
    organ           VARCHAR(8),                    -- 肝心脾肺肾
    emotion         VARCHAR(8),                    -- 怒喜思悲恐
    generates       VARCHAR(4) REFERENCES knowledge.elements(name),
    restrains       VARCHAR(4) REFERENCES knowledge.elements(name)
);

COMMENT ON TABLE knowledge.elements IS '五行及生克关系';


-- ============================================================
-- 天干表
-- ============================================================
CREATE TABLE knowledge.heavenly_stems (
    name            VARCHAR(4) PRIMARY KEY,        -- 甲乙丙丁戊己庚辛壬癸
    element         VARCHAR(4) NOT NULL REFERENCES knowledge.elements(name),
    yin_yang        VARCHAR(4) NOT NULL,
    number          SMALLINT NOT NULL UNIQUE
);


-- ============================================================
-- 地支表
-- ============================================================
CREATE TABLE knowledge.earthly_branches (
    name            VARCHAR(4) PRIMARY KEY,        -- 子丑寅卯辰巳午未申酉戌亥
    element         VARCHAR(4) NOT NULL REFERENCES knowledge.elements(name),
    yin_yang        VARCHAR(4) NOT NULL,
    animal          VARCHAR(8),
    month           SMALLINT,                      -- 对应月份
    hours           VARCHAR(20),                   -- 对应时辰
    -- 冲合关系通过关联表维护
    clashes_with    VARCHAR(4)[] DEFAULT '{}',      -- 六冲
    combines_with   JSONB DEFAULT '[]'::JSONB       -- 六合/三合
);


-- ============================================================
-- 六亲表
-- ============================================================
CREATE TABLE knowledge.six_relatives (
    name            VARCHAR(8) PRIMARY KEY,        -- 父母/官鬼/妻财/子孙/兄弟
    description     TEXT NOT NULL,                 -- "生我者"
    represents      TEXT,                          -- 代表含义
    keywords        TEXT[]
);


-- ============================================================
-- 六神表
-- ============================================================
CREATE TABLE knowledge.six_spirits (
    name            VARCHAR(8) PRIMARY KEY,        -- 青龙/朱雀/勾陈/螣蛇/白虎/玄武
    element         VARCHAR(4) REFERENCES knowledge.elements(name),
    nature          VARCHAR(8),                    -- 吉/凶/中
    represents      TEXT,
    keywords        TEXT[]
);


-- ============================================================
-- 卦变关系表（错、综、互、变）
-- ============================================================
CREATE TABLE knowledge.hexagram_relations (
    id              SERIAL PRIMARY KEY,
    source_id       SMALLINT NOT NULL REFERENCES knowledge.hexagrams(id),
    target_id       SMALLINT NOT NULL REFERENCES knowledge.hexagrams(id),
    relation_type   VARCHAR(20) NOT NULL
                    CHECK (relation_type IN ('reverse', 'opposite', 'mutual', 'transform')),
    -- reverse: 综卦, opposite: 错卦, mutual: 互卦, transform: 变卦
    moving_lines    SMALLINT[],                    -- 变卦时的动爻位置
    description     TEXT,

    UNIQUE (source_id, target_id, relation_type)
);

CREATE INDEX idx_hex_rel_source ON knowledge.hexagram_relations (source_id);
CREATE INDEX idx_hex_rel_target ON knowledge.hexagram_relations (target_id);
CREATE INDEX idx_hex_rel_type ON knowledge.hexagram_relations (relation_type);
```

### 2.4 用户行为数据（持续增长）

```sql
-- ============================================================
-- 卦记录表（核心业务表，数据量最大）
-- ============================================================
CREATE TABLE divination.records (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES core.users(id),

    -- 起卦信息
    method          VARCHAR(20) NOT NULL
                    CHECK (method IN ('coin', 'time', 'plum_blossom', 'random', 'manual')),
    question        TEXT NOT NULL,                 -- 用户问题
    question_topic  VARCHAR(50),                   -- 问题主题分类
    question_tags   TEXT[] DEFAULT '{}',            -- 问题标签

    -- 卦象数据
    hexagram_id     SMALLINT NOT NULL REFERENCES knowledge.hexagrams(id),
    changed_hexagram_id SMALLINT REFERENCES knowledge.hexagrams(id),
    moving_lines    SMALLINT[] DEFAULT '{}',        -- 动爻位置 [1,3,5]
    line_states     JSONB NOT NULL,
    -- [
    --   {"position": 1, "yin_yang": "yang", "is_moving": false, "element": "金", "branch": "子", "stem": "甲", "relative": "兄弟"},
    --   ...
    -- ]

    -- 干支时间
    time_ganzhi     JSONB NOT NULL,
    -- {
    --   "year_stem": "甲", "year_branch": "子",
    --   "month_stem": "丙", "month_branch": "寅",
    --   "day_stem": "庚", "day_branch": "午",
    --   "hour_stem": "戊", "hour_branch": "子",
    --   "jieqi": "大寒"
    -- }

    -- 世应
    world_position  SMALLINT CHECK (world_position BETWEEN 1 AND 6),
    response_position SMALLINT CHECK (response_position BETWEEN 1 AND 6),

    -- AI 解释
    ai_interpretation TEXT,                        -- AI 生成的解释
    ai_model_used   VARCHAR(64),                   -- 使用的模型
    ai_tier         VARCHAR(20),                   -- Tier 1-4
    ai_tokens_used  INTEGER DEFAULT 0,
    ai_cost_usd     NUMERIC(10,6) DEFAULT 0,

    -- 用户反馈
    user_rating     SMALLINT CHECK (user_rating BETWEEN 1 AND 5),
    user_feedback   TEXT,
    is_bookmarked   BOOLEAN DEFAULT false,

    -- 情绪分析（由 AI 分析）
    sentiment       VARCHAR(20)
                    CHECK (sentiment IN ('positive', 'neutral', 'anxious', 'negative', 'mixed')),
    sentiment_score NUMERIC(4,3),                  -- -1.0 ~ 1.0

    -- 安全标记
    risk_flags      TEXT[] DEFAULT '{}',

    -- 时间戳
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    divination_time TIMESTAMPTZ NOT NULL DEFAULT now()  -- 起卦时间（可能与创建时间不同）
);

-- 核心查询索引
CREATE INDEX idx_records_user_time ON divination.records (user_id, created_at DESC);
CREATE INDEX idx_records_hexagram ON divination.records (hexagram_id);
CREATE INDEX idx_records_changed_hex ON divination.records (changed_hexagram_id) WHERE changed_hexagram_id IS NOT NULL;
CREATE INDEX idx_records_topic ON divination.records (question_topic) WHERE question_topic IS NOT NULL;
CREATE INDEX idx_records_sentiment ON divination.records (sentiment) WHERE sentiment IS NOT NULL;
CREATE INDEX idx_records_rating ON divination.records (user_rating) WHERE user_rating IS NOT NULL;
CREATE INDEX idx_records_bookmarked ON divination.records (user_id) WHERE is_bookmarked = true;
CREATE INDEX idx_records_tags ON divination.records USING GIN (question_tags);
CREATE INDEX idx_records_created ON divination.records (created_at);
CREATE INDEX idx_records_line_states ON divination.records USING GIN (line_states);

COMMENT ON TABLE divination.records IS '卦记录，系统核心业务表';


-- ============================================================
-- 用户行为事件表（细粒度行为追踪）
-- ============================================================
CREATE TABLE divination.events (
    id              BIGSERIAL PRIMARY KEY,
    user_id         UUID NOT NULL REFERENCES core.users(id),
    session_id      UUID,
    record_id       UUID REFERENCES divination.records(id) ON DELETE SET NULL,

    event_type      VARCHAR(50) NOT NULL,
    -- 'page_view', 'question_submit', 'hexagram_generated',
    -- 'interpretation_viewed', 'feedback_given', 'share',
    -- 'bookmark', 'export', 'search', 'ai_follow_up'

    event_data      JSONB DEFAULT '{}'::JSONB,
    -- {
    --   "page": "/hexagram/qian",
    --   "duration_ms": 15000,
    --   "scroll_depth": 0.8,
    --   "click_target": "follow_up_button"
    -- }

    -- 设备信息
    platform        VARCHAR(20),                   -- ios/android/web
    device_id       VARCHAR(128),
    ip_hash         VARCHAR(64),                   -- IP 的哈希（隐私保护）

    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 按时间分区（月分区）
CREATE TABLE divination.events_partitioned (
    LIKE divination.events INCLUDING ALL
) PARTITION BY RANGE (created_at);

-- 创建月分区的函数
CREATE OR REPLACE FUNCTION divination.create_monthly_partition()
RETURNS void AS $$
DECLARE
    next_month DATE := date_trunc('month', now()) + interval '1 month';
    partition_name TEXT;
BEGIN
    partition_name := 'events_' || to_char(next_month, 'YYYY_MM');
    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS divination.%I PARTITION OF divination.events_partitioned
         FOR VALUES FROM (%L) TO (%L)',
        partition_name,
        next_month,
        next_month + interval '1 month'
    );
END;
$$ LANGUAGE plpgsql;

CREATE INDEX idx_events_user_type ON divination.events (user_id, event_type, created_at DESC);
CREATE INDEX idx_events_session ON divination.events (session_id) WHERE session_id IS NOT NULL;
CREATE INDEX idx_events_record ON divination.events (record_id) WHERE record_id IS NOT NULL;
CREATE INDEX idx_events_type_time ON divination.events (event_type, created_at DESC);
```

### 2.5 用户长期画像

```sql
-- ============================================================
-- 用户画像表（聚合画像，定期离线更新）
-- ============================================================
CREATE TABLE core.user_profiles (
    user_id         UUID PRIMARY KEY REFERENCES core.users(id) ON DELETE CASCADE,

    -- 统计聚合
    total_divinations   INTEGER NOT NULL DEFAULT 0,
    total_ai_queries    INTEGER NOT NULL DEFAULT 0,
    total_feedback      INTEGER NOT NULL DEFAULT 0,
    avg_rating          NUMERIC(3,2),              -- 平均评分
    streak_days         INTEGER DEFAULT 0,         -- 连续使用天数
    longest_streak      INTEGER DEFAULT 0,

    -- 卦象偏好（JSONB 字段，定期聚合更新）
    frequent_hexagrams  JSONB DEFAULT '{}'::JSONB,
    -- {"乾": 12, "坤": 8, "坎": 15, ...}

    frequent_elements   JSONB DEFAULT '{}'::JSONB,
    -- {"木": 0.3, "火": 0.2, "土": 0.15, "金": 0.2, "水": 0.15}

    question_topics     JSONB DEFAULT '{}'::JSONB,
    -- {"事业": 45, "感情": 30, "健康": 15, "财运": 10}

    -- 情绪轨迹（按月聚合）
    emotional_trajectory JSONB DEFAULT '[]'::JSONB,
    -- [
    --   {"period": "2025-01", "positive": 5, "neutral": 3, "anxious": 2, "negative": 1},
    --   {"period": "2025-02", "positive": 7, "neutral": 2, "anxious": 4, "negative": 0}
    -- ]

    -- 行为模式
    active_hours        JSONB DEFAULT '{}'::JSONB,  -- 活跃时段分布
    peak_day_of_week    SMALLINT,                   -- 最活跃星期几
    avg_session_length  INTEGER,                    -- 平均会话时长(秒)
    question_complexity NUMERIC(3,2),               -- 问题复杂度评分

    -- 变化轨迹摘要
    topic_trajectories  JSONB DEFAULT '[]'::JSONB,
    -- [
    --   {
    --     "topic": "事业",
    --     "trend": "improving",
    --     "dominant_hexagrams": ["乾", "大有"],
    --     "key_turning_points": [...],
    --     "pattern": "cyclical"
    --   }
    -- ]

    -- 记忆衰减
    decay_summary       JSONB DEFAULT '{}'::JSONB,

    -- 时间戳
    first_divination_at TIMESTAMPTZ,
    last_divination_at  TIMESTAMPTZ,
    profile_updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE core.user_profiles IS '用户画像，由离线聚合任务定期更新';


-- ============================================================
-- 用户记忆衰减表
-- ============================================================
CREATE TABLE divination.memory_decay (
    id              SERIAL PRIMARY KEY,
    user_id         UUID NOT NULL REFERENCES core.users(id) ON DELETE CASCADE,
    record_id       UUID NOT NULL REFERENCES divination.records(id) ON DELETE CASCADE,

    -- 衰减评分
    relevance_score NUMERIC(5,4) NOT NULL,         -- 当前相关性 0-1
    decay_factor    NUMERIC(5,4) NOT NULL,         -- 衰减因子
    days_elapsed    INTEGER NOT NULL,

    -- 压缩状态
    compression_level VARCHAR(20) NOT NULL DEFAULT 'full'
                      CHECK (compression_level IN ('full', 'essential', 'summary', 'archived')),
    compressed_data JSONB,                         -- 压缩后的数据

    last_decay_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, record_id)
);

CREATE INDEX idx_decay_user ON divination.memory_decay (user_id, relevance_score DESC);
CREATE INDEX idx_decay_level ON divination.memory_decay (compression_level) WHERE compression_level != 'full';
```

### 2.6 Prompt 与配置

```sql
-- ============================================================
-- Prompt 模板表
-- ============================================================
CREATE TABLE config.prompt_templates (
    id              VARCHAR(64) PRIMARY KEY,       -- hexagram_base_v5
    category        VARCHAR(30) NOT NULL,          -- interpretation/trend/evolution/safety
    version         VARCHAR(20) NOT NULL,
    content_hash    VARCHAR(64) NOT NULL,          -- SHA-256

    -- 模板内容
    system_prompt   TEXT NOT NULL,
    user_prompt     TEXT NOT NULL,
    variables       JSONB NOT NULL DEFAULT '[]'::JSONB,

    -- 配置
    model_preference VARCHAR(64)[],
    max_tokens      INTEGER DEFAULT 2000,
    temperature     NUMERIC(3,2) DEFAULT 0.7,
    tier            VARCHAR(20),                   -- tier_1 ~ tier_4

    -- 评估
    avg_score       NUMERIC(3,2),
    eval_count      INTEGER DEFAULT 0,

    -- 状态
    is_active       BOOLEAN DEFAULT true,
    is_draft        BOOLEAN DEFAULT false,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_prompts_category ON config.prompt_templates (category, is_active);
CREATE INDEX idx_prompts_version ON config.prompt_templates (id, version);


-- ============================================================
-- Prompt 版本历史表
-- ============================================================
CREATE TABLE config.prompt_versions (
    id              SERIAL PRIMARY KEY,
    prompt_id       VARCHAR(64) NOT NULL REFERENCES config.prompt_templates(id),
    version         VARCHAR(20) NOT NULL,
    content_hash    VARCHAR(64) NOT NULL,
    system_prompt   TEXT NOT NULL,
    user_prompt     TEXT NOT NULL,
    change_summary  TEXT,
    created_by      UUID REFERENCES core.users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (prompt_id, version)
);


-- ============================================================
-- 系统配置表
-- ============================================================
CREATE TABLE config.settings (
    key             VARCHAR(128) PRIMARY KEY,
    value           JSONB NOT NULL,
    description     TEXT,
    is_sensitive    BOOLEAN DEFAULT false,          -- 敏感配置（如 API key 引用）
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by      UUID REFERENCES core.users(id)
);

-- 初始化关键配置
INSERT INTO config.settings (key, value, description) VALUES
('ai.model_tiers', '{"tier_1": ["deepseek-chat", "qwen-turbo"], "tier_2": ["qwen-max"], "tier_3": ["claude-sonnet-4-6"], "tier_4": ["claude-opus-4-5"]}', '模型分层配置'),
('rag.fusion_weights', '{"vector": 0.35, "graph": 0.30, "rule": 0.35}', 'RAG 融合权重'),
('memory.decay_half_life_days', '90', '记忆衰减半衰期'),
('safety.forbidden_phrases', '["一定会", "必然", "保证", "绝对", "百分之百"]', '安全禁止词'),
('limits.free_daily_divinations', '3', '免费用户每日卦数限制'),
('limits.vip_daily_divinations', '{"1": 10, "2": 30, "3": 100, "4": -1, "5": -1}', 'VIP 每日限制');


-- ============================================================
-- A/B 测试实验表
-- ============================================================
CREATE TABLE config.experiments (
    id              VARCHAR(64) PRIMARY KEY,
    name            VARCHAR(128) NOT NULL,
    description     TEXT,

    variant_a       JSONB NOT NULL,                -- {"prompt_id": "...", "model": "..."}
    variant_b       JSONB NOT NULL,
    traffic_split   NUMERIC(3,2) DEFAULT 0.50,     -- A 的流量比例

    metrics         TEXT[] NOT NULL DEFAULT '{}',
    min_samples     INTEGER DEFAULT 100,

    status          VARCHAR(20) NOT NULL DEFAULT 'draft'
                    CHECK (status IN ('draft', 'running', 'paused', 'completed')),
    winner          VARCHAR(10),                   -- 'a' / 'b' / null

    started_at      TIMESTAMPTZ,
    ended_at        TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);


-- ============================================================
-- A/B 测试结果表
-- ============================================================
CREATE TABLE config.experiment_results (
    id              BIGSERIAL PRIMARY KEY,
    experiment_id   VARCHAR(64) NOT NULL REFERENCES config.experiments(id),
    variant         VARCHAR(10) NOT NULL CHECK (variant IN ('a', 'b')),
    user_id         UUID NOT NULL REFERENCES core.users(id),
    record_id       UUID REFERENCES divination.records(id),

    metrics         JSONB NOT NULL,
    -- {"fluency": 4.2, "relevance": 3.8, "safety": 1.0}

    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_exp_results_experiment ON config.experiment_results (experiment_id, variant);
```

### 2.7 计费与额度

```sql
-- ============================================================
-- 用户额度表
-- ============================================================
CREATE TABLE billing.user_credits (
    user_id         UUID PRIMARY KEY REFERENCES core.users(id) ON DELETE CASCADE,
    free_remaining  INTEGER NOT NULL DEFAULT 3,     -- 今日免费额度
    paid_remaining  INTEGER NOT NULL DEFAULT 0,     -- 付费额度
    bonus_remaining INTEGER NOT NULL DEFAULT 0,     -- 奖励额度
    reset_at        TIMESTAMPTZ NOT NULL,           -- 免费额度重置时间
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);


-- ============================================================
-- 消费记录表
-- ============================================================
CREATE TABLE billing.transactions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES core.users(id),
    record_id       UUID REFERENCES divination.records(id),

    type            VARCHAR(20) NOT NULL
                    CHECK (type IN ('divination', 'deep_analysis', 'export', 'vip_purchase')),
    credits_used    INTEGER NOT NULL DEFAULT 1,
    cost_source     VARCHAR(20) NOT NULL
                    CHECK (cost_source IN ('free', 'paid', 'bonus')),

    amount_cents    INTEGER DEFAULT 0,             -- 实际金额（分）
    currency        VARCHAR(3) DEFAULT 'CNY',

    metadata        JSONB DEFAULT '{}'::JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_tx_user ON billing.transactions (user_id, created_at DESC);
CREATE INDEX idx_tx_type ON billing.transactions (type, created_at DESC);
```

### 2.8 完整 DDL 汇总

```sql
-- 完整建库脚本执行顺序：
-- 1. CREATE SCHEMA
-- 2. knowledge.* (静态数据)
-- 3. core.users, core.user_sessions
-- 4. core.user_profiles
-- 5. config.* (配置)
-- 6. divination.* (业务数据)
-- 7. billing.* (计费)
-- 8. 初始化数据 (八卦、五行、六十四卦、爻辞)
```

---

## 3. Neo4j 图谱设计

### 3.1 节点类型总览

| 节点标签 | 数量 | 用途 | 关键属性 |
|---------|------|------|---------|
| `Hexagram` | 64 | 六十四卦 | name, number, binary, element |
| `Line` | 384 | 爻 | position, yin_yang, text, six_relative |
| `Trigram` | 8 | 八卦 | name, binary, nature, element |
| `Element` | 5 | 五行 | name, nature, season, direction |
| `HeavenlyStem` | 10 | 天干 | name, element, yin_yang |
| `EarthlyBranch` | 12 | 地支 | name, element, animal |
| `Role` | 5 | 六亲 | name, description |
| `Spirit` | 6 | 六神 | name, element, nature |
| `User` | N | 用户节点 | user_id, dominant_element |
| `DivinationRecord` | N | 卦记录 | record_id, timestamp, sentiment |
| `Topic` | ~20 | 主题标签 | name, category |
| `TimePattern` | N | 时间模式 | pattern_type, description |

### 3.2 节点定义（Cypher）

```cypher
// ============================================================
// 五行节点（5 个，图谱起点）
// ============================================================
CREATE (e:Element {
  name: "木",
  nature: "曲直",
  season: "春",
  direction: "东",
  color: "青",
  organ: "肝",
  emotion: "怒",
  represents: "生长、条达、舒展"
})

// ============================================================
// 八卦节点（8 个）
// ============================================================
CREATE (t:Trigram {
  name: "乾",
  symbol: "☰",
  binary: "111",
  nature: "天",
  element: "金",
  family_role: "父",
  body_part: "首",
  animal: "马",
  direction: "西北",
  represents: "刚健、进取、领导"
})

// ============================================================
// 卦节点（64 个）
// ============================================================
CREATE (h:Hexagram {
  name: "乾",
  number: 1,
  unicode: "䷀",
  binary: "111111",
  upper_trigram: "乾",
  lower_trigram: "乾",
  element: "金",
  judgement: "元亨利贞",
  image: "天行健，君子以自强不息",
  keywords: ["刚健", "进取", "领导", "创造"],
  modern_summary: "纯阳之卦，象征天道刚健，万物创始"
})

// ============================================================
// 爻节点（每卦 6 个，共 384 个）
// ============================================================
CREATE (l:Line {
  position: 1,
  yin_yang: "yang",
  text: "潜龙勿用",
  image_text: "潜龙勿用，阳在下也",
  naijia_stem: "甲",
  naijia_branch: "子",
  six_relative: "兄弟",
  keywords: ["潜伏", "等待", "积蓄"]
})

// ============================================================
// 六亲节点（5 个）
// ============================================================
CREATE (r:Role {
  name: "父母",
  description: "生我者",
  represents: "文书、长辈、庇护、操劳",
  keywords: ["保护", "约束", "教育"]
})

// ============================================================
// 六神节点（6 个）
// ============================================================
CREATE (s:Spirit {
  name: "青龙",
  element: "木",
  nature: "吉",
  represents: "喜庆、文书、贵人、吉祥",
  keywords: ["喜事", "贵人", "顺利"]
})

// ============================================================
// 天干节点（10 个）
// ============================================================
CREATE (hs:HeavenlyStem {
  name: "甲",
  element: "木",
  yin_yang: "阳",
  number: 1,
  represents: "栋梁之木、开始"
})

// ============================================================
// 地支节点（12 个）
// ============================================================
CREATE (eb:EarthlyBranch {
  name: "子",
  element: "水",
  yin_yang: "阳",
  animal: "鼠",
  month: 11,
  hours: "23:00-01:00",
  represents: "开始、种子、潜藏"
})

// ============================================================
// 用户节点（动态增长）
// ============================================================
CREATE (u:User {
  user_id: "uuid-string",
  created_at: datetime(),
  dominant_element: "木",
  question_frequency: 2.5,
  vip_level: 0,
  total_divinations: 42
})

// ============================================================
// 卦记录节点（动态增长）
// ============================================================
CREATE (dr:DivinationRecord {
  record_id: "uuid-string",
  timestamp: datetime(),
  question: "事业方面最近如何？",
  question_topic: "事业",
  sentiment: "anxious",
  sentiment_score: -0.3,
  ai_model: "claude-sonnet-4-6",
  rating: 4
})

// ============================================================
// 主题节点（有限集合）
// ============================================================
CREATE (tp:Topic {
  name: "事业",
  category: "life",
  keywords: ["工作", "升职", "创业", "领导"]
})
```

### 3.3 关系定义

```cypher
// ============================================================
// 五行关系（静态，10 条边）
// ============================================================
// 相生（5 条）
MATCH (a:Element {name:"木"}), (b:Element {name:"火"}) CREATE (a)-[:GENERATES {cycle:"相生", description:"木生火"}]->(b)
MATCH (a:Element {name:"火"}), (b:Element {name:"土"}) CREATE (a)-[:GENERATES {cycle:"相生", description:"火生土"}]->(b)
MATCH (a:Element {name:"土"}), (b:Element {name:"金"}) CREATE (a)-[:GENERATES {cycle:"相生", description:"土生金"}]->(b)
MATCH (a:Element {name:"金"}), (b:Element {name:"水"}) CREATE (a)-[:GENERATES {cycle:"相生", description:"金生水"}]->(b)
MATCH (a:Element {name:"水"}), (b:Element {name:"木"}) CREATE (a)-[:GENERATES {cycle:"相生", description:"水生木"}]->(b)

// 相克（5 条）
MATCH (a:Element {name:"木"}), (b:Element {name:"土"}) CREATE (a)-[:RESTRAINS {cycle:"相克", description:"木克土"}]->(b)
MATCH (a:Element {name:"土"}), (b:Element {name:"水"}) CREATE (a)-[:RESTRAINS {cycle:"相克", description:"土克水"}]->(b)
MATCH (a:Element {name:"水"}), (b:Element {name:"火"}) CREATE (a)-[:RESTRAINS {cycle:"相克", description:"水克火"}]->(b)
MATCH (a:Element {name:"火"}), (b:Element {name:"金"}) CREATE (a)-[:RESTRAINS {cycle:"相克", description:"火克金"}]->(b)
MATCH (a:Element {name:"金"}), (b:Element {name:"木"}) CREATE (a)-[:RESTRAINS {cycle:"相克", description:"金克木"}]->(b)

// ============================================================
// 卦爻关系（64 * 6 = 384 条）
// ============================================================
MATCH (h:Hexagram {name:"乾"}), (l:Line {position:1})
WHERE l IN (lines_of_qian) // 实际通过数据导入脚本关联
CREATE (h)-[:HAS_LINE {position: 1}]->(l)

// ============================================================
// 卦-八卦关系（64 * 2 = 128 条）
// ============================================================
MATCH (h:Hexagram {name:"乾"}), (t:Trigram {name:"乾"})
CREATE (h)-[:HAS_UPPER]->(t)
CREATE (h)-[:HAS_LOWER]->(t)

// ============================================================
// 卦变关系（约 400+ 条）
// ============================================================
// 错卦（阴阳相反）
MATCH (a:Hexagram {name:"乾"}), (b:Hexagram {name:"坤"})
CREATE (a)-[:OPPOSITE_OF {description:"错卦，阴阳全反"}]->(b)

// 综卦（上下颠倒）
MATCH (a:Hexagram {name:"屯"}), (b:Hexagram {name:"蒙"})
CREATE (a)-[:REVERSES_TO {description:"综卦，上下颠倒"}]->(b)

// 互卦（取二三四五爻）
MATCH (a:Hexagram {name:"乾"}), (b:Hexagram {name:"乾"})
CREATE (a)-[:MUTUAL_WITH {description:"互卦"}]->(b)

// 变卦（动爻变化）
MATCH (a:Hexagram {name:"乾"}), (b:Hexagram {name:"姤"})
CREATE (a)-[:TRANSFORMS_TO {moving_lines:[1], description:"初爻变"}]->(b)

// ============================================================
// 爻-六亲关系
// ============================================================
MATCH (l:Line), (r:Role {name:"兄弟"})
WHERE l.six_relative = "兄弟"
CREATE (l)-[:HAS_ROLE]->(r)

// ============================================================
// 爻-五行关系
// ============================================================
MATCH (l:Line)-[:NAIJIA]->(eb:EarthlyBranch)
CREATE (l)-[:HAS_ELEMENT]->(eb.element)

// ============================================================
// 爻-天干地支关系（纳甲）
// ============================================================
MATCH (l:Line {position:1}), (hs:HeavenlyStem {name:"甲"}), (eb:EarthlyBranch {name:"子"})
CREATE (l)-[:NAIJIA {stem:"甲", branch:"子"}]->(hs)
CREATE (l)-[:NAIJIA {stem:"甲", branch:"子"}]->(eb)

// ============================================================
// 地支冲合关系（6 冲 + 6 合 + 三合局）
// ============================================================
// 六冲
MATCH (a:EarthlyBranch {name:"子"}), (b:EarthlyBranch {name:"午"})
CREATE (a)-[:CLASHES_WITH {type:"六冲"}]->(b)
CREATE (b)-[:CLASHES_WITH {type:"六冲"}]->(a)

// 六合
MATCH (a:EarthlyBranch {name:"子"}), (b:EarthlyBranch {name:"丑"})
CREATE (a)-[:COMBINES_WITH {type:"六合", generates:"土"}]->(b)
CREATE (b)-[:COMBINES_WITH {type:"六合", generates:"土"}]->(a)

// 三合（以申子辰合水局为例）
MATCH (a:EarthlyBranch {name:"申"}), (b:EarthlyBranch {name:"子"}), (c:EarthlyBranch {name:"辰"})
CREATE (a)-[:THREE_HARMONY {type:"三合", element:"水"}]->(b)
CREATE (b)-[:THREE_HARMONY {type:"三合", element:"水"}]->(c)
CREATE (c)-[:THREE_HARMONY {type:"三合", element:"水"}]->(a)

// ============================================================
// 用户动态关系
// ============================================================
// 用户 → 卦记录
MATCH (u:User {user_id:$uid}), (dr:DivinationRecord {record_id:$rid})
CREATE (u)-[:QUERIED {timestamp: datetime()}]->(dr)

// 卦记录 → 结果卦
MATCH (dr:DivinationRecord {record_id:$rid}), (h:Hexagram {name:"乾"})
CREATE (dr)-[:RESULTED_IN]->(h)

// 卦记录 → 变卦
MATCH (dr:DivinationRecord), (h:Hexagram {name:"姤"})
WHERE dr.moving_lines IS NOT NULL
CREATE (dr)-[:CHANGED_TO]->(h)

// 卦记录 → 主题
MATCH (dr:DivinationRecord), (tp:Topic {name:"事业"})
CREATE (dr)-[:ABOUT_TOPIC]->(tp)

// 用户 → 主题偏好（带权重）
MATCH (u:User), (tp:Topic {name:"事业"})
CREATE (u)-[:INTERESTED_IN {weight: 0.45, count: 45}]->(tp)

// 用户 → 五行偏好
MATCH (u:User), (e:Element {name:"木"})
CREATE (u)-[:PREFERS_ELEMENT {weight: 0.3, count: 30}]->(e)
```

### 3.4 索引与约束

```cypher
// ============================================================
// 唯一约束
// ============================================================
CREATE CONSTRAINT hex_name IF NOT EXISTS FOR (h:Hexagram) REQUIRE h.name IS UNIQUE;
CREATE CONSTRAINT hex_number IF NOT EXISTS FOR (h:Hexagram) REQUIRE h.number IS UNIQUE;
CREATE CONSTRAINT hex_binary IF NOT EXISTS FOR (h:Hexagram) REQUIRE h.binary IS UNIQUE;
CREATE CONSTRAINT tri_name IF NOT EXISTS FOR (t:Trigram) REQUIRE t.name IS UNIQUE;
CREATE CONSTRAINT tri_binary IF NOT EXISTS FOR (t:Trigram) REQUIRE t.binary IS UNIQUE;
CREATE CONSTRAINT elem_name IF NOT EXISTS FOR (e:Element) REQUIRE e.name IS UNIQUE;
CREATE CONSTRAINT role_name IF NOT EXISTS FOR (r:Role) REQUIRE r.name IS UNIQUE;
CREATE CONSTRAINT spirit_name IF NOT EXISTS FOR (s:Spirit) REQUIRE s.name IS UNIQUE;
CREATE CONSTRAINT stem_name IF NOT EXISTS FOR (hs:HeavenlyStem) REQUIRE hs.name IS UNIQUE;
CREATE CONSTRAINT branch_name IF NOT EXISTS FOR (eb:EarthlyBranch) REQUIRE eb.name IS UNIQUE;
CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE;
CREATE CONSTRAINT record_id IF NOT EXISTS FOR (dr:DivinationRecord) REQUIRE dr.record_id IS UNIQUE;
CREATE CONSTRAINT topic_name IF NOT EXISTS FOR (tp:Topic) REQUIRE tp.name IS UNIQUE;

// ============================================================
// 性能索引
// ============================================================
CREATE INDEX hex_element IF NOT EXISTS FOR (h:Hexagram) ON (h.element);
CREATE INDEX hex_upper IF NOT EXISTS FOR (h:Hexagram) ON (h.upper_trigram);
CREATE INDEX hex_lower IF NOT EXISTS FOR (h:Hexagram) ON (h.lower_trigram);
CREATE INDEX line_pos IF NOT EXISTS FOR (l:Line) ON (l.position);
CREATE INDEX line_relative IF NOT EXISTS FOR (l:Line) ON (l.six_relative);
CREATE INDEX record_ts IF NOT EXISTS FOR (dr:DivinationRecord) ON (dr.timestamp);
CREATE INDEX record_sentiment IF NOT EXISTS FOR (dr:DivinationRecord) ON (dr.sentiment);
CREATE INDEX record_topic IF NOT EXISTS FOR (dr:DivinationRecord) ON (dr.question_topic);

// ============================================================
// 全文索引
// ============================================================
CREATE FULLTEXT INDEX hex_text IF NOT EXISTS
  FOR (h:Hexagram) ON EACH [h.judgement, h.image, h.modern_summary];
CREATE FULLTEXT INDEX line_text IF NOT EXISTS
  FOR (l:Line) ON EACH [l.text, l.image_text];
CREATE FULLTEXT INDEX record_q IF NOT EXISTS
  FOR (dr:DivinationRecord) ON EACH [dr.question];
```

### 3.5 高频查询模板

```cypher
// Q1: 以卦为中心的完整关系图（2 跳）
MATCH path = (h:Hexagram {name: $name})-[*1..2]-(related)
RETURN nodes(path) AS nodes, relationships(path) AS rels
LIMIT 100

// Q2: 五行关系链（以某行为中心）
MATCH (e:Element {name: $element})
OPTIONAL MATCH (e)<-[:GENERATES]-(g:Element)
OPTIONAL MATCH (e)-[:GENERATES]->(s:Element)
OPTIONAL MATCH (e)<-[:RESTRAINS]-(r:Element)
OPTIONAL MATCH (e)-[:RESTRAINS]->(rs:Element)
RETURN e.name, g.name AS 生我, s.name AS 我生, r.name AS 克我, rs.name AS 我克

// Q3: 用户近期卦象轨迹
MATCH (u:User {user_id: $uid})-[:QUERIED]->(dr:DivinationRecord)-[:RESULTED_IN]->(h:Hexagram)
WHERE dr.timestamp > datetime() - duration({days: 30})
RETURN h.name, dr.timestamp, dr.question_topic, dr.sentiment
ORDER BY dr.timestamp DESC

// Q4: 用户五行偏好分析
MATCH (u:User {user_id: $uid})-[:QUERIED]->(dr:DivinationRecord)-[:RESULTED_IN]->(h:Hexagram)
WITH h.element AS elem, count(*) AS freq
RETURN elem, freq ORDER BY freq DESC

// Q5: 相似卦查找（共享上卦或下卦）
MATCH (h:Hexagram {name: $name})-[:HAS_UPPER]->(t)<-[:HAS_UPPER]-(similar)
WHERE similar <> h
RETURN collect(similar.name) AS same_upper

// Q6: 卦变路径（本卦到变卦的完整变化链）
MATCH (h:Hexagram {name: $name})
OPTIONAL MATCH (h)-[:TRANSFORMS_TO]->(changed)
OPTIONAL MATCH (h)-[:OPPOSITE_OF]->(opposite)
OPTIONAL MATCH (h)-[:REVERSES_TO]->(reverse)
OPTIONAL MATCH (h)-[:MUTUAL_WITH]->(mutual)
RETURN h, changed, opposite, reverse, mutual

// Q7: 主题关联的高频卦象
MATCH (tp:Topic {name: $topic})<-[:ABOUT_TOPIC]-(dr:DivinationRecord)-[:RESULTED_IN]->(h:Hexagram)
WITH h.name AS hex, count(*) AS freq
RETURN hex, freq ORDER BY freq DESC LIMIT 10

// Q8: 用户情绪与卦象的关联
MATCH (u:User {user_id: $uid})-[:QUERIED]->(dr:DivinationRecord)-[:RESULTED_IN]->(h:Hexagram)
WHERE dr.timestamp > datetime() - duration({days: 90})
RETURN h.name, dr.sentiment, count(*) AS occurrences
ORDER BY occurrences DESC
```

---

## 4. Qdrant 集合设计

### 4.1 集合总览

| Collection | 内容 | Embedding 模型 | 维度 | 距离度量 | 预估文档数 |
|-----------|------|---------------|------|---------|-----------|
| `yijing_texts` | 易经原文（卦辞、爻辞、象辞） | bge-m3 | 1024 | Cosine | ~500 |
| `commentaries` | 历代注释（王弼、程颐、朱熹） | bge-m3 | 1024 | Cosine | ~3,000 |
| `modern_explanations` | 白话文解释、现代案例 | bge-m3 | 1024 | Cosine | ~2,000 |
| `five_elements_rules` | 五行生克、旺衰规则 | jina-embeddings-v3 | 1024 | Cosine | ~800 |
| `divination_cases` | 历史卦例、解卦记录 | bge-m3 | 1024 | Cosine | ~50,000 |
| `user_history` | 用户历史卦记录（私有） | jina-embeddings-v3 | 1024 | Cosine | 100,000+ |

### 4.2 集合详细设计

```python
# qdrant_schema.py

from qdrant_client.models import (
    Distance, VectorParams, PayloadSchemaType,
    PayloadIndexParams, OptimizersConfigDiff,
    HnswConfigDiff, ScalarQuantizationConfig,
    ScalarType
)

# ============================================================
# Collection 1: yijing_texts（易经原文）
# ============================================================
YIJING_TEXTS_CONFIG = {
    "collection_name": "yijing_texts",
    "vectors_config": VectorParams(
        size=1024,
        distance=Distance.COSINE,
        on_disk=True,                    # 向量存磁盘，节省内存
    ),
    "optimizers_config": OptimizersConfigDiff(
        indexing_threshold=1000,          # 索引触发阈值
        memmap_threshold=20000,           # 内存映射阈值
    ),
    "hnsw_config": HnswConfigDiff(
        m=16,                             # HNSM 连接数
        ef_construct=100,                 # 构建时的搜索宽度
        on_disk=True,
    ),
}

# Payload 索引
YIJING_TEXTS_PAYLOAD_INDEXES = [
    {"field_name": "hexagram_name", "field_type": PayloadSchemaType.KEYWORD},
    {"field_name": "hexagram_id", "field_type": PayloadSchemaType.INTEGER},
    {"field_name": "line_position", "field_type": PayloadSchemaType.INTEGER},
    {"field_name": "text_type", "field_type": PayloadSchemaType.KEYWORD},
    # text_type: "judgement" | "image" | "tuan" | "line_text" | "line_image"
    {"field_name": "source", "field_type": PayloadSchemaType.KEYWORD},
    {"field_name": "chapter", "field_type": PayloadSchemaType.KEYWORD},
]

# Payload 结构示例
YIJING_TEXTS_PAYLOAD_EXAMPLE = {
    "hexagram_name": "乾",
    "hexagram_id": 1,
    "line_position": None,                # 卦辞为 None，爻辞为 1-6
    "text_type": "judgement",
    "text": "乾：元亨利贞。",
    "source": "周易原文",
    "chapter": "上经",
    "tags": ["乾", "纯阳", "天"],
}


# ============================================================
# Collection 2: commentaries（历代注释）
# ============================================================
COMMENTARIES_CONFIG = {
    "collection_name": "commentaries",
    "vectors_config": VectorParams(size=1024, distance=Distance.COSINE, on_disk=True),
}

COMMENTARIES_PAYLOAD_INDEXES = [
    {"field_name": "hexagram_name", "field_type": PayloadSchemaType.KEYWORD},
    {"field_name": "author", "field_type": PayloadSchemaType.KEYWORD},
    # author: "王弼" | "程颐" | "朱熹" | "来知德" | "尚秉和"
    {"field_name": "dynasty", "field_type": PayloadSchemaType.KEYWORD},
    # dynasty: "魏" | "宋" | "明" | "清"
    {"field_name": "line_position", "field_type": PayloadSchemaType.INTEGER},
    {"field_name": "commentary_type", "field_type": PayloadSchemaType.KEYWORD},
    # commentary_type: "philosophical" | "practical" | "cosmological"
    {"field_name": "keywords", "field_type": PayloadSchemaType.KEYWORD, is_tenant=True},
]


# ============================================================
# Collection 3: modern_explanations（现代白话解释）
# ============================================================
MODERN_EXPLANATIONS_CONFIG = {
    "collection_name": "modern_explanations",
    "vectors_config": VectorParams(size=1024, distance=Distance.COSINE, on_disk=True),
}

MODERN_EXPLANATIONS_PAYLOAD_INDEXES = [
    {"field_name": "hexagram_name", "field_type": PayloadSchemaType.KEYWORD},
    {"field_name": "line_position", "field_type": PayloadSchemaType.INTEGER},
    {"field_name": "difficulty_level", "field_type": PayloadSchemaType.KEYWORD},
    # difficulty_level: "beginner" | "intermediate" | "advanced"
    {"field_name": "style", "field_type": PayloadSchemaType.KEYWORD},
    # style: "academic" | "casual" | "practical"
    {"field_name": "source_book", "field_type": PayloadSchemaType.KEYWORD},
]


# ============================================================
# Collection 4: five_elements_rules（五行规则）
# ============================================================
FIVE_ELEMENTS_CONFIG = {
    "collection_name": "five_elements_rules",
    "vectors_config": VectorParams(size=1024, distance=Distance.COSINE, on_disk=True),
}

FIVE_ELEMENTS_PAYLOAD_INDEXES = [
    {"field_name": "rule_type", "field_type": PayloadSchemaType.KEYWORD},
    # rule_type: "generate" | "restrain" | "prosper" | "decline" | "clash" | "combine" | "punishment"
    {"field_name": "element_a", "field_type": PayloadSchemaType.KEYWORD},
    {"field_name": "element_b", "field_type": PayloadSchemaType.KEYWORD},
    {"field_name": "application", "field_type": PayloadSchemaType.KEYWORD},
    # application: "divination" | "fengshui" | "medicine" | "general"
    {"field_name": "confidence", "field_type": PayloadSchemaType.FLOAT},
]


# ============================================================
# Collection 5: divination_cases（历史卦例）
# ============================================================
DIVINATION_CASES_CONFIG = {
    "collection_name": "divination_cases",
    "vectors_config": VectorParams(size=1024, distance=Distance.COSINE, on_disk=True),
    "optimizers_config": OptimizersConfigDiff(
        indexing_threshold=5000,
        memmap_threshold=50000,
    ),
}

DIVINATION_CASES_PAYLOAD_INDEXES = [
    {"field_name": "hexagram_name", "field_type": PayloadSchemaType.KEYWORD},
    {"field_name": "changed_hexagram", "field_type": PayloadSchemaType.KEYWORD},
    {"field_name": "question_topic", "field_type": PayloadSchemaType.KEYWORD},
    {"field_name": "sentiment", "field_type": PayloadSchemaType.KEYWORD},
    {"field_name": "result_accuracy", "field_type": PayloadSchemaType.FLOAT},
    {"field_name": "is_classic", "field_type": PayloadSchemaType.BOOL},
    # is_classic: true 表示古籍经典卦例
    {"field_name": "time_period", "field_type": PayloadSchemaType.KEYWORD},
]


# ============================================================
# Collection 6: user_history（用户历史，私有）
# ============================================================
USER_HISTORY_CONFIG = {
    "collection_name": "user_history",
    "vectors_config": VectorParams(size=1024, distance=Distance.COSINE, on_disk=True),
    "optimizers_config": OptimizersConfigDiff(
        indexing_threshold=10000,
        memmap_threshold=100000,
    ),
}

USER_HISTORY_PAYLOAD_INDEXES = [
    {"field_name": "user_id", "field_type": PayloadSchemaType.KEYWORD},  # 关键过滤字段
    {"field_name": "record_id", "field_type": PayloadSchemaType.KEYWORD},
    {"field_name": "hexagram_name", "field_type": PayloadSchemaType.KEYWORD},
    {"field_name": "question_topic", "field_type": PayloadSchemaType.KEYWORD},
    {"field_name": "sentiment", "field_type": PayloadSchemaType.KEYWORD},
    {"field_name": "timestamp", "field_type": PayloadSchemaType.DATETIME},
    {"field_name": "is_bookmarked", "field_type": PayloadSchemaType.BOOL},
]
```

### 4.3 检索策略

```python
# qdrant_retrieval.py

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range

class VectorRetriever:
    """向量检索器，支持跨 Collection 检索和过滤。"""

    def __init__(self, client: QdrantClient):
        self.client = client
        self.collections = [
            "yijing_texts",
            "commentaries",
            "modern_explanations",
            "five_elements_rules",
            "divination_cases",
        ]

    async def search(
        self,
        query_vector: list[float],
        hexagram_context: dict | None = None,
        user_id: str | None = None,
        top_k: int = 10,
        score_threshold: float = 0.65,
    ) -> list[dict]:
        """跨 Collection 检索，带上下文过滤。"""

        all_results = []

        # 根据上下文选择目标 Collections
        targets = self._select_targets(hexagram_context)

        for collection in targets:
            search_filter = self._build_filter(collection, hexagram_context, user_id)

            results = self.client.search(
                collection_name=collection,
                query_vector=query_vector,
                query_filter=search_filter,
                limit=top_k,
                score_threshold=score_threshold,
                with_payload=True,
            )

            for r in results:
                all_results.append({
                    "id": str(r.id),
                    "score": r.score,
                    "payload": r.payload,
                    "source": collection,
                })

        # 按 score 排序
        all_results.sort(key=lambda x: x["score"], reverse=True)
        return all_results[:top_k * 2]

    async def search_user_history(
        self,
        user_id: str,
        query_vector: list[float],
        top_k: int = 5,
        days: int = 90,
    ) -> list[dict]:
        """用户历史向量检索（隔离用户数据）。"""

        import datetime
        cutoff = (datetime.datetime.utcnow() - datetime.timedelta(days=days)).isoformat()

        search_filter = Filter(must=[
            FieldCondition(key="user_id", match=MatchValue(value=user_id)),
            FieldCondition(key="timestamp", range=Range(gte=cutoff)),
        ])

        results = self.client.search(
            collection_name="user_history",
            query_vector=query_vector,
            query_filter=search_filter,
            limit=top_k,
            with_payload=True,
        )

        return [{"id": str(r.id), "score": r.score, "payload": r.payload} for r in results]

    def _select_targets(self, context: dict | None) -> list[str]:
        """根据上下文动态选择检索目标。"""
        if context is None:
            return self.collections

        targets = ["yijing_texts"]
        if context.get("hexagram_name"):
            targets.extend(["commentaries", "five_elements_rules"])
        if context.get("include_cases"):
            targets.append("divination_cases")
        if context.get("include_modern"):
            targets.append("modern_explanations")
        return targets

    def _build_filter(
        self,
        collection: str,
        context: dict | None,
        user_id: str | None,
    ) -> Filter | None:
        """构建 Collection 特定的过滤条件。"""
        conditions = []

        if context and context.get("hexagram_name"):
            conditions.append(
                FieldCondition(key="hexagram_name", match=MatchValue(value=context["hexagram_name"]))
            )

        if collection == "user_history" and user_id:
            conditions.append(
                FieldCondition(key="user_id", match=MatchValue(value=user_id))
            )

        if context and context.get("line_position"):
            conditions.append(
                FieldCondition(key="line_position", match=MatchValue(value=context["line_position"]))
            )

        return Filter(must=conditions) if conditions else None
```

### 4.4 量化与性能优化

```python
# qdrant_optimization.py

from qdrant_client.models import ScalarQuantizationConfig, ScalarType

# 标量量化配置（降低内存占用 4x，精度损失 <1%）
SCALAR_QUANTIZATION = ScalarQuantizationConfig(
    scalar=ScalarType.INT8,
    always_ram=True,                      # 量化后仍在内存中
)

# 对大数据集 Collection 应用量化
LARGE_COLLECTIONS = ["divination_cases", "user_history"]

def apply_quantization(client: QdrantClient):
    for collection in LARGE_COLLECTIONS:
        client.update_collection(
            collection_name=collection,
            quantization_config=SCALAR_QUANTIZATION,
        )
```

---

## 5. Redis 缓存策略

### 5.1 Key 命名规范

```
{业务域}:{实体}:{标识}:{子资源}

示例：
  session:{session_id}:data
  user:{user_id}:profile
  hexagram:乾:full
  cache:hot:hexagram:{hexagram_name}
  ratelimit:{user_id}:divination
  lock:divination:{user_id}
```

### 5.2 Key 设计明细

```python
# redis_keys.py

from dataclasses import dataclass
from datetime import timedelta

@dataclass
class RedisKeyPattern:
    pattern: str
    ttl: timedelta | None
    description: str
    data_type: str            # string / hash / list / set / sorted_set / stream

KEY_REGISTRY: dict[str, RedisKeyPattern] = {

    # ============================================================
    # 会话与认证
    # ============================================================
    "session:{session_id}:data": RedisKeyPattern(
        pattern="session:{session_id}:data",
        ttl=timedelta(hours=24),
        description="用户会话数据（JWT payload + 设备信息）",
        data_type="hash",
    ),
    "session:{session_id}:memory": RedisKeyPattern(
        pattern="session:{session_id}:memory",
        ttl=timedelta(hours=2),
        description="工作记忆（当前会话的上下文、中间推理结果）",
        data_type="string",   # JSON 序列化
    ),
    "token:blacklist:{jti}": RedisKeyPattern(
        pattern="token:blacklist:{jti}",
        ttl=timedelta(hours=24),
        description="JWT 黑名单（已注销的 token）",
        data_type="string",
    ),

    # ============================================================
    # 用户数据缓存
    # ============================================================
    "user:{user_id}:profile": RedisKeyPattern(
        pattern="user:{user_id}:profile",
        ttl=timedelta(minutes=30),
        description="用户画像缓存",
        data_type="hash",
    ),
    "user:{user_id}:recent": RedisKeyPattern(
        pattern="user:{user_id}:recent",
        ttl=timedelta(minutes=15),
        description="用户最近 10 条卦记录摘要",
        data_type="list",
    ),
    "user:{user_id}:credits": RedisKeyPattern(
        pattern="user:{user_id}:credits",
        ttl=timedelta(hours=1),
        description="用户剩余额度",
        data_type="hash",
    ),

    # ============================================================
    # 静态知识缓存（长 TTL，手动失效）
    # ============================================================
    "hexagram:{hexagram_name}:full": RedisKeyPattern(
        pattern="hexagram:{hexagram_name}:full",
        ttl=timedelta(days=7),
        description="卦的完整数据（卦辞、爻辞、五行、纳甲）",
        data_type="string",   # JSON
    ),
    "hexagram:{hexagram_name}:relations": RedisKeyPattern(
        pattern="hexagram:{hexagram_name}:relations",
        ttl=timedelta(days=7),
        description="卦变关系（错综互变）",
        data_type="string",   # JSON
    ),
    "element:{element_name}:relations": RedisKeyPattern(
        pattern="element:{element_name}:relations",
        ttl=timedelta(days=30),
        description="五行生克关系",
        data_type="hash",
    ),
    "trigram:{trigram_name}:data": RedisKeyPattern(
        pattern="trigram:{trigram_name}:data",
        ttl=timedelta(days=30),
        description="八卦完整数据",
        data_type="hash",
    ),

    # ============================================================
    # 热点查询缓存
    # ============================================================
    "cache:interpretation:{hash}": RedisKeyPattern(
        pattern="cache:interpretation:{content_hash}",
        ttl=timedelta(hours=6),
        description="AI 解释缓存（相同输入的解释结果）",
        data_type="string",
    ),
    "cache:rag:{hash}": RedisKeyPattern(
        pattern="cache:rag:{query_hash}",
        ttl=timedelta(hours=1),
        description="RAG 检索结果缓存",
        data_type="string",   # JSON
    ),
    "cache:embedding:{hash}": RedisKeyPattern(
        pattern="cache:embedding:{text_hash}",
        ttl=timedelta(days=7),
        description="Embedding 向量缓存",
        data_type="string",   # JSON array
    ),

    # ============================================================
    # 频率限制
    # ============================================================
    "ratelimit:{user_id}:{action}": RedisKeyPattern(
        pattern="ratelimit:{user_id}:{action}",
        ttl=None,             # 由限流算法动态设置
        description="用户操作频率限制",
        data_type="string",   # 计数器
    ),

    # ============================================================
    # 分布式锁
    # ============================================================
    "lock:divination:{user_id}": RedisKeyPattern(
        pattern="lock:divination:{user_id}",
        ttl=timedelta(seconds=30),
        description="起卦操作锁（防重复提交）",
        data_type="string",
    ),
    "lock:profile_update:{user_id}": RedisKeyPattern(
        pattern="lock:profile_update:{user_id}",
        ttl=timedelta(seconds=10),
        description="画像更新锁",
        data_type="string",
    ),

    # ============================================================
    # 统计计数器
    # ============================================================
    "stats:daily:{date}:divinations": RedisKeyPattern(
        pattern="stats:daily:{YYYY-MM-DD}:divinations",
        ttl=timedelta(days=2),
        description="每日卦数统计",
        data_type="string",
    ),
    "stats:daily:{date}:users": RedisKeyPattern(
        pattern="stats:daily:{YYYY-MM-DD}:active_users",
        ttl=timedelta(days=2),
        description="每日活跃用户集合",
        data_type="set",
    ),
    "stats:user:{user_id}:daily:{date}": RedisKeyPattern(
        pattern="stats:user:{user_id}:daily:{YYYY-MM-DD}",
        ttl=timedelta(hours=48),
        description="用户每日操作计数",
        data_type="hash",
    ),

    # ============================================================
    # 消息队列（用于异步任务）
    # ============================================================
    "queue:async_tasks": RedisKeyPattern(
        pattern="queue:async_tasks",
        ttl=None,
        description="异步任务队列（画像更新、记忆衰减、ClickHouse 写入）",
        data_type="list",
    ),
    "stream:events": RedisKeyPattern(
        pattern="stream:events",
        ttl=timedelta(days=3),
        description="事件流（用于异步消费）",
        data_type="stream",
    ),
}
```

### 5.3 缓存策略详解

```python
# cache_strategy.py

import hashlib
import json
from datetime import timedelta

class CacheStrategy:
    """YI-AI 缓存策略实现。"""

    def __init__(self, redis_client):
        self.redis = redis_client

    # ============================================================
    # Cache-Aside 模式（用户画像、卦数据）
    # ============================================================

    async def get_user_profile(self, user_id: str) -> dict | None:
        """Cache-Aside: 先读缓存，未命中再读 PG 并回填。"""
        cache_key = f"user:{user_id}:profile"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        # 缓存未命中，从 PG 读取
        profile = await self._load_profile_from_pg(user_id)
        if profile:
            await self.redis.setex(
                cache_key,
                timedelta(minutes=30),
                json.dumps(profile, ensure_ascii=False),
            )
        return profile

    async def invalidate_user_profile(self, user_id: str):
        """用户画像更新时，主动失效缓存。"""
        await self.redis.delete(f"user:{user_id}:profile")
        await self.redis.delete(f"user:{user_id}:recent")

    # ============================================================
    # Write-Through 模式（卦记录写入时同步更新缓存）
    # ============================================================

    async def save_divination_record(self, record: dict):
        """Write-Through: 同时写 PG 和更新 Redis 缓存。"""
        # 写入 PG
        await self._save_to_pg(record)

        # 更新 Redis（最近记录列表）
        user_id = record["user_id"]
        recent_key = f"user:{user_id}:recent"
        await self.redis.lpush(recent_key, json.dumps({
            "id": record["id"],
            "hexagram": record["hexagram_name"],
            "question": record["question"][:50],
            "time": record["created_at"].isoformat(),
        }, ensure_ascii=False))
        await self.redis.ltrim(recent_key, 0, 9)  # 保留最近 10 条
        await self.redis.expire(recent_key, 900)    # 15 分钟 TTL

        # 失效相关缓存
        await self.invalidate_user_profile(user_id)

    # ============================================================
    # 热点缓存（静态知识）
    # ============================================================

    async def get_hexagram_full(self, hexagram_name: str) -> dict:
        """获取卦的完整数据（高频访问，7天 TTL）。"""
        cache_key = f"hexagram:{hexagram_name}:full"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        data = await self._load_hexagram_from_pg(hexagram_name)
        if data:
            await self.redis.setex(
                cache_key,
                timedelta(days=7),
                json.dumps(data, ensure_ascii=False),
            )
        return data

    # ============================================================
    # AI 结果缓存（相同输入复用）
    # ============================================================

    async def get_cached_interpretation(
        self,
        hexagram_name: str,
        question: str,
        time_ganzhi: dict,
    ) -> str | None:
        """获取缓存的 AI 解释（相同输入 6 小时内复用）。"""
        cache_key = self._make_interpretation_key(hexagram_name, question, time_ganzhi)
        return await self.redis.get(cache_key)

    async def cache_interpretation(
        self,
        hexagram_name: str,
        question: str,
        time_ganzhi: dict,
        interpretation: str,
    ):
        """缓存 AI 解释结果。"""
        cache_key = self._make_interpretation_key(hexagram_name, question, time_ganzhi)
        await self.redis.setex(cache_key, timedelta(hours=6), interpretation)

    def _make_interpretation_key(self, hexagram: str, question: str, ganzhi: dict) -> str:
        """生成解释缓存 key（相同卦 + 问题 + 时间 = 相同 key）。"""
        content = f"{hexagram}:{question}:{json.dumps(ganzhi, sort_keys=True)}"
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        return f"cache:interpretation:{content_hash}"

    # ============================================================
    # Embedding 缓存（避免重复计算）
    # ============================================================

    async def get_cached_embedding(self, text: str) -> list[float] | None:
        """获取缓存的 Embedding。"""
        text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        cached = await self.redis.get(f"cache:embedding:{text_hash}")
        if cached:
            return json.loads(cached)
        return None

    async def cache_embedding(self, text: str, embedding: list[float]):
        """缓存 Embedding 向量。"""
        text_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        await self.redis.setex(
            f"cache:embedding:{text_hash}",
            timedelta(days=7),
            json.dumps(embedding),
        )

    # ============================================================
    # 频率限制（滑动窗口）
    # ============================================================

    async def check_rate_limit(
        self,
        user_id: str,
        action: str,
        max_count: int,
        window_seconds: int,
    ) -> tuple[bool, int]:
        """
        滑动窗口频率限制。
        返回: (是否允许, 剩余次数)
        """
        key = f"ratelimit:{user_id}:{action}"
        now = await self.redis.time()
        window_start = now[0] - window_seconds

        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)  # 移除窗口外的记录
        pipe.zadd(key, {str(now[0]): now[0]})         # 添加当前请求
        pipe.zcard(key)                                # 统计窗口内请求数
        pipe.expire(key, window_seconds)               # 设置 TTL
        results = await pipe.execute()

        current_count = results[2]
        allowed = current_count <= max_count
        remaining = max(0, max_count - current_count)

        return allowed, remaining

    # ============================================================
    # 工作记忆（会话级）
    # ============================================================

    async def get_working_memory(self, session_id: str) -> dict:
        """获取当前会话的工作记忆。"""
        data = await self.redis.get(f"session:{session_id}:memory")
        return json.loads(data) if data else {}

    async def update_working_memory(self, session_id: str, updates: dict):
        """更新工作记忆（合并更新）。"""
        current = await self.get_working_memory(session_id)
        current.update(updates)
        current["last_updated"] = datetime.utcnow().isoformat()
        await self.redis.setex(
            f"session:{session_id}:memory",
            timedelta(hours=2),
            json.dumps(current, ensure_ascii=False),
        )
```

### 5.4 淘汰策略

```
Redis 内存淘汰策略配置 (redis.conf):

maxmemory 4gb
maxmemory-policy allkeys-lfu

# LFU (Least Frequently Used) 策略：
# - 优先淘汰访问频率最低的 key
# - 适合 YI-AI 场景：静态知识 key 高频访问不会被淘汰
# - 冷门用户缓存自然淘汰

# 各类 key 的 TTL 设计确保自然过期：
# - 会话数据: 24h
# - 用户画像: 30min
# - 静态知识: 7-30d
# - AI 缓存: 6h
# - Embedding: 7d
# - 频率限制: 动态
```

---

## 6. ClickHouse 日志设计

### 6.1 表设计

```sql
-- ============================================================
-- 数据库
-- ============================================================
CREATE DATABASE IF NOT EXISTS yiai_analytics;

-- ============================================================
-- 1. 请求日志表（每次 API 请求一条）
-- ============================================================
CREATE TABLE yiai_analytics.api_requests (
    -- 请求标识
    request_id      UUID,
    user_id         UUID,
    session_id      UUID,

    -- 请求信息
    method          LowCardinality(String),        -- GET/POST/WS
    path            String,                        -- /api/v1/divination
    endpoint        LowCardinality(String),        -- 归一化端点
    status_code     UInt16,
    error_code      Nullable(String),

    -- 性能指标
    duration_ms     UInt32,                        -- 总耗时
    ttft_ms         Nullable(UInt32),              -- 首 token 时间（流式）
    db_time_ms      UInt32 DEFAULT 0,              -- 数据库耗时
    ai_time_ms      UInt32 DEFAULT 0,              -- AI 调用耗时
    rag_time_ms     UInt32 DEFAULT 0,              -- RAG 检索耗时

    -- AI 相关
    ai_model        Nullable(String),              -- 使用的模型
    ai_tier         Nullable(String),              -- Tier 1-4
    ai_tokens_input UInt32 DEFAULT 0,
    ai_tokens_output UInt32 DEFAULT 0,
    ai_cost_usd     Float64 DEFAULT 0,

    -- 用户信息
    platform        LowCardinality(String),        -- ios/android/web
    app_version     String DEFAULT '',
    ip_country      LowCardinality(String),
    ip_city         String DEFAULT '',

    -- 时间
    created_at      DateTime DEFAULT now(),

    -- 分区键
    _date           Date DEFAULT toDate(created_at)
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(_date)
ORDER BY (endpoint, user_id, created_at)
TTL created_at + INTERVAL 12 MONTH DELETE
SETTINGS index_granularity = 8192;


-- ============================================================
-- 2. 卦事件表（每次起卦/解释/反馈一条）
-- ============================================================
CREATE TABLE yiai_analytics.divination_events (
    event_id        UUID,
    user_id         UUID,
    record_id       UUID,
    session_id      UUID,

    -- 事件类型
    event_type      LowCardinality(String),
    -- 'hexagram_generated', 'interpretation_viewed', 'feedback_given',
    -- 'bookmark', 'share', 'export', 'follow_up_question'

    -- 卦象数据
    hexagram_name   LowCardinality(String),
    changed_hexagram Nullable(LowCardinality(String)),
    question_topic  LowCardinality(String),
    divination_method LowCardinality(String),

    -- AI 数据
    ai_model        Nullable(String),
    ai_tier         Nullable(String),
    ai_tokens       UInt32 DEFAULT 0,
    ai_cost_usd     Float64 DEFAULT 0,

    -- 用户反馈
    rating          Nullable(UInt8),
    sentiment       Nullable(LowCardinality(String)),
    sentiment_score Nullable(Float32),

    -- 事件数据
    event_data      String DEFAULT '{}',           -- JSON

    -- 时间
    event_time      DateTime DEFAULT now(),
    _date           Date DEFAULT toDate(event_time)
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(_date)
ORDER BY (event_type, hexagram_name, event_time)
TTL event_time + INTERVAL 24 MONTH DELETE;


-- ============================================================
-- 3. AI 调用日志表（每次 LLM 调用一条）
-- ============================================================
CREATE TABLE yiai_analytics.ai_calls (
    call_id         UUID,
    user_id         UUID,
    record_id       Nullable(UUID),

    -- 模型信息
    provider        LowCardinality(String),        -- openai/anthropic/deepseek/qwen
    model_id        String,
    tier            LowCardinality(String),

    -- 请求/响应
    prompt_tokens   UInt32,
    completion_tokens UInt32,
    total_tokens    UInt32,

    -- 性能
    latency_ms      UInt32,                        -- 总延迟
    ttft_ms         Nullable(UInt32),              -- 首 token 延迟
    tokens_per_sec  Float32,                       -- 生成速度

    -- 成本
    cost_usd        Float64,

    -- 质量
    is_fallback     Bool DEFAULT false,            -- 是否降级调用
    retry_count     UInt8 DEFAULT 0,
    error_type      Nullable(String),
    safety_flag     Bool DEFAULT false,            -- 是否触发安全检查

    -- 时间
    created_at      DateTime DEFAULT now(),
    _date           Date DEFAULT toDate(created_at)
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(_date)
ORDER BY (provider, model_id, created_at)
TTL created_at + INTERVAL 12 MONTH DELETE;


-- ============================================================
-- 4. RAG 检索日志表
-- ============================================================
CREATE TABLE yiai_analytics.rag_queries (
    query_id        UUID,
    user_id         UUID,
    record_id       Nullable(UUID),

    -- 检索信息
    query_text      String,
    hexagram_context Nullable(String),

    -- 向量检索
    vector_results_count UInt16 DEFAULT 0,
    vector_top_score     Float32 DEFAULT 0,
    vector_latency_ms    UInt32 DEFAULT 0,

    -- 图谱检索
    graph_results_count  UInt16 DEFAULT 0,
    graph_latency_ms     UInt32 DEFAULT 0,

    -- 规则检索
    rule_results_count   UInt16 DEFAULT 0,

    -- 融合
    fusion_method        LowCardinality(String),   -- rrf / weighted
    fusion_latency_ms    UInt32 DEFAULT 0,

    -- 总延迟
    total_latency_ms     UInt32,

    -- 时间
    created_at      DateTime DEFAULT now(),
    _date           Date DEFAULT toDate(created_at)
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(_date)
ORDER BY (user_id, created_at)
TTL created_at + INTERVAL 6 MONTH DELETE;


-- ============================================================
-- 5. 用户行为时序表（用于趋势分析）
-- ============================================================
CREATE TABLE yiai_analytics.user_metrics_daily (
    user_id         UUID,
    date            Date,

    -- 活动指标
    divination_count UInt16 DEFAULT 0,
    session_count    UInt16 DEFAULT 0,
    total_time_sec   UInt32 DEFAULT 0,

    -- 卦象分布
    hexagram_distribution String DEFAULT '{}',     -- JSON: {"乾": 2, "坤": 1}
    element_distribution   String DEFAULT '{}',    -- JSON: {"木": 3, "火": 2}
    topic_distribution     String DEFAULT '{}',    -- JSON: {"事业": 2, "感情": 1}

    -- 情绪指标
    sentiment_avg    Float32 DEFAULT 0,
    sentiment_distribution String DEFAULT '{}',    -- JSON: {"positive": 3, "anxious": 1}

    -- 消费指标
    ai_tokens_used   UInt32 DEFAULT 0,
    ai_cost_usd      Float64 DEFAULT 0,
    credits_used     UInt16 DEFAULT 0,

    -- 评分
    avg_rating       Float32 DEFAULT 0,
    feedback_count   UInt16 DEFAULT 0
)
ENGINE = SummingMergeTree()
PARTITION BY toYear(date)
ORDER BY (user_id, date)
TTL date + INTERVAL 36 MONTH DELETE;


-- ============================================================
-- 6. 系统监控指标表
-- ============================================================
CREATE TABLE yiai_analytics.system_metrics (
    metric_name     LowCardinality(String),
    metric_value    Float64,
    tags            Map(String, String) DEFAULT {},
    recorded_at     DateTime DEFAULT now(),
    _date           Date DEFAULT toDate(recorded_at)
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(_date)
ORDER BY (metric_name, recorded_at)
TTL recorded_at + INTERVAL 6 MONTH DELETE;
```

### 6.2 物化视图（预聚合）

```sql
-- ============================================================
-- 每小时 API 请求聚合
-- ============================================================
CREATE MATERIALIZED VIEW yiai_analytics.api_hourly_mv
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(hour)
ORDER BY (endpoint, hour)
AS SELECT
    toStartOfHour(created_at) AS hour,
    endpoint,
    count() AS request_count,
    countIf(status_code >= 400) AS error_count,
    avg(duration_ms) AS avg_duration,
    quantile(0.95)(duration_ms) AS p95_duration,
    sum(ai_cost_usd) AS total_cost,
    uniq(user_id) AS unique_users
FROM yiai_analytics.api_requests
GROUP BY hour, endpoint;


-- ============================================================
-- 每日卦象统计
-- ============================================================
CREATE MATERIALIZED VIEW yiai_analytics.hexagram_daily_mv
ENGINE = SummingMergeTree()
PARTITION BY toYear(date)
ORDER BY (hexagram_name, date)
AS SELECT
    toDate(event_time) AS date,
    hexagram_name,
    event_type,
    count() AS event_count,
    uniq(user_id) AS unique_users,
    avgIf(rating, rating > 0) AS avg_rating
FROM yiai_analytics.divination_events
GROUP BY date, hexagram_name, event_type;


-- ============================================================
-- 每日 AI 模型使用统计
-- ============================================================
CREATE MATERIALIZED VIEW yiai_analytics.ai_daily_mv
ENGINE = SummingMergeTree()
PARTITION BY toYear(date)
ORDER BY (provider, model_id, date)
AS SELECT
    toDate(created_at) AS date,
    provider,
    model_id,
    tier,
    count() AS call_count,
    sum(prompt_tokens) AS total_prompt_tokens,
    sum(completion_tokens) AS total_completion_tokens,
    sum(cost_usd) AS total_cost,
    avg(latency_ms) AS avg_latency,
    countIf(is_fallback) AS fallback_count,
    countIf(safety_flag) AS safety_flag_count
FROM yiai_analytics.ai_calls
GROUP BY date, provider, model_id, tier;
```

### 6.3 常用查询

```sql
-- Q1: 过去 7 天每日活跃用户和卦数
SELECT
    toDate(created_at) AS date,
    uniq(user_id) AS dau,
    count() AS total_requests
FROM yiai_analytics.api_requests
WHERE created_at >= now() - INTERVAL 7 DAY
GROUP BY date ORDER BY date;

-- Q2: 最热门的 10 个卦象（过去 30 天）
SELECT
    hexagram_name,
    count() AS occurrences,
    uniq(user_id) AS unique_users,
    avgIf(rating, rating > 0) AS avg_rating
FROM yiai_analytics.divination_events
WHERE event_type = 'hexagram_generated'
  AND event_time >= now() - INTERVAL 30 DAY
GROUP BY hexagram_name
ORDER BY occurrences DESC
LIMIT 10;

-- Q3: AI 模型成本分析（按月）
SELECT
    toStartOfMonth(date) AS month,
    provider,
    model_id,
    sum(call_count) AS calls,
    sum(total_cost) AS cost_usd,
    sum(total_prompt_tokens + total_completion_tokens) AS total_tokens
FROM yiai_analytics.ai_daily_mv
GROUP BY month, provider, model_id
ORDER BY month DESC, cost_usd DESC;

-- Q4: API P95 延迟趋势（按天）
SELECT
    toStartOfDay(hour) AS day,
    endpoint,
    avg(avg_duration) AS avg_ms,
    max(p95_duration) AS p95_ms,
    sum(request_count) AS total_requests
FROM yiai_analytics.api_hourly_mv
WHERE hour >= now() - INTERVAL 30 DAY
GROUP BY day, endpoint
ORDER BY day DESC;

-- Q5: 用户情绪变化趋势
SELECT
    user_id,
    date,
    sentiment_avg,
    hexagram_distribution,
    topic_distribution
FROM yiai_analytics.user_metrics_daily
WHERE user_id = {user_id:UUID}
  AND date >= today() - INTERVAL 90 DAY
ORDER BY date;
```

---

## 7. MinIO 对象存储设计

### 7.1 Bucket 设计

| Bucket | 用途 | 访问策略 | 生命周期 |
|--------|------|---------|---------|
| `yiai-documents` | 知识库源文档（PDF、TXT、古籍扫描件） | 私有 | 永久 |
| `yiai-exports` | 用户导出的报告（PDF、PNG） | 私有，签名 URL | 7 天自动删除 |
| `yiai-avatars` | 用户头像 | 公开读 | 用户删除时清理 |
| `yiai-backups` | 数据库备份 | 私有 | 90 天滚动删除 |
| `yiai-temp` | 临时文件（AI 生成中间结果） | 私有 | 24 小时自动删除 |

### 7.2 目录结构

```
yiai-documents/
├── classics/                    # 古籍原文
│   ├── yijing_original.txt      # 周易原文
│   ├── xiangci.txt              # 象辞
│   ├── tuanci.txt               # 彖辞
│   └── scans/                   # 古籍扫描件 (PDF/PNG)
│       ├── wang_bi_commentary.pdf
│       └── cheng_yi_commentary.pdf
├── commentaries/                # 注释文献
│   ├── wang_bi/                 # 王弼注
│   ├── cheng_yi/                # 程颐注
│   └── zhu_xi/                  # 朱熹注
├── modern/                      # 现代解释
│   ├── white_book/              # 白话文
│   └── case_studies/            # 案例
└── rules/                       # 规则文档
    ├── five_elements.md
    └── six_relatives.md

yiai-exports/
├── {user_id}/
│   ├── {record_id}/
│   │   ├── interpretation.pdf
│   │   └── hexagram_chart.png
│   └── reports/
│       ├── monthly_2025_05.pdf
│       └── trend_analysis.pdf

yiai-backups/
├── postgres/
│   ├── daily/
│   │   └── 2025-05-29.sql.gz
│   └── weekly/
│       └── 2025-W22.sql.gz
├── neo4j/
│   └── 2025-05-29.dump
├── qdrant/
│   └── 2025-05-29.snapshot
└── clickhouse/
    └── 2025-05-29/
```

### 7.3 访问策略

```python
# minio_policy.py

from minio import Minio
from datetime import timedelta

class MinIOStorage:
    def __init__(self, client: Minio):
        self.client = client

    async def upload_document(self, bucket: str, object_name: str, data: bytes, content_type: str):
        """上传知识库文档。"""
        from io import BytesIO
        self.client.put_object(
            bucket_name=bucket,
            object_name=object_name,
            data=BytesIO(data),
            length=len(data),
            content_type=content_type,
        )

    async def get_export_url(self, user_id: str, object_name: str) -> str:
        """生成导出文件的签名 URL（7天有效）。"""
        return self.client.presigned_get_object(
            bucket_name="yiai-exports",
            object_name=f"{user_id}/{object_name}",
            expires=timedelta(days=7),
        )

    async def cleanup_temp(self):
        """清理 24 小时前的临时文件。"""
        objects = self.client.list_objects("yiai-temp", recursive=True)
        from datetime import datetime, timedelta
        cutoff = datetime.utcnow() - timedelta(hours=24)
        for obj in objects:
            if obj.last_modified < cutoff:
                self.client.remove_object("yiai-temp", obj.object_name)
```

---

## 8. 数据同步策略

### 8.1 同步架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    数据同步策略                                   │
│                                                                 │
│  ┌─────────┐    同步写入     ┌─────────┐                       │
│  │   App   │ ──────────────▶ │PostgreSQL│  (主数据源)           │
│  └────┬────┘                 └────┬─────┘                       │
│       │                          │                              │
│       │ 异步事件                 │ CDC / 异步任务               │
│       ▼                          ▼                              │
│  ┌─────────┐              ┌─────────┐  ┌─────────┐             │
│  │ ClickHouse│◀───────────│  Redis   │  │  Neo4j  │             │
│  │ (日志)   │  异步消费    │ (缓存)   │  │ (图谱)  │             │
│  └─────────┘              └─────────┘  └─────────┘             │
│                                    │                            │
│                                    │ 异步任务                   │
│                                    ▼                            │
│                              ┌─────────┐                        │
│                              │ Qdrant  │                        │
│                              │ (向量)  │                        │
│                              └─────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 同步场景详解

```python
# sync_strategies.py

class DataSyncManager:
    """数据同步管理器。"""

    # ============================================================
    # 场景 1: 起卦写入（核心路径，需要低延迟）
    # ============================================================

    async def sync_divination_write(self, record: dict):
        """
        起卦写入同步策略：
        1. 同步写入 PostgreSQL（ACID 事务保证）
        2. 异步写入 Redis（缓存更新）
        3. 异步写入 ClickHouse（日志记录）
        4. 异步写入 Qdrant（向量索引）
        5. 异步写入 Neo4j（图谱更新）
        """
        # Step 1: 同步写入 PG（必须成功）
        await self.pg.save_record(record)

        # Step 2-5: 异步任务（失败可重试）
        await self.task_queue.enqueue_batch([
            {"task": "sync_redis_cache", "data": record, "priority": "high"},
            {"task": "sync_clickhouse_event", "data": record, "priority": "medium"},
            {"task": "sync_qdrant_vector", "data": record, "priority": "medium"},
            {"task": "sync_neo4j_graph", "data": record, "priority": "low"},
        ])

    # ============================================================
    # 场景 2: 用户画像更新（离线聚合，非实时）
    # ============================================================

    async def sync_user_profile(self, user_id: str):
        """
        用户画像同步策略：
        1. 从 PG 聚合用户数据
        2. 更新 PG user_profiles 表
        3. 同步到 Neo4j 用户节点
        4. 失效 Redis 缓存
        5. 更新 Qdrant 用户历史向量
        """
        # 聚合计算
        profile = await self._aggregate_user_data(user_id)

        # 更新 PG
        await self.pg.update_user_profile(user_id, profile)

        # 同步 Neo4j
        await self.neo4j.sync_user_profile(user_id, profile)

        # 失效缓存
        await self.redis.invalidate_user_profile(user_id)

    # ============================================================
    # 场景 3: 静态知识更新（低频，手动触发）
    # ============================================================

    async def sync_knowledge_update(self, entity_type: str, entity_id: str):
        """
        知识数据更新同步：
        1. 更新 PostgreSQL
        2. 全量刷新 Redis 缓存
        3. 更新 Neo4j 图谱
        4. 重新生成 Qdrant 向量（如果文本变化）
        """
        # PG 更新
        data = await self.pg.update_knowledge(entity_type, entity_id)

        # Redis 缓存刷新
        await self.redis.set(
            f"{entity_type}:{entity_id}:full",
            json.dumps(data),
            ex=timedelta(days=7),
        )

        # Neo4j 更新
        await self.neo4j.update_knowledge_node(entity_type, entity_id, data)

        # Qdrant 重新嵌入（如果文本变化）
        if data.get("text_changed"):
            embedding = await self.embedding_model.encode(data["text"])
            await self.qdrant.upsert(entity_type, entity_id, embedding, data["payload"])

    # ============================================================
    # 场景 4: ClickHouse 异步写入（批量，容忍延迟）
    # ============================================================

    async def sync_clickhouse_batch(self, events: list[dict]):
        """
        ClickHouse 批量写入策略：
        - 攒批写入（每 1000 条或每 5 秒）
        - 失败重试（最多 3 次）
        - 写入 Redis Stream 作为缓冲
        """
        try:
            await self.clickhouse.batch_insert("api_requests", events)
        except Exception as e:
            # 失败时写入 Redis Stream 缓冲
            for event in events:
                await self.redis.xadd("stream:clickhouse_buffer", event)
            logger.error(f"ClickHouse batch write failed: {e}")
```

### 8.3 一致性保证

| 场景 | 一致性级别 | 策略 | 容忍延迟 |
|------|-----------|------|---------|
| 起卦写入 | 强一致（PG） | 同步写 PG，异步同步其他 | 最终一致（秒级） |
| 用户画像 | 最终一致 | 定时聚合任务 | 分钟级 |
| 知识图谱 | 最终一致 | 事件驱动异步 | 秒级 |
| 向量索引 | 最终一致 | 异步嵌入+写入 | 秒~分钟级 |
| 日志记录 | 最终一致 | 批量异步写入 | 秒~分钟级 |
| 缓存数据 | 最终一致 | Cache-Aside + TTL | 分钟级 |

### 8.4 冲突解决

```python
# conflict_resolution.py

class ConflictResolver:
    """数据冲突解决策略。"""

    # PostgreSQL 作为 Single Source of Truth
    # 其他存储都是 PG 的派生/缓存

    async def resolve_pg_neo4j_conflict(self, user_id: str):
        """PG 与 Neo4j 数据不一致时，以 PG 为准。"""
        pg_data = await self.pg.get_user_profile(user_id)
        neo4j_data = await self.neo4j.get_user_profile(user_id)

        if pg_data["updated_at"] > neo4j_data.get("updated_at", ""):
            await self.neo4j.sync_user_profile(user_id, pg_data)
            return "neo4j_synced_from_pg"
        return "no_conflict"

    async def resolve_cache_invalidation(self, entity_type: str, entity_id: str):
        """缓存与源数据不一致时，失效缓存。"""
        await self.redis.delete(f"{entity_type}:{entity_id}:full")
        return "cache_invalidated"
```

---

## 9. 数据备份恢复方案

### 9.1 备份策略总览

| 存储 | 备份方式 | 频率 | 保留策略 | 存储位置 |
|------|---------|------|---------|---------|
| PostgreSQL | pg_dump 全量 + WAL 归档 | 每日全量 + 持续 WAL | 7天日备 + 4周周备 + 3月月备 | MinIO + 异地 |
| Neo4j | neo4j-admin dump | 每日 | 7天日备 + 4周周备 | MinIO |
| Qdrant | 快照 API | 每日 | 7天日备 | MinIO |
| Redis | RDB + AOF | RDB 每小时 + AOF 持续 | 7天 RDB | 本地 + MinIO |
| ClickHouse | clickhouse-backup | 每日 | 30天 | MinIO |
| MinIO | 跨站点复制 | 持续 | 90天 | 异地 MinIO |

### 9.2 PostgreSQL 备份

```bash
#!/bin/bash
# backup_postgres.sh

BACKUP_DIR="/backups/postgres"
DATE=$(date +%Y-%m-%d)
WEEK=$(date +%Y-W%V)

# ============================================================
# 全量备份（每日凌晨 3 点）
# ============================================================
pg_dump \
  -h localhost \
  -U yiai_admin \
  -d yiai \
  --format=custom \
  --compress=9 \
  --file="${BACKUP_DIR}/daily/yiai_${DATE}.dump"

# 上传到 MinIO
mc cp "${BACKUP_DIR}/daily/yiai_${DATE}.dump" \
  minio/yiai-backups/postgres/daily/

# ============================================================
# 周备份（每周日凌晨）
# ============================================================
if [ "$(date +%u)" = "7" ]; then
  cp "${BACKUP_DIR}/daily/yiai_${DATE}.dump" \
     "${BACKUP_DIR}/weekly/yiai_${WEEK}.dump"
  mc cp "${BACKUP_DIR}/weekly/yiai_${WEEK}.dump" \
    minio/yiai-backups/postgres/weekly/
fi

# ============================================================
# 月备份（每月 1 号）
# ============================================================
if [ "$(date +%d)" = "01" ]; then
  MONTH=$(date +%Y-%m)
  cp "${BACKUP_DIR}/daily/yiai_${DATE}.dump" \
     "${BACKUP_DIR}/monthly/yiai_${MONTH}.dump"
  mc cp "${BACKUP_DIR}/monthly/yiai_${MONTH}.dump" \
    minio/yiai-backups/postgres/monthly/
fi

# ============================================================
# 清理过期备份
# ============================================================
# 本地：保留 7 天
find ${BACKUP_DIR}/daily -mtime +7 -delete

# MinIO：保留策略由 lifecycle 配置管理
# daily: 7天, weekly: 28天, monthly: 90天

# ============================================================
# WAL 归档（用于 Point-in-Time Recovery）
# ============================================================
# postgresql.conf 配置:
# archive_mode = on
# archive_command = 'mc cp %p minio/yiai-backups/postgres/wal/%f'
# wal_level = replica
```

### 9.3 Neo4j 备份

```bash
#!/bin/bash
# backup_neo4j.sh

DATE=$(date +%Y-%m-%d)
NEO4J_HOME="/var/lib/neo4j"
BACKUP_DIR="/backups/neo4j"

# 停止 Neo4j（dump 需要离线或使用 online backup）
# 在线备份需要 Enterprise 版本
# 社区版需要停止服务

# 使用 neo4j-admin dump
neo4j-admin database dump \
  neo4j \
  --to-path="${BACKUP_DIR}/neo4j_${DATE}.dump"

# 上传到 MinIO
mc cp "${BACKUP_DIR}/neo4j_${DATE}.dump" \
  minio/yiai-backups/neo4j/

# 恢复命令：
# neo4j-admin database load neo4j --from-path="${BACKUP_DIR}/neo4j_${DATE}.dump" --overwrite-destination
```

### 9.4 Qdrant 备份

```python
# backup_qdrant.py

from qdrant_client import QdrantClient
import subprocess

def backup_qdrant():
    """Qdrant 快照备份。"""
    client = QdrantClient(url="http://localhost:6333")
    collections = client.get_collections().collections

    date = datetime.now().strftime("%Y-%m-%d")

    for collection in collections:
        name = collection.name

        # 创建快照
        snapshot = client.create_snapshot(collection_name=name)

        # 下载快照
        snapshot_url = f"http://localhost:6333/collections/{name}/snapshots/{snapshot.name}"
        local_path = f"/backups/qdrant/{name}_{date}.snapshot"

        subprocess.run(["curl", "-o", local_path, snapshot_url], check=True)

        # 上传到 MinIO
        subprocess.run([
            "mc", "cp", local_path,
            f"minio/yiai-backups/qdrant/{name}/"
        ], check=True)

        print(f"Backed up collection: {name}")

# 恢复命令（通过 API）：
# client.restore_snapshot(collection_name=name, snapshot_path=local_path)
```

### 9.5 Redis 备份

```bash
#!/bin/bash
# backup_redis.sh

DATE=$(date +%Y-%m-%d-%H)
BACKUP_DIR="/backups/redis"

# 触发 RDB 快照
redis-cli BGSAVE

# 等待完成
while [ "$(redis-cli LASTSAVE)" = "$LAST_SAVE" ]; do
  sleep 1
done

# 复制 RDB 文件
cp /var/lib/redis/dump.rdb "${BACKUP_DIR}/redis_${DATE}.rdb"

# 上传到 MinIO
mc cp "${BACKUP_DIR}/redis_${DATE}.rdb" \
  minio/yiai-backups/redis/

# 恢复：
# 1. 停止 Redis
# 2. 替换 dump.rdb
# 3. 启动 Redis
```

### 9.6 ClickHouse 备份

```bash
#!/bin/bash
# backup_clickhouse.sh

DATE=$(date +%Y-%m-%d)

# 使用 clickhouse-backup 工具
clickhouse-backup create "yiai_${DATE}"

# 上传到 MinIO
clickhouse-backup upload "yiai_${DATE}"

# 清理旧备份
clickhouse-backup list | tail -n +30 | awk '{print $1}' | xargs -I {} clickhouse-backup delete {}

# 恢复：
# clickhouse-backup restore "yiai_${DATE}"
```

### 9.7 恢复演练

```python
# recovery_drill.py

class RecoveryDrill:
    """恢复演练管理器。"""

    async def drill_postgres_recovery(self):
        """PostgreSQL 恢复演练。"""
        # 1. 下载最新备份
        # 2. 恢复到测试实例
        # 3. 验证数据完整性
        # 4. 记录恢复时间
        pass

    async def verify_backup_integrity(self):
        """验证备份完整性。"""
        checks = {
            "postgres": self._check_pg_backup,
            "neo4j": self._check_neo4j_backup,
            "qdrant": self._check_qdrant_backup,
            "redis": self._check_redis_backup,
        }
        results = {}
        for name, check_fn in checks.items():
            try:
                results[name] = await check_fn()
            except Exception as e:
                results[name] = {"status": "FAILED", "error": str(e)}
        return results
```

---

## 10. 数据安全和隐私保护

### 10.1 安全架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    数据安全分层                                    │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Layer 1: 传输安全                                         │  │
│  │ - 全链路 TLS 1.3                                         │  │
│  │ - 内部服务 mTLS                                          │  │
│  │ - WebSocket WSS                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Layer 2: 存储加密                                         │  │
│  │ - PostgreSQL TDE (透明数据加密)                           │  │
│  │ - MinIO SSE-S3 (服务端加密)                               │  │
│  │ - Qdrant 静态加密                                        │  │
│  │ - Redis TLS + AUTH                                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Layer 3: 访问控制                                         │  │
│  │ - RBAC (角色基础访问控制)                                 │  │
│  │ - 数据库用户最小权限                                     │  │
│  │ - API Key + JWT 认证                                     │  │
│  │ - 行级安全策略 (PostgreSQL RLS)                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Layer 4: 数据脱敏                                         │  │
│  │ - 手机号/邮箱部分遮蔽                                     │  │
│  │ - IP 地址哈希化                                          │  │
│  │ - 日志中敏感字段脱敏                                     │  │
│  │ - ClickHouse 中无直接用户标识                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Layer 5: 审计追踪                                         │  │
│  │ - 所有数据变更记录                                       │  │
│  │ - 管理员操作日志                                         │  │
│  │ - 异常访问告警                                           │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 10.2 数据库用户权限

```sql
-- ============================================================
-- PostgreSQL 用户权限最小化
-- ============================================================

-- 应用用户（读写业务数据，不可修改 schema）
CREATE USER yiai_app WITH PASSWORD '${APP_DB_PASSWORD}';
GRANT CONNECT ON DATABASE yiai TO yiai_app;
GRANT USAGE ON SCHEMA core, divination, knowledge, config, billing TO yiai_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA core, divination, billing TO yiai_app;
GRANT SELECT ON ALL TABLES IN SCHEMA knowledge TO yiai_app;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA config TO yiai_app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA core, divination, billing TO yiai_app;

-- 只读用户（分析、报表）
CREATE USER yiai_readonly WITH PASSWORD '${READONLY_DB_PASSWORD}';
GRANT CONNECT ON DATABASE yiai TO yiai_readonly;
GRANT USAGE ON SCHEMA core, divination, knowledge, config, billing TO yiai_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA core, divination, knowledge, config, billing TO yiai_readonly;

-- 管理员（DDL 操作，日常不使用）
CREATE USER yiai_admin WITH PASSWORD '${ADMIN_DB_PASSWORD}';
GRANT ALL PRIVILEGES ON DATABASE yiai TO yiai_admin;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA core, divination, knowledge, config, billing TO yiai_admin;

-- ============================================================
-- 行级安全策略（用户只能看到自己的数据）
-- ============================================================

ALTER TABLE divination.records ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_records_policy ON divination.records
    FOR ALL
    USING (user_id = current_setting('app.current_user_id')::UUID)
    WITH CHECK (user_id = current_setting('app.current_user_id')::UUID);

ALTER TABLE divination.events ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_events_policy ON divination.events
    FOR ALL
    USING (user_id = current_setting('app.current_user_id')::UUID)
    WITH CHECK (user_id = current_setting('app.current_user_id')::UUID);
```

### 10.3 数据脱敏

```python
# data_masking.py

import hashlib
import re

class DataMasker:
    """数据脱敏工具。"""

    @staticmethod
    def mask_phone(phone: str) -> str:
        """手机号脱敏：138****1234"""
        if not phone or len(phone) < 7:
            return phone
        return phone[:3] + "****" + phone[-4:]

    @staticmethod
    def mask_email(email: str) -> str:
        """邮箱脱敏：u***@example.com"""
        if not email or "@" not in email:
            return email
        local, domain = email.split("@", 1)
        return local[0] + "***@" + domain

    @staticmethod
    def hash_ip(ip: str) -> str:
        """IP 地址哈希化（不可逆）。"""
        return hashlib.sha256(ip.encode()).hexdigest()[:16]

    @staticmethod
    def mask_nickname(nickname: str) -> str:
        """昵称脱敏：保留首尾字符。"""
        if len(nickname) <= 2:
            return nickname
        return nickname[0] + "*" * (len(nickname) - 2) + nickname[-1]

    @staticmethod
    def mask_question(question: str, keep_chars: int = 10) -> str:
        """问题脱敏：保留前 N 个字符。"""
        if len(question) <= keep_chars:
            return question
        return question[:keep_chars] + "..."

    def mask_for_clickhouse(self, event: dict) -> dict:
        """ClickHouse 日志脱敏。"""
        masked = event.copy()
        if "user_id" in masked:
            masked["user_id_hash"] = hashlib.sha256(
                str(masked.pop("user_id")).encode()
            ).hexdigest()[:16]
        if "ip" in masked:
            masked["ip_hash"] = self.hash_ip(masked.pop("ip"))
        if "question" in masked:
            masked["question"] = self.mask_question(masked["question"])
        return masked
```

### 10.4 GDPR / 个人信息保护

```python
# gdpr_compliance.py

class GDPRCompliance:
    """GDPR / 个保法合规工具。"""

    async def export_user_data(self, user_id: str) -> dict:
        """数据导出（用户有权获取自己的全部数据）。"""
        return {
            "profile": await self.pg.get_user_profile(user_id),
            "divination_records": await self.pg.get_all_records(user_id),
            "events": await self.pg.get_all_events(user_id),
            "graph_data": await self.neo4j.get_user_graph_data(user_id),
            "vector_data": await self.qdrant.get_user_vectors(user_id),
            "exported_at": datetime.utcnow().isoformat(),
        }

    async def delete_user_data(self, user_id: str, hard_delete: bool = False):
        """用户数据删除。"""
        if hard_delete:
            # 物理删除（不可恢复）
            await self.pg.execute("DELETE FROM divination.events WHERE user_id = $1", user_id)
            await self.pg.execute("DELETE FROM divination.records WHERE user_id = $1", user_id)
            await self.pg.execute("DELETE FROM core.user_profiles WHERE user_id = $1", user_id)
            await self.pg.execute("DELETE FROM core.user_sessions WHERE user_id = $1", user_id)
            await self.pg.execute("DELETE FROM core.users WHERE id = $1", user_id)
        else:
            # 软删除（保留 30 天后物理删除）
            await self.pg.execute(
                "UPDATE core.users SET status = 'deleted', deleted_at = now() WHERE id = $1",
                user_id
            )

        # 清理其他存储
        await self.neo4j.delete_user_data(user_id)
        await self.qdrant.delete_user_vectors(user_id)
        await self.redis.delete(f"user:{user_id}:*")
        await self.clickhouse.anonymize_user_data(user_id)

    async def handle_data_breach(self, affected_user_ids: list[str]):
        """数据泄露应急响应。"""
        # 1. 立即失效所有会话
        for uid in affected_user_ids:
            await self.redis.delete(f"session:*:data")  # 按用户过滤

        # 2. 强制密码重置
        await self.pg.execute(
            "UPDATE core.users SET password_hash = NULL WHERE id = ANY($1)",
            affected_user_ids
        )

        # 3. 通知用户（记录到审计日志）
        for uid in affected_user_ids:
            await self.audit_log.record(
                action="data_breach_notification",
                user_id=uid,
                details={"breach_time": datetime.utcnow().isoformat()}
            )
```

### 10.5 密钥管理

```python
# secret_management.py

"""
密钥管理策略：
- 所有密钥通过环境变量注入，不硬编码
- 生产环境使用 Vault/AWS Secrets Manager
- 密钥定期轮换（90 天）
"""

import os

class SecretManager:
    """密钥管理。"""

    # 必需的密钥列表
    REQUIRED_SECRETS = [
        "DATABASE_URL",
        "REDIS_URL",
        "NEO4J_PASSWORD",
        "QDRANT_API_KEY",
        "MINIO_ACCESS_KEY",
        "MINIO_SECRET_KEY",
        "JWT_SECRET_KEY",
        "JWT_REFRESH_SECRET",
        "DEEPSEEK_API_KEY",
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "QWEN_API_KEY",
    ]

    def validate_secrets(self):
        """启动时验证所有必需密钥存在。"""
        missing = [s for s in self.REQUIRED_SECRETS if not os.environ.get(s)]
        if missing:
            raise RuntimeError(f"Missing required secrets: {missing}")

    def get_database_url(self) -> str:
        return os.environ["DATABASE_URL"]

    def get_redis_url(self) -> str:
        return os.environ["REDIS_URL"]
```

---

## 11. 数据增长预测和容量规划

### 11.1 数据增长模型

#### 用户增长预测

| 阶段 | 时间 | 累计用户 | DAU | 日新增卦数 | 说明 |
|------|------|---------|-----|-----------|------|
| MVP | 0-6 月 | 1,000 | 100 | 200 | 内测 |
| 增长期 | 6-12 月 | 10,000 | 1,000 | 3,000 | 公测推广 |
| 规模期 | 1-2 年 | 100,000 | 10,000 | 30,000 | 正式运营 |
| 成熟期 | 2-5 年 | 1,000,000 | 100,000 | 300,000 | 大规模 |

#### 单条数据大小估算

| 数据类型 | 单条大小 | 说明 |
|---------|---------|------|
| 用户记录 | ~2 KB | 基础信息 + JSONB 偏好 |
| 卦记录 | ~5 KB | 包含 AI 解释、JSONB 数据 |
| 用户画像 | ~4 KB | JSONB 聚合数据 |
| 行为事件 | ~0.5 KB | 细粒度事件 |
| AI 调用日志 | ~0.3 KB | ClickHouse 行 |
| 向量 (1024 维) | ~4 KB | float32 |
| Neo4j 节点 | ~1 KB | 平均属性大小 |

### 11.2 PostgreSQL 容量规划

```
PostgreSQL 存储估算（5 年）：

用户表 (core.users):
  1,000,000 用户 × 2 KB = 2 GB

卦记录表 (divination.records):
  300,000/天 × 365天 × 5年 = 547,500,000 条
  547,500,000 × 5 KB = 2,737,500 MB ≈ 2.67 TB

用户画像 (core.user_profiles):
  1,000,000 × 4 KB = 4 GB

行为事件 (divination.events):
  300,000/天 × 3 (每次卦3个事件) × 365 × 5 = 1,642,500,000 条
  1,642,500,000 × 0.5 KB = 821,250 MB ≈ 802 GB

Prompt 模板 (config.prompt_templates):
  ~100 条 × 5 KB = 0.5 MB (忽略不计)

其他配置/计费表:
  ~1 GB

总计: ~3.5 TB (不含索引和 WAL)
含索引 (1.3x): ~4.5 TB

推荐配置:
  - 存储: 6 TB SSD (NVMe)
  - 内存: 64 GB (shared_buffers = 16 GB)
  - CPU: 16 核
  - 分区: 按月分区 records 和 events 表
  - 归档: 超过 2 年的 records 迁移到冷存储
```

### 11.3 Neo4j 容量规划

```
Neo4j 存储估算：

静态节点 (不变):
  - Hexagram: 64
  - Line: 384
  - Trigram: 8
  - Element: 5
  - Role: 5
  - Spirit: 6
  - HeavenlyStem: 10
  - EarthlyBranch: 12
  - Topic: ~20
  小计: ~514 节点, ~2,000 关系

动态节点 (随用户增长):
  - User: 1,000,000 节点
  - DivinationRecord: 547,500,000 节点

动态关系:
  - User-QUERIED-Record: 547,500,000
  - Record-RESULTED_IN-Hexagram: 547,500,000
  - Record-ABOUT_TOPIC-Topic: 547,500,000
  - User-INTERESTED_IN-Topic: ~10,000,000
  - User-PREFERS_ELEMENT-Element: ~5,000,000

总计: ~550,000,000 节点, ~1,650,000,000 关系
存储: ~500 GB (含索引)

优化策略:
  - 超过 1 年的 DivinationRecord 节点归档到 PostgreSQL
  - Neo4j 中仅保留近 1 年的动态数据
  - 静态图谱保持完整

推荐配置:
  - 存储: 1 TB SSD
  - 内存: 32 GB (heap + pagecache)
  - CPU: 8 核
  - 版本: Neo4j 5.x Enterprise (支持在线备份)
```

### 11.4 Qdrant 容量规划

```
Qdrant 存储估算：

向量数据 (1024 维 float32):
  yijing_texts:        500 × 4 KB = 2 MB
  commentaries:      3,000 × 4 KB = 12 MB
  modern_explanations: 2,000 × 4 KB = 8 MB
  five_elements_rules: 800 × 4 KB = 3.2 MB
  divination_cases:  50,000 × 4 KB = 200 MB
  user_history:    100,000+ × 4 KB = 400+ MB

总计: ~625 MB 向量 + Payload 约 1.5 GB

5 年后 (user_history 增长):
  user_history: 547,500,000 × 4 KB = 2,190,000 MB ≈ 2.14 TB

优化策略:
  - 标量量化 (INT8): 内存占用降低 4x → ~535 GB
  - user_history 按用户分区，冷用户数据存磁盘
  - 定期清理过期向量

推荐配置:
  - 存储: 3 TB SSD
  - 内存: 64 GB (热数据)
  - CPU: 8 核
```

### 11.5 Redis 容量规划

```
Redis 内存估算:

会话数据:
  10,000 DAU × 1 KB = 10 MB

工作记忆:
  1,000 并发会话 × 5 KB = 5 MB

用户画像缓存:
  100,000 活跃用户 × 4 KB = 400 MB

卦数据缓存:
  64 卦 × 2 KB = 0.13 MB

AI 结果缓存:
  ~100,000 条 × 2 KB = 200 MB

Embedding 缓存:
  ~500,000 条 × 4 KB = 2 GB

频率限制:
  10,000 DAU × 100 字节 = 1 MB

总计: ~2.7 GB

推荐配置:
  - 内存: 4 GB (留余量)
  - 策略: allkeys-lfu
  - 集群: 单节点 (MVP) → 主从 (规模期)
```

### 11.6 ClickHouse 容量规划

```
ClickHouse 存储估算 (压缩后):

api_requests:
  300,000/天 × 365 × 5 = 547,500,000 行
  压缩后 ~0.1 KB/行 = 54.75 GB

divination_events:
  900,000/天 × 365 × 5 = 1,642,500,000 行
  压缩后 ~0.08 KB/行 = 131.4 GB

ai_calls:
  300,000/天 × 365 × 5 = 547,500,000 行
  压缩后 ~0.05 KB/行 = 27.4 GB

rag_queries:
  300,000/天 × 365 × 5 = 547,500,000 行
  压缩后 ~0.06 KB/行 = 32.85 GB

user_metrics_daily:
  1,000,000 用户 × 365 × 5 = 1,825,000,000 行 (但实际只有活跃用户)
  ~100,000 活跃 × 365 × 5 = 182,500,000 行
  压缩后 ~0.2 KB/行 = 36.5 GB

总计: ~283 GB (压缩后)

推荐配置:
  - 存储: 500 GB SSD
  - 内存: 32 GB
  - CPU: 16 核 (列式存储需要多核并行)
```

### 11.7 总容量规划汇总

| 存储 | MVP (0-6月) | 增长期 (6-12月) | 规模期 (1-2年) | 成熟期 (2-5年) |
|------|------------|----------------|---------------|---------------|
| PostgreSQL | 10 GB | 100 GB | 1 TB | 6 TB |
| Neo4j | 1 GB | 10 GB | 100 GB | 1 TB |
| Qdrant | 1 GB | 5 GB | 50 GB | 3 TB |
| Redis | 512 MB | 2 GB | 4 GB | 8 GB |
| ClickHouse | 5 GB | 30 GB | 100 GB | 500 GB |
| MinIO | 10 GB | 50 GB | 200 GB | 1 TB |
| **总计** | **~28 GB** | **~197 GB** | **~1.5 TB** | **~11.5 TB** |

### 11.8 硬件推荐

#### MVP 阶段（单机/小集群）

```
服务器 1 (应用 + PostgreSQL + Redis):
  - CPU: 8 核
  - 内存: 32 GB
  - 存储: 500 GB NVMe SSD
  - 网络: 1 Gbps

服务器 2 (Neo4j + Qdrant + ClickHouse):
  - CPU: 16 核
  - 内存: 64 GB
  - 存储: 1 TB NVMe SSD
  - 网络: 1 Gbps

服务器 3 (MinIO + 备份):
  - CPU: 4 核
  - 内存: 16 GB
  - 存储: 4 TB HDD
  - 网络: 1 Gbps
```

#### 规模期（分布式）

```
PostgreSQL: 主从复制 + 读写分离
  - 主节点: 16 核 / 128 GB / 4 TB NVMe
  - 从节点: 8 核 / 64 GB / 4 TB NVMe

Neo4j: 单实例 (或 Causal Cluster)
  - 16 核 / 64 GB / 2 TB NVMe

Qdrant: 分片集群
  - 3 节点 × (8 核 / 64 GB / 2 TB NVMe)

Redis: 主从 + Sentinel
  - 主节点: 8 核 / 16 GB
  - 从节点: 8 核 / 16 GB

ClickHouse: 集群
  - 3 分片 × 2 副本
  - 每节点: 16 核 / 64 GB / 1 TB NVMe

MinIO: 分布式
  - 4 节点 × 4 TB HDD
```

---

## 附录 A: 数据库连接配置

```yaml
# config/database.yaml

postgresql:
  host: ${PG_HOST:-localhost}
  port: ${PG_PORT:-5432}
  database: yiai
  username: yiai_app
  password: ${DATABASE_PASSWORD}
  pool_size: 20
  max_overflow: 10
  ssl_mode: verify-full
  ssl_cert: /certs/pg-client.crt
  ssl_key: /certs/pg-client.key
  ssl_ca: /certs/pg-ca.crt

redis:
  url: ${REDIS_URL:-redis://localhost:6379}
  password: ${REDIS_PASSWORD}
  db: 0
  max_connections: 50
  ssl: true

neo4j:
  uri: bolt://${NEO4J_HOST:-localhost}:7687
  username: neo4j
  password: ${NEO4J_PASSWORD}
  max_connection_pool_size: 50
  encrypted: true

qdrant:
  url: http://${QDRANT_HOST:-localhost}:6333
  api_key: ${QDRANT_API_KEY}
  timeout: 30
  prefer_grpc: true

clickhouse:
  host: ${CLICKHOUSE_HOST:-localhost}
  port: 9000
  database: yiai_analytics
  username: yiai_app
  password: ${CLICKHOUSE_PASSWORD}

minio:
  endpoint: ${MINIO_ENDPOINT:-localhost:9000}
  access_key: ${MINIO_ACCESS_KEY}
  secret_key: ${MINIO_SECRET_KEY}
  secure: true
  region: cn-east-1
```

---

## 附录 B: 数据库迁移策略

```python
# migrations/strategy.py

"""
迁移工具: Alembic (PostgreSQL) + 自定义脚本 (其他)

迁移原则:
1. 所有 DDL 变更通过迁移脚本，禁止手动修改
2. 迁移脚本必须可回滚
3. 生产环境迁移前在 staging 验证
4. 大表变更使用 online DDL (pg_repack / CREATE INDEX CONCURRENTLY)
"""

# PostgreSQL 迁移 (Alembic)
# alembic/versions/
# ├── 001_create_users.py
# ├── 002_create_hexagrams.py
# ├── 003_create_divination_records.py
# └── ...

# Neo4j 迁移
# migrations/neo4j/
# ├── 001_create_constraints.cypher
# ├── 002_create_indexes.cypher
# └── 003_seed_data.cypher

# ClickHouse 迁移
# migrations/clickhouse/
# ├── 001_create_tables.sql
# └── 002_create_materialized_views.sql
```

---

*本文档版本: 1.0.0*
*最后更新: 2026-05-29*
*关联文档: yiai.md (总体架构), ai-architecture.md (AI 架构)*
