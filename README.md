# LAN Port Scanner

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)
![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)

一个功能强大的局域网端口扫描工具，支持隐蔽扫描、服务识别和高性能异步扫描。

[功能特性](#功能特性) • [安装](#安装) • [使用方法](#使用方法) • [技术原理](#技术原理) • [许可证](#许可证)

</div>

---

## 功能特性

### 🖥️ 现代化图形界面
- **专业设计**: 现代化的桌面应用界面，操作直观
- **实时反馈**: 扫描进度实时显示，结果即时更新
- **数据可视化**: 表格展示扫描结果，支持排序和筛选
- **多格式导出**: 支持 JSON、CSV 格式导出
- **详情查看**: 双击查看端口详细信息

### 🚀 高性能扫描
- **异步并发**: 基于 Python asyncio 实现高速并发扫描
- **智能限流**: 可配置的并发连接数，避免网络拥塞
- **快速响应**: 支持自定义超时时间，优化扫描速度

### 🕵️ 隐蔽扫描技术
- **随机化扫描**: 随机化主机和端口扫描顺序，避免被检测
- **动态延迟**: 可配置的随机延迟范围，模拟正常流量
- **轻量连接**: 使用 TCP 连接测试，快速断开，减少日志记录

### 🔍 服务识别
- **Banner 抓取**: 自动获取服务 banner 信息
- **服务指纹**: 内置常见服务特征库，智能识别服务类型
- **版本检测**: 尝试识别服务版本信息

### 💻 多种使用方式
- **图形界面 (GUI)**: 现代化的桌面应用，操作简单直观
- **命令行 (CLI)**: 强大的命令行工具，支持脚本化
- **Python 模块**: 可作为 Python 库导入使用

---

## 安装

### 前置要求
- Python 3.7 或更高版本
- pip 包管理器

### 一键启动（推荐）

**Windows 用户：**
```bash
# 双击运行 运行.bat
# 或在命令行中执行
运行.bat
```

**Linux/macOS 用户：**
```bash
# 添加执行权限
chmod +x 运行.sh

# 运行脚本
./运行.sh
```

**自动化功能：**
- ✅ 自动检测 Python 环境
- ✅ 自动创建虚拟环境
- ✅ 自动安装依赖包
- ✅ 自动启动图形界面
- ✅ 错误提示和解决方案

### 手动安装

1. 克隆仓库
```bash
git clone https://github.com/mason369/lan-port-scanner.git
cd lan-port-scanner
```

2. 创建虚拟环境（可选但推荐）
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 启动应用
```bash
python app.py
```

---

## 使用方法

### 图形界面模式（推荐）

启动现代化 GUI 应用：
```bash
python app.py
```

**界面特性：**
- 🎨 现代化设计，操作直观
- 📡 自动检测本地网络
- 🔌 多种端口扫描模式（常用/Top 100/自定义）
- ⚙️ 灵活的扫描参数配置
- 🕵️ 一键启用隐蔽模式
- 📊 实时统计信息展示
- 💾 支持 JSON/CSV 格式导出
- 📋 一键复制结果到剪贴板
- 🔍 双击查看端口详细信息

**使用步骤：**
1. 启动应用后自动检测本地网络
2. 选择扫描模式和配置参数
3. 点击"开始扫描"按钮
4. 实时查看扫描结果
5. 导出或复制结果

### 命令行模式

#### 基本用法

扫描本地网络的常用端口：
```bash
python cli.py --auto --common
```

扫描指定网络段：
```bash
python cli.py -n 192.168.1 -r 1-254 --common
```

#### 高级用法

扫描自定义端口：
```bash
python cli.py -n 192.168.1 -r 1-100 -p 80,443,8080,3306
```

扫描端口范围：
```bash
python cli.py -n 192.168.1 -r 1-50 -p 1-1000
```

高速扫描（增加并发数）：
```bash
python cli.py --auto --top100 -c 200 -t 0.5
```

导出结果：
```bash
python cli.py --auto --common -o results.json
```

#### 命令行参数说明

```
网络配置:
  -n, --network NETWORK    网络前缀 (如: 192.168.1)
  -r, --range RANGE        主机范围 (如: 1-254), 默认: 1-254
  --auto                   自动检测本地网络

端口配置:
  -p, --ports PORTS        自定义端口 (如: 80,443 或 1-1000)
  --common                 扫描常用端口 (18个)
  --top100                 扫描 Top 100 端口
  --all                    扫描所有端口 (1-65535)

扫描参数:
  -c, --concurrent N       最大并发连接数, 默认: 100
  -t, --timeout SECONDS    连接超时时间, 默认: 1.0
  --no-stealth             禁用隐蔽模式
  --delay RANGE            随机延迟范围, 默认: 0.01-0.1

输出选项:
  -o, --output FILE        输出文件 (JSON 格式)
  -v, --verbose            详细输出
  --no-banner              不显示 banner 信息
```

### 作为 Python 模块使用

```python
import asyncio
from scanner import StealthScanner, COMMON_PORTS

async def scan_network():
    # 创建扫描器
    scanner = StealthScanner(
        max_concurrent=100,
        timeout=1.0,
        delay_range=(0.01, 0.1),
        randomize=True
    )

    # 扫描网络
    results = await scanner.scan_network(
        network_prefix="192.168.1",
        ports=COMMON_PORTS,
        host_range=(1, 254)
    )

    # 处理结果
    for ip, ports in results.items():
        print(f"主机: {ip}")
        for result in ports:
            print(f"  端口 {result.port}: {result.service}")

# 运行扫描
asyncio.run(scan_network())
```

---

## 技术原理

### 隐蔽扫描技术

本工具实现了多种反检测技术，降低被入侵检测系统（IDS）和防火墙发现的概率：

1. **随机化扫描顺序**
   - 随机化主机扫描顺序
   - 随机化端口扫描顺序
   - 避免顺序扫描的特征模式

2. **动态延迟**
   - 在每次连接之间添加随机延迟
   - 模拟正常用户行为
   - 可配置延迟范围

3. **轻量级连接**
   - 使用 TCP 连接测试而非 SYN 扫描
   - 快速建立和断开连接
   - 减少日志记录

4. **并发控制**
   - 使用信号量限制并发连接数
   - 避免网络拥塞和异常流量
   - 可根据网络环境调整

### 服务识别机制

服务识别通过以下方式实现：

1. **端口映射**: 基于 IANA 端口分配表的常见端口服务映射
2. **Banner 抓取**: 连接到开放端口并读取服务 banner
3. **特征匹配**: 使用服务特征指纹库进行模式匹配
4. **协议探测**: 针对特定协议发送探测包

### 性能优化

- **异步 I/O**: 使用 asyncio 实现非阻塞 I/O 操作
- **并发扫描**: 同时扫描多个主机和端口
- **连接池**: 复用连接资源，减少开销
- **超时控制**: 快速跳过无响应的端口

---

## 使用场景

### ✅ 合法用途
- 网络管理和维护
- 安全审计和渗透测试（授权）
- 网络资产发现
- 服务可用性监控
- 学习网络安全知识

### ⚠️ 法律声明

**重要**: 本工具仅供合法的网络管理、安全研究和教育目的使用。

- ✅ 仅扫描您拥有或获得授权的网络
- ✅ 在进行安全测试前获得书面授权
- ❌ 禁止未经授权扫描他人网络
- ❌ 禁止用于任何非法目的

未经授权的端口扫描可能违反计算机欺诈和滥用法（CFAA）或其他相关法律。使用本工具即表示您同意遵守所有适用的法律法规，并对您的行为负全部责任。

---

## 技术参考

本项目参考了以下技术文献和开源项目：

- [Asyncio Port Scanner in Python](https://superfastpython.com/asyncio-port-scanner/)
- [Nmap Stealth Scanning Techniques](https://haktechs.com/nmap-stealth-scanning-avoid-detection-while-scanning/)
- [Building a Custom Security Tool: Python Port Scanner](https://blog.shellnetsecurity.com/posts/2025/building-custom-port-scanner-python/)
- [FingerprintX: Fast Port Fingerprint Scanner](https://www.praetorian.com/blog/fingerprintx)
- [Identifying Services with TCP Stateless Scanning](https://www.mdpi.com/2079-9292/15/2/446)

---

## 项目结构

```
lan-port-scanner/
├── app.py              # 现代化图形界面（推荐）
├── scanner.py          # 核心扫描引擎
├── gui.py              # 基础图形界面
├── cli.py              # 命令行界面
├── examples.py         # 使用示例
├── 运行.bat            # Windows 一键启动脚本
├── 运行.sh             # Linux/macOS 一键启动脚本
├── 启动.bat            # Windows 简易启动脚本
├── 启动.sh             # Linux/macOS 简易启动脚本
├── requirements.txt    # 依赖包列表
├── 快速入门.md         # 快速入门指南
├── README.md           # 项目文档
├── LICENSE             # Apache 2.0 许可证
└── .gitignore          # Git 忽略文件
```

---

## 常见问题

### Q: 扫描速度慢怎么办？
A: 可以尝试以下方法：
- 增加并发数 (`-c 200`)
- 减少超时时间 (`-t 0.5`)
- 禁用隐蔽模式 (`--no-stealth`)
- 减少扫描的端口数量

### Q: 为什么有些端口扫描不到？
A: 可能的原因：
- 防火墙阻止了连接
- 主机不在线
- 超时时间设置过短
- 网络延迟较高

### Q: 如何避免被检测？
A: 建议：
- 启用隐蔽模式
- 降低并发数
- 增加延迟范围
- 分批次扫描

---

## 贡献

欢迎贡献代码、报告问题或提出建议！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: add some amazing feature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 许可证

本项目采用 Apache License 2.0 许可证。详见 [LICENSE](LICENSE) 文件。

```
Copyright 2026 mason369

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

---

## 联系方式

- GitHub: [@mason369](https://github.com/mason369)
- Issues: [提交问题](https://github.com/mason369/lan-port-scanner/issues)

---

<div align="center">

**⭐ 如果这个项目对您有帮助，请给个 Star！⭐**

Made with ❤️ by mason369

</div>
