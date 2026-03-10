#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
局域网端口扫描器 - 命令行界面
提供命令行参数支持
"""

import argparse
import asyncio
import sys
from scanner import StealthScanner, get_local_network, COMMON_PORTS, TOP_100_PORTS
from tabulate import tabulate


def parse_ports(port_str: str) -> list:
    """
    解析端口字符串
    支持格式: "80,443,8080" 或 "1-1000" 或混合 "80,443,1000-2000"
    """
    ports = []
    for part in port_str.split(','):
        part = part.strip()
        if '-' in part:
            start, end = map(int, part.split('-'))
            ports.extend(range(start, end + 1))
        else:
            ports.append(int(part))
    return sorted(set(ports))


async def main():
    parser = argparse.ArgumentParser(
        description='局域网端口扫描器 - 隐蔽、快速、准确',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s -n 192.168.1 -r 1-100 --common          # 扫描常用端口
  %(prog)s -n 192.168.1 -r 1-254 --top100          # 扫描 Top 100 端口
  %(prog)s -n 192.168.1 -r 1-10 -p 80,443,8080     # 扫描自定义端口
  %(prog)s --auto --common -c 200                  # 自动检测网络并高速扫描
        """
    )

    # 网络配置
    parser.add_argument('-n', '--network', type=str,
                       help='网络前缀 (如: 192.168.1)')
    parser.add_argument('-r', '--range', type=str, default='1-254',
                       help='主机范围 (如: 1-254 或 10-20), 默认: 1-254')
    parser.add_argument('--auto', action='store_true',
                       help='自动检测本地网络')

    # 端口配置
    port_group = parser.add_mutually_exclusive_group()
    port_group.add_argument('-p', '--ports', type=str,
                           help='自定义端口 (如: 80,443,8080 或 1-1000)')
    port_group.add_argument('--common', action='store_true',
                           help='扫描常用端口')
    port_group.add_argument('--top100', action='store_true',
                           help='扫描 Top 100 端口')
    port_group.add_argument('--all', action='store_true',
                           help='扫描所有端口 (1-65535, 非常慢!)')

    # 扫描参数
    parser.add_argument('-c', '--concurrent', type=int, default=100,
                       help='最大并发连接数, 默认: 100')
    parser.add_argument('-t', '--timeout', type=float, default=1.0,
                       help='连接超时时间(秒), 默认: 1.0')
    parser.add_argument('--no-stealth', action='store_true',
                       help='禁用隐蔽模式（不推荐）')
    parser.add_argument('--delay', type=str, default='0.01-0.1',
                       help='随机延迟范围(秒), 默认: 0.01-0.1')

    # 输出选项
    parser.add_argument('-o', '--output', type=str,
                       help='输出文件 (JSON 格式)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='详细输出')
    parser.add_argument('--no-banner', action='store_true',
                       help='不显示 banner 信息')

    args = parser.parse_args()

    # 确定网络
    if args.auto:
        network = get_local_network()
        print(f"[*] 自动检测到网络: {network}.0/24")
    elif args.network:
        network = args.network
    else:
        print("错误: 请指定网络 (-n) 或使用 --auto 自动检测")
        sys.exit(1)

    # 确定端口
    if args.ports:
        ports = parse_ports(args.ports)
    elif args.common:
        ports = COMMON_PORTS
    elif args.top100:
        ports = TOP_100_PORTS
    elif args.all:
        ports = list(range(1, 65536))
        print("[!] 警告: 扫描所有 65535 个端口将花费很长时间!")
    else:
        print("错误: 请指定端口范围 (-p, --common, --top100, --all)")
        sys.exit(1)

    # 解析主机范围
    if '-' in args.range:
        start, end = map(int, args.range.split('-'))
    else:
        start = end = int(args.range)

    # 解析延迟范围
    delay_min, delay_max = map(float, args.delay.split('-'))

    # 显示扫描信息
    print("\n" + "="*60)
    print("局域网端口扫描器 v1.0")
    print("="*60)
    print(f"目标网络: {network}.{start}-{end}")
    print(f"端口数量: {len(ports)}")
    print(f"并发连接: {args.concurrent}")
    print(f"超时时间: {args.timeout}s")
    print(f"隐蔽模式: {'启用' if not args.no_stealth else '禁用'}")
    print("="*60 + "\n")

    # 创建扫描器
    scanner = StealthScanner(
        max_concurrent=args.concurrent,
        timeout=args.timeout,
        delay_range=(delay_min, delay_max) if not args.no_stealth else (0, 0),
        randomize=not args.no_stealth
    )

    # 开始扫描
    print("[*] 开始扫描...")
    import time
    start_time = time.time()

    results = await scanner.scan_network(
        network_prefix=network,
        ports=ports,
        host_range=(start, end)
    )

    elapsed = time.time() - start_time

    # 显示结果
    print(f"\n[+] 扫描完成! 耗时: {elapsed:.2f} 秒")
    print("="*60 + "\n")

    if not results:
        print("[-] 未发现开放端口")
        return

    # 统计信息
    total_hosts = len(results)
    total_ports = sum(len(ports) for ports in results.values())
    print(f"[+] 发现 {total_hosts} 个活跃主机，{total_ports} 个开放端口\n")

    # 格式化输出
    table_data = []
    for ip, port_results in sorted(results.items()):
        for result in port_results:
            row = [
                result.ip,
                result.port,
                result.state,
                result.service
            ]
            if not args.no_banner and result.banner:
                row.append(result.banner[:50])
            table_data.append(row)

    headers = ["IP地址", "端口", "状态", "服务"]
    if not args.no_banner:
        headers.append("Banner")

    print(tabulate(table_data, headers=headers, tablefmt="grid"))

    # 导出结果
    if args.output:
        import json
        export_data = []
        for ip, port_results in results.items():
            for result in port_results:
                export_data.append({
                    "ip": result.ip,
                    "port": result.port,
                    "state": result.state,
                    "service": result.service,
                    "banner": result.banner,
                    "timestamp": result.timestamp.isoformat()
                })

        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        print(f"\n[+] 结果已导出到: {args.output}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[!] 用户中断扫描")
        sys.exit(0)
