# YI-AI 前端架构与可视化系统设计文档

> 版本: 1.0.0 | 技术栈: Nuxt 4 + Vue 3 + TailwindCSS + shadcn-vue + GSAP + Cytoscape.js + D3.js + Three.js + Pinia

---

## 目录

1. [前端整体架构](#1-前端整体架构)
2. [设计系统](#2-设计系统)
3. [太极动画系统](#3-太极动画系统)
4. [六爻排盘组件](#4-六爻排盘组件)
5. [知识图谱可视化](#5-知识图谱可视化)
6. [时间演化树](#6-时间演化树)
7. [3D 场景设计](#7-3d-场景设计)
8. [性能优化策略](#8-性能优化策略)
9. [响应式与无障碍设计](#9-响应式与无障碍设计)

---

## 1. 前端整体架构

### 1.1 目录结构

```
app/
├── assets/
│   ├── fonts/                      # 自定义字体（思源宋体、霞鹜文楷等）
│   ├── textures/                   # 水墨纹理、噪点、纸张纹理
│   └── shaders/                    # GLSL 着色器（太极、水墨效果）
├── components/
│   ├── ui/                         # shadcn-vue 基础组件
│   │   ├── button/
│   │   ├── card/
│   │   ├── dialog/
│   │   ├── select/
│   │   └── ...
│   ├── visualization/              # 可视化组件（核心）
│   │   ├── taiji/                  # 太极动画系统
│   │   │   ├── TaijiCanvas.vue     # 主画布（Canvas 2D / WebGL）
│   │   │   ├── TaijiRing.vue       # 外圈卦象环
│   │   │   └── useTaiji.ts         # 太极动画 composable
│   │   ├── liuyao/                 # 六爻排盘系统
│   │   │   ├── LiuyaoBoard.vue     # 排盘主面板
│   │   │   ├── YaoLine.vue         # 单爻组件
│   │   │   ├── YaoFlip.vue         # 动爻翻转动画
│   │   │   ├── GuaCard.vue         # 卦卡
│   │   │   └── useLiuyao.ts        # 六爻逻辑 composable
│   │   ├── graph/                  # 知识图谱
│   │   │   ├── KnowledgeGraph.vue  # Cytoscape 主容器
│   │   │   ├── GraphNode.vue       # 自定义节点渲染
│   │   │   ├── GraphLegend.vue     # 图例
│   │   │   └── useGraph.ts         # 图谱 composable
│   │   ├── evolution/              # 时间演化树
│   │   │   ├── EvolutionTree.vue   # D3 演化树
│   │   │   ├── TimelineAxis.vue    # 时间轴
│   │   │   ├── StateNode.vue       # 状态节点
│   │   │   └── useEvolution.ts     # 演化 composable
│   │   └── scene3d/                # 3D 场景
│   │       ├── HexagramScene.vue   # Three.js 主场景
│   │       ├── TrigramMesh.vue     # 八卦 3D 模型
│   │       ├── Particles.vue       # 粒子系统
│   │       └── useScene3D.ts       # 3D composable
│   ├── layout/
│   │   ├── AppShell.vue            # 整体布局壳
│   │   ├── Sidebar.vue             # 侧边导航
│   │   ├── Header.vue              # 顶栏
│   │   └── Footer.vue
│   └── shared/
│       ├── InkBrush.vue            # 水墨笔触装饰
│       ├── GlowBorder.vue          # 赛博发光边框
│       ├── ScrollReveal.vue        # 滚动揭示动画
│       └── TransitionOrchestrator.vue  # 页面转场编排
├── composables/
│   ├── useAnimation.ts             # GSAP 通用动画
│   ├── useBreakpoint.ts            # 响应式断点
│   ├── useColorScheme.ts           # 主题切换
│   ├── useInkEffect.ts             # 水墨效果
│   ├── useParticleField.ts         # 粒子场
│   ├── useReducedMotion.ts         # 无障碍：减少动画
│   └── useTheme.ts                 # 主题管理
├── engine/                         # 前端确定性引擎（纯函数，无副作用）
│   ├── hexagram.ts                 # 卦象计算
│   ├── wuxing.ts                   # 五行关系
│   ├── liuqin.ts                   # 六亲推导
│   ├── najia.ts                    # 纳甲规则
│   ├── ganzhi.ts                   # 干支计算
│   └── evolution.ts                # 状态演化逻辑
├── lib/
│   ├── cytoscape-config.ts         # Cytoscape 样式与布局配置
│   ├── three-materials.ts          # Three.js 材质库
│   ├── gsap-presets.ts             # GSAP 动画预设
│   ├── d3-layouts.ts               # D3 布局算法封装
│   └── shader-chunks.ts            # GLSL 着色器片段
├── pages/
│   ├── index.vue                   # 首页（太极 + 入口）
│   ├── divination/
│   │   ├── index.vue               # 起卦页
│   │   └── [id].vue                # 卦详情页（排盘 + 图谱 + 演化）
│   ├── graph/
│   │   └── index.vue               # 知识图谱全屏页
│   ├── evolution/
│   │   └── index.vue               # 演化时间轴页
│   └── settings/
│       └── index.vue               # 设置页
├── plugins/
│   ├── gsap.client.ts              # GSAP 客户端插件
│   ├── three.client.ts             # Three.js 客户端插件
│   └── cytoscape.client.ts         # Cytoscape 客户端插册
├── stores/
│   ├── hexagram.ts                 # 卦象状态
│   ├── divination.ts               # 占卜会话状态
│   ├── graph.ts                    # 图谱交互状态
│   ├── evolution.ts                # 演化状态
│   ├── theme.ts                    # 主题状态
│   └── user.ts                     # 用户状态
├── types/
│   ├── hexagram.ts                 # 卦象类型定义
│   ├── wuxing.ts                   # 五行类型
│   ├── graph.ts                    # 图谱数据类型
│   └── animation.ts                # 动画参数类型
├── app.vue
├── nuxt.config.ts
└── tailwind.config.ts
```

### 1.2 模块划分

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          YI-AI 前端模块总览                               │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │                        展示层 (Presentation)                        │ │
│  │  Pages → Layout → Components → Visualization                       │ │
│  └──────────────────────────────┬──────────────────────────────────────┘ │
│                                 │                                        │
│  ┌──────────────────────────────▼──────────────────────────────────────┐ │
│  │                        状态层 (State)                                │ │
│  │  Pinia Stores ← Composables ← Engine (纯函数)                      │ │
│  └──────────────────────────────┬──────────────────────────────────────┘ │
│                                 │                                        │
│  ┌──────────────────────────────▼──────────────────────────────────────┐ │
│  │                        服务层 (Service)                              │ │
│  │  API Routes (Nuxt) / WebSocket / SSR Data Fetching                 │ │
│  └──────────────────────────────┬──────────────────────────────────────┘ │
│                                 │                                        │
│  ┌──────────────────────────────▼──────────────────────────────────────┐ │
│  │                        渲染层 (Renderer)                             │ │
│  │  Canvas 2D (太极) │ SVG/D3 (演化树) │ WebGL/Three.js (3D)         │ │
│  │  Cytoscape Canvas (图谱) │ DOM/CSS (六爻排盘)                       │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
```

### 1.3 状态管理 (Pinia)

```typescript
// stores/hexagram.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { HexagramData, YaoLine, WuXingElement } from '~/types/hexagram'

export const useHexagramStore = defineStore('hexagram', () => {
  // --- State ---
  const currentHexagram = ref<HexagramData | null>(null)
  const changedHexagram = ref<HexagramData | null>(null)
  const movingLines = ref<number[]>([])      // 动爻位置 [1-6]
  const history = ref<HexagramData[]>([])     // 历史卦记录

  // --- Getters ---
  const yaoLines = computed<YaoLine[]>(() => {
    return currentHexagram.value?.lines ?? []
  })

  const hasMovingLines = computed(() => movingLines.value.length > 0)

  const fiveElements = computed(() => {
    const elements = new Set<WuXingElement>()
    yaoLines.value.forEach(l => elements.add(l.element))
    return [...elements]
  })

  // --- Actions ---
  function setHexagram(data: HexagramData) {
    currentHexagram.value = Object.freeze(data)  // 不可变
    history.value = [...history.value, data]
  }

  function setMovingLines(positions: number[]) {
    movingLines.value = [...positions]
  }

  function setChangedHexagram(data: HexagramData) {
    changedHexagram.value = Object.freeze(data)
  }

  function clearSession() {
    currentHexagram.value = null
    changedHexagram.value = null
    movingLines.value = []
  }

  return {
    currentHexagram, changedHexagram, movingLines, history,
    yaoLines, hasMovingLines, fiveElements,
    setHexagram, setMovingLines, setChangedHexagram, clearSession,
  }
})
```

```typescript
// stores/divination.ts
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useDivinationStore = defineStore('divination', () => {
  const phase = ref<'idle' | 'casting' | 'resolving' | 'interpreting' | 'complete'>('idle')
  const question = ref('')
  const aiInterpretation = ref('')
  const streamingText = ref('')
  const sessionId = ref<string | null>(null)

  function startCasting(q: string) {
    phase.value = 'casting'
    question.value = q
    streamingText.value = ''
    aiInterpretation.value = ''
  }

  function setPhase(p: typeof phase.value) {
    phase.value = p
  }

  function appendStreamChunk(chunk: string) {
    streamingText.value += chunk
  }

  function finalizeInterpretation(text: string) {
    aiInterpretation.value = text
    phase.value = 'complete'
  }

  return {
    phase, question, aiInterpretation, streamingText, sessionId,
    startCasting, setPhase, appendStreamChunk, finalizeInterpretation,
  }
})
```

```typescript
// stores/graph.ts
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useGraphStore = defineStore('graph', () => {
  const selectedNodeId = ref<string | null>(null)
  const filterTypes = ref<string[]>(['Hexagram', 'Element', 'Role', 'Trigram'])
  const layoutAlgorithm = ref<'cose' | 'dagre' | 'circle' | 'concentric'>('cose')
  const hoverDepth = ref(2)              // 悬停时展开的跳数
  const isFullscreen = ref(false)

  function selectNode(id: string | null) {
    selectedNodeId.value = id
  }

  function toggleFilter(type: string) {
    const idx = filterTypes.value.indexOf(type)
    if (idx >= 0) filterTypes.value.splice(idx, 1)
    else filterTypes.value.push(type)
  }

  return {
    selectedNodeId, filterTypes, layoutAlgorithm, hoverDepth, isFullscreen,
    selectNode, toggleFilter,
  }
})
```

### 1.4 数据流架构

```
用户操作
    │
    ▼
┌─────────────────────────────────────────────┐
│  Vue Component (响应式视图)                    │
│    │                                         │
│    ▼                                         │
│  Composable (useXxx)                         │
│    │  - 封装 GSAP/D3/Cytoscape 实例          │
│    │  - 管理生命周期 (onMounted/onUnmounted)   │
│    ▼                                         │
│  Pinia Store (全局状态)                        │
│    │  - 卦象数据、图谱数据、演化数据            │
│    │  - 不可变更新                             │
│    ▼                                         │
│  Engine (纯函数计算)                           │
│    │  - 五行生克、六亲推导、纳甲               │
│    │  - 状态演化、概率树生成                   │
│    ▼                                         │
│  API Layer (Nuxt useFetch / $fetch)          │
│    │  - SSR 数据预取                          │
│    │  - WebSocket 流式接收                    │
│    ▼                                         │
│  后端 FastAPI / WebSocket                     │
└─────────────────────────────────────────────┘
```

### 1.5 SSR / 客户端策略

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  ssr: true,

  // 可视化重型组件仅客户端渲染
  build: {
    transpile: ['three', 'gsap', 'cytoscape'],
  },

  // 组件自动导入策略
  components: [
    { path: '~/components/ui', prefix: '' },
    { path: '~/components/visualization', prefix: 'Viz' },
    { path: '~/components/layout', prefix: '' },
    { path: '~/components/shared', prefix: '' },
  ],

  // 动态导入重型可视化库
  experimental: {
    payloadExtraction: true,
  },

  // 优化 CSS
  css: [
    '~/assets/styles/tokens.css',
    '~/assets/styles/global.css',
  ],
})
```

需要在浏览器环境运行的可视化组件使用 `<ClientOnly>` 包裹：

```vue
<!-- pages/divination/[id].vue -->
<template>
  <div class="divination-page">
    <!-- SSR: 排盘数据、文本内容 -->
    <GuaCard :hexagram="hexagram" />

    <!-- CSR: 可视化动画 -->
    <ClientOnly>
      <VizTaijiCanvas :hexagram="hexagram" />
      <VizKnowledgeGraph :hexagram-name="hexagram.name" />
      <VizEvolutionTree :chain="evolutionChain" />
    </ClientOnly>
  </div>
</template>
```

---

## 2. 设计系统

### 2.1 设计 Token

#### CSS 自定义属性定义

```css
/* assets/styles/tokens.css */

:root {
  /* ===================== 色彩系统 ===================== */

  /* --- 基础色板 (赛博东方) --- */
  --yi-black-void:    oklch(5% 0.01 270);       /* 深渊黑 - 主背景 */
  --yi-black-deep:    oklch(10% 0.01 270);      /* 深黑 - 卡片背景 */
  --yi-black-surface: oklch(15% 0.015 270);     /* 表面黑 - 面板 */
  --yi-black-elevated:oklch(20% 0.015 270);     /* 抬升黑 - 弹窗 */

  --yi-gold-bright:   oklch(85% 0.18 85);       /* 明金 - 强调、标题 */
  --yi-gold-primary:  oklch(75% 0.16 80);       /* 主金 - 主要元素 */
  --yi-gold-muted:    oklch(55% 0.12 75);       /* 暗金 - 次要文字 */
  --yi-gold-ghost:    oklch(35% 0.08 75);       /* 幽金 - 装饰线条 */

  --yi-ink-white:     oklch(95% 0.01 270);      /* 宣纸白 - 主文字 */
  --yi-ink-light:     oklch(75% 0.01 270);      /* 淡墨 - 次文字 */
  --yi-ink-medium:    oklch(50% 0.01 270);      /* 中墨 - 辅助 */

  /* --- 五行色 --- */
  --yi-wuxing-jin:    oklch(80% 0.12 90);       /* 金 - 白/金 */
  --yi-wuxing-mu:     oklch(65% 0.18 145);      /* 木 - 青 */
  --yi-wuxing-shui:   oklch(55% 0.15 250);      /* 水 - 黑/蓝 */
  --yi-wuxing-huo:    oklch(65% 0.22 25);       /* 火 - 赤/红 */
  --yi-wuxing-tu:     oklch(70% 0.10 80);       /* 土 - 黄 */

  /* --- 状态色 --- */
  --yi-status-yang:   oklch(90% 0.05 85);       /* 阳 - 明亮 */
  --yi-status-yin:    oklch(30% 0.05 250);       /* 阴 - 深沉 */
  --yi-status-moving: oklch(70% 0.22 30);       /* 动爻 - 橙红警示 */
  --yi-status-static: oklch(50% 0.05 270);       /* 静爻 - 中性 */

  /* --- 发光效果色 --- */
  --yi-glow-gold:     oklch(80% 0.18 85 / 0.6);
  --yi-glow-cyan:     oklch(75% 0.12 200 / 0.5);
  --yi-glow-magenta:  oklch(65% 0.20 330 / 0.4);

  /* ===================== 排版系统 ===================== */

  /* --- 字体族 --- */
  --yi-font-display:  'LXGW WenKai', 'Noto Serif SC', serif;  /* 标题: 霞鹜文楷 */
  --yi-font-body:     'Noto Sans SC', system-ui, sans-serif;   /* 正文 */
  --yi-font-mono:     'JetBrains Mono', 'Fira Code', monospace; /* 数字/代码 */
  --yi-font-gua:      'SimSun', 'Songti SC', serif;            /* 卦象符号 */

  /* --- 字号 (流式缩放) --- */
  --yi-text-xs:    clamp(0.70rem, 0.66rem + 0.20vw, 0.80rem);
  --yi-text-sm:    clamp(0.80rem, 0.75rem + 0.25vw, 0.90rem);
  --yi-text-base:  clamp(0.95rem, 0.88rem + 0.35vw, 1.10rem);
  --yi-text-lg:    clamp(1.10rem, 1.00rem + 0.50vw, 1.35rem);
  --yi-text-xl:    clamp(1.30rem, 1.10rem + 1.00vw, 1.80rem);
  --yi-text-2xl:   clamp(1.60rem, 1.30rem + 1.50vw, 2.40rem);
  --yi-text-3xl:   clamp(2.00rem, 1.50rem + 2.50vw, 3.50rem);
  --yi-text-hero:  clamp(3.00rem, 1.50rem + 7.50vw, 8.00rem);

  /* --- 行高 --- */
  --yi-leading-tight:  1.25;
  --yi-leading-normal: 1.60;
  --yi-leading-loose:  1.80;

  /* --- 字重 --- */
  --yi-weight-regular: 400;
  --yi-weight-medium:  500;
  --yi-weight-bold:    700;

  /* ===================== 间距系统 ===================== */

  --yi-space-1:   clamp(0.25rem, 0.22rem + 0.15vw, 0.35rem);
  --yi-space-2:   clamp(0.50rem, 0.44rem + 0.30vw, 0.70rem);
  --yi-space-3:   clamp(0.75rem, 0.66rem + 0.45vw, 1.05rem);
  --yi-space-4:   clamp(1.00rem, 0.88rem + 0.60vw, 1.40rem);
  --yi-space-6:   clamp(1.50rem, 1.30rem + 1.00vw, 2.10rem);
  --yi-space-8:   clamp(2.00rem, 1.75rem + 1.25vw, 2.80rem);
  --yi-space-12:  clamp(3.00rem, 2.60rem + 2.00vw, 4.20rem);
  --yi-space-16:  clamp(4.00rem, 3.50rem + 2.50vw, 5.60rem);
  --yi-space-24:  clamp(6.00rem, 5.20rem + 4.00vw, 8.40rem);

  /* --- 区块间距 (Section) --- */
  --yi-space-section: clamp(4rem, 3rem + 5vw, 10rem);

  /* ===================== 圆角 ===================== */

  --yi-radius-sm:   4px;
  --yi-radius-md:   8px;
  --yi-radius-lg:   16px;
  --yi-radius-xl:   24px;
  --yi-radius-full: 9999px;

  /* ===================== 阴影 ===================== */

  --yi-shadow-sm:
    0 1px 2px oklch(0% 0 0 / 0.25);
  --yi-shadow-md:
    0 4px 12px oklch(0% 0 0 / 0.30),
    0 1px 3px oklch(0% 0 0 / 0.20);
  --yi-shadow-lg:
    0 12px 40px oklch(0% 0 0 / 0.40),
    0 4px 12px oklch(0% 0 0 / 0.25);
  --yi-shadow-glow:
    0 0 20px var(--yi-glow-gold),
    0 0 60px oklch(80% 0.18 85 / 0.20);
  --yi-shadow-cyber:
    0 0 2px var(--yi-glow-cyan),
    0 0 8px var(--yi-glow-cyan),
    inset 0 0 4px oklch(75% 0.12 200 / 0.10);

  /* ===================== 边框 ===================== */

  --yi-border-subtle:  1px solid oklch(25% 0.01 270);
  --yi-border-gold:    1px solid var(--yi-gold-ghost);
  --yi-border-glow:    1px solid oklch(80% 0.18 85 / 0.30);

  /* ===================== 动效 ===================== */

  --yi-duration-instant: 100ms;
  --yi-duration-fast:    200ms;
  --yi-duration-normal:  400ms;
  --yi-duration-slow:    800ms;
  --yi-duration-reveal:  1200ms;

  --yi-ease-out-expo:  cubic-bezier(0.16, 1, 0.3, 1);
  --yi-ease-out-back:  cubic-bezier(0.34, 1.56, 0.64, 1);
  --yi-ease-in-expo:   cubic-bezier(0.7, 0, 0.84, 0);
  --yi-ease-inout:     cubic-bezier(0.45, 0, 0.55, 1);

  /* ===================== Z-Index 层级 ===================== */

  --yi-z-base:     0;
  --yi-z-above:    10;
  --yi-z-overlay:  100;
  --yi-z-modal:    200;
  --yi-z-toast:    300;
  --yi-z-tooltip:  400;
}

/* ===================== 暗色主题 (默认) ===================== */
[data-theme="dark"] {
  /* 暗色主题即默认值，无需覆盖 */
}

/* ===================== 亮色主题 (扩展) ===================== */
[data-theme="light"] {
  --yi-black-void:    oklch(97% 0.005 85);
  --yi-black-deep:    oklch(94% 0.008 85);
  --yi-black-surface: oklch(91% 0.010 85);
  --yi-black-elevated:oklch(88% 0.010 85);
  --yi-ink-white:     oklch(12% 0.02 270);
  --yi-ink-light:     oklch(35% 0.02 270);
  --yi-ink-medium:    oklch(55% 0.02 270);
  --yi-gold-bright:   oklch(50% 0.18 80);
  --yi-gold-primary:  oklch(45% 0.15 80);
  --yi-shadow-glow:
    0 0 20px oklch(50% 0.18 85 / 0.30),
    0 0 60px oklch(50% 0.18 85 / 0.10);
}
```

### 2.2 组件库规范 (shadcn-vue 扩展)

基于 shadcn-vue 的 `New York` 风格，覆盖主题变量以适配赛博东方风格：

```typescript
// tailwind.config.ts
import type { Config } from 'tailwindcss'

export default <Config>{
  darkMode: ['class', '[data-theme="dark"]'],
  content: [
    './components/**/*.{vue,ts}',
    './layouts/**/*.vue',
    './pages/**/*.vue',
    './app.vue',
  ],
  theme: {
    extend: {
      colors: {
        yi: {
          void:    'var(--yi-black-void)',
          deep:    'var(--yi-black-deep)',
          surface: 'var(--yi-black-surface)',
          elevated:'var(--yi-black-elevated)',
          gold:    {
            bright: 'var(--yi-gold-bright)',
            DEFAULT:'var(--yi-gold-primary)',
            muted:  'var(--yi-gold-muted)',
            ghost:  'var(--yi-gold-ghost)',
          },
          ink: {
            DEFAULT:'var(--yi-ink-white)',
            light:  'var(--yi-ink-light)',
            medium: 'var(--yi-ink-medium)',
          },
          wuxing: {
            jin:  'var(--yi-wuxing-jin)',
            mu:   'var(--yi-wuxing-mu)',
            shui: 'var(--yi-wuxing-shui)',
            huo:  'var(--yi-wuxing-huo)',
            tu:   'var(--yi-wuxing-tu)',
          },
        },
      },
      fontFamily: {
        display: ['var(--yi-font-display)'],
        body:    ['var(--yi-font-body)'],
        mono:    ['var(--yi-font-mono)'],
        gua:     ['var(--yi-font-gua)'],
      },
      fontSize: {
        xs:    'var(--yi-text-xs)',
        sm:    'var(--yi-text-sm)',
        base:  'var(--yi-text-base)',
        lg:    'var(--yi-text-lg)',
        xl:    'var(--yi-text-xl)',
        '2xl': 'var(--yi-text-2xl)',
        '3xl': 'var(--yi-text-3xl)',
        hero:  'var(--yi-text-hero)',
      },
      spacing: {
        'yi-1': 'var(--yi-space-1)',
        'yi-2': 'var(--yi-space-2)',
        'yi-3': 'var(--yi-space-3)',
        'yi-4': 'var(--yi-space-4)',
        'yi-6': 'var(--yi-space-6)',
        'yi-8': 'var(--yi-space-8)',
        'yi-12':'var(--yi-space-12)',
        'yi-16':'var(--yi-space-16)',
        'yi-24':'var(--yi-space-24)',
        'yi-section': 'var(--yi-space-section)',
      },
      borderRadius: {
        yi: 'var(--yi-radius-md)',
      },
      boxShadow: {
        yi:       'var(--yi-shadow-md)',
        'yi-lg':  'var(--yi-shadow-lg)',
        'yi-glow':'var(--yi-shadow-glow)',
        'yi-cyber':'var(--yi-shadow-cyber)',
      },
      transitionDuration: {
        yi:       'var(--yi-duration-normal)',
        'yi-fast':'var(--yi-duration-fast)',
        'yi-slow':'var(--yi-duration-slow)',
      },
      transitionTimingFunction: {
        'yi-expo':   'var(--yi-ease-out-expo)',
        'yi-back':   'var(--yi-ease-out-back)',
        'yi-expo-in':'var(--yi-ease-in-expo)',
      },
      keyframes: {
        'ink-spread': {
          '0%':   { transform: 'scale(0)', opacity: '0.8' },
          '100%': { transform: 'scale(1)', opacity: '0' },
        },
        'glow-pulse': {
          '0%, 100%': { opacity: '0.4' },
          '50%':      { opacity: '1' },
        },
        'cyber-scan': {
          '0%':   { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' },
        },
      },
      animation: {
        'ink-spread':  'ink-spread 1.5s var(--yi-ease-out-expo) forwards',
        'glow-pulse':  'glow-pulse 3s ease-in-out infinite',
        'cyber-scan':  'cyber-scan 4s linear infinite',
      },
    },
  },
}
```

### 2.3 主题系统

```typescript
// composables/useTheme.ts
import { ref, watch, onMounted } from 'vue'

type Theme = 'dark' | 'light'
type AccentMode = 'gold' | 'cyan' | 'magenta'

const theme = ref<Theme>('dark')
const accent = ref<AccentMode>('gold')

export function useTheme() {
  function setTheme(t: Theme) {
    theme.value = t
    document.documentElement.setAttribute('data-theme', t)
    localStorage.setItem('yi-theme', t)
  }

  function toggleTheme() {
    setTheme(theme.value === 'dark' ? 'light' : 'dark')
  }

  function setAccent(a: AccentMode) {
    accent.value = a
    document.documentElement.setAttribute('data-accent', a)
  }

  onMounted(() => {
    const saved = localStorage.getItem('yi-theme') as Theme | null
    if (saved) setTheme(saved)
    else if (window.matchMedia('(prefers-color-scheme: light)').matches) {
      setTheme('light')
    }
  })

  return { theme, accent, setTheme, toggleTheme, setAccent }
}
```

### 2.4 全局样式

```css
/* assets/styles/global.css */

/* --- 基础重置 --- */
*,
*::before,
*::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html {
  font-family: var(--yi-font-body);
  font-size: 16px;
  line-height: var(--yi-leading-normal);
  color: var(--yi-ink-white);
  background-color: var(--yi-black-void);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}

body {
  min-height: 100dvh;
  overflow-x: hidden;
}

/* --- 无障碍: 减少动画 --- */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

/* --- 滚动条 (赛博东方) --- */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: var(--yi-black-deep);
}

::-webkit-scrollbar-thumb {
  background: var(--yi-gold-ghost);
  border-radius: var(--yi-radius-full);
}

::-webkit-scrollbar-thumb:hover {
  background: var(--yi-gold-muted);
}

/* --- 选区颜色 --- */
::selection {
  background-color: oklch(80% 0.18 85 / 0.30);
  color: var(--yi-gold-bright);
}

/* --- 焦点环 --- */
:focus-visible {
  outline: 2px solid var(--yi-gold-primary);
  outline-offset: 2px;
}

/* --- 水墨纹理叠加层 --- */
.ink-texture::after {
  content: '';
  position: absolute;
  inset: 0;
  background-image: url('/textures/ink-noise.webp');
  background-size: 256px 256px;
  opacity: 0.04;
  pointer-events: none;
  mix-blend-mode: overlay;
}

/* --- 赛博扫描线 --- */
.cyber-scanline::before {
  content: '';
  position: absolute;
  inset: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    oklch(75% 0.12 200 / 0.03) 2px,
    oklch(75% 0.12 200 / 0.03) 4px
  );
  pointer-events: none;
}

/* --- 金边发光框 --- */
.glow-border {
  border: var(--yi-border-glow);
  box-shadow: var(--yi-shadow-glow);
}
```

---

## 3. 太极动画系统

### 3.1 技术方案

采用 **Canvas 2D + requestAnimationFrame** 作为主渲染方案，辅以 CSS transform 实现外圈卦象环的旋转。

选择 Canvas 2D 而非 WebGL 的原因：
- 太极图形以 2D 矢量绘制为主，Canvas 2D 的 `arc`、`bezierCurveTo` 性能足够
- 复杂度远低于 3D 场景，无需 GPU 加速
- 兼容性更好，降级成本低
- 外圈使用 DOM + CSS transform 可获得 GPU 合成层加速

### 3.2 太极核心绘制

```typescript
// composables/useTaiji.ts
import { ref, onMounted, onUnmounted, watch, type Ref } from 'vue'

interface TaijiConfig {
  size: number            // 画布尺寸 (px)
  rotationSpeed: number   // 旋转速度 (rad/s)
  breatheAmplitude: number // 呼吸幅度 (0-1)
  breatheSpeed: number    // 呼吸频率 (Hz)
  colorYang: string       // 阳色
  colorYin: string        // 阴色
  colorGlow: string       // 发光色
  particleCount: number   // 粒子数量
}

const DEFAULT_CONFIG: TaijiConfig = {
  size: 400,
  rotationSpeed: 0.15,
  breatheAmplitude: 0.03,
  breatheSpeed: 0.4,
  colorYang: '#f5e6c8',   // 暖白（宣纸色）
  colorYin: '#1a1a2e',    // 深空蓝黑
  colorGlow: '#d4a843',   // 金辉
  particleCount: 60,
}

export function useTaiji(
  canvasRef: Ref<HTMLCanvasElement | null>,
  config: Partial<TaijiConfig> = {},
) {
  const cfg = { ...DEFAULT_CONFIG, ...config }
  const rotation = ref(0)
  const breathe = ref(0)
  let animationId: number | null = null
  let ctx: CanvasRenderingContext2D | null = null
  let lastTime = 0

  // 粒子系统
  interface Particle {
    angle: number
    radius: number
    speed: number
    size: number
    opacity: number
    phase: number
  }

  const particles: Particle[] = []

  function initParticles() {
    particles.length = 0
    for (let i = 0; i < cfg.particleCount; i++) {
      particles.push({
        angle: Math.random() * Math.PI * 2,
        radius: cfg.size * 0.35 + Math.random() * cfg.size * 0.18,
        speed: 0.2 + Math.random() * 0.4,
        size: 0.5 + Math.random() * 2,
        opacity: 0.1 + Math.random() * 0.5,
        phase: Math.random() * Math.PI * 2,
      })
    }
  }

  // 绘制太极阴阳鱼
  function drawTaiji(c: CanvasRenderingContext2D, cx: number, cy: number, r: number, rot: number) {
    c.save()
    c.translate(cx, cy)
    c.rotate(rot)

    // 外圆 - 阳面（右半）
    c.beginPath()
    c.arc(0, 0, r, -Math.PI / 2, Math.PI / 2)
    c.fillStyle = cfg.colorYang
    c.fill()

    // 外圆 - 阴面（左半）
    c.beginPath()
    c.arc(0, 0, r, Math.PI / 2, -Math.PI / 2)
    c.fillStyle = cfg.colorYin
    c.fill()

    // 阳中阴弧 (S 曲线左半)
    c.beginPath()
    c.arc(0, -r / 2, r / 2, Math.PI / 2, -Math.PI / 2)
    c.fillStyle = cfg.colorYin
    c.fill()

    // 阴中阳弧 (S 曲线右半)
    c.beginPath()
    c.arc(0, r / 2, r / 2, -Math.PI / 2, Math.PI / 2)
    c.fillStyle = cfg.colorYang
    c.fill()

    // 阳眼（阴面中的阳点）
    c.beginPath()
    c.arc(0, -r / 2, r * 0.1, 0, Math.PI * 2)
    c.fillStyle = cfg.colorYang
    c.fill()

    // 阴眼（阳面中的阴点）
    c.beginPath()
    c.arc(0, r / 2, r * 0.1, 0, Math.PI * 2)
    c.fillStyle = cfg.colorYin
    c.fill()

    c.restore()
  }

  // 绘制金辉光晕
  function drawGlow(c: CanvasRenderingContext2D, cx: number, cy: number, r: number) {
    const gradient = c.createRadialGradient(cx, cy, r * 0.8, cx, cy, r * 1.4)
    gradient.addColorStop(0, 'transparent')
    gradient.addColorStop(0.6, 'transparent')
    gradient.addColorStop(0.8, `${cfg.colorGlow}15`)
    gradient.addColorStop(1, 'transparent')
    c.fillStyle = gradient
    c.fillRect(cx - r * 1.5, cy - r * 1.5, r * 3, r * 3)
  }

  // 绘制环绕粒子
  function drawParticles(c: CanvasRenderingContext2D, cx: number, cy: number, time: number) {
    for (const p of particles) {
      const a = p.angle + time * p.speed
      const wobble = Math.sin(time * 2 + p.phase) * 4
      const x = cx + Math.cos(a) * (p.radius + wobble)
      const y = cy + Math.sin(a) * (p.radius + wobble)
      const pulse = 0.5 + 0.5 * Math.sin(time * 3 + p.phase)

      c.beginPath()
      c.arc(x, y, p.size * pulse, 0, Math.PI * 2)
      c.fillStyle = `${cfg.colorGlow}${Math.round(p.opacity * pulse * 255).toString(16).padStart(2, '0')}`
      c.fill()
    }
  }

  function frame(timestamp: number) {
    if (!ctx || !canvasRef.value) return

    const dt = lastTime ? (timestamp - lastTime) / 1000 : 0.016
    lastTime = timestamp

    // 更新状态
    rotation.value += cfg.rotationSpeed * dt
    breathe.value = Math.sin(timestamp / 1000 * cfg.breatheSpeed * Math.PI * 2) * cfg.breatheAmplitude

    const c = ctx
    const w = canvasRef.value.width
    const h = canvasRef.value.height
    const cx = w / 2
    const cy = h / 2
    const baseR = Math.min(w, h) / 2 * 0.6
    const r = baseR * (1 + breathe.value)

    // 清除
    c.clearRect(0, 0, w, h)

    // 绘制
    drawGlow(c, cx, cy, r)
    drawParticles(c, cx, cy, timestamp / 1000)
    drawTaiji(c, cx, cy, r, rotation.value)

    animationId = requestAnimationFrame(frame)
  }

  function start() {
    const canvas = canvasRef.value
    if (!canvas) return

    // 设置 DPR
    const dpr = window.devicePixelRatio || 1
    const rect = canvas.getBoundingClientRect()
    canvas.width = rect.width * dpr
    canvas.height = rect.height * dpr

    ctx = canvas.getContext('2d')
    if (ctx) ctx.scale(dpr, dpr)

    initParticles()
    animationId = requestAnimationFrame(frame)
  }

  function stop() {
    if (animationId !== null) {
      cancelAnimationFrame(animationId)
      animationId = null
    }
  }

  // 无障碍：检测减少动画偏好
  const prefersReducedMotion = ref(false)

  function checkReducedMotion() {
    prefersReducedMotion.value = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (prefersReducedMotion.value) {
      cfg.rotationSpeed = 0
      cfg.breatheAmplitude = 0
      cfg.particleCount = 0
    }
  }

  onMounted(() => {
    checkReducedMotion()
    start()
  })

  onUnmounted(() => {
    stop()
  })

  return {
    rotation,
    breathe,
    prefersReducedMotion,
    start,
    stop,
  }
}
```

### 3.3 太极 Vue 组件

```vue
<!-- components/visualization/taiji/TaijiCanvas.vue -->
<script setup lang="ts">
import { ref } from 'vue'
import { useTaiji } from './useTaiji'

interface Props {
  size?: number
  rotationSpeed?: number
  breatheAmplitude?: number
}

const props = withDefaults(defineProps<Props>(), {
  size: 400,
  rotationSpeed: 0.15,
  breatheAmplitude: 0.03,
})

const canvasRef = ref<HTMLCanvasElement | null>(null)

const { rotation, breathe, prefersReducedMotion } = useTaiji(canvasRef, {
  size: props.size,
  rotationSpeed: props.rotationSpeed,
  breatheAmplitude: props.breatheAmplitude,
})
</script>

<template>
  <div
    class="taiji-container"
    :style="{ width: `${size}px`, height: `${size}px` }"
    role="img"
    aria-label="太极阴阳动态图"
  >
    <canvas
      ref="canvasRef"
      class="taiji-canvas"
      :width="size"
      :height="size"
      :style="{ width: `${size}px`, height: `${size}px` }"
    />

    <!-- 外圈卦象环 (CSS transform, GPU 合成层) -->
    <div
      class="taiji-ring"
      :style="{ transform: `rotate(${rotation}rad)` }"
    >
      <span
        v-for="(gua, i) in ['☰','☱','☲','☳','☴','坎','☶','☷']"
        :key="gua"
        class="gua-symbol"
        :style="{ transform: `rotate(${i * 45}deg) translateY(-${size * 0.42}px)` }"
        aria-hidden="true"
      >
        {{ gua }}
      </span>
    </div>

    <!-- 无障碍: 静态替代 -->
    <div v-if="prefersReducedMotion" class="taiji-static" aria-hidden="true">
      <span class="taiji-yin">阴</span>
      <span class="taiji-yang">阳</span>
    </div>
  </div>
</template>

<style scoped>
.taiji-container {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.taiji-canvas {
  position: absolute;
  inset: 0;
}

.taiji-ring {
  position: absolute;
  inset: 0;
  will-change: transform;
}

.gua-symbol {
  position: absolute;
  left: 50%;
  top: 50%;
  font-family: var(--yi-font-gua);
  font-size: 1.25rem;
  color: var(--yi-gold-muted);
  transform-origin: 0 0;
  user-select: none;
}

.taiji-static {
  display: flex;
  gap: var(--yi-space-4);
  font-family: var(--yi-font-display);
  font-size: var(--yi-text-2xl);
  color: var(--yi-gold-primary);
}
</style>
```

### 3.4 性能优化

| 策略 | 实现 | 效果 |
|------|------|------|
| DPR 适配 | `canvas.width = rect.width * dpr` + `ctx.scale(dpr, dpr)` | 高清无模糊 |
| 减少重绘 | Canvas 仅在 `requestAnimationFrame` 中绘制，无额外触发 | 稳定 60fps |
| 减少 GC | 粒子数组预分配，避免每帧创建对象 | 零 GC 压力 |
| 可见性暂停 | `IntersectionObserver` 检测可见性，不可见时暂停 | 节省 CPU |
| 无障碍降级 | `prefers-reduced-motion` 时停止旋转和粒子 | 可访问性 |
| GPU 合成层 | 外圈卦象环使用 `will-change: transform` + CSS transform | 独立合成层 |

```typescript
// 可见性暂停优化
const observer = new IntersectionObserver(([entry]) => {
  if (entry.isIntersecting) start()
  else stop()
}, { threshold: 0.1 })

onMounted(() => {
  if (canvasRef.value) observer.observe(canvasRef.value)
})

onUnmounted(() => {
  observer.disconnect()
  stop()
})
```

---

## 4. 六爻排盘组件

### 4.1 组件架构

```
LiuyaoBoard.vue
├── GuaHeader.vue              # 卦名、卦辞
├── SixSpiritsRow.vue          # 六神行
├── YaoRow × 6                 # 六爻行 (从上到下)
│   ├── YaoPosition.vue        # 爻位标识
│   ├── YaoLine.vue            # 爻线 (阴/阳/动)
│   │   └── YaoFlip.vue        # 动爻翻转动画
│   ├── YaoNajia.vue           # 纳甲 (干支)
│   ├── YaoSixQin.vue          # 六亲
│   ├── YaoWorldResponse.vue   # 世应标记
│   └── YaoText.vue            # 爻辞
├── GuaChanged.vue             # 变卦区域
└── GuaFooter.vue              # 错卦/综卦/互卦
```

### 4.2 爻线绘制

```typescript
// composables/useLiuyao.ts
import { computed, ref } from 'vue'
import type { YaoLine, HexagramData } from '~/types/hexagram'

export interface YaoDisplayData {
  position: number         // 1-6 (从下到上)
  yinYang: 'yin' | 'yang'
  isMoving: boolean
  isWorld: boolean         // 世爻
  isResponse: boolean      // 应爻
  najia: string            // 纳甲 (如 "甲子")
  sixQin: string           // 六亲
  sixSpirit: string        // 六神
  text: string             // 爻辞
  element: string          // 五行
}

export function useLiuyao(hexagram: () => HexagramData | null) {
  const movingFlipStates = ref<Map<number, boolean>>(new Map())

  const displayLines = computed<YaoDisplayData[]>(() => {
    const h = hexagram()
    if (!h) return []
    return h.lines.map((line, i) => ({
      position: i + 1,
      yinYang: line.yinYang,
      isMoving: h.movingLines.includes(i + 1),
      isWorld: h.worldPosition === i + 1,
      isResponse: h.responsePosition === i + 1,
      najia: line.najia,
      sixQin: line.sixQin,
      sixSpirit: line.sixSpirit,
      text: line.text,
      element: line.element,
    }))
  })

  function triggerFlip(position: number) {
    movingFlipStates.value.set(position, true)
    // GSAP 翻转动画完成后重置
    setTimeout(() => {
      movingFlipStates.value.set(position, false)
    }, 800)
  }

  function triggerAllMovingFlips() {
    const h = hexagram()
    if (!h) return
    h.movingLines.forEach((pos, i) => {
      setTimeout(() => triggerFlip(pos), i * 200)
    })
  }

  return {
    displayLines,
    movingFlipStates,
    triggerFlip,
    triggerAllMovingFlips,
  }
}
```

### 4.3 爻行 Vue 组件

```vue
<!-- components/visualization/liuyao/YaoRow.vue -->
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { gsap } from 'gsap'
import type { YaoDisplayData } from './useLiuyao'

interface Props {
  data: YaoDisplayData
  isFlipping: boolean
  index: number      // 0-5，用于入场动画延迟
}

const props = defineProps<Props>()

const lineRef = ref<HTMLDivElement | null>(null)
const flipContainerRef = ref<HTMLDivElement | null>(null)

// 爻线样式
const lineClasses = computed(() => ({
  'yao-line': true,
  'yao-line--yang': props.data.yinYang === 'yang',
  'yao-line--yin': props.data.yinYang === 'yin',
  'yao-line--moving': props.data.isMoving,
  'yao-line--world': props.data.isWorld,
  'yao-line--response': props.data.isResponse,
}))

// 六亲色彩映射
const sixQinColor = computed(() => {
  const map: Record<string, string> = {
    '父母': 'var(--yi-wuxing-tu)',
    '官鬼': 'var(--yi-wuxing-huo)',
    '妻财': 'var(--yi-wuxing-jin)',
    '子孙': 'var(--yi-wuxing-shui)',
    '兄弟': 'var(--yi-wuxing-mu)',
  }
  return map[props.data.sixQin] ?? 'var(--yi-ink-medium)'
})

// 入场动画
onMounted(() => {
  if (lineRef.value) {
    gsap.from(lineRef.value, {
      x: -30,
      opacity: 0,
      duration: 0.6,
      delay: props.index * 0.1,
      ease: 'expo.out',
    })
  }
})

// 翻转动画
function playFlip() {
  if (!flipContainerRef.value || !props.data.isMoving) return
  gsap.timeline()
    .to(flipContainerRef.value, {
      rotateY: 90,
      duration: 0.3,
      ease: 'power2.in',
    })
    .set(flipContainerRef.value, {
      // 切换阴阳
    })
    .to(flipContainerRef.value, {
      rotateY: 0,
      duration: 0.5,
      ease: 'back.out(1.7)',
    })
}

defineExpose({ playFlip })
</script>

<template>
  <div ref="lineRef" :class="lineClasses" role="row">
    <!-- 爻位 -->
    <div class="yao-position" role="cell">
      <span class="position-number">{{ data.position }}</span>
      <span v-if="data.isWorld" class="world-badge">世</span>
      <span v-if="data.isResponse" class="response-badge">应</span>
    </div>

    <!-- 爻线 (核心视觉) -->
    <div ref="flipContainerRef" class="yao-visual" role="cell">
      <template v-if="data.yinYang === 'yang'">
        <!-- 阳爻: 一条实线 -->
        <div class="yao-solid" />
      </template>
      <template v-else>
        <!-- 阴爻: 两条断线 -->
        <div class="yao-broken">
          <span class="yao-segment" />
          <span class="yao-gap" />
          <span class="yao-segment" />
        </div>
      </template>

      <!-- 动爻标记 -->
      <div v-if="data.isMoving" class="moving-indicator" aria-label="动爻">
        <span class="moving-dot" />
      </div>
    </div>

    <!-- 纳甲 -->
    <div class="yao-najia" role="cell">
      {{ data.najia }}
    </div>

    <!-- 六亲 -->
    <div class="yao-six-qin" :style="{ color: sixQinColor }" role="cell">
      {{ data.sixQin }}
    </div>

    <!-- 六神 -->
    <div class="yao-six-spirit" role="cell">
      {{ data.sixSpirit }}
    </div>

    <!-- 爻辞 -->
    <div class="yao-text" role="cell">
      {{ data.text }}
    </div>
  </div>
</template>

<style scoped>
.yao-row {
  display: grid;
  grid-template-columns: 60px 120px 80px 80px 80px 1fr;
  gap: var(--yi-space-2);
  align-items: center;
  padding: var(--yi-space-2) var(--yi-space-3);
  border-bottom: var(--yi-border-subtle);
  transition: background-color var(--yi-duration-fast) var(--yi-ease-out-expo);
}

.yao-row:hover {
  background-color: oklch(80% 0.18 85 / 0.05);
}

/* 阳爻 */
.yao-solid {
  height: 6px;
  background: var(--yi-gold-primary);
  border-radius: 1px;
  box-shadow: 0 0 8px var(--yi-glow-gold);
}

/* 阴爻 */
.yao-broken {
  display: flex;
  align-items: center;
  gap: 12px;
}

.yao-segment {
  flex: 1;
  height: 6px;
  background: var(--yi-gold-primary);
  border-radius: 1px;
  box-shadow: 0 0 8px var(--yi-glow-gold);
}

.yao-gap {
  width: 12px;
}

/* 动爻 */
.yao-line--moving .yao-solid,
.yao-line--moving .yao-segment {
  background: var(--yi-status-moving);
  box-shadow: 0 0 12px oklch(70% 0.22 30 / 0.6);
  animation: glow-pulse 2s ease-in-out infinite;
}

.moving-indicator {
  position: absolute;
  right: -20px;
  top: 50%;
  transform: translateY(-50%);
}

.moving-dot {
  display: block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--yi-status-moving);
  animation: glow-pulse 1.5s ease-in-out infinite;
}

/* 世爻 / 应爻 */
.yao-line--world {
  background-color: oklch(80% 0.18 85 / 0.08);
}

.world-badge,
.response-badge {
  display: inline-block;
  width: 18px;
  height: 18px;
  line-height: 18px;
  text-align: center;
  font-size: 0.7rem;
  font-family: var(--yi-font-display);
  border-radius: var(--yi-radius-full);
}

.world-badge {
  background: var(--yi-gold-primary);
  color: var(--yi-black-void);
}

.response-badge {
  border: 1px solid var(--yi-gold-muted);
  color: var(--yi-gold-muted);
}

/* 六神 */
.yao-six-spirit {
  font-family: var(--yi-font-display);
  color: var(--yi-gold-muted);
  font-size: var(--yi-text-sm);
}

/* 爻辞 */
.yao-text {
  font-family: var(--yi-font-display);
  color: var(--yi-ink-light);
  font-size: var(--yi-text-sm);
  line-height: var(--yi-leading-tight);
}

/* 响应式 */
@media (max-width: 768px) {
  .yao-row {
    grid-template-columns: 40px 80px 60px 60px 1fr;
  }
  .yao-six-spirit {
    display: none; /* 小屏隐藏六神列 */
  }
  .yao-text {
    display: none; /* 小屏隐藏爻辞列 */
  }
}
</style>
```

### 4.4 动爻翻转动画

```vue
<!-- components/visualization/liuyao/YaoFlip.vue -->
<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { gsap } from 'gsap'

interface Props {
  fromYang: boolean
  toYang: boolean
  autoPlay?: boolean
  delay?: number
}

const props = withDefaults(defineProps<Props>(), {
  autoPlay: false,
  delay: 0,
})

const emit = defineEmits<{ complete: [] }>()

const containerRef = ref<HTMLDivElement | null>(null)
const isFlipped = ref(false)

async function playFlip() {
  if (!containerRef.value) return

  const tl = gsap.timeline({
    onComplete: () => {
      isFlipped.value = true
      emit('complete')
    },
  })

  tl
    // 第一阶段: 翻转到侧面 (消失)
    .to(containerRef.value, {
      rotateY: 90,
      scaleX: 0.3,
      duration: 0.35,
      ease: 'power2.in',
      delay: props.delay,
    })
    // 中间: 切换内容 (不可见)
    .call(() => { isFlipped.value = !isFlipped.value })
    // 第二阶段: 从侧面翻转回正面 (出现)
    .to(containerRef.value, {
      rotateY: 0,
      scaleX: 1,
      duration: 0.5,
      ease: 'back.out(1.7)',
    })
    // 粒子爆发效果
    .call(() => {
      emitBurst()
    }, [], '-=0.2')
}

function emitBurst() {
  // 使用 GSAP 快速创建 8 个"光点"向外扩散
  if (!containerRef.value) return
  const rect = containerRef.value.getBoundingClientRect()
  const cx = rect.left + rect.width / 2
  const cy = rect.top + rect.height / 2

  for (let i = 0; i < 8; i++) {
    const dot = document.createElement('div')
    dot.className = 'flip-burst-dot'
    document.body.appendChild(dot)

    const angle = (i / 8) * Math.PI * 2
    const distance = 30 + Math.random() * 20

    gsap.set(dot, { x: cx, y: cy, scale: 1, opacity: 1 })
    gsap.to(dot, {
      x: cx + Math.cos(angle) * distance,
      y: cy + Math.sin(angle) * distance,
      scale: 0,
      opacity: 0,
      duration: 0.6,
      ease: 'expo.out',
      onComplete: () => dot.remove(),
    })
  }
}

if (props.autoPlay) {
  onMounted(() => playFlip())
}

defineExpose({ playFlip })
</script>

<template>
  <div
    ref="containerRef"
    class="yao-flip"
    :style="{ perspective: '600px' }"
  >
    <div class="yao-flip-inner">
      <template v-if="!isFlipped ? fromYang : toYang">
        <div class="yao-solid" />
      </template>
      <template v-else>
        <div class="yao-broken">
          <span class="yao-segment" />
          <span class="yao-gap" />
          <span class="yao-segment" />
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.yao-flip {
  transform-style: preserve-3d;
  will-change: transform;
}

.yao-flip-inner {
  position: relative;
}

/* 全局: 翻转爆发粒子 */
:global(.flip-burst-dot) {
  position: fixed;
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--yi-gold-bright);
  pointer-events: none;
  z-index: var(--yi-z-toast);
}
</style>
```

### 4.5 响应式布局

| 断点 | 排盘布局 | 策略 |
|------|---------|------|
| >= 1280px | 完整 6 列网格 | 显示全部信息 |
| 1024-1279px | 5 列，隐藏爻辞 | 爻辞悬浮显示 |
| 768-1023px | 4 列，隐藏六神+爻辞 | 精简模式 |
| < 768px | 卡片式堆叠 | 每爻一行卡片 |

---

## 5. 知识图谱可视化

### 5.1 技术方案

使用 **Cytoscape.js** 作为图谱渲染引擎，配合自定义样式和布局算法。

选择 Cytoscape.js 的原因：
- 原生支持复杂图布局算法（cose, dagre, cola）
- 自定义节点/边样式能力强
- 事件系统完善（点击、悬停、拖拽）
- 性能可处理 1000+ 节点
- 社区活跃，文档完善

### 5.2 图谱数据模型

```typescript
// types/graph.ts

export interface GraphNode {
  id: string
  label: string
  type: 'Hexagram' | 'Element' | 'Role' | 'Trigram' | 'Spirit' | 'Branch' | 'Stem'
  properties: Record<string, unknown>
}

export interface GraphEdge {
  id: string
  source: string
  target: string
  type: string  // 'GENERATES' | 'RESTRAINS' | 'HAS_LINE' | 'TRANSFORMS_TO' | ...
  properties: Record<string, unknown>
}

export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

// Cytoscape 元素格式
export interface CytoscapeElement {
  data: {
    id: string
    label: string
    type: string
    parent?: string
    [key: string]: unknown
  }
  classes?: string
  position?: { x: number; y: number }
}
```

### 5.3 图谱 Composable

```typescript
// composables/useGraph.ts
import { ref, watch, onMounted, onUnmounted, type Ref } from 'vue'
import cytoscape, { type Core, type EventObject } from 'cytoscape'
import type { GraphData, CytoscapeElement } from '~/types/graph'
import { useGraphStore } from '~/stores/graph'

// 节点样式配置
const NODE_STYLES: Record<string, { color: string; shape: string; size: number }> = {
  Hexagram: { color: 'var(--yi-gold-primary)',  shape: 'hexagon',       size: 50 },
  Element:  { color: 'var(--yi-wuxing-huo)',    shape: 'ellipse',       size: 40 },
  Role:     { color: 'var(--yi-wuxing-mu)',     shape: 'round-rectangle', size: 36 },
  Trigram:  { color: 'var(--yi-gold-bright)',    shape: 'diamond',       size: 44 },
  Spirit:   { color: 'var(--yi-wuxing-shui)',   shape: 'star',          size: 32 },
  Branch:   { color: 'var(--yi-wuxing-tu)',     shape: 'rectangle',     size: 30 },
  Stem:     { color: 'var(--yi-wuxing-jin)',    shape: 'triangle',      size: 28 },
}

// 边样式配置
const EDGE_STYLES: Record<string, { color: string; style: string; width: number }> = {
  GENERATES:    { color: 'var(--yi-wuxing-mu)',   style: 'solid',  width: 2 },
  RESTRAINS:    { color: 'var(--yi-wuxing-huo)',  style: 'dashed', width: 2 },
  HAS_LINE:     { color: 'var(--yi-gold-ghost)',  style: 'solid',  width: 1 },
  TRANSFORMS_TO:{ color: 'var(--yi-status-moving)',style: 'solid', width: 3 },
  ERRORS_TO:    { color: 'var(--yi-glow-cyan)',   style: 'dotted', width: 2 },
  REVERSES_TO:  { color: 'var(--yi-glow-magenta)',style: 'dotted', width: 2 },
  MUTUAL_WITH:  { color: 'var(--yi-gold-muted)',  style: 'dashed', width: 1.5 },
  HAS_ROLE:     { color: 'var(--yi-wuxing-tu)',   style: 'solid',  width: 1 },
  HAS_ELEMENT:  { color: 'var(--yi-ink-medium)',  style: 'solid',  width: 1 },
}

export function useGraph(
  containerRef: Ref<HTMLElement | null>,
  data: () => GraphData,
) {
  let cy: Core | null = null
  const store = useGraphStore()
  const isLoading = ref(true)

  function toCytoscapeElements(graphData: GraphData): CytoscapeElement[] {
    const elements: CytoscapeElement[] = []

    for (const node of graphData.nodes) {
      const style = NODE_STYLES[node.type] ?? NODE_STYLES.Hexagram
      elements.push({
        data: {
          id: node.id,
          label: node.label,
          type: node.type,
          ...node.properties,
        },
        classes: `node-${node.type.toLowerCase()}`,
      })
    }

    for (const edge of graphData.edges) {
      elements.push({
        data: {
          id: edge.id,
          source: edge.source,
          target: edge.target,
          type: edge.type,
          ...edge.properties,
        },
        classes: `edge-${edge.type.toLowerCase()}`,
      })
    }

    return elements
  }

  function getCytoscapeStyle(): cytoscape.Stylesheet[] {
    const styles: cytoscape.Stylesheet[] = []

    // 基础节点样式
    styles.push({
      selector: 'node',
      style: {
        label: 'data(label)',
        'text-valign': 'center',
        'text-halign': 'center',
        'font-family': 'var(--yi-font-display)',
        'font-size': '12px',
        'color': 'var(--yi-ink-white)',
        'text-outline-color': 'var(--yi-black-void)',
        'text-outline-width': 2,
        'background-opacity': 0.9,
        'border-width': 2,
        'border-opacity': 0.6,
        'overlay-opacity': 0,
        'transition-property': 'background-color, border-color, width, height',
        'transition-duration': 200,
      } as any,
    })

    // 各类型节点样式
    for (const [type, style] of Object.entries(NODE_STYLES)) {
      styles.push({
        selector: `node.node-${type.toLowerCase()}`,
        style: {
          'background-color': style.color,
          'border-color': style.color,
          'shape': style.shape,
          'width': style.size,
          'height': style.size,
        } as any,
      })
    }

    // 基础边样式
    styles.push({
      selector: 'edge',
      style: {
        'curve-style': 'bezier',
        'target-arrow-shape': 'triangle',
        'target-arrow-color': 'data(color)',
        'arrow-scale': 0.8,
        'label': 'data(type)',
        'font-size': '9px',
        'color': 'var(--yi-ink-medium)',
        'text-rotation': 'autorotate',
        'text-margin-y': -10,
        'overlay-opacity': 0,
        'transition-property': 'line-color, width, opacity',
        'transition-duration': 200,
      } as any,
    })

    // 各类型边样式
    for (const [type, style] of Object.entries(EDGE_STYLES)) {
      styles.push({
        selector: `edge.edge-${type.toLowerCase()}`,
        style: {
          'line-color': style.color,
          'line-style': style.style,
          'width': style.width,
          'target-arrow-color': style.color,
        } as any,
      })
    }

    // 悬停高亮
    styles.push({
      selector: 'node:active',
      style: {
        'overlay-opacity': 0.1,
        'overlay-color': 'var(--yi-gold-bright)',
      } as any,
    })

    // 选中状态
    styles.push({
      selector: 'node:selected',
      style: {
        'border-width': 4,
        'border-color': 'var(--yi-gold-bright)',
        'background-blacken': -0.1,
      } as any,
    })

    // 暗淡非关联节点
    styles.push({
      selector: '.faded',
      style: {
        'opacity': 0.15,
      } as any,
    })

    return styles
  }

  function initCytoscape() {
    if (!containerRef.value) return

    const elements = toCytoscapeElements(data())

    cy = cytoscape({
      container: containerRef.value,
      elements,
      style: getCytoscapeStyle(),
      layout: {
        name: store.layoutAlgorithm,
        animate: true,
        animationDuration: 800,
        animationEasing: 'expo.out',
        fit: true,
        padding: 40,
        nodeRepulsion: () => 8000,
        idealEdgeLength: () => 120,
        edgeElasticity: () => 100,
        gravity: 0.3,
        numIter: 1000,
      } as any,
      minZoom: 0.2,
      maxZoom: 4,
      wheelSensitivity: 0.3,
    })

    // 事件绑定
    bindEvents()
    isLoading.value = false
  }

  function bindEvents() {
    if (!cy) return

    // 节点点击: 展开/收起关联
    cy.on('tap', 'node', (evt: EventObject) => {
      const nodeId = evt.target.id()
      store.selectNode(nodeId)
      highlightNeighbors(nodeId)
    })

    // 点击空白: 取消选中
    cy.on('tap', (evt: EventObject) => {
      if (evt.target === cy) {
        store.selectNode(null)
        clearHighlight()
      }
    })

    // 节点悬停: 显示详情 tooltip
    cy.on('mouseover', 'node', (evt: EventObject) => {
      const node = evt.target
      node.style('border-width', 4)
    })

    cy.on('mouseout', 'node', (evt: EventObject) => {
      const node = evt.target
      if (!node.selected()) {
        node.style('border-width', 2)
      }
    })
  }

  function highlightNeighbors(nodeId: string) {
    if (!cy) return

    // 重置所有
    cy.elements().removeClass('faded')

    const neighborhood = cy.getElementById(nodeId).neighborhood().add(cy.getElementById(nodeId))
    const others = cy.elements().not(neighborhood)

    others.addClass('faded')
  }

  function clearHighlight() {
    if (!cy) return
    cy.elements().removeClass('faded')
  }

  function changeLayout(algorithm: string) {
    if (!cy) return
    store.layoutAlgorithm = algorithm as any
    cy.layout({
      name: algorithm,
      animate: true,
      animationDuration: 800,
      animationEasing: 'expo.out',
      fit: true,
      padding: 40,
    } as any).run()
  }

  function filterByType(types: string[]) {
    if (!cy) return
    store.filterTypes = types

    cy.nodes().forEach(node => {
      const type = node.data('type')
      if (types.includes(type)) {
        node.style('display', 'element')
      } else {
        node.style('display', 'none')
      }
    })

    // 隐藏孤立边
    cy.edges().forEach(edge => {
      const src = edge.source().style('display')
      const tgt = edge.target().style('display')
      edge.style('display', (src === 'element' && tgt === 'element') ? 'element' : 'none')
    })
  }

  function exportPng(): string {
    if (!cy) return ''
    return cy.png({ bg: 'var(--yi-black-void)', full: true, scale: 2 })
  }

  onMounted(() => {
    initCytoscape()
  })

  onUnmounted(() => {
    if (cy) {
      cy.destroy()
      cy = null
    }
  })

  // 布局变更时重排
  watch(() => store.layoutAlgorithm, (algo) => {
    changeLayout(algo)
  })

  return {
    isLoading,
    changeLayout,
    filterByType,
    highlightNeighbors,
    clearHighlight,
    exportPng,
    getCytoscape: () => cy,
  }
}
```

### 5.4 图谱 Vue 组件

```vue
<!-- components/visualization/graph/KnowledgeGraph.vue -->
<script setup lang="ts">
import { ref, computed, toRef } from 'vue'
import type { GraphData } from '~/types/graph'
import { useGraph } from './useGraph'

interface Props {
  data: GraphData
  height?: string
}

const props = withDefaults(defineProps<Props>(), {
  height: '600px',
})

const containerRef = ref<HTMLElement | null>(null)

const {
  isLoading,
  changeLayout,
  filterByType,
  exportPng,
} = useGraph(containerRef, () => props.data)

const layoutOptions = [
  { value: 'cose', label: '力导向' },
  { value: 'dagre', label: '层次' },
  { value: 'circle', label: '环形' },
  { value: 'concentric', label: '同心圆' },
]

const filterOptions = [
  { value: 'Hexagram', label: '卦', color: 'var(--yi-gold-primary)' },
  { value: 'Element', label: '五行', color: 'var(--yi-wuxing-huo)' },
  { value: 'Trigram', label: '八卦', color: 'var(--yi-gold-bright)' },
  { value: 'Role', label: '六亲', color: 'var(--yi-wuxing-mu)' },
  { value: 'Spirit', label: '六神', color: 'var(--yi-wuxing-shui)' },
]
</script>

<template>
  <div class="knowledge-graph" role="figure" aria-label="易学知识图谱">
    <!-- 工具栏 -->
    <div class="graph-toolbar">
      <select
        class="yi-select"
        @change="changeLayout(($event.target as HTMLSelectElement).value)"
        aria-label="布局算法"
      >
        <option v-for="opt in layoutOptions" :key="opt.value" :value="opt.value">
          {{ opt.label }}
        </option>
      </select>

      <div class="graph-filters" role="group" aria-label="节点类型筛选">
        <button
          v-for="opt in filterOptions"
          :key="opt.value"
          class="filter-chip"
          :style="{ '--chip-color': opt.color }"
          @click="filterByType([opt.value])"
        >
          {{ opt.label }}
        </button>
      </div>

      <button class="yi-btn" @click="exportPng" aria-label="导出图片">
        导出
      </button>
    </div>

    <!-- 图谱画布 -->
    <div
      ref="containerRef"
      class="graph-canvas"
      :style="{ height }"
      role="img"
      aria-label="知识关系网络图"
    />

    <!-- 加载状态 -->
    <div v-if="isLoading" class="graph-loading" aria-live="polite">
      <div class="loading-spinner" />
      <span>构建知识网络...</span>
    </div>
  </div>
</template>

<style scoped>
.knowledge-graph {
  position: relative;
  background: var(--yi-black-deep);
  border-radius: var(--yi-radius-lg);
  overflow: hidden;
  border: var(--yi-border-subtle);
}

.graph-toolbar {
  display: flex;
  align-items: center;
  gap: var(--yi-space-3);
  padding: var(--yi-space-3);
  border-bottom: var(--yi-border-subtle);
  background: var(--yi-black-surface);
}

.graph-canvas {
  width: 100%;
}

.graph-loading {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--yi-space-3);
  background: oklch(5% 0.01 270 / 0.80);
  color: var(--yi-gold-muted);
  font-family: var(--yi-font-display);
}

.filter-chip {
  padding: var(--yi-space-1) var(--yi-space-2);
  border: 1px solid var(--chip-color);
  border-radius: var(--yi-radius-full);
  background: transparent;
  color: var(--chip-color);
  font-size: var(--yi-text-xs);
  cursor: pointer;
  transition: all var(--yi-duration-fast);
}

.filter-chip:hover,
.filter-chip.active {
  background: oklch(from var(--chip-color) l c h / 0.15);
}
</style>
```

### 5.5 布局算法对比

| 算法 | 适用场景 | 优势 | 劣势 |
|------|---------|------|------|
| `cose` (力导向) | 通用关系网络 | 自动避免重叠，美观 | 大图收敛慢 |
| `dagre` (层次) | 有向无环图（卦变链） | 层次清晰 | 需要有向结构 |
| `circle` (环形) | 五行生克环 | 结构对称 | 不适合复杂关系 |
| `concentric` (同心圆) | 以某卦为中心的辐射 | 中心突出 | 外圈拥挤 |

### 5.6 性能优化

```typescript
// 1. 视口裁剪: 仅渲染可见区域的节点
cy.viewportExtents({
  x1: 0, y1: 0, x2: containerWidth, y2: containerHeight,
})

// 2. 分层加载: 先加载 1 跳关系，再按需加载 2 跳
function loadIncrementally(centerNodeId: string) {
  const oneHop = getOneHopData(centerNodeId)
  cy.add(toCytoscapeElements(oneHop))
  cy.layout({ name: 'cose', animate: true }).run()

  // 用户点击某节点时再加载 2 跳
  cy.one('tap', 'node', async (evt) => {
    const twoHop = await getTwoHopData(evt.target.id())
    cy.add(toCytoscapeElements(twoHop))
    cy.layout({ name: 'cose', animate: true }).run()
  })
}

// 3. WebGL 渲染 (超大图)
// 当节点数 > 2000 时，切换到 Cytoscape 的 WebGL 扩展
if (graphData.nodes.length > 2000) {
  // 使用 cytoscape-canvas 或 piecelayout 等优化
  cy.renderer()
}
```

---

## 6. 时间演化树

### 6.1 技术方案

使用 **D3.js** 的 `d3.tree()` 和 `d3.linkHorizontal()` 布局，结合 GSAP 实现节点状态转移动画。

### 6.2 演化数据模型

```typescript
// types/evolution.ts

export interface EvolutionNode {
  id: string
  hexagramName: string
  hexagramNumber: number
  timestamp: string
  movingLines: number[]
  probability: number       // 转移概率 0-1
  state: 'active' | 'past' | 'future' | 'branching'
  children: EvolutionNode[]
  metadata: {
    question?: string
    sentiment?: string
    aiSummary?: string
  }
}

export interface EvolutionTree {
  root: EvolutionNode
  totalDepth: number
  totalNodes: number
}
```

### 6.3 D3 布局与渲染

```typescript
// composables/useEvolution.ts
import { ref, watch, onMounted, onUnmounted, type Ref } from 'vue'
import * as d3 from 'd3'
import { gsap } from 'gsap'
import type { EvolutionNode, EvolutionTree } from '~/types/evolution'

export function useEvolution(
  svgRef: Ref<SVGSVGElement | null>,
  treeData: () => EvolutionTree | null,
) {
  let svg: d3.Selection<SVGSVGElement, unknown, null, undefined> | null = null
  let g: d3.Selection<SVGGElement, unknown, null, undefined> | null = null
  const selectedNode = ref<EvolutionNode | null>(null)

  function render() {
    const data = treeData()
    if (!svgRef.value || !data) return

    // 清除旧内容
    d3.select(svgRef.value).selectAll('*').remove()

    const width = svgRef.value.clientWidth
    const height = svgRef.value.clientHeight
    const margin = { top: 40, right: 120, bottom: 40, left: 80 }

    svg = d3.select(svgRef.value)
      .attr('viewBox', `0 0 ${width} ${height}`)

    g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`)

    // 创建层级数据
    const root = d3.hierarchy(data.root, d => d.children)

    // 树布局
    const treeLayout = d3.tree<EvolutionNode>()
      .size([height - margin.top - margin.bottom, width - margin.left - margin.right])
      .separation((a, b) => (a.parent === b.parent ? 1 : 1.5))

    treeLayout(root)

    // 绘制连接线 (贝塞尔曲线)
    const linkGenerator = d3.linkHorizontal<d3.HierarchyLink<EvolutionNode>, d3.HierarchyPointNode<EvolutionNode>>()
      .x(d => d.y)
      .y(d => d.x)

    g.selectAll('.evolution-link')
      .data(root.links())
      .join('path')
      .attr('class', 'evolution-link')
      .attr('d', linkGenerator)
      .attr('fill', 'none')
      .attr('stroke', d => getLinkColor(d.target.data))
      .attr('stroke-width', d => Math.max(1, d.target.data.probability * 4))
      .attr('stroke-dasharray', d => d.target.data.state === 'future' ? '6,4' : 'none')
      .attr('opacity', 0)
      .transition()
      .duration(800)
      .delay((_, i) => i * 50)
      .attr('opacity', 0.6)

    // 绘制节点
    const nodes = g.selectAll('.evolution-node')
      .data(root.descendants())
      .join('g')
      .attr('class', 'evolution-node')
      .attr('transform', d => `translate(${d.y},${d.x})`)
      .attr('cursor', 'pointer')
      .on('click', (_, d) => {
        selectedNode.value = d.data
      })

    // 节点圆
    nodes.append('circle')
      .attr('r', d => getNodeRadius(d.data))
      .attr('fill', d => getNodeColor(d.data))
      .attr('stroke', 'var(--yi-gold-ghost)')
      .attr('stroke-width', 1.5)
      .attr('opacity', 0)
      .transition()
      .duration(600)
      .delay((_, i) => i * 80)
      .attr('opacity', 1)

    // 卦名标签
    nodes.append('text')
      .attr('dy', '0.35em')
      .attr('x', d => d.children ? -12 : 12)
      .attr('text-anchor', d => d.children ? 'end' : 'start')
      .attr('font-family', 'var(--yi-font-display)')
      .attr('font-size', '12px')
      .attr('fill', 'var(--yi-ink-white)')
      .text(d => d.data.hexagramName)

    // 概率标签
    nodes.filter(d => d.data.probability < 1)
      .append('text')
      .attr('dy', '-1em')
      .attr('text-anchor', 'middle')
      .attr('font-family', 'var(--yi-font-mono)')
      .attr('font-size', '9px')
      .attr('fill', 'var(--yi-gold-muted)')
      .text(d => `${(d.data.probability * 100).toFixed(0)}%`)

    // 动爻标记
    nodes.filter(d => d.data.movingLines.length > 0)
      .append('circle')
      .attr('r', 3)
      .attr('cx', d => d.children ? -24 : 24)
      .attr('fill', 'var(--yi-status-moving)')
      .attr('class', 'moving-pulse')
  }

  function getNodeRadius(node: EvolutionNode): number {
    const base = 8
    switch (node.state) {
      case 'active':     return base * 1.5
      case 'branching':  return base * 1.2
      case 'past':       return base
      case 'future':     return base * 0.8
    }
  }

  function getNodeColor(node: EvolutionNode): string {
    switch (node.state) {
      case 'active':     return 'var(--yi-gold-bright)'
      case 'past':       return 'var(--yi-gold-muted)'
      case 'future':     return 'var(--yi-glow-cyan)'
      case 'branching':  return 'var(--yi-status-moving)'
    }
  }

  function getLinkColor(node: EvolutionNode): string {
    if (node.state === 'future') return 'var(--yi-glow-cyan)'
    if (node.probability > 0.7) return 'var(--yi-gold-primary)'
    if (node.probability > 0.3) return 'var(--yi-gold-muted)'
    return 'var(--yi-gold-ghost)'
  }

  // 缩放与平移
  function setupZoom() {
    if (!svg || !g) return

    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.3, 3])
      .on('zoom', (event) => {
        g!.attr('transform', event.transform)
      })

    svg.call(zoom)
  }

  onMounted(() => {
    render()
    setupZoom()
  })

  watch(treeData, () => {
    render()
  }, { deep: true })

  onUnmounted(() => {
    if (svg) svg.selectAll('*').remove()
  })

  return {
    selectedNode,
    render,
  }
}
```

### 6.4 演化树 Vue 组件

```vue
<!-- components/visualization/evolution/EvolutionTree.vue -->
<script setup lang="ts">
import { ref, computed } from 'vue'
import type { EvolutionTree, EvolutionNode } from '~/types/evolution'
import { useEvolution } from './useEvolution'

interface Props {
  data: EvolutionTree
}

const props = defineProps<Props>()

const svgRef = ref<SVGSVGElement | null>(null)

const { selectedNode } = useEvolution(svgRef, () => props.data)
</script>

<template>
  <div class="evolution-tree">
    <!-- SVG 画布 -->
    <svg
      ref="svgRef"
      class="evolution-svg"
      role="img"
      aria-label="卦象时间演化树"
    />

    <!-- 详情面板 -->
    <Transition name="slide">
      <div v-if="selectedNode" class="evolution-detail">
        <h3 class="detail-title">{{ selectedNode.hexagramName }}</h3>
        <div class="detail-meta">
          <span>概率: {{ (selectedNode.probability * 100).toFixed(0) }}%</span>
          <span v-if="selectedNode.movingLines.length">
            动爻: {{ selectedNode.movingLines.join(', ') }}
          </span>
        </div>
        <p v-if="selectedNode.metadata.aiSummary" class="detail-summary">
          {{ selectedNode.metadata.aiSummary }}
        </p>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.evolution-tree {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 400px;
  background: var(--yi-black-deep);
  border-radius: var(--yi-radius-lg);
  overflow: hidden;
}

.evolution-svg {
  width: 100%;
  height: 100%;
}

.evolution-detail {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 300px;
  padding: var(--yi-space-4);
  background: var(--yi-black-surface);
  border-left: var(--yi-border-gold);
  overflow-y: auto;
}

/* D3 节点脉冲动画 */
:deep(.moving-pulse) {
  animation: glow-pulse 1.5s ease-in-out infinite;
}

/* 过渡动画 */
.slide-enter-active,
.slide-leave-active {
  transition: transform var(--yi-duration-normal) var(--yi-ease-out-expo);
}
.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
}
</style>
```

---

## 7. 3D 场景设计

### 7.1 技术方案

使用 **Three.js** 实现 3D 卦象展示和空间效果。

场景组成：
1. **3D 卦象**: 六爻立体制作（阴/阳爻的 3D 几何体）
2. **八卦环**: 八卦符号围绕中心旋转的环形阵列
3. **粒子系统**: 五行粒子流动效果
4. **后处理**: Bloom 发光、水墨风格后处理

### 7.2 3D 场景 Composable

```typescript
// composables/useScene3D.ts
import { ref, onMounted, onUnmounted, watch, type Ref } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js'
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js'
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js'

interface Scene3DConfig {
  backgroundColor: string
  bloomStrength: number
  bloomRadius: number
  bloomThreshold: number
  cameraDistance: number
  autoRotate: boolean
  autoRotateSpeed: number
}

const DEFAULT_CONFIG: Scene3DConfig = {
  backgroundColor: '#0a0a14',
  bloomStrength: 1.5,
  bloomRadius: 0.4,
  bloomThreshold: 0.2,
  cameraDistance: 8,
  autoRotate: true,
  autoRotateSpeed: 0.3,
}

export function useScene3D(
  containerRef: Ref<HTMLElement | null>,
  config: Partial<Scene3DConfig> = {},
) {
  const cfg = { ...DEFAULT_CONFIG, ...config }
  let scene: THREE.Scene | null = null
  let camera: THREE.PerspectiveCamera | null = null
  let renderer: THREE.WebGLRenderer | null = null
  let controls: OrbitControls | null = null
  let composer: EffectComposer | null = null
  let animationId: number | null = null
  let clock: THREE.Clock | null = null

  // 3D 对象引用
  const hexagramGroup = new THREE.Group()
  const trigramRing = new THREE.Group()
  const particleSystem = new THREE.Points()

  function initScene() {
    if (!containerRef.value) return

    const rect = containerRef.value.getBoundingClientRect()
    const width = rect.width
    const height = rect.height

    // 场景
    scene = new THREE.Scene()
    scene.background = new THREE.Color(cfg.backgroundColor)
    scene.fog = new THREE.FogExp2(cfg.backgroundColor, 0.05)

    // 相机
    camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 100)
    camera.position.set(0, 2, cfg.cameraDistance)

    // 渲染器
    renderer = new THREE.WebGLRenderer({
      antialias: true,
      alpha: false,
      powerPreference: 'high-performance',
    })
    renderer.setSize(width, height)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.toneMapping = THREE.ACESFilmicToneMapping
    renderer.toneMappingExposure = 1.2
    containerRef.value.appendChild(renderer.domElement)

    // 控制器
    controls = new OrbitControls(camera, renderer.domElement)
    controls.enableDamping = true
    controls.dampingFactor = 0.05
    controls.autoRotate = cfg.autoRotate
    controls.autoRotateSpeed = cfg.autoRotateSpeed
    controls.minDistance = 3
    controls.maxDistance = 20

    // 后处理
    composer = new EffectComposer(renderer)
    const renderPass = new RenderPass(scene, camera)
    composer.addPass(renderPass)

    const bloomPass = new UnrealBloomPass(
      new THREE.Vector2(width, height),
      cfg.bloomStrength,
      cfg.bloomRadius,
      cfg.bloomThreshold,
    )
    composer.addPass(bloomPass)

    // 光照
    setupLighting()

    // 构建场景对象
    buildHexagram3D()
    buildTrigramRing()
    buildParticleSystem()

    // 添加到场景
    scene.add(hexagramGroup)
    scene.add(trigramRing)

    clock = new THREE.Clock()

    // 响应式
    const resizeObserver = new ResizeObserver(() => {
      handleResize()
    })
    resizeObserver.observe(containerRef.value)
  }

  function setupLighting() {
    if (!scene) return

    // 环境光 (暗调)
    const ambient = new THREE.AmbientLight(0x1a1a2e, 0.3)
    scene.add(ambient)

    // 主方向光 (金色暖光)
    const dirLight = new THREE.DirectionalLight(0xd4a843, 1.0)
    dirLight.position.set(5, 8, 5)
    scene.add(dirLight)

    // 补光 (青色冷光)
    const fillLight = new THREE.DirectionalLight(0x4a9ebf, 0.4)
    fillLight.position.set(-5, 3, -5)
    scene.add(fillLight)

    // 点光源 (中心)
    const pointLight = new THREE.PointLight(0xd4a843, 2, 10)
    pointLight.position.set(0, 0, 0)
    scene.add(pointLight)
  }

  function buildHexagram3D() {
    // 六爻 3D 几何体
    const yangMaterial = new THREE.MeshStandardMaterial({
      color: 0xf5e6c8,
      emissive: 0xd4a843,
      emissiveIntensity: 0.3,
      metalness: 0.6,
      roughness: 0.3,
    })

    const yinMaterial = new THREE.MeshStandardMaterial({
      color: 0x1a1a2e,
      emissive: 0x4a9ebf,
      emissiveIntensity: 0.2,
      metalness: 0.4,
      roughness: 0.5,
    })

    const lineSpacing = 0.5
    const lineWidth = 3
    const lineHeight = 0.15
    const lineDepth = 0.4

    for (let i = 0; i < 6; i++) {
      const y = (i - 2.5) * lineSpacing
      const isYang = Math.random() > 0.5 // 替换为实际数据

      if (isYang) {
        // 阳爻: 整条
        const geo = new THREE.BoxGeometry(lineWidth, lineHeight, lineDepth)
        const mesh = new THREE.Mesh(geo, yangMaterial)
        mesh.position.set(0, y, 0)
        hexagramGroup.add(mesh)
      } else {
        // 阴爻: 两段 (中间断开)
        const segGeo = new THREE.BoxGeometry(lineWidth * 0.4, lineHeight, lineDepth)

        const left = new THREE.Mesh(segGeo, yinMaterial)
        left.position.set(-lineWidth * 0.25, y, 0)
        hexagramGroup.add(left)

        const right = new THREE.Mesh(segGeo, yinMaterial)
        right.position.set(lineWidth * 0.25, y, 0)
        hexagramGroup.add(right)
      }
    }
  }

  function buildTrigramRing() {
    // 八卦符号围绕中心的环形排列
    const trigramNames = ['乾', '坤', '震', '巽', '坎', '离', '艮', '兑']
    const radius = 4
    const symbolMaterial = new THREE.MeshStandardMaterial({
      color: 0xd4a843,
      emissive: 0xd4a843,
      emissiveIntensity: 0.5,
      transparent: true,
      opacity: 0.7,
    })

    trigramNames.forEach((name, i) => {
      const angle = (i / 8) * Math.PI * 2
      const x = Math.cos(angle) * radius
      const z = Math.sin(angle) * radius

      // 使用 TextGeometry 或 Sprite 显示卦名
      const canvas = document.createElement('canvas')
      canvas.width = 128
      canvas.height = 128
      const ctx = canvas.getContext('2d')!
      ctx.fillStyle = '#d4a843'
      ctx.font = '80px serif'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'
      ctx.fillText(name, 64, 64)

      const texture = new THREE.CanvasTexture(canvas)
      const spriteMaterial = new THREE.SpriteMaterial({
        map: texture,
        transparent: true,
        opacity: 0.8,
      })
      const sprite = new THREE.Sprite(spriteMaterial)
      sprite.position.set(x, 0, z)
      sprite.scale.set(0.8, 0.8, 1)
      trigramRing.add(sprite)
    })
  }

  function buildParticleSystem() {
    // 五行粒子流动
    const count = 500
    const positions = new Float32Array(count * 3)
    const colors = new Float32Array(count * 3)
    const sizes = new Float32Array(count)

    const colorMap = [
      new THREE.Color(0xf5e6c8), // 金
      new THREE.Color(0x4a9ebf), // 水
      new THREE.Color(0x2d8a4e), // 木
      new THREE.Color(0xd4503a), // 火
      new THREE.Color(0xc4a843), // 土
    ]

    for (let i = 0; i < count; i++) {
      const theta = Math.random() * Math.PI * 2
      const phi = Math.random() * Math.PI
      const r = 2 + Math.random() * 4

      positions[i * 3] = r * Math.sin(phi) * Math.cos(theta)
      positions[i * 3 + 1] = r * Math.cos(phi)
      positions[i * 3 + 2] = r * Math.sin(phi) * Math.sin(theta)

      const color = colorMap[Math.floor(Math.random() * colorMap.length)]
      colors[i * 3] = color.r
      colors[i * 3 + 1] = color.g
      colors[i * 3 + 2] = color.b

      sizes[i] = 0.02 + Math.random() * 0.05
    }

    const geometry = new THREE.BufferGeometry()
    geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3))
    geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1))

    const material = new THREE.PointsMaterial({
      size: 0.05,
      vertexColors: true,
      transparent: true,
      opacity: 0.6,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    })

    particleSystem.geometry = geometry
    particleSystem.material = material
    scene?.add(particleSystem)
  }

  function animate() {
    if (!scene || !camera || !composer || !clock) return

    animationId = requestAnimationFrame(animate)

    const elapsed = clock.getElapsedTime()

    // 卦象缓慢旋转
    hexagramGroup.rotation.y = elapsed * 0.1

    // 八卦环旋转
    trigramRing.rotation.y = elapsed * 0.2

    // 粒子系统运动
    const positions = particleSystem.geometry.attributes.position.array as Float32Array
    for (let i = 0; i < positions.length; i += 3) {
      const x = positions[i]
      const z = positions[i + 2]
      const angle = Math.atan2(z, x) + 0.002
      const r = Math.sqrt(x * x + z * z)
      positions[i] = Math.cos(angle) * r
      positions[i + 2] = Math.sin(angle) * r
      positions[i + 1] += Math.sin(elapsed * 2 + i) * 0.001
    }
    particleSystem.geometry.attributes.position.needsUpdate = true

    controls?.update()
    composer.render()
  }

  function handleResize() {
    if (!containerRef.value || !camera || !renderer || !composer) return
    const rect = containerRef.value.getBoundingClientRect()
    const w = rect.width
    const h = rect.height

    camera.aspect = w / h
    camera.updateProjectionMatrix()
    renderer.setSize(w, h)
    composer.setSize(w, h)
  }

  function start() {
    initScene()
    animate()
  }

  function stop() {
    if (animationId !== null) {
      cancelAnimationFrame(animationId)
      animationId = null
    }
    renderer?.dispose()
  }

  // 入场动画: 爻线逐条出现
  function playEntrance() {
    hexagramGroup.children.forEach((child, i) => {
      const mesh = child as THREE.Mesh
      mesh.scale.set(0, 0, 0)
      gsap.to(mesh.scale, {
        x: 1, y: 1, z: 1,
        duration: 0.6,
        delay: i * 0.15,
        ease: 'back.out(1.7)',
      })
    })
  }

  // 动爻翻转 3D 动画
  function flipLine3D(position: number) {
    const line = hexagramGroup.children[position]
    if (!line) return

    gsap.to(line.rotation, {
      x: Math.PI,
      duration: 0.8,
      ease: 'power2.inOut',
      onComplete: () => {
        line.rotation.x = 0
      },
    })
  }

  onMounted(() => {
    start()
  })

  onUnmounted(() => {
    stop()
  })

  return {
    playEntrance,
    flipLine3D,
    handleResize,
  }
}
```

### 7.3 3D 场景 Vue 组件

```vue
<!-- components/visualization/scene3d/HexagramScene.vue -->
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useScene3D } from './useScene3D'

