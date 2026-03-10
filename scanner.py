#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
局域网端口扫描器 - 主扫描模块
支持隐蔽扫描、服务识别和异步高性能扫描
"""

import asyncio
import socket
import random
import time
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ScanResult:
    """扫描结果数据类"""
    ip: str
    port: int
    state: str
    service: str
    banner: str = ""
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class ServiceDetector:
    """服务检测器 - 识别端口上运行的服务"""

    # 常见端口到服务的映射
    COMMON_PORTS = {
        20: "FTP-DATA", 21: "FTP", 22: "SSH", 23: "Telnet",
        25: "SMTP", 53: "DNS", 80: "HTTP", 110: "POP3",
        143: "IMAP", 443: "HTTPS", 445: "SMB", 3306: "MySQL",
        3389: "RDP", 5432: "PostgreSQL", 5900: "VNC", 6379: "Redis",
        8080: "HTTP-Proxy", 8443: "HTTPS-Alt", 27017: "MongoDB",
        9200: "Elasticsearch", 11211: "Memcached", 50000: "SAP"
    }

    # 服务特征指纹
    SERVICE_SIGNATURES = {
        b"SSH-": "SSH",
        b"220": "SMTP/FTP",
        b"HTTP/": "HTTP",
        b"+OK": "POP3",
        b"* OK": "IMAP",
        b"mysql": "MySQL",
        b"Redis": "Redis",
        b"MongoDB": "MongoDB",
        b"Elasticsearch": "Elasticsearch"
    }

    @classmethod
    def get_service_name(cls, port: int) -> str:
        """根据端口号获取服务名称"""
        return cls.COMMON_PORTS.get(port, f"Unknown-{port}")

    @classmethod
    async def detect_service(cls, ip: str, port: int, timeout: float = 2.0) -> Tuple[str, str]:
        """
        通过 banner 抓取检测服务
        返回: (服务名称, banner内容)
        """
        service = cls.get_service_name(port)
        banner = ""

        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=timeout
            )

            # 尝试读取 banner
            try:
                data = await asyncio.wait_for(reader.read(1024), timeout=1.0)
                banner = data.decode('utf-8', errors='ignore').strip()

                # 根据 banner 特征识别服务
                for signature, svc_name in cls.SERVICE_SIGNATURES.items():
                    if signature in data:
                        service = svc_name
                        break
            except asyncio.TimeoutError:
                pass

            writer.close()
            await writer.wait_closed()

        except Exception:
            pass

        return service, banner


class StealthScanner:
    """隐蔽扫描器 - 实现反检测扫描技术"""

    def __init__(self,
                 max_concurrent: int = 100,
                 timeout: float = 1.0,
                 delay_range: Tuple[float, float] = (0.01, 0.1),
                 randomize: bool = True):
        """
        初始化扫描器

        Args:
            max_concurrent: 最大并发连接数
            timeout: 连接超时时间（秒）
            delay_range: 随机延迟范围（秒）
            randomize: 是否随机化扫描顺序
        """
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.delay_range = delay_range
        self.randomize = randomize
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.results: List[ScanResult] = []

    async def _scan_port(self, ip: str, port: int) -> Optional[ScanResult]:
        """
        扫描单个端口
        使用异步 socket 连接测试端口状态
        """
        async with self.semaphore:
            # 添加随机延迟以避免检测
            if self.randomize:
                delay = random.uniform(*self.delay_range)
                await asyncio.sleep(delay)

            try:
                # 尝试建立 TCP 连接
                conn = asyncio.open_connection(ip, port)
                reader, writer = await asyncio.wait_for(conn, timeout=self.timeout)

                # 端口开放，进行服务检测
                service, banner = await ServiceDetector.detect_service(ip, port, self.timeout)

                writer.close()
                await writer.wait_closed()

                return ScanResult(
                    ip=ip,
                    port=port,
                    state="open",
                    service=service,
                    banner=banner[:100]  # 限制 banner 长度
                )

            except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
                # 端口关闭或被过滤
                return None

    async def scan_host(self, ip: str, ports: List[int]) -> List[ScanResult]:
        """
        扫描单个主机的多个端口

        Args:
            ip: 目标 IP 地址
            ports: 要扫描的端口列表

        Returns:
            开放端口的扫描结果列表
        """
        # 随机化端口扫描顺序
        if self.randomize:
            ports = ports.copy()
            random.shuffle(ports)

        # 并发扫描所有端口
        tasks = [self._scan_port(ip, port) for port in ports]
        results = await asyncio.gather(*tasks)

        # 过滤掉 None 结果（关闭的端口）
        open_ports = [r for r in results if r is not None]
        self.results.extend(open_ports)

        return open_ports

    async def scan_network(self, network_prefix: str, ports: List[int],
                          host_range: Tuple[int, int] = (1, 254)) -> Dict[str, List[ScanResult]]:
        """
        扫描整个网络段

        Args:
            network_prefix: 网络前缀，如 "192.168.1"
            ports: 要扫描的端口列表
            host_range: 主机范围，默认 1-254

        Returns:
            字典，键为 IP 地址，值为该主机的扫描结果列表
        """
        start_host, end_host = host_range
        hosts = [f"{network_prefix}.{i}" for i in range(start_host, end_host + 1)]

        # 随机化主机扫描顺序
        if self.randomize:
            random.shuffle(hosts)

        network_results = {}

        for host in hosts:
            results = await self.scan_host(host, ports)
            if results:
                network_results[host] = results

        return network_results

    def get_results(self) -> List[ScanResult]:
        """获取所有扫描结果"""
        return self.results

    def clear_results(self):
        """清空扫描结果"""
        self.results.clear()


def get_local_network() -> str:
    """
    自动获取本机所在的局域网网段

    Returns:
        网络前缀，如 "192.168.1"
    """
    try:
        # 创建一个 UDP socket 连接到外部地址（不实际发送数据）
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()

        # 提取网络前缀（前三段）
        network_prefix = '.'.join(local_ip.split('.')[:3])
        return network_prefix
    except Exception:
        # 默认返回常见的局域网段
        return "192.168.1"


# 常用端口列表
COMMON_PORTS = [
    21, 22, 23, 25, 53, 80, 110, 143, 443, 445,
    3306, 3389, 5432, 5900, 6379, 8080, 8443, 27017
]

TOP_100_PORTS = [
    7, 9, 13, 21, 22, 23, 25, 26, 37, 53, 79, 80, 81, 88, 106, 110, 111, 113,
    119, 135, 139, 143, 144, 179, 199, 389, 427, 443, 444, 445, 465, 513, 514,
    515, 543, 544, 548, 554, 587, 631, 646, 873, 990, 993, 995, 1025, 1026,
    1027, 1028, 1029, 1110, 1433, 1720, 1723, 1755, 1900, 2000, 2001, 2049,
    2121, 2717, 3000, 3128, 3306, 3389, 3986, 4899, 5000, 5009, 5051, 5060,
    5101, 5190, 5357, 5432, 5631, 5666, 5800, 5900, 6000, 6001, 6646, 7070,
    8000, 8008, 8009, 8080, 8081, 8443, 8888, 9100, 9999, 10000, 32768, 49152,
    49153, 49154, 49155, 49156, 49157
]


if __name__ == "__main__":
    # 示例用法
    async def main():
        print("局域网端口扫描器")
        print("=" * 50)

        # 获取本地网络
        network = get_local_network()
        print(f"检测到本地网络: {network}.0/24")

        # 创建扫描器
        scanner = StealthScanner(
            max_concurrent=50,
            timeout=1.0,
            delay_range=(0.01, 0.05),
            randomize=True
        )

        print(f"\n开始扫描常用端口...")
        start_time = time.time()

        # 扫描网络（示例：只扫描 .1 到 .10）
        results = await scanner.scan_network(
            network_prefix=network,
            ports=COMMON_PORTS,
            host_range=(1, 10)
        )

        elapsed = time.time() - start_time

        # 显示结果
        print(f"\n扫描完成！耗时: {elapsed:.2f} 秒")
        print("=" * 50)

        if results:
            for ip, ports in results.items():
                print(f"\n主机: {ip}")
                print(f"{'端口':<8} {'状态':<8} {'服务':<20} {'Banner'}")
                print("-" * 70)
                for result in ports:
                    banner_preview = result.banner[:40] if result.banner else ""
                    print(f"{result.port:<8} {result.state:<8} {result.service:<20} {banner_preview}")
        else:
            print("未发现开放端口")

    asyncio.run(main())
