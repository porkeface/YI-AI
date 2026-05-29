#!/bin/bash

echo "==================================="
echo "  YI-AI 前端启动脚本"
echo "==================================="
echo ""

# 检查Node.js
if ! command -v node &> /dev/null; then
    echo "错误: 未找到Node.js，请先安装Node.js"
    exit 1
fi

# 检查npm
if ! command -v npm &> /dev/null; then
    echo "错误: 未找到npm，请先安装npm"
    exit 1
fi

echo "Node.js版本: $(node -v)"
echo "npm版本: $(npm -v)"
echo ""

# 检查是否已安装依赖
if [ ! -d "node_modules" ]; then
    echo "正在安装依赖..."
    npm install
    echo ""
fi

echo "启动开发服务器..."
echo "访问地址: http://localhost:3000"
echo ""
echo "按 Ctrl+C 停止服务器"
echo ""

npm run dev