const containerRef = ref<HTMLElement | null>(null)

const { playEntrance, flipLine3D } = useScene3D(containerRef, {
  bloomStrength: 1.5,
  autoRotate: true,
  autoRotateSpeed: 0.3,
})
</script>

<template>
  <div class="scene3d-wrapper">
    <div ref="containerRef" class="scene3d-container" />

    <!-- 叠加 UI -->
    <div class="scene3d-overlay">
      <button class="yi-btn" @click="playEntrance">重播入场</button>
    </div>
  </div>
</template>

<style scoped>
.scene3d-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 500px;
  border-radius: var(--yi-radius-lg);
  overflow: hidden;
  border: var(--yi-border-glow);
  box-shadow: var(--yi-shadow-cyber);
}

.scene3d-container {
  width: 100%;
  height: 100%;
}

.scene3d-overlay {
  position: absolute;
  bottom: var(--yi-space-4);
  right: var(--yi-space-4);
  display: flex;
  gap: var(--yi-space-2);
}
</style>
```

### 7.4 3D 性能策略

| 策略 | 实现 | 目标 |
|------|------|------|
| 像素比限制 | `Math.min(devicePixelRatio, 2)` | 避免 4K 屏幕过载 |
| LOD 简化 | 根据相机距离降低几何体精度 | 远距离渲染更快 |
| 实例化渲染 | `THREE.InstancedMesh` 用于重复几何体 | 减少 draw call |
| 可见性检测 | `IntersectionObserver` 暂停不可见场景 | 节省 GPU |
| 后处理降级 | 低端设备跳过 Bloom pass | 保证流畅度 |
| 几何体缓存 | `BufferGeometry` 复用 | 减少内存分配 |

---

## 8. 性能优化策略

### 8.1 代码分割与懒加载

```typescript
// nuxt.config.ts 中的路由级代码分割 (Nuxt 自动处理)

