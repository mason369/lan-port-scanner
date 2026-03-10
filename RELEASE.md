# Release 发布指南

## 自动发布（推荐）

### 通过 Git Tag 触发

1. 创建并推送 tag：
```bash
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

2. GitHub Actions 会自动：
   - 构建 Windows 可执行文件
   - 构建 Linux 可执行文件
   - 创建 Release
   - 上传文件到 Release

### 手动触发

1. 访问 GitHub Actions 页面
2. 选择 "Build and Release" workflow
3. 点击 "Run workflow"
4. 选择分支并运行

## 本地构建

### Windows

```bash
# 运行构建脚本
.\build_windows.bat

# 或手动构建
pip install pyinstaller
pyinstaller LAN-Port-Scanner.spec

# 输出位置
dist\LAN-Port-Scanner.exe
```

### Linux

```bash
# 运行构建脚本
chmod +x build_linux.sh
./build_linux.sh

# 或手动构建
pip install pyinstaller
pyinstaller --name="lan-port-scanner" --onefile --add-data "scanner.py:." app_qt.py

# 输出位置
dist/lan-port-scanner
```

## 手动创建 Release

1. 访问 GitHub 仓库
2. 点击 "Releases"
3. 点击 "Create a new release"
4. 填写信息：
   - Tag: v1.0.0
   - Title: v1.0.0 - 首个正式版本
   - Description: 见下方模板
5. 上传构建的可执行文件
6. 发布

## Release 描述模板

```markdown
## 局域网端口扫描器 v1.0.0

### 🎉 首个正式版本

这是局域网端口扫描器的首个正式版本，提供了完整的功能和跨平台支持。

### 📦 下载

**Windows 用户:**
- 下载 `LAN-Port-Scanner.exe`
- 双击运行，无需安装 Python
- 支持 Windows 7/8/10/11 (64-bit)

**Linux 用户:**
- 下载 `lan-port-scanner`
- 添加执行权限: `chmod +x lan-port-scanner`
- 运行: `./lan-port-scanner`
- 支持 Ubuntu 20.04+, Debian 11+, CentOS 8+

### ✨ 主要特性

- 🖥️ **PyQt6 现代化界面** - 专业的图形界面设计
- 🚀 **高性能扫描** - 异步并发，可配置并发数
- 🕵️ **隐蔽扫描** - 随机化、动态延迟，避免检测
- 🔍 **服务识别** - 自动识别 20+ 常见服务
- 🌐 **跨平台支持** - Windows/Linux/macOS 完美兼容
- 💾 **结果导出** - 支持 JSON/CSV 格式

### 🚀 快速开始

1. 下载对应平台的可执行文件
2. 直接运行（无需安装 Python）
3. 配置扫描参数
4. 点击"开始扫描"

### 📚 使用说明

**基本操作:**
1. 自动检测或手动输入网络段
2. 选择端口扫描模式（常用/Top100/自定义）
3. 调整扫描参数（并发数、超时时间）
4. 启用隐蔽模式（推荐）
5. 开始扫描

**高级功能:**
- 双击结果查看详情
- 导出结果为 JSON/CSV
- 复制结果到剪贴板
- 实时统计信息

### 🔧 从源码运行

如果你想从源码运行或进行开发：

```bash
# 克隆仓库
git clone https://github.com/mason369/lan-port-scanner.git
cd lan-port-scanner

# 安装依赖
pip install PyQt6 tabulate

# 运行
python app_qt.py
```

### 📋 系统要求

**Windows:**
- Windows 7/8/10/11 (64-bit)
- 无需安装 Python（使用可执行文件）

**Linux:**
- Ubuntu 20.04+, Debian 11+, CentOS 8+
- 需要图形环境 (X11/Wayland)
- 无需安装 Python（使用可执行文件）

**从源码运行:**
- Python 3.7+
- PyQt6
- tabulate

### ⚠️ 重要提示

**法律声明:**
- 本工具仅供合法的网络管理和安全研究使用
- 请遵守当地法律法规
- 未经授权扫描他人网络可能违法

**使用建议:**
- 仅扫描您拥有或获得授权的网络
- 启用隐蔽模式以减少对网络的影响
- 合理设置并发数和超时时间

### 🐛 已知问题

- Linux 下需要图形环境，SSH 连接需要 X11 转发
- 某些防火墙可能拦截扫描流量
- 大规模扫描可能触发 IDS 告警

### 📞 技术支持

- **文档**: https://github.com/mason369/lan-port-scanner
- **Issues**: https://github.com/mason369/lan-port-scanner/issues
- **作者**: @mason369

### 🙏 致谢

感谢所有参考的开源项目和技术文献。

---

**完整更新日志**: https://github.com/mason369/lan-port-scanner/blob/master/CHANGELOG.md
```

## 版本号规范

遵循语义化版本 (Semantic Versioning):

- **主版本号 (Major)**: 不兼容的 API 修改
- **次版本号 (Minor)**: 向下兼容的功能性新增
- **修订号 (Patch)**: 向下兼容的问题修正

示例:
- v1.0.0 - 首个正式版本
- v1.1.0 - 添加新功能
- v1.1.1 - 修复 bug
- v2.0.0 - 重大更新

## 发布检查清单

发布前确认：

- [ ] 所有测试通过
- [ ] 文档已更新
- [ ] CHANGELOG 已更新
- [ ] 版本号已更新
- [ ] 构建成功（Windows + Linux）
- [ ] 可执行文件已测试
- [ ] Release 说明已准备
- [ ] Tag 已创建并推送

## 发布后

1. 验证 Release 页面
2. 测试下载链接
3. 更新 README 徽章
4. 发布公告（如需要）
5. 监控 Issues 反馈
