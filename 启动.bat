@echo off
chcp 65001 >nul
title 局域网端口扫描器

echo.
echo ========================================
echo   局域网端口扫描器 v1.0
echo ========================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.7+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [信息] 检测到 Python 环境
echo.

REM 检查依赖是否安装
python -c "import tabulate" >nul 2>&1
if errorlevel 1 (
    echo [信息] 正在安装依赖包...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
    echo [成功] 依赖安装完成
    echo.
)

echo [信息] 启动图形界面...
echo.
python app.py

if errorlevel 1 (
    echo.
    echo [错误] 程序运行出错
    pause
)