// 组件级懒加载
const TaijiCanvas = defineAsyncComponent(() =>
  import('~/components/visualization/taiji/TaijiCanvas.vue')
)

const KnowledgeGraph = defineAsyncComponent(() =>
  import('~/components/visualization/graph/KnowledgeGraph.vue')
)

const HexagramScene = defineAsyncComponent(() =>
  import('~/components/visualization/scene3d/HexagramScene.vue')
)
```

### 8.2 可视化库按需加载

```typescript
// plugins/gsap.client.ts
export default defineNuxtPlugin(async () => {
  const gsap = await import('gsap')
  const { ScrollTrigger } = await import('gsap/ScrollTrigger')
  gsap.default.registerPlugin(ScrollTrigger)

  return { provide: { gsap: gsap.default } }
})

// plugins/three.client.ts
export default defineNuxtPlugin(async () => {
  // 仅在需要 3D 的页面加载
  const route = useRoute()
  if (!route.meta.needs3D) return

  const THREE = await import('three')
  return { provide: { three: THREE } }
})
```

### 8.3 Canvas 与 GPU 优化

```typescript
// 1. Canvas 离屏渲染 (OffscreenCanvas)
const offscreen = new OffscreenCanvas(width, height)
const ctx = offscreen.getContext('2d')

// 2. requestAnimationFrame 帧率限制 (30fps 省电模式)
let lastFrameTime = 0
const TARGET_FPS = 30
const FRAME_INTERVAL = 1000 / TARGET_FPS

