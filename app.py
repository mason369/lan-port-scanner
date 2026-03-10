#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
局域网端口扫描器 - 现代化图形界面
提供专业的桌面应用体验
"""

import asyncio
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from threading import Thread
from datetime import datetime
import json
import sys

from scanner import StealthScanner, get_local_network, COMMON_PORTS, TOP_100_PORTS


class ModernScannerGUI:
    """现代化扫描器图形界面"""

    def __init__(self, root):
        self.root = root
        self.root.title("局域网端口扫描器 v1.0")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)

        # 设置主题颜色
        self.colors = {
            'primary': '#2196F3',
            'success': '#4CAF50',
            'warning': '#FF9800',
            'danger': '#F44336',
            'bg': '#F5F5F5',
            'card': '#FFFFFF'
        }

        self.scanner = None
        self.is_scanning = False
        self.scan_results = {}

        self._setup_styles()
        self._setup_ui()
        self._center_window()

    def _setup_styles(self):
        """设置样式"""
        style = ttk.Style()
        style.theme_use('clam')

        # 配置按钮样式
        style.configure('Primary.TButton',
                       background=self.colors['primary'],
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       padding=10)

        style.configure('Success.TButton',
                       background=self.colors['success'],
                       foreground='white',
                       borderwidth=0,
                       padding=10)

        style.configure('Danger.TButton',
                       background=self.colors['danger'],
                       foreground='white',
                       borderwidth=0,
                       padding=10)

        # 配置标签框样式
        style.configure('Card.TLabelframe',
                       background=self.colors['card'],
                       borderwidth=1,
                       relief='solid')

        style.configure('Card.TLabelframe.Label',
                       background=self.colors['card'],
                       font=('Arial', 10, 'bold'))

    def _center_window(self):
        """窗口居中显示"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def _setup_ui(self):
        """设置用户界面"""
        # 主容器
        main_container = ttk.Frame(self.root, padding=10)
        main_container.pack(fill=tk.BOTH, expand=True)

        # 左侧面板（配置区）
        left_panel = ttk.Frame(main_container, width=350)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)

        # 右侧面板（结果区）
        right_panel = ttk.Frame(main_container)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._setup_left_panel(left_panel)
        self._setup_right_panel(right_panel)

    def _setup_left_panel(self, parent):
        """设置左侧配置面板"""

        # 标题
        title_frame = ttk.Frame(parent)
        title_frame.pack(fill=tk.X, pady=(0, 20))

        title_label = tk.Label(title_frame,
                              text="🔍 端口扫描器",
                              font=('Arial', 18, 'bold'),
                              fg=self.colors['primary'])
        title_label.pack()

        subtitle_label = tk.Label(title_frame,
                                 text="快速、隐蔽、准确",
                                 font=('Arial', 10),
                                 fg='gray')
        subtitle_label.pack()

        # 网络配置卡片
        network_card = ttk.LabelFrame(parent, text="📡 网络配置", style='Card.TLabelframe', padding=15)
        network_card.pack(fill=tk.X, pady=(0, 10))

        # 自动检测按钮
        detect_frame = ttk.Frame(network_card)
        detect_frame.pack(fill=tk.X, pady=(0, 10))

        self.network_var = tk.StringVar(value=get_local_network())
        network_label = ttk.Label(detect_frame, text="网络段:")
        network_label.pack(side=tk.LEFT)

        network_entry = ttk.Entry(detect_frame, textvariable=self.network_var, width=15)
        network_entry.pack(side=tk.LEFT, padx=5)

        ttk.Label(detect_frame, text=".0/24").pack(side=tk.LEFT)

        ttk.Button(detect_frame, text="🔄", width=3,
                  command=self._auto_detect_network).pack(side=tk.RIGHT)

        # 主机范围
        host_frame = ttk.Frame(network_card)
        host_frame.pack(fill=tk.X, pady=5)

        ttk.Label(host_frame, text="主机范围:").pack(side=tk.LEFT)
        self.host_start_var = tk.StringVar(value="1")
        ttk.Entry(host_frame, textvariable=self.host_start_var, width=5).pack(side=tk.LEFT, padx=5)
        ttk.Label(host_frame, text="-").pack(side=tk.LEFT)
        self.host_end_var = tk.StringVar(value="254")
        ttk.Entry(host_frame, textvariable=self.host_end_var, width=5).pack(side=tk.LEFT, padx=5)

        # 端口配置卡片
        port_card = ttk.LabelFrame(parent, text="🔌 端口配置", style='Card.TLabelframe', padding=15)
        port_card.pack(fill=tk.X, pady=(0, 10))

        self.port_mode_var = tk.StringVar(value="common")

        modes = [
            ("常用端口 (18个)", "common"),
            ("Top 100 端口", "top100"),
            ("自定义端口", "custom")
        ]

        for text, value in modes:
            ttk.Radiobutton(port_card, text=text,
                          variable=self.port_mode_var,
                          value=value,
                          command=self._on_port_mode_change).pack(anchor=tk.W, pady=2)

        # 自定义端口输入
        self.custom_port_frame = ttk.Frame(port_card)
        self.custom_port_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Label(self.custom_port_frame, text="端口列表:").pack(anchor=tk.W)
        self.custom_ports_var = tk.StringVar(value="80,443,8080,3306,3389")
        self.custom_ports_entry = ttk.Entry(self.custom_port_frame,
                                           textvariable=self.custom_ports_var)
        self.custom_ports_entry.pack(fill=tk.X, pady=2)
        ttk.Label(self.custom_port_frame,
                 text="提示: 用逗号分隔，如 80,443,8080",
                 font=('Arial', 8),
                 foreground='gray').pack(anchor=tk.W)

        self.custom_port_frame.pack_forget()  # 初始隐藏

        # 扫描参数卡片
        param_card = ttk.LabelFrame(parent, text="⚙️ 扫描参数", style='Card.TLabelframe', padding=15)
        param_card.pack(fill=tk.X, pady=(0, 10))

        # 并发数
        concurrent_frame = ttk.Frame(param_card)
        concurrent_frame.pack(fill=tk.X, pady=5)
        ttk.Label(concurrent_frame, text="并发连接数:").pack(side=tk.LEFT)
        self.concurrent_var = tk.StringVar(value="100")
        concurrent_spinbox = ttk.Spinbox(concurrent_frame,
                                        from_=10, to=500, increment=10,
                                        textvariable=self.concurrent_var,
                                        width=10)
        concurrent_spinbox.pack(side=tk.RIGHT)

        # 超时时间
        timeout_frame = ttk.Frame(param_card)
        timeout_frame.pack(fill=tk.X, pady=5)
        ttk.Label(timeout_frame, text="超时时间(秒):").pack(side=tk.LEFT)
        self.timeout_var = tk.StringVar(value="1.0")
        timeout_spinbox = ttk.Spinbox(timeout_frame,
                                     from_=0.5, to=10.0, increment=0.5,
                                     textvariable=self.timeout_var,
                                     width=10)
        timeout_spinbox.pack(side=tk.RIGHT)

        # 隐蔽模式
        self.stealth_var = tk.BooleanVar(value=True)
        stealth_check = ttk.Checkbutton(param_card,
                                       text="🕵️ 启用隐蔽模式（推荐）",
                                       variable=self.stealth_var)
        stealth_check.pack(anchor=tk.W, pady=(10, 0))

        # 控制按钮
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(20, 0))

        self.scan_button = tk.Button(button_frame,
                                     text="🚀 开始扫描",
                                     command=self.start_scan,
                                     bg=self.colors['success'],
                                     fg='white',
                                     font=('Arial', 12, 'bold'),
                                     relief=tk.FLAT,
                                     cursor='hand2',
                                     height=2)
        self.scan_button.pack(fill=tk.X, pady=(0, 5))

        self.stop_button = tk.Button(button_frame,
                                     text="⏹️ 停止扫描",
                                     command=self.stop_scan,
                                     bg=self.colors['danger'],
                                     fg='white',
                                     font=('Arial', 12, 'bold'),
                                     relief=tk.FLAT,
                                     cursor='hand2',
                                     state=tk.DISABLED,
                                     height=2)
        self.stop_button.pack(fill=tk.X)

        # 进度信息
        self.progress_var = tk.StringVar(value="就绪")
        progress_label = ttk.Label(parent,
                                  textvariable=self.progress_var,
                                  font=('Arial', 10),
                                  foreground=self.colors['primary'])
        progress_label.pack(pady=(10, 0))

        # 统计信息
        stats_frame = ttk.LabelFrame(parent, text="📊 统计信息", style='Card.TLabelframe', padding=10)
        stats_frame.pack(fill=tk.X, pady=(10, 0))

        self.stats_text = tk.Text(stats_frame, height=4, font=('Consolas', 9), relief=tk.FLAT)
        self.stats_text.pack(fill=tk.X)
        self.stats_text.insert('1.0', "活跃主机: 0\n开放端口: 0\n扫描耗时: 0.00 秒\n扫描状态: 就绪")
        self.stats_text.config(state=tk.DISABLED)

    def _setup_right_panel(self, parent):
        """设置右侧结果面板"""

        # 工具栏
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(toolbar, text="扫描结果", font=('Arial', 14, 'bold')).pack(side=tk.LEFT)

        # 右侧工具按钮
        tool_buttons = ttk.Frame(toolbar)
        tool_buttons.pack(side=tk.RIGHT)

        ttk.Button(tool_buttons, text="📋 复制", command=self._copy_results).pack(side=tk.LEFT, padx=2)
        ttk.Button(tool_buttons, text="💾 导出", command=self.export_results).pack(side=tk.LEFT, padx=2)
        ttk.Button(tool_buttons, text="🗑️ 清空", command=self.clear_results).pack(side=tk.LEFT, padx=2)

        # 结果表格
        result_frame = ttk.Frame(parent)
        result_frame.pack(fill=tk.BOTH, expand=True)

        # 创建 Treeview
        columns = ("IP地址", "端口", "状态", "服务", "Banner", "时间")
        self.tree = ttk.Treeview(result_frame, columns=columns, show="headings", height=20)

        # 设置列
        self.tree.heading("IP地址", text="IP地址", command=lambda: self._sort_column("IP地址"))
        self.tree.heading("端口", text="端口", command=lambda: self._sort_column("端口"))
        self.tree.heading("状态", text="状态")
        self.tree.heading("服务", text="服务")
        self.tree.heading("Banner", text="Banner信息")
        self.tree.heading("时间", text="扫描时间")

        self.tree.column("IP地址", width=120, anchor=tk.CENTER)
        self.tree.column("端口", width=80, anchor=tk.CENTER)
        self.tree.column("状态", width=80, anchor=tk.CENTER)
        self.tree.column("服务", width=120, anchor=tk.CENTER)
        self.tree.column("Banner", width=350)
        self.tree.column("时间", width=150, anchor=tk.CENTER)

        # 添加滚动条
        vsb = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(result_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # 布局
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')

        result_frame.grid_rowconfigure(0, weight=1)
        result_frame.grid_columnconfigure(0, weight=1)

        # 添加标签样式
        self.tree.tag_configure('open', background='#E8F5E9')
        self.tree.tag_configure('closed', background='#FFEBEE')

        # 双击查看详情
        self.tree.bind('<Double-1>', self._show_detail)

        # 状态栏
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(10, 0))

        self.status_var = tk.StringVar(value="就绪 - 等待开始扫描")
        status_label = ttk.Label(status_frame,
                                textvariable=self.status_var,
                                relief=tk.SUNKEN,
                                padding=5)
        status_label.pack(fill=tk.X)

    def _auto_detect_network(self):
        """自动检测网络"""
        network = get_local_network()
        self.network_var.set(network)
        messagebox.showinfo("检测成功", f"检测到网络段: {network}.0/24")

    def _on_port_mode_change(self):
        """端口模式改变时的处理"""
        if self.port_mode_var.get() == "custom":
            self.custom_port_frame.pack(fill=tk.X, pady=(5, 0))
        else:
            self.custom_port_frame.pack_forget()

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
                ports = []
                for part in ports_str.split(','):
                    part = part.strip()
                    if '-' in part:
                        start, end = map(int, part.split('-'))
                        ports.extend(range(start, end + 1))
                    else:
                        ports.append(int(part))
                return sorted(set(ports))
            except ValueError:
                messagebox.showerror("错误", "端口格式错误！\n支持格式: 80,443,8080 或 1-1000")
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

            if not (1 <= host_start <= 254 and 1 <= host_end <= 254):
                raise ValueError("主机范围必须在 1-254 之间")
            if host_start > host_end:
                raise ValueError("起始主机不能大于结束主机")

        except ValueError as e:
            messagebox.showerror("参数错误", f"请检查输入参数！\n{str(e)}")
            return

        ports = self._get_ports()
        if not ports:
            return

        # 确认扫描
        host_count = host_end - host_start + 1
        total_scans = host_count * len(ports)

        if total_scans > 10000:
            if not messagebox.askyesno("确认扫描",
                                      f"将扫描 {host_count} 个主机的 {len(ports)} 个端口\n"
                                      f"总计 {total_scans} 次连接尝试\n\n是否继续？"):
                return

        # 更新 UI 状态
        self.is_scanning = True
        self.scan_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress_var.set("🔄 扫描中...")
        self.status_var.set(f"正在扫描 {network}.{host_start}-{host_end}，端口数: {len(ports)}")

        # 清空之前的结果
        self.scan_results = {}
        self.scan_start_time = datetime.now()

        # 在新线程中运行扫描
        thread = Thread(target=self._run_scan,
                       args=(network, host_start, host_end, ports, concurrent, timeout))
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
            self.root.after(0, messagebox.showerror, "扫描错误", f"扫描过程中发生错误:\n{str(e)}")
        finally:
            self.root.after(0, self._scan_finished)

    def _update_results(self, results):
        """更新扫描结果到表格"""
        self.scan_results = results
        total_hosts = len(results)
        total_ports = sum(len(ports) for ports in results.values())

        for ip, ports in sorted(results.items()):
            for result in ports:
                time_str = result.timestamp.strftime('%H:%M:%S')
                self.tree.insert("", tk.END,
                               values=(
                                   result.ip,
                                   result.port,
                                   result.state,
                                   result.service,
                                   result.banner[:60] if result.banner else "",
                                   time_str
                               ),
                               tags=('open',))

        # 更新统计信息
        elapsed = (datetime.now() - self.scan_start_time).total_seconds()
        self._update_stats(total_hosts, total_ports, elapsed)

        self.status_var.set(f"✅ 扫描完成！发现 {total_hosts} 个活跃主机，{total_ports} 个开放端口")

    def _update_stats(self, hosts, ports, elapsed):
        """更新统计信息"""
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete('1.0', tk.END)
        self.stats_text.insert('1.0',
                              f"活跃主机: {hosts}\n"
                              f"开放端口: {ports}\n"
                              f"扫描耗时: {elapsed:.2f} 秒\n"
                              f"扫描状态: 完成")
        self.stats_text.config(state=tk.DISABLED)

    def _scan_finished(self):
        """扫描完成后的清理工作"""
        self.is_scanning = False
        self.scan_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.progress_var.set("✅ 就绪")

    def stop_scan(self):
        """停止扫描"""
        if messagebox.askyesno("确认停止", "确定要停止当前扫描吗？"):
            self.is_scanning = False
            self.status_var.set("⏹️ 扫描已停止")
            self._scan_finished()

    def clear_results(self):
        """清空结果"""
        if self.tree.get_children():
            if messagebox.askyesno("确认清空", "确定要清空所有扫描结果吗？"):
                for item in self.tree.get_children():
                    self.tree.delete(item)
                self.scan_results = {}
                self.status_var.set("🗑️ 结果已清空")
                self._update_stats(0, 0, 0)

    def export_results(self):
        """导出结果"""
        items = self.tree.get_children()
        if not items:
            messagebox.showinfo("提示", "没有可导出的结果")
            return

        # 选择保存位置
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("CSV文件", "*.csv"), ("所有文件", "*.*")],
            initialfile=f"scan_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

        if not filename:
            return

        try:
            results = []
            for item in items:
                values = self.tree.item(item)["values"]
                results.append({
                    "ip": values[0],
                    "port": values[1],
                    "state": values[2],
                    "service": values[3],
                    "banner": values[4],
                    "time": values[5]
                })

            if filename.endswith('.json'):
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
            elif filename.endswith('.csv'):
                import csv
                with open(filename, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=results[0].keys())
                    writer.writeheader()
                    writer.writerows(results)

            messagebox.showinfo("导出成功", f"结果已导出到:\n{filename}")
        except Exception as e:
            messagebox.showerror("导出失败", f"导出过程中发生错误:\n{str(e)}")

    def _copy_results(self):
        """复制结果到剪贴板"""
        items = self.tree.get_children()
        if not items:
            messagebox.showinfo("提示", "没有可复制的结果")
            return

        text = "IP地址\t端口\t状态\t服务\tBanner\t时间\n"
        for item in items:
            values = self.tree.item(item)["values"]
            text += "\t".join(str(v) for v in values) + "\n"

        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("复制成功", "结果已复制到剪贴板")

    def _sort_column(self, col):
        """排序列"""
        items = [(self.tree.set(item, col), item) for item in self.tree.get_children('')]
        items.sort()

        for index, (val, item) in enumerate(items):
            self.tree.move(item, '', index)

    def _show_detail(self, event):
        """显示详细信息"""
        selection = self.tree.selection()
        if not selection:
            return

        item = selection[0]
        values = self.tree.item(item)["values"]

        detail_text = f"""
扫描详情
{'='*50}

IP 地址:    {values[0]}
端口:       {values[1]}
状态:       {values[2]}
服务:       {values[3]}
扫描时间:   {values[5]}

Banner 信息:
{values[4] if values[4] else '(无)'}
        """

        detail_window = tk.Toplevel(self.root)
        detail_window.title("端口详情")
        detail_window.geometry("500x400")

        text_widget = tk.Text(detail_window, wrap=tk.WORD, font=('Consolas', 10))
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_widget.insert('1.0', detail_text)
        text_widget.config(state=tk.DISABLED)

        ttk.Button(detail_window, text="关闭", command=detail_window.destroy).pack(pady=10)


def main():
    """主函数"""
    root = tk.Tk()
    app = ModernScannerGUI(root)

    # 设置窗口图标（如果有的话）
    try:
        root.iconbitmap('icon.ico')
    except:
        pass

    root.mainloop()


if __name__ == "__main__":
    main()
