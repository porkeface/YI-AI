# YI-AI 前端

易学AI系统前端项目，基于Nuxt 4 + Vue 3 + TypeScript。

## 技术栈

- Nuxt 4
- Vue 3 (Composition API)
- TypeScript
- Tailwind CSS
- Pinia (状态管理)
- GSAP (动画)

## 快速开始

### 方式一：使用启动脚本（推荐）

**Windows:**
```bash
start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

### 方式二：手动启动

#### 安装依赖

```bash
npm install
# 或
yarn install
# 或
pnpm install
```

#### 启动开发服务器

```bash
npm run dev
# 或
yarn dev
# 或
pnpm dev
```

访问 http://localhost:3000

### 构建生产版本

```bash
npm run build
# 或
yarn build
# 或
pnpm build
```

## 项目结构

```
frontend/
├── .env                    # 环境变量
├── .env.example            # 环境变量示例
├── .gitignore              # Git忽略配置
├── README.md               # 项目说明
├── app.vue                 # 应用入口
├── nuxt.config.ts          # Nuxt配置
├── package.json            # 依赖配置
├── start.bat               # Windows启动脚本
├── start.sh                # Linux/Mac启动脚本
├── tailwind.config.ts      # Tailwind配置
├── tsconfig.json           # TypeScript配置
│
├── assets/
│   └── css/
│       ├── main.css        # 全局样式
│       └── transitions.css # 过渡动画
│
├── components/
│   ├── hexagram/           # 六爻相关组件
│   │   ├── AnalysisPanel.vue   # 分析面板
│   │   ├── HexagramChart.vue   # 排盘表格
│   │   ├── TaijiAnimation.vue  # 太极动画
│   │   ├── YinYangLine.vue     # 单爻渲染
│   │   └── index.ts            # 组件索引
│   └── ui/                 # UI组件库
│       ├── Button.vue          # 按钮
│       ├── InputField.vue      # 输入框
│       ├── Modal.vue           # 模态框
│       ├── Notification.vue    # 通知
│       ├── ... (40+ UI组件)
│       └── index.ts            # 组件索引
│
├── composables/            # 组合函数
│   ├── useApi.ts           # API请求
│   ├── useHexagram.ts      # 六爻工具
│   ├── useMockData.ts      # Mock数据
│   ├── useNotification.ts  # 通知管理
│   └── index.ts            # 组合函数索引
│
├── data/                   # 数据文件
│   ├── hexagrams.ts        # 六十四卦数据
│   └── index.ts            # 数据索引
│
├── layouts/
│   └── default.vue         # 默认布局
│
├── pages/
│   ├── index.vue           # 首页
│   ├── divination.vue      # 起卦页
│   ├── history.vue         # 历史页
│   ├── graph.vue           # 图谱页
│   └── test.vue            # 测试页
│
├── stores/
│   └── divination.ts       # 起卦状态管理
│
└── types/
    ├── hexagram.ts         # 类型定义
    └── index.ts            # 类型索引
