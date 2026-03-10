@echo off
chcp 65001 >nul
title 局域网端口扫描器 - 自动安装

echo.
echo ========================================
echo   局域网端口扫描器 v1.0
echo   自动安装和启动
echo ========================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python
    echo.
    echo 请先安装 Python 3.7 或更高版本
    echo 下载地址: https://www.python.org/downloads/
    echo.
    echo 安装时请勾选 "Add Python to PATH"
    pause
    exit /b 1
)

echo [✓] 检测到 Python 环境
python --version
echo.

REM 检查虚拟环境是否存在
if not exist "venv" (
    echo [信息] 首次运行，正在创建虚拟环境...
    python -m venv venv
    if errorlevel 1 (
        echo [错误] 虚拟环境创建失败
        echo.
        echo 请确保 Python 安装完整，包含 venv 模块
        pause
        exit /b 1
    )
    echo [✓] 虚拟环境创建成功
    echo.
) else (
    echo [✓] 虚拟环境已存在
    echo.
)

REM 激活虚拟环境
echo [信息] 激活虚拟环境...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [错误] 虚拟环境激活失败
    pause
    exit /b 1
)
echo [✓] 虚拟环境已激活
echo.

REM 检查依赖是否安装
python -c "import tabulate" >nul 2>&1
if errorlevel 1 (
    echo [信息] 正在安装依赖包...
    echo.
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [错误] 依赖安装失败
        echo.
        echo 可能的原因:
        echo 1. 网络连接问题
        echo 2. pip 版本过旧
        echo 3. 权限不足
        echo.
        echo 解决方案:
        echo 1. 检查网络连接
        echo 2. 运行: python -m pip install --upgrade pip
        echo 3. 以管理员身份运行此脚本
        pause
        exit /b 1
    )
    echo.
    echo [✓] 依赖安装完成
    echo.
) else (
    echo [✓] 依赖已安装
    echo.
)

REM 启动应用
echo ========================================
echo   正在启动图形界面...
echo ========================================
echo.
python app.py

REM 检查退出状态
if errorlevel 1 (
    echo.
    echo ========================================
    echo [错误] 程序运行出错
    echo ========================================
    echo.
    echo 可能的原因:
    echo 1. 缺少必要的依赖
    echo 2. Python 版本不兼容
    echo 3. 图形界面环境问题
    echo.
    echo 解决方案:
    echo 1. 删除 venv 文件夹后重新运行
    echo 2. 确保 Python 版本 3.7+
    echo 3. 尝试运行命令行版本: python cli.py --help
    echo.
    pause
)

REM 退出时保持窗口打开（如果有错误）
if errorlevel 1 pause