function limitedFrame(timestamp: number) {
  if (timestamp - lastFrameTime >= FRAME_INTERVAL) {
    render(timestamp)
    lastFrameTime = timestamp
  }
  animationId = requestAnimationFrame(limitedFrame)
}

// 3. WebGL 纹理压缩
const loader = new THREE.CompressedTextureLoader()
const texture = loader.load('texture.ktx2') // KTX2 压缩格式
```

### 8.4 内存管理

```typescript
// 1. 可视化实例生命周期管理
onUnmounted(() => {
  // Three.js
  renderer?.dispose()
  scene?.traverse(obj => {
    if (obj instanceof THREE.Mesh) {
      obj.geometry.dispose()
      if (Array.isArray(obj.material)) {
        obj.material.forEach(m => m.dispose())
      } else {
        obj.material.dispose()
      }
    }
  })

  // Cytoscape
  cy?.destroy()

  // D3
  svg?.selectAll('*').remove()

  // Canvas
  ctx = null
})

// 2. 大数据集虚拟化
// 知识图谱: 仅渲染视口内节点
// 演化树: 深度超过 5 层时折叠
```

### 8.5 加载策略

```
┌──────────────────────────────────────────────────────┐
│                   加载优先级                            │
│                                                      │
│  P0 (立即):                                          │
│    - 首屏 CSS tokens + global.css                    │
│    - 关键字体 (font-display: swap)                    │
│    - 太极核心绘制 (Canvas 2D)                         │
│                                                      │
│  P1 (空闲):                                          │
│    - GSAP 核心                                        │
│    - 六爻排盘 DOM                                     │
│    - Pinia stores                                    │
│                                                      │
│  P2 (按需):                                          │
│    - Cytoscape.js (用户进入图谱页时)                   │
│    - D3.js (用户进入演化页时)                          │
│    - Three.js (用户进入 3D 页时)                       │
│                                                      │
│  P3 (后台):                                          │
│    - 图谱增量数据                                      │
│    - 演化树历史数据                                    │
│    - 用户历史记录                                      │
└──────────────────────────────────────────────────────┘
```

### 8.6 性能监控

```typescript
// composables/usePerformanceMonitor.ts
export function usePerformanceMonitor() {
  // Core Web Vitals
  function measureLCP() {
    new PerformanceObserver((list) => {
      const entries = list.getEntries()
      const lcp = entries[entries.length - 1]
      console.log('[Perf] LCP:', lcp.startTime.toFixed(0), 'ms')
    }).observe({ type: 'largest-contentful-paint', buffered: true })
  }

  function measureFPS() {
    let frames = 0
    let lastTime = performance.now()

    function count() {
      frames++
      const now = performance.now()
      if (now - lastTime >= 1000) {
        console.log('[Perf] FPS:', frames)
        frames = 0
        lastTime = now
      }
      requestAnimationFrame(count)
    }
    requestAnimationFrame(count)
  }

  // 可视化帧率监控
  function monitorVisualizationFPS(canvas: HTMLCanvasElement) {
    // 如果 FPS 持续低于 30，触发降级策略
    const fpsBuffer: number[] = []
    const FPS_THRESHOLD = 30

    return {
      onFrame: (fps: number) => {
        fpsBuffer.push(fps)
        if (fpsBuffer.length > 60) fpsBuffer.shift()
        const avg = fpsBuffer.reduce((a, b) => a + b) / fpsBuffer.length
        if (avg < FPS_THRESHOLD) {
          triggerDegradation()
        }
      },
    }
  }

  function triggerDegradation() {
    // 降级策略: 减少粒子、关闭 Bloom、降低分辨率
    console.warn('[Perf] 低帧率，触发降级策略')
  }

  return { measureLCP, measureFPS, monitorVisualizationFPS }
}
```

---

## 9. 响应式与无障碍设计

### 9.1 响应式断点

```typescript
// composables/useBreakpoint.ts
import { ref, onMounted, onUnmounted } from 'vue'

