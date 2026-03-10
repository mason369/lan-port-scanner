#!/bin/bash

echo ""
echo "========================================"
echo "  局域网端口扫描器 v1.0"
echo "========================================"
echo ""

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到 Python3，请先安装 Python 3.7+"
    exit 1
fi

echo "[信息] 检测到 Python 环境"
echo ""

# 检查依赖是否安装
if ! python3 -c "import tabulate" &> /dev/null; then
    echo "[信息] 正在安装依赖包..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "[错误] 依赖安装失败"
        exit 1
    fi
    echo "[成功] 依赖安装完成"
    echo ""
fi

echo "[信息] 启动图形界面..."
echo ""
python3 app.py

if [ $? -ne 0 ]; then
    echo ""
    echo "[错误] 程序运行出错"
    read -p "按回车键退出..."
fi
