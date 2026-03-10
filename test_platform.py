#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跨平台兼容性测试脚本
测试应用在不同平台上的运行情况
"""

import sys
import platform
import tkinter as tk
from tkinter import ttk


def test_platform_info():
    """测试平台信息"""
    print("=" * 60)
    print("平台信息测试")
    print("=" * 60)
    print(f"操作系统: {platform.system()}")
    print(f"系统版本: {platform.release()}")
    print(f"Python 版本: {sys.version}")
    print(f"平台标识: {sys.platform}")
    print(f"架构: {platform.machine()}")
    print()


def test_tkinter():
    """测试 tkinter 可用性"""
    print("=" * 60)
    print("Tkinter 测试")
    print("=" * 60)

    try:
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口

        # 测试 tkinter 版本
        print(f"Tkinter 版本: {tk.TkVersion}")
        print(f"Tcl 版本: {tk.TclVersion}")

        # 测试可用主题
        style = ttk.Style()
        themes = style.theme_names()
        print(f"可用主题: {', '.join(themes)}")

        # 测试当前主题
        current_theme = style.theme_use()
        print(f"当前主题: {current_theme}")

        root.destroy()
        print("✅ Tkinter 测试通过")
        return True

    except Exception as e:
        print(f"❌ Tkinter 测试失败: {e}")
        return False


def test_dependencies():
    """测试依赖包"""
    print()
    print("=" * 60)
    print("依赖包测试")
    print("=" * 60)

    dependencies = {
        'asyncio': '异步 I/O',
        'socket': '网络通信',
        'json': 'JSON 处理',
        'datetime': '日期时间',
        'threading': '多线程',
    }

    all_ok = True
    for module, desc in dependencies.items():
        try:
            __import__(module)
            print(f"✅ {module:15} - {desc}")
        except ImportError:
            print(f"❌ {module:15} - {desc} (未安装)")
            all_ok = False

    # 测试可选依赖
    print()
    print("可选依赖:")
    try:
        import tabulate
        print(f"✅ tabulate - 表格格式化 (版本: {tabulate.__version__})")
    except ImportError:
        print("⚠️  tabulate - 表格格式化 (未安装，CLI 模式需要)")

    return all_ok


def test_scanner_module():
    """测试扫描器模块"""
    print()
    print("=" * 60)
    print("扫描器模块测试")
    print("=" * 60)

    try:
        from scanner import StealthScanner, get_local_network, COMMON_PORTS
        print("✅ scanner 模块导入成功")

        # 测试网络检测
        network = get_local_network()
        print(f"✅ 本地网络检测: {network}.0/24")

        # 测试端口列表
        print(f"✅ 常用端口数量: {len(COMMON_PORTS)}")

        return True

    except Exception as e:
        print(f"❌ scanner 模块测试失败: {e}")
        return False


def test_gui_creation():
    """测试 GUI 创建"""
    print()
    print("=" * 60)
    print("GUI 创建测试")
    print("=" * 60)

    try:
        from app import ModernScannerGUI

        root = tk.Tk()
        root.withdraw()

        # 尝试创建 GUI 实例
        app = ModernScannerGUI(root)
        print("✅ GUI 实例创建成功")

        # 测试窗口属性
        print(f"✅ 窗口标题: {root.title()}")
        print(f"✅ 窗口大小: {root.geometry()}")

        root.destroy()
        return True

    except Exception as e:
        print(f"❌ GUI 创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_font_support():
    """测试字体支持"""
    print()
    print("=" * 60)
    print("字体支持测试")
    print("=" * 60)

    try:
        root = tk.Tk()
        root.withdraw()

        import tkinter.font as tkfont

        # 获取可用字体
        fonts = tkfont.families()
        print(f"可用字体数量: {len(fonts)}")

        # 测试常用字体
        common_fonts = ['Arial', 'Helvetica', 'Courier', 'Times', 'Consolas', 'Monaco']
        available_fonts = []

        for font in common_fonts:
            if font in fonts:
                available_fonts.append(font)
                print(f"✅ {font}")
            else:
                print(f"⚠️  {font} (不可用)")

        root.destroy()

        if available_fonts:
            print(f"\n推荐使用字体: {available_fonts[0]}")
            return True
        else:
            print("\n⚠️  警告: 没有找到常用字体")
            return False

    except Exception as e:
        print(f"❌ 字体测试失败: {e}")
        return False


def run_all_tests():
    """运行所有测试"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "跨平台兼容性测试" + " " * 15 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    results = {
        '平台信息': True,
        'Tkinter': test_tkinter(),
        '依赖包': test_dependencies(),
        '扫描器模块': test_scanner_module(),
        'GUI 创建': test_gui_creation(),
        '字体支持': test_font_support(),
    }

    # 显示平台信息（总是成功）
    test_platform_info()

    # 总结
    print()
    print("=" * 60)
    print("测试总结")
    print("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:15} {status}")

    print()
    print(f"总计: {passed}/{total} 项测试通过")

    if passed == total:
        print()
        print("🎉 所有测试通过！应用可以在此平台正常运行。")
        return 0
    else:
        print()
        print("⚠️  部分测试失败，应用可能无法正常运行。")
        print()
        print("解决方案:")

        if not results['Tkinter']:
            print("- 安装 tkinter:")
            if sys.platform == 'linux':
                print("  Ubuntu/Debian: sudo apt install python3-tk")
                print("  CentOS/RHEL:   sudo yum install python3-tkinter")
            elif sys.platform == 'darwin':
                print("  macOS: brew install python-tk")

        if not results['依赖包']:
            print("- 安装依赖包: pip install -r requirements.txt")

        if not results['扫描器模块']:
            print("- 确保 scanner.py 文件存在且没有语法错误")

        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    print()
    input("按回车键退出...")
    sys.exit(exit_code)