const BREAKPOINTS = {
  sm: 640,
  md: 768,
  lg: 1024,
  xl: 1280,
  '2xl': 1536,
} as const

type Breakpoint = keyof typeof BREAKPOINTS

export function useBreakpoint() {
  const current = ref<Breakpoint>('lg')
  const width = ref(0)

  function update() {
    width.value = window.innerWidth
    if (width.value < BREAKPOINTS.sm) current.value = 'sm'  // 不使用 (移动端完整布局)
    else if (width.value < BREAKPOINTS.md) current.value = 'sm'
    else if (width.value < BREAKPOINTS.lg) current.value = 'md'
    else if (width.value < BREAKPOINTS.xl) current.value = 'lg'
    else if (width.value < BREAKPOINTS['2xl']) current.value = 'xl'
    else current.value = '2xl'
  }

  const isMobile = computed(() => width.value < BREAKPOINTS.md)
  const isTablet = computed(() => width.value >= BREAKPOINTS.md && width.value < BREAKPOINTS.lg)
  const isDesktop = computed(() => width.value >= BREAKPOINTS.lg)

  onMounted(() => {
    update()
    window.addEventListener('resize', update)
  })

  onUnmounted(() => {
    window.removeEventListener('resize', update)
  })

  return { current, width, isMobile, isTablet, isDesktop }
}
```

### 9.2 响应式布局策略

```vue
<!-- app.vue (布局壳) -->
<script setup lang="ts">
const { isMobile, isTablet } = useBreakpoint()
</script>

