@echo off
echo ===================================
echo   YI-AI 前端启动脚本
echo ===================================
echo.

:: 检查Node.js
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo 错误: 未找到Node.js，请先安装Node.js
    pause
    exit /b 1
)

:: 检查npm
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo 错误: 未找到npm，请先安装npm
    pause
    exit /b 1
)

echo Node.js版本:
node -v
echo npm版本:
npm -v
echo.

:: 检查是否已安装依赖
if not exist "node_modules" (
    echo 正在安装依赖...
    npm install
    echo.
)

echo 启动开发服务器...
echo 访问地址: http://localhost:3000
echo.
echo 按 Ctrl+C 停止服务器
echo.

npm run dev
pause