```

## 功能特性

### 已实现

- ✅ 赛博东方设计风格
- ✅ 太极动画
- ✅ 六爻排盘展示
- ✅ 多种起卦方式（时间/数字/手动）
- ✅ Mock数据演示
- ✅ 响应式设计
- ✅ 深色/亮色主题切换
- ✅ 通知系统
- ✅ 性能监控（开发模式）
- ✅ 可访问性检查（开发模式）

### 待实现

- ⏳ 后端API集成
- ⏳ 历史记录
- ⏳ 卦象图谱
- ⏳ AI解卦

## UI组件库

项目包含40+个可复用的UI组件：

| 组件 | 说明 |
|------|------|
| Button | 按钮组件，支持多种样式 |
| InputField | 输入框组件 |
| Textarea | 文本区域组件 |
| Select | 下拉选择组件 |
| Checkbox | 复选框组件 |
| RadioButton | 单选按钮组件 |
| Toggle | 开关组件 |
| Slider | 滑块组件 |
| Card | 卡片组件 |
| Modal | 模态框组件 |
| Notification | 通知组件 |
| Tooltip | 工具提示组件 |
| Dropdown | 下拉菜单组件 |
| Tabs | 标签页组件 |
| Accordion | 折叠面板组件 |
| Pagination | 分页组件 |
| DataTable | 数据表格组件 |
| LoadingSpinner | 加载动画组件 |
| Skeleton | 骨架屏组件 |
| EmptyState | 空状态组件 |
| ErrorBoundary | 错误边界组件 |
| Breadcrumb | 面包屑导航组件 |
| StepIndicator | 步骤指示器组件 |
| ProgressBar | 进度条组件 |
| Badge | 徽章组件 |
| Tag | 标签组件 |
| Avatar | 头像组件 |
| Divider | 分割线组件 |
| Space | 间距组件 |
| ResponsiveContainer | 响应式容器组件 |
| ResponsiveNav | 响应式导航组件 |
| PageTransition | 页面过渡组件 |
| BackToTop | 返回顶部按钮组件 |
| ThemeToggle | 主题切换组件 |
| LanguageSwitcher | 语言切换组件 |
| SeoHead | SEO头部组件 |
| PerformanceMonitor | 性能监控组件 |
| AccessibilityChecker | 可访问性检查组件 |
| AccessibilityHelper | 无障碍访问辅助组件 |

## 设计规范

### 配色方案

- 主色调：金色 (#d4a017)
- 背景色：深墨 (#121212)
- 五行配色：
  - 金：白银 (#c0c0c0)
  - 木：绿 (#228b22)
  - 水：蓝 (#1e90ff)
  - 火：红 (#dc143c)
  - 土：黄 (#daa520)

### 字体

- 中文：Noto Serif SC
- 等宽：系统默认

## 组件使用示例

### 基础组件

```vue
<template>
  <!-- 按钮 -->
  <Button variant="primary" size="lg" @click="handleClick">
    点击我
  </Button>

  <!-- 输入框 -->
  <InputField v-model="value" placeholder="请输入..." />

  <!-- 卡片 -->
  <Card bordered hoverable>
    <template #header>
      <h3>卡片标题</h3>
    </template>
    <p>卡片内容</p>
  </Card>

  <!-- 模态框 -->
  <Modal v-model:visible="showModal" title="提示">
    <p>这是模态框内容</p>
  </Modal>
</template>
```

### 排盘组件

```vue
<template>
  <!-- 太极动画 -->
  <TaijiAnimation />

  <!-- 六爻排盘 -->
  <HexagramChart
    :hexagram="hexagram"
    :changed-hexagram="changedHexagram"
  />

  <!-- 分析面板 -->
  <AnalysisPanel :analysis="analysis" />
</template>
```

### 通知系统

```vue
<script setup>
import { useNotification } from '~/composables/useNotification'

const notification = useNotification()

function showNotification() {
  notification.success('成功', '操作已完成')
  notification.error('错误', '操作失败')
  notification.warning('警告', '请注意')
  notification.info('提示', '这是一条消息')
}
</script>
```

## 环境变量

创建 `.env` 文件：

```bash
# 后端API地址
API_BASE=http://localhost:8000
```

## 开发指南

### 添加新页面

1. 在 `pages/` 目录下创建 `.vue` 文件
2. 使用 `<script setup>` 语法
3. 导入需要的组件和组合函数

### 添加新组件

1. 在 `components/` 目录下创建 `.vue` 文件
2. 使用 TypeScript 定义 Props 和 Emits
3. 更新 `index.ts` 导出文件

### 添加新组合函数

1. 在 `composables/` 目录下创建 `.ts` 文件
2. 使用 TypeScript 定义返回类型
3. 更新 `index.ts` 导出文件

## 许可证

MIT