<template>
  <div class="app-shell" :class="{ 'is-mobile': isMobile, 'is-tablet': isTablet }">
    <!-- 桌面: 侧边栏 + 主内容 -->
    <template v-if="!isMobile">
      <Sidebar />
      <main class="main-content">
        <NuxtPage />
      </main>
    </template>

    <!-- 移动端: 底部导航 + 全宽内容 -->
    <template v-else>
      <main class="main-content--mobile">
        <NuxtPage />
      </main>
      <BottomNav />
    </template>
  </div>
</template>

<style scoped>
.app-shell {
  display: grid;
  min-height: 100dvh;
}

/* 桌面 */
@media (min-width: 768px) {
  .app-shell {
    grid-template-columns: 240px 1fr;
  }
}

/* 移动端 */
.is-mobile .app-shell {
  grid-template-rows: 1fr auto;
}
</style>
```

### 9.3 可视化响应式适配

| 组件 | 移动端 (<768px) | 平板 (768-1024px) | 桌面 (>1024px) |
|------|----------------|-------------------|----------------|
| 太极动画 | 200px 尺寸，关闭粒子 | 300px，减少粒子 | 400px，完整效果 |
| 六爻排盘 | 卡片堆叠模式 | 精简 4 列 | 完整 6 列 |
| 知识图谱 | 触摸缩放，简化节点 | 标准模式 | 完整交互 |
| 演化树 | 垂直方向 | 标准水平 | 水平 + 侧栏详情 |
| 3D 场景 | 低分辨率，关闭 Bloom | 中等质量 | 完整后处理 |

### 9.4 无障碍设计 (WCAG 2.1 AA)

```typescript
// composables/useReducedMotion.ts
import { ref, onMounted, onUnmounted } from 'vue'

