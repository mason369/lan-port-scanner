#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Linux 平台兼容性测试
"""

import sys
import platform
import subprocess


def test_linux_compatibility():
    """测试 Linux 平台兼容性"""
    print("=" * 60)
    print("Linux 平台兼容性测试")
    print("=" * 60)
    print()

    # 检查操作系统
    if platform.system() != 'Linux':
        print(f"⚠️  当前系统: {platform.system()}")
        print("此测试脚本专为 Linux 设计")
        print()

    print(f"系统: {platform.system()}")
    print(f"发行版: {platform.platform()}")
    print(f"Python 版本: {sys.version}")
    print()

    # 检查 Python 版本
    if sys.version_info < (3, 7):
        print("❌ Python 版本过低，需要 3.7+")
        return False
    else:
        print("✅ Python 版本符合要求")

    # 检查 PyQt6
    print()
    print("检查 PyQt6...")
    try:
        import PyQt6
        from PyQt6.QtWidgets import QApplication
        print(f"✅ PyQt6 已安装 (版本: {PyQt6.QtCore.PYQT_VERSION_STR})")

        # 测试 QApplication
        app = QApplication([])
        print("✅ QApplication 可以创建")
        app.quit()

    except ImportError as e:
        print(f"❌ PyQt6 未安装: {e}")
        print()
        print("安装方法:")
        print("  Ubuntu/Debian: sudo apt install python3-pyqt6")
        print("  或: pip install PyQt6")
        return False
    except Exception as e:
        print(f"⚠️  PyQt6 测试失败: {e}")
        print("可能需要图形环境 (X11/Wayland)")

    # 检查显示环境
    print()
    print("检查显示环境...")
    display = subprocess.run(['echo', '$DISPLAY'], capture_output=True, text=True)
    if display.stdout.strip():
        print(f"✅ DISPLAY 环境变量已设置")
    else:
        print("⚠️  DISPLAY 环境变量未设置")
        print("可能需要:")
        print("  - 本地图形环境")
        print("  - SSH X11 转发: ssh -X user@host")

    # 检查必要的系统库
    print()
    print("检查系统库...")
    libs = [
        'libxcb-xinerama0',
        'libxcb-cursor0',
        'libxcb-icccm4',
        'libxcb-image0',
        'libxcb-keysyms1',
        'libxcb-randr0',
        'libxcb-render-util0',
        'libxcb-shape0'
    ]

    for lib in libs:
        result = subprocess.run(
            ['dpkg', '-l', lib],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✅ {lib}")
        else:
            print(f"⚠️  {lib} (可选)")

    # 检查扫描器模块
    print()
    print("检查扫描器模块...")
    try:
        from scanner import StealthScanner, get_local_network
        print("✅ scanner 模块可以导入")

        network = get_local_network()
        print(f"✅ 网络检测: {network}.0/24")
    except Exception as e:
        print(f"❌ scanner 模块错误: {e}")
        return False

    # 检查 GUI 模块
    print()
    print("检查 GUI 模块...")
    try:
        from app_qt import ModernScannerGUI
        print("✅ app_qt 模块可以导入")
    except Exception as e:
        print(f"❌ app_qt 模块错误: {e}")
        return False

    print()
    print("=" * 60)
    print("✅ Linux 平台兼容性测试通过！")
    print("=" * 60)
    print()
    print("启动应用:")
    print("  python3 app_qt.py")
    print()

    return True


if __name__ == "__main__":
    try:
        success = test_linux_compatibility()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n测试中断")
        sys.exit(1)
