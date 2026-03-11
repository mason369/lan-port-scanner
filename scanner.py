#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
局域网端口扫描器 - 高性能扫描引擎
支持主机发现、并发扫描、服务识别
"""

import asyncio
import socket
import random
import struct
import time
from typing import List, Dict, Tuple, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ScanResult:
    """扫描结果"""
    ip: str
    port: int
    state: str
    service: str
    banner: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


class ServiceDetector:
    """服务检测器"""

    COMMON_PORTS = {
        20: "FTP-DATA", 21: "FTP", 22: "SSH", 23: "Telnet",
        25: "SMTP", 53: "DNS", 67: "DHCP", 68: "DHCP",
        69: "TFTP", 80: "HTTP", 110: "POP3", 111: "RPC",
        119: "NNTP", 123: "NTP", 135: "MSRPC", 137: "NetBIOS",
        138: "NetBIOS", 139: "NetBIOS", 143: "IMAP", 161: "SNMP",
        179: "BGP", 389: "LDAP", 443: "HTTPS", 445: "SMB",
        465: "SMTPS", 514: "Syslog", 515: "LPD", 587: "SMTP",
        631: "IPP", 636: "LDAPS", 993: "IMAPS", 995: "POP3S",
        1080: "SOCKS", 1433: "MSSQL", 1521: "Oracle",
        1723: "PPTP", 1883: "MQTT", 2049: "NFS",
        2181: "ZooKeeper", 3000: "Grafana", 3306: "MySQL",
        3389: "RDP", 4369: "EPMD", 5432: "PostgreSQL",
        5672: "AMQP", 5900: "VNC", 5984: "CouchDB",
        6379: "Redis", 6443: "K8s-API", 7001: "WebLogic",
        8000: "HTTP-Alt", 8008: "HTTP-Alt", 8080: "HTTP-Proxy",
        8443: "HTTPS-Alt", 8888: "HTTP-Alt", 9090: "Prometheus",
        9092: "Kafka", 9200: "Elasticsearch", 9300: "ES-Transport",
        11211: "Memcached", 15672: "RabbitMQ", 27017: "MongoDB",
        50000: "SAP", 50070: "HDFS",
    }

    SERVICE_PROBES = {
        b"SSH-": "SSH",
        b"220 ": "SMTP/FTP",
        b"220-": "FTP",
        b"HTTP/": "HTTP",
        b"+OK": "POP3",
        b"* OK": "IMAP",
        b"mysql": "MySQL",
        b"\x00\x00\x00": "MySQL",
        b"Redis": "Redis",
        b"-ERR": "Redis",
        b"MongoDB": "MongoDB",
        b"Elasticsearch": "Elasticsearch",
        b"RFB ": "VNC",
        b"\x03\x00": "RDP",
        b"AMQP": "AMQP",
    }

    @classmethod
    def get_service_name(cls, port: int) -> str:
        return cls.COMMON_PORTS.get(port, "Unknown")

    @classmethod
    async def grab_banner(cls, ip: str, port: int, timeout: float = 1.5) -> Tuple[str, str]:
        """单次连接完成端口探测 + banner 抓取 + 服务识别"""
        service = cls.get_service_name(port)
        banner = ""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port), timeout=timeout
            )
            try:
                data = await asyncio.wait_for(reader.read(1024), timeout=0.8)
                if data:
                    banner = data.decode('utf-8', errors='replace').strip()[:200]
                    for sig, svc in cls.SERVICE_PROBES.items():
                        if sig in data:
                            service = svc
                            break
            except asyncio.TimeoutError:
                pass
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass
        return service, banner


class StealthScanner:
    """高性能隐蔽扫描器"""

    def __init__(self,
                 max_concurrent: int = 500,
                 timeout: float = 0.6,
                 delay_range: Tuple[float, float] = (0.001, 0.01),
                 randomize: bool = True,
                 on_result: Optional[Callable] = None,
                 on_progress: Optional[Callable] = None):
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.delay_range = delay_range
        self.randomize = randomize
        self.on_result = on_result
        self.on_progress = on_progress
        self.results: List[ScanResult] = []
        self._stopped = False

    def stop(self):
        self._stopped = True

    async def _ping_host(self, ip: str, ports: List[int] = None) -> bool:
        """快速探测主机是否存活（并发 TCP ping 多个端口）"""
        if self._stopped:
            return False
        probe_ports = ports or [80, 443, 22, 445, 3389, 8080, 135, 139]

        async def try_port(port):
            try:
                conn = asyncio.open_connection(ip, port)
                reader, writer = await asyncio.wait_for(conn, timeout=0.25)
                writer.close()
                await writer.wait_closed()
                return True
            except (asyncio.TimeoutError, ConnectionRefusedError):
                return True
            except OSError:
                return False

        tasks = [try_port(p) for p in probe_ports[:6]]
        results = await asyncio.gather(*tasks)
        return any(results)

    async def discover_hosts(self, network_prefix: str,
                            host_range: Tuple[int, int] = (1, 254)) -> List[str]:
        """高并发发现活跃主机"""
        start, end = host_range
        all_ips = [f"{network_prefix}.{i}" for i in range(start, end + 1)]

        if self.randomize:
            random.shuffle(all_ips)

        sem = asyncio.Semaphore(100)
        alive = []

        async def check(ip):
            async with sem:
                if await self._ping_host(ip):
                    alive.append(ip)

        tasks = [check(ip) for ip in all_ips]
        total = len(tasks)

        # 一次性全部并发
        batch_size = 100
        for i in range(0, total, batch_size):
            if self._stopped:
                break
            batch = tasks[i:i + batch_size]
            await asyncio.gather(*batch)
            if self.on_progress:
                done = min(i + batch_size, total)
                self.on_progress(f"主机发现: {done}/{total}，已发现 {len(alive)} 个活跃主机")

        return alive

    async def _scan_port(self, ip: str, port: int, sem: asyncio.Semaphore) -> Optional[ScanResult]:
        """扫描单个端口 - 单次连接完成探测和识别"""
        if self._stopped:
            return None

        async with sem:
            if self.randomize and self.delay_range[1] > 0:
                await asyncio.sleep(random.uniform(*self.delay_range))

            try:
                conn = asyncio.open_connection(ip, port)
                reader, writer = await asyncio.wait_for(conn, timeout=self.timeout)

                service = ServiceDetector.get_service_name(port)
                banner = ""
                try:
                    data = await asyncio.wait_for(reader.read(1024), timeout=0.4)
                    if data:
                        banner = data.decode('utf-8', errors='replace').strip()[:200]
                        for sig, svc in ServiceDetector.SERVICE_PROBES.items():
                            if sig in data:
                                service = svc
                                break
                except asyncio.TimeoutError:
                    pass

                writer.close()
                try:
                    await asyncio.wait_for(writer.wait_closed(), timeout=0.2)
                except (asyncio.TimeoutError, OSError):
                    pass

                result = ScanResult(
                    ip=ip, port=port, state="open",
                    service=service, banner=banner
                )
                self.results.append(result)

                if self.on_result:
                    self.on_result(result)

                return result

            except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
                return None

    async def scan_host(self, ip: str, ports: List[int]) -> List[ScanResult]:
        """扫描单个主机"""
        if self.randomize:
            ports = ports.copy()
            random.shuffle(ports)

        sem = asyncio.Semaphore(self.max_concurrent)
        tasks = [self._scan_port(ip, port, sem) for port in ports]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None]

    async def scan_network(self, network_prefix: str, ports: List[int],
                          host_range: Tuple[int, int] = (1, 254)) -> Dict[str, List[ScanResult]]:
        """扫描整个网络 - 先发现主机再全并发扫描"""
        self._stopped = False
        self.results.clear()

        # 阶段 1: 主机发现
        if self.on_progress:
            self.on_progress("阶段 1/2: 正在发现活跃主机...")

        alive_hosts = await self.discover_hosts(network_prefix, host_range)

        if not alive_hosts:
            if self.on_progress:
                self.on_progress("未发现活跃主机，尝试直接扫描...")
            start, end = host_range
            alive_hosts = [f"{network_prefix}.{i}" for i in range(start, end + 1)]

        if self.on_progress:
            self.on_progress(f"阶段 2/2: 扫描 {len(alive_hosts)} 个主机的 {len(ports)} 个端口...")

        # 阶段 2: 全并发扫描
        sem = asyncio.Semaphore(self.max_concurrent)

        all_tasks = []
        for host in alive_hosts:
            scan_ports = ports.copy()
            if self.randomize:
                random.shuffle(scan_ports)
            for port in scan_ports:
                all_tasks.append(self._scan_port(host, port, sem))

        if self.randomize:
            random.shuffle(all_tasks)

        total = len(all_tasks)
        batch_size = self.max_concurrent * 3
        completed = 0

        for i in range(0, total, batch_size):
            if self._stopped:
                break
            batch = all_tasks[i:i + batch_size]
            await asyncio.gather(*batch)
            completed = min(i + batch_size, total)
            if self.on_progress:
                pct = int(completed / total * 100)
                found = len(self.results)
                self.on_progress(f"扫描进度: {pct}% ({completed}/{total})，已发现 {found} 个开放端口")

        # 整理结果
        network_results = {}
        for result in self.results:
            if result.ip not in network_results:
                network_results[result.ip] = []
            network_results[result.ip].append(result)

        for ip in network_results:
            network_results[ip].sort(key=lambda r: r.port)

        return network_results

    def get_results(self) -> List[ScanResult]:
        return self.results

    def clear_results(self):
        self.results.clear()


def get_local_network() -> str:
    """自动获取本机所在的局域网网段"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return '.'.join(local_ip.split('.')[:3])
    except Exception:
        return "192.168.1"


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