export function useReducedMotion() {
  const prefersReducedMotion = ref(false)
  let mediaQuery: MediaQueryList | null = null

  function check() {
    mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    prefersReducedMotion.value = mediaQuery.matches
    mediaQuery.addEventListener('change', check)
  }

  onMounted(check)
  onUnmounted(() => {
    mediaQuery?.removeEventListener('change', check)
  })

  return { prefersReducedMotion }
}
```

#### 无障碍清单

| 要求 | 实现 |
|------|------|
| **色彩对比** | 金色文字 (#d4a843) 在深黑背景 (#0a0a14) 上的对比度 >= 7:1 |
| **键盘导航** | 所有交互元素可通过 Tab/Enter 操作 |
| **屏幕阅读器** | ARIA 标签: `role="img"`, `aria-label`, `aria-live` |
| **减少动画** | `prefers-reduced-motion` 时停止所有动画 |
| **焦点可见** | `:focus-visible` 金色轮廓 |
| **文本替代** | 可视化图表提供文本描述 |
| **语义化** | 使用 `<main>`, `<nav>`, `<section>`, `<figure>` |
| **字体缩放** | 使用 `clamp()` 流式字号，支持浏览器缩放 |
| **触控目标** | 移动端按钮最小 44x44px |

```vue
<!-- 无障碍示例: 太极动画文本替代 -->
<template>
  <figure class="taiji-figure">
    <canvas
      ref="canvasRef"
      role="img"
      aria-label="太极阴阳动态图。阴阳鱼持续缓慢旋转，代表阴阳相互转化的哲学概念。"
    />
    <figcaption class="sr-only">
      太极图：圆形图案内包含阴阳双鱼，白色阳鱼和黑色阴鱼相互环抱，
      阳中有阴眼，阴中有阳眼，象征对立统一、循环变化。
    </figcaption>
  </figure>
