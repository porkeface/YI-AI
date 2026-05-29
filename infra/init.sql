-- YI-AI 数据库初始化
-- 基础易学静态数据表

-- 八卦
CREATE TABLE IF NOT EXISTS trigrams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(10) NOT NULL UNIQUE,      -- 乾兑离震巽坎艮坤
    symbol VARCHAR(10) NOT NULL,            -- ☰☱☲☳☴☵☶☷
    binary_rep VARCHAR(3) NOT NULL UNIQUE,  -- 111,110,101,100,011,010,001,000
    element VARCHAR(5) NOT NULL,            -- 五行属性
    nature VARCHAR(20),                     -- 自然象
    direction VARCHAR(10),                  -- 方位
    family VARCHAR(10),                     -- 家族
    body VARCHAR(10),                       -- 身体
    animal VARCHAR(10),                     -- 动物
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 六十四卦
CREATE TABLE IF NOT EXISTS hexagrams (
    id SERIAL PRIMARY KEY,
    number INT NOT NULL UNIQUE,             -- 1-64 序号
    name VARCHAR(10) NOT NULL,              -- 卦名
    symbol VARCHAR(20),                     -- 卦符
    upper_trigram_id INT NOT NULL REFERENCES trigrams(id),
    lower_trigram_id INT NOT NULL REFERENCES trigrams(id),
    binary_rep VARCHAR(6) NOT NULL UNIQUE,  -- 6位二进制
    judgment TEXT,                           -- 卦辞
    image TEXT,                              -- 象辞
    element VARCHAR(5) NOT NULL,            -- 五行属性
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 爻辞
CREATE TABLE IF NOT EXISTS line_texts (
    id SERIAL PRIMARY KEY,
    hexagram_id INT NOT NULL REFERENCES hexagrams(id),
    position INT NOT NULL CHECK (position BETWEEN 1 AND 6),
    text TEXT NOT NULL,                     -- 爻辞
    image TEXT,                             -- 小象辞
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(hexagram_id, position)
);

-- 五行关系
CREATE TABLE IF NOT EXISTS element_relations (
    id SERIAL PRIMARY KEY,
    source VARCHAR(5) NOT NULL,
    target VARCHAR(5) NOT NULL,
    relation VARCHAR(10) NOT NULL,          -- 生/克/被生/被克
    UNIQUE(source, target, relation)
);

-- 天干
CREATE TABLE IF NOT EXISTS heavenly_stems (
    id SERIAL PRIMARY KEY,
    name VARCHAR(5) NOT NULL UNIQUE,        -- 甲乙丙丁戊己庚辛壬癸
    element VARCHAR(5) NOT NULL,
    yin_yang VARCHAR(5) NOT NULL,
    order_num INT NOT NULL
);

-- 地支
CREATE TABLE IF NOT EXISTS earthly_branches (
    id SERIAL PRIMARY KEY,
    name VARCHAR(5) NOT NULL UNIQUE,        -- 子丑寅卯辰巳午未申酉戌亥
    element VARCHAR(5) NOT NULL,
    yin_yang VARCHAR(5) NOT NULL,
    animal VARCHAR(5),                      -- 生肖
    order_num INT NOT NULL
);

-- 地支关系（冲合刑害）
CREATE TABLE IF NOT EXISTS branch_relations (
    id SERIAL PRIMARY KEY,
    branch1 VARCHAR(5) NOT NULL,
    branch2 VARCHAR(5) NOT NULL,
    relation VARCHAR(10) NOT NULL,          -- 冲/合/刑/害
    UNIQUE(branch1, branch2, relation)
);

-- 六亲
CREATE TABLE IF NOT EXISTS six_relatives (
    id SERIAL PRIMARY KEY,
    name VARCHAR(10) NOT NULL UNIQUE,       -- 父母/官鬼/妻财/子孙/兄弟
    description TEXT
);

-- 六神
CREATE TABLE IF NOT EXISTS six_spirits (
    id SERIAL PRIMARY KEY,
    name VARCHAR(10) NOT NULL UNIQUE,       -- 青龙/朱雀/勾陈/螣蛇/白虎/玄武
    element VARCHAR(5),
    description TEXT
);

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 占卜记录
CREATE TABLE IF NOT EXISTS divination_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    question TEXT,                          -- 用户问题
    question_type VARCHAR(50),              -- 问题类型
    hexagram_id INT NOT NULL REFERENCES hexagrams(id),
    moving_lines INT[] DEFAULT '{}',        -- 动爻位置
    changed_hexagram_id INT REFERENCES hexagrams(id),  -- 变卦
    rule_result JSONB,                      -- 规则分析结果
    ai_interpretation TEXT,                 -- AI解释
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_hexagram_number ON hexagrams(number);
CREATE INDEX idx_hexagram_binary ON hexagrams(binary_rep);
CREATE INDEX idx_line_text_hexagram ON line_texts(hexagram_id);
CREATE INDEX idx_divination_user ON divination_records(user_id);
CREATE INDEX idx_divination_created ON divination_records(created_at);
