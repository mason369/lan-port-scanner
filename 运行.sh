#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "========================================"
echo "  局域网端口扫描器 v1.0"
echo "  自动安装和启动"
echo "========================================"
echo ""

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[错误] 未检测到 Python3${NC}"
    echo ""
    echo "请先安装 Python 3.7 或更高版本"
    echo ""
    echo "Ubuntu/Debian: sudo apt install python3 python3-venv python3-pip"
    echo "CentOS/RHEL:   sudo yum install python3 python3-pip"
    echo "macOS:         brew install python3"
    echo ""
    exit 1
fi

echo -e "${GREEN}[✓] 检测到 Python 环境${NC}"
python3 --version
echo ""

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo -e "${BLUE}[信息] 首次运行，正在创建虚拟环境...${NC}"
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}[错误] 虚拟环境创建失败${NC}"
        echo ""
        echo "请确保已安装 python3-venv 模块"
        echo "Ubuntu/Debian: sudo apt install python3-venv"
        echo ""
        exit 1
    fi
    echo -e "${GREEN}[✓] 虚拟环境创建成功${NC}"
    echo ""
else
    echo -e "${GREEN}[✓] 虚拟环境已存在${NC}"
    echo ""
fi

# 激活虚拟环境
echo -e "${BLUE}[信息] 激活虚拟环境...${NC}"
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo -e "${RED}[错误] 虚拟环境激活失败${NC}"
    exit 1
fi
echo -e "${GREEN}[✓] 虚拟环境已激活${NC}"
echo ""

# 检查依赖是否安装
if ! python -c "import tabulate" &> /dev/null; then
    echo -e "${BLUE}[信息] 正在安装依赖包...${NC}"
    echo ""
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo ""
        echo -e "${RED}[错误] 依赖安装失败${NC}"
        echo ""
        echo "可能的原因:"
        echo "1. 网络连接问题"
        echo "2. pip 版本过旧"
        echo "3. 权限不足"
        echo ""
        echo "解决方案:"
        echo "1. 检查网络连接"
        echo "2. 运行: python -m pip install --upgrade pip"
        echo "3. 确保有写入权限"
        echo ""
        exit 1
    fi
    echo ""
    echo -e "${GREEN}[✓] 依赖安装完成${NC}"
    echo ""
else
    echo -e "${GREEN}[✓] 依赖已安装${NC}"
    echo ""
fi

# 启动应用
echo "========================================"
echo "  正在启动图形界面..."
echo "========================================"
echo ""
python app.py

# 检查退出状态
if [ $? -ne 0 ]; then
    echo ""
    echo "========================================"
    echo -e "${RED}[错误] 程序运行出错${NC}"
    echo "========================================"
    echo ""
    echo "可能的原因:"
    echo "1. 缺少必要的依赖"
    echo "2. Python 版本不兼容"
    echo "3. 图形界面环境问题（需要 X11/Wayland）"
    echo ""
    echo "解决方案:"
    echo "1. 删除 venv 文件夹后重新运行"
    echo "2. 确保 Python 版本 3.7+"
    echo "3. 尝试运行命令行版本: python cli.py --help"
    echo "4. 确保有图形界面环境（SSH 连接需要 X11 转发）"
    echo ""
    read -p "按回车键退出..."
fi
