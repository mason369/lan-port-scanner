# 快速启动指南

## Windows 用户

### 方式 1: 双击启动（最简单）

1. 找到 `start.bat` 文件
2. 双击运行
3. 等待自动安装完成
4. 图形界面自动启动

### 方式 2: PowerShell 启动

```powershell
# 打开 PowerShell
# 进入项目目录
cd C:\端口扫描软件

# 运行启动脚本
.\start.bat
```

### 方式 3: 命令提示符启动

```cmd
# 打开 CMD
# 进入项目目录
cd C:\端口扫描软件

# 运行启动脚本
start.bat
```

### 方式 4: 手动启动

```cmd
# 1. 创建虚拟环境（首次）
python -m venv venv

# 2. 激活虚拟环境
venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动应用
python app.py
```

## Linux/macOS 用户

### 方式 1: 脚本启动（推荐）

```bash
# 添加执行权限（首次）
chmod +x 运行.sh

# 运行脚本
./运行.sh
```

### 方式 2: 手动启动

```bash
# 1. 创建虚拟环境（首次）
python3 -m venv venv

# 2. 激活虚拟环境
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动应用
python app.py
```

## 常见问题

### Q: 双击 start.bat 后闪退？

**原因**: Python 未安装或未添加到 PATH

**解决方案**:
1. 下载 Python: https://www.python.org/downloads/
2. 安装时勾选 "Add Python to PATH"
3. 重启电脑
4. 再次运行 start.bat

### Q: 提示 "Python not found"？

**解决方案**:
```cmd
# 检查 Python 是否安装
python --version

# 如果提示找不到命令，需要安装 Python
# 或将 Python 添加到 PATH 环境变量
```

### Q: 依赖安装失败？

**解决方案**:
```cmd
# 升级 pip
python -m pip install --upgrade pip

# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q: 图形界面无法启动？

**Windows**:
- 确保安装了完整的 Python（包含 tkinter）
- 重新安装 Python，勾选所有组件

**Linux**:
```bash
# Ubuntu/Debian
sudo apt install python3-tk

# CentOS/RHEL
sudo yum install python3-tkinter
```

**macOS**:
```bash
# 使用 Homebrew
brew install python-tk
```

### Q: 如何使用命令行版本？

如果图形界面无法启动，可以使用命令行版本：

```bash
# 查看帮助
python cli.py --help

# 快速扫描
python cli.py --auto --common

# 自定义扫描
python cli.py -n 192.168.1 -r 1-100 -p 80,443,8080
```

## 首次使用建议

1. **小范围测试**
   - 主机范围: 1-10
   - 端口模式: 常用端口
   - 启用隐蔽模式

2. **检查结果**
   - 查看扫描结果是否正确
   - 确认服务识别是否准确

3. **调整参数**
   - 根据网络情况调整并发数
   - 根据需求选择端口范围

4. **导出结果**
   - 测试导出功能
   - 确认文件格式正确

## 卸载

### 完全卸载

```bash
# 1. 删除虚拟环境
# Windows
rmdir /s venv

# Linux/macOS
rm -rf venv

# 2. 删除项目文件夹
# 直接删除整个项目目录即可
```

### 保留配置卸载

```bash
# 只删除虚拟环境和缓存
# Windows
rmdir /s venv
del /s *.pyc
rmdir /s __pycache__

# Linux/macOS
rm -rf venv
find . -name "*.pyc" -delete
find . -name "__pycache__" -delete
```

## 更新

```bash
# 进入项目目录
cd lan-port-scanner

# 拉取最新代码
git pull

# 更新依赖
pip install -r requirements.txt --upgrade

# 重新启动
python app.py
```

## 获取帮助

- 查看 README.md - 完整文档
- 查看 使用说明.md - 详细说明
- 查看 界面说明.md - 界面指南
- GitHub Issues: https://github.com/mason369/lan-port-scanner/issues
