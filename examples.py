#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用示例 - 演示如何使用扫描器模块
"""

import asyncio
from scanner import StealthScanner, get_local_network, COMMON_PORTS


async def example_1_basic_scan():
    """示例 1: 基本扫描"""
    print("=" * 60)
    print("示例 1: 基本端口扫描")
    print("=" * 60)

    scanner = StealthScanner()

    # 扫描本机的常用端口
    results = await scanner.scan_host("127.0.0.1", [80, 443, 3306, 8080])

    print(f"\n发现 {len(results)} 个开放端口:")
    for result in results:
        print(f"  端口 {result.port}: {result.service}")


async def example_2_network_scan():
    """示例 2: 网络扫描"""
    print("\n" + "=" * 60)
    print("示例 2: 局域网扫描")
    print("=" * 60)

    # 自动检测本地网络
    network = get_local_network()
    print(f"检测到网络: {network}.0/24")

    scanner = StealthScanner(
        max_concurrent=50,
        timeout=1.0,
        randomize=True
    )

    # 扫描网络中的前 5 个主机
    results = await scanner.scan_network(
        network_prefix=network,
        ports=[80, 443, 22, 3389],
        host_range=(1, 5)
    )

    print(f"\n发现 {len(results)} 个活跃主机:")
    for ip, ports in results.items():
        print(f"\n主机 {ip}:")
        for result in ports:
            print(f"  端口 {result.port}: {result.service}")
            if result.banner:
                print(f"    Banner: {result.banner[:50]}")


async def example_3_stealth_scan():
    """示例 3: 隐蔽扫描"""
    print("\n" + "=" * 60)
    print("示例 3: 隐蔽扫描模式")
    print("=" * 60)

    scanner = StealthScanner(
        max_concurrent=20,  # 降低并发数
        timeout=2.0,        # 增加超时时间
        delay_range=(0.1, 0.5),  # 增加延迟
        randomize=True      # 启用随机化
    )

    print("使用隐蔽模式扫描...")
    results = await scanner.scan_host("127.0.0.1", COMMON_PORTS)

    print(f"\n发现 {len(results)} 个开放端口")


async def example_4_service_detection():
    """示例 4: 服务检测"""
    print("\n" + "=" * 60)
    print("示例 4: 服务识别和 Banner 抓取")
    print("=" * 60)

    scanner = StealthScanner()

    # 扫描并识别服务
    results = await scanner.scan_host("127.0.0.1", [80, 443, 22, 3306, 6379])

    print("\n服务识别结果:")
    for result in results:
        print(f"\n端口 {result.port}:")
        print(f"  服务: {result.service}")
        print(f"  状态: {result.state}")
        if result.banner:
            print(f"  Banner: {result.banner}")


async def main():
    """运行所有示例"""
    print("\n局域网端口扫描器 - 使用示例\n")

    try:
        await example_1_basic_scan()
        await example_2_network_scan()
        await example_3_stealth_scan()
        await example_4_service_detection()

        print("\n" + "=" * 60)
        print("所有示例运行完成！")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n错误: {e}")


if __name__ == "__main__":
    asyncio.run(main())
