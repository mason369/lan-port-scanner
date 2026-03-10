#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
局域网端口扫描器 - 图形界面
提供友好的 GUI 界面进行扫描操作
"""

import asyncio
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from threading import Thread
from datetime import datetime
import json

from scanner import StealthScanner, get_local_network, COMMON_PORTS, TOP_100_PORTS


class ScannerGUI:
    """扫描器图形界面"""

    def __init__(self, root):
        self.root = root
        self.root.title("局域网端口扫描器")
        self.root.geometry("900x700")

        self.scanner = None
        self.is_scanning = False

        self._setup_ui()

    def _setup_ui(self):
        """设置用户界面"""

        # 顶部配置区域
        config_frame = ttk.LabelFrame(self.root, text="扫描配置", padding=10)
        config_frame.pack(fill=tk.X, padx=10, pady=5)

        # 网络配置
        ttk.Label(config_frame, text="网络段:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.network_var = tk.StringVar(value=get_local_network())
        network_entry = ttk.Entry(config_frame, textvariable=self.network_var, width=20)
        network_entry.grid(row=0, column=1, sticky=tk.W, pady=5)
        ttk.Label(config_frame, text=".0/24").grid(row=0, column=2, sticky=tk.W, pady=5)

        # 主机范围
        ttk.Label(config_frame, text="主机范围:").grid(row=0, column=3, sticky=tk.W, padx=(20, 0), pady=5)
        self.host_start_var = tk.StringVar(value="1")
        ttk.Entry(config_frame, textvariable=self.host_start_var, width=5).grid(row=0, column=4, pady=5)
        ttk.Label(config_frame, text="-").grid(row=0, column=5, pady=5)
        self.host_end_var = tk.StringVar(value="254")
        ttk.Entry(config_frame, textvariable=self.host_end_var, width=5).grid(row=0, column=6, pady=5)

        # 端口选择
        ttk.Label(config_frame, text="端口范围:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.port_mode_var = tk.StringVar(value="common")
        ttk.Radiobutton(config_frame, text="常用端口", variable=self.port_mode_var,
                       value="common").grid(row=1, column=1, sticky=tk.W)
        ttk.Radiobutton(config_frame, text="Top 100", variable=self.port_mode_var,
                       value="top100").grid(row=1, column=2, sticky=tk.W)
        ttk.Radiobutton(config_frame, text="自定义", variable=self.port_mode_var,
                       value="custom").grid(row=1, column=3, sticky=tk.W)

        # 自定义端口
        ttk.Label(config_frame, text="自定义端口:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.custom_ports_var = tk.StringVar(value="80,443,8080")
        ttk.Entry(config_frame, textvariable=self.custom_ports_var, width=40).grid(
            row=2, column=1, columnspan=4, sticky=tk.W, pady=5)
        ttk.Label(config_frame, text="(用逗号分隔)").grid(row=2, column=5, columnspan=2, sticky=tk.W)

        # 扫描参数
        ttk.Label(config_frame, text="并发数:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.concurrent_var = tk.StringVar(value="100")
        ttk.Entry(config_frame, textvariable=self.concurrent_var, width=10).grid(
            row=3, column=1, sticky=tk.W, pady=5)

        ttk.Label(config_frame, text="超时(秒):").grid(row=3, column=3, sticky=tk.W, padx=(20, 0), pady=5)
        self.timeout_var = tk.StringVar(value="1.0")
        ttk.Entry(config_frame, textvariable=self.timeout_var, width=10).grid(
            row=3, column=4, sticky=tk.W, pady=5)

        # 隐蔽模式
        self.stealth_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(config_frame, text="启用隐蔽模式（随机化扫描）",
                       variable=self.stealth_var).grid(row=4, column=0, columnspan=3, sticky=tk.W, pady=5)

        # 控制按钮
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=10, pady=5)

        self.scan_button = ttk.Button(button_frame, text="开始扫描", command=self.start_scan)
        self.scan_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(button_frame, text="停止扫描", command=self.stop_scan, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        ttk.Button(button_frame, text="清空结果", command=self.clear_results).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="导出结果", command=self.export_results).pack(side=tk.LEFT, padx=5)

        # 进度条
        self.progress_var = tk.StringVar(value="就绪")
        ttk.Label(button_frame, textvariable=self.progress_var).pack(side=tk.LEFT, padx=20)

        # 结果显示区域
        result_frame = ttk.LabelFrame(self.root, text="扫描结果", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 创建 Treeview 表格
        columns = ("IP地址", "端口", "状态", "服务", "Banner")
        self.tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=15)

        # 设置列
        self.tree.heading("IP地址", text="IP地址")
        self.tree.heading("端口", text="端口")
        self.tree.heading("状态", text="状态")
        self.tree.heading("服务", text="服务")
        self.tree.heading("Banner", text="Banner")

        self.tree.column("IP地址", width=120)
        self.tree.column("端口", width=80)
        self.tree.column("状态", width=80)
        self.tree.column("服务", width=150)
        self.tree.column("Banner", width=400)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 状态栏
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, padx=10, pady=5)

        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(status_frame, textvariable=self.status_var, relief=tk.SUNKEN).pack(fill=tk.X)

    def _get_ports(self):
        """获取要扫描的端口列表"""
        mode = self.port_mode_var.get()

        if mode == "common":
            return COMMON_PORTS
        elif mode == "top100":
            return TOP_100_PORTS
        else:  # custom
            try:
                ports_str = self.custom_ports_var.get()
                ports = [int(p.strip()) for p in ports_str.split(",") if p.strip()]
                return ports
            except ValueError:
                messagebox.showerror("错误", "自定义端口格式错误！请使用逗号分隔的数字。")
                return []

    def start_scan(self):
        """开始扫描"""
        if self.is_scanning:
            return

        # 验证输入
        try:
            network = self.network_var.get()
            host_start = int(self.host_start_var.get())
            host_end = int(self.host_end_var.get())
            concurrent = int(self.concurrent_var.get())
            timeout = float(self.timeout_var.get())
        except ValueError:
            messagebox.showerror("错误", "请检查输入参数！")
            return

        ports = self._get_ports()
        if not ports:
            return

        # 更新 UI 状态
        self.is_scanning = True
        self.scan_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress_var.set("扫描中...")
        self.status_var.set(f"正在扫描 {network}.{host_start}-{host_end}，端口数: {len(ports)}")

        # 在新线程中运行扫描
        thread = Thread(target=self._run_scan, args=(network, host_start, host_end, ports, concurrent, timeout))
        thread.daemon = True
        thread.start()

    def _run_scan(self, network, host_start, host_end, ports, concurrent, timeout):
        """在后台线程中运行扫描"""
        try:
            # 创建扫描器
            self.scanner = StealthScanner(
                max_concurrent=concurrent,
                timeout=timeout,
                delay_range=(0.01, 0.1) if self.stealth_var.get() else (0, 0),
                randomize=self.stealth_var.get()
            )

            # 运行异步扫描
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            results = loop.run_until_complete(
                self.scanner.scan_network(
                    network_prefix=network,
                    ports=ports,
                    host_range=(host_start, host_end)
                )
            )

            loop.close()

            # 更新结果到 UI
            self.root.after(0, self._update_results, results)

        except Exception as e:
            self.root.after(0, messagebox.showerror, "扫描错误", str(e))
        finally:
            self.root.after(0, self._scan_finished)

    def _update_results(self, results):
        """更新扫描结果到表格"""
        total_hosts = len(results)
        total_ports = sum(len(ports) for ports in results.values())

        for ip, ports in results.items():
            for result in ports:
                self.tree.insert("", tk.END, values=(
                    result.ip,
                    result.port,
                    result.state,
                    result.service,
                    result.banner[:50] if result.banner else ""
                ))

        self.status_var.set(f"扫描完成！发现 {total_hosts} 个活跃主机，{total_ports} 个开放端口")

    def _scan_finished(self):
        """扫描完成后的清理工作"""
        self.is_scanning = False
        self.scan_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.progress_var.set("就绪")

    def stop_scan(self):
        """停止扫描"""
        self.is_scanning = False
        self.status_var.set("扫描已停止")
        self._scan_finished()

    def clear_results(self):
        """清空结果"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.status_var.set("结果已清空")

    def export_results(self):
        """导出结果到 JSON 文件"""
        items = self.tree.get_children()
        if not items:
            messagebox.showinfo("提示", "没有可导出的结果")
            return

        results = []
        for item in items:
            values = self.tree.item(item)["values"]
            results.append({
                "ip": values[0],
                "port": values[1],
                "state": values[2],
                "service": values[3],
                "banner": values[4]
            })

        filename = f"scan_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("成功", f"结果已导出到 {filename}")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败: {str(e)}")


def main():
    """主函数"""
    root = tk.Tk()
    app = ScannerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