</template>
```

### 9.5 触摸手势支持

```typescript
// composables/useTouchGestures.ts
import type { Ref } from 'vue'

export function useTouchGestures(
  elementRef: Ref<HTMLElement | null>,
  callbacks: {
    onPinch?: (scale: number) => void
    onSwipe?: (direction: 'left' | 'right' | 'up' | 'down') => void
    onTap?: (x: number, y: number) => void
  },
) {
  let initialDistance = 0
  let initialScale = 1

  function handleTouchStart(e: TouchEvent) {
    if (e.touches.length === 2) {
      // 双指: 捏合开始
      initialDistance = getDistance(e.touches[0], e.touches[1])
    }
  }

  function handleTouchMove(e: TouchEvent) {
    if (e.touches.length === 2 && callbacks.onPinch) {
      const currentDistance = getDistance(e.touches[0], e.touches[1])
      const scale = currentDistance / initialDistance
      callbacks.onPinch(scale)
    }
  }

  function handleTouchEnd(e: TouchEvent) {
    if (e.changedTouches.length === 1 && callbacks.onSwipe) {
      // 单指滑动检测
      // ... 检测滑动方向
    }
  }

  function getDistance(t1: Touch, t2: Touch): number {
    return Math.hypot(t2.clientX - t1.clientX, t2.clientY - t1.clientY)
  }

  // 绑定事件
  // ...

  return {}
}
```

---

## 附录 A: 技术选型对照表

| 场景 | 技术选择 | 替代方案 | 选择理由 |
|------|---------|---------|---------|
| 太极动画 | Canvas 2D | SVG, WebGL | 2D 矢量足够，兼容性好，CPU 绘制可控 |
| 六爻排盘 | DOM + CSS + GSAP | Canvas | 交互密集，DOM 更易维护和无障碍 |
| 知识图谱 | Cytoscape.js | D3-force, Sigma.js | 原生图布局丰富，API 成熟 |
| 演化树 | D3.js | Cytoscape (dagre) | D3 树布局更灵活，SVG 渲染精细 |
| 3D 场景 | Three.js | Babylon.js | 生态更大，与 GSAP 集成好 |
| 动画引擎 | GSAP | Motion One, Framer Motion | 复杂时间线控制最强，性能优秀 |
| 状态管理 | Pinia | Vuex, Zustand | Vue 3 官方推荐，TypeScript 支持好 |

## 附录 B: 依赖清单

```json
{
  "dependencies": {
    "nuxt": "^4.0",
    "vue": "^3.5",
    "pinia": "^2.2",
    "@nuxtjs/tailwindcss": "^6.12",
    "tailwindcss": "^3.4",
    "gsap": "^3.12",
    "cytoscape": "^3.30",
    "d3": "^7.9",
    "three": "^0.170",
    "shadcn-nuxt": "^0.10",
    "@vueuse/core": "^11.0"
  },
  "devDependencies": {
    "@types/three": "^0.170",
    "@types/d3": "^7.4",
    "@types/cytoscape": "^3.21",
    "typescript": "^5.5"
  }
}
```

## 附录 C: 文件规模控制

| 目录/文件 | 行数上限 | 策略 |
|----------|---------|------|
| 单个 Vue 组件 | 300 行 | 超出提取 composable |
| 单个 composable | 200 行 | 拆分逻辑函数 |
| 单个 Store | 150 行 | 按领域拆分 |
| Engine 模块 | 300 行 | 按功能拆分 |
| 全局 CSS | 200 行 | 使用 tokens + 组件 scoped |

---

*文档版本: 1.0.0*
*关联文档: yiai.md (总体架构), ai-architecture.md (AI 架构)*
