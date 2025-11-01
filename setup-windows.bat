@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
echo ╔════════════════════════════════════════╗
echo ║  TrendRadar MCP One-Click Setup (Windows)    ║
echo ╚════════════════════════════════════════╝
echo.

REM 获取当前目录
set "PROJECT_ROOT=%CD%"
echo 📍 Project directory: %PROJECT_ROOT%
echo.

REM 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未检测到 Python，请先安装 Python 3.10+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查 UV
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo [1/3] 🔧 UV not installed，installing automatically...
    echo.
    
    REM 使用 Bypass 执行策略
    powershell -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    
    if %errorlevel% neq 0 (
        echo ❌ UV installation failed
        echo.
        echo 请Manual installation UV:
        echo   方法1: 访问 https://docs.astral.sh/uv/getting-started/installation/
        echo   方法2: 使用 pip install uv
        pause
        exit /b 1
    )
    
    echo.
    echo ✅ UV 安装Complete
    echo ⚠️  重要: 请按照以下步骤操作:
    echo   1. 关闭此窗口
    echo   2. 重新打开Command提示符（或 PowerShell）
    echo   3. 回到Project directory: cd "%PROJECT_ROOT%"
    echo   4. 重新运行此脚本: setup-windows.bat
    echo.
    pause
    exit /b 0
) else (
    echo [1/3] ✅ UV installed
    uv --version
)

echo.
echo [2/3] 📦 Installing project dependencies...
echo.

REM 使用 UV 安装依赖
uv sync
if %errorlevel% neq 0 (
    echo ❌ Dependency installation failed
    echo.
    echo Possible reasons:
    echo   - 缺少 pyproject.toml 文件
    echo   - 网络连接问题
    echo   - Python 版本不兼容
    pause
    exit /b 1
)

echo.
echo [3/3] ✅ Checking configuration files...

if not exist "config\config.yaml" (
    echo ⚠️  配置文件不存在: config\config.yaml
    if exist "config\config.example.yaml" (
        echo 提示: 发现示例配置文件，请复制并修改:
        echo   copy config\config.example.yaml config\config.yaml
    )
    echo.
)

REM Get UV path
for /f "tokens=*" %%i in ('where uv 2^>nul') do set "UV_PATH=%%i"

if not defined UV_PATH (
    echo ⚠️  无法Get UV path，请手动查找
    set "UV_PATH=uv"
)

echo.
echo ╔════════════════════════════════════════╗
echo ║           Setup complete！                   ║
echo ╚════════════════════════════════════════╝
echo.
echo 📋 MCP 服务器配置信息:
echo.
echo   Command: %UV_PATH%
echo   工作目录: %PROJECT_ROOT%
echo.
echo   参数（逐行填入）:
echo     --directory
echo     %PROJECT_ROOT%
echo     run
echo     python
echo     -m
echo     mcp_server.server
echo.
echo 📖 详细教程: README-Cherry-Studio.md
echo.
pause
