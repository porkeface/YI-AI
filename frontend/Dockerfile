# 构建阶段
FROM node:18-alpine AS builder

WORKDIR /app

# 复制依赖文件
COPY package*.json ./

# 安装依赖
RUN npm ci

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# 生产阶段
FROM node:18-alpine AS production

WORKDIR /app

# 复制构建产物
COPY --from=builder /app/.output ./.output
COPY --from=builder /app/package*.json ./

# 安装生产依赖
RUN npm ci --only=production

# 暴露端口
EXPOSE 3000

# 启动应用
CMD ["node", ".output/server/index.mjs"]
