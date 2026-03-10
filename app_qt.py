#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
局域网端口扫描器 - PyQt6 现代化图形界面
提供专业的桌面应用体验
"""

import asyncio
import sys
from datetime import datetime
from threading import Thread
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QSpinBox, QDoubleSpinBox,
    QRadioButton, QCheckBox, QTableWidget, QTableWidgetItem,
    QGroupBox, QMessageBox, QFileDialog, QHeaderView, QProgressBar,
    QTextEdit, QButtonGroup, QSplitter
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QIcon

from scanner import StealthScanner, get_local_network, COMMON_PORTS, TOP_100_PORTS


class ScanThread(QThread):
    """扫描线程"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, network, host_start, host_end, ports, concurrent, timeout, stealth):
        super().__init__()
        self.network = network
        self.host_start = host_start
        self.host_end = host_end
        self.ports = ports
        self.concurrent = concurrent
        self.timeout = timeout
        self.stealth = stealth

    def run(self):
        """运行扫描"""
        try:
            self.progress.emit("正在初始化扫描器...")

            scanner = StealthScanner(
                max_concurrent=self.concurrent,
                timeout=self.timeout,
                delay_range=(0.01, 0.1) if self.stealth else (0, 0),
                randomize=self.stealth
            )

            self.progress.emit("开始扫描...")

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            results = loop.run_until_complete(
                scanner.scan_network(
                    network_prefix=self.network,
                    ports=self.ports,
                    host_range=(self.host_start, self.host_end)
                )
            )

            loop.close()

            self.finished.emit(results)

        except Exception as e:
            self.error.emit(str(e))


class ModernScannerGUI(QMainWindow):
    """现代化扫描器 PyQt6 界面"""

    def __init__(self):
        super().__init__()
        self.scan_thread: Optional[ScanThread] = None
        self.scan_results = {}
        self.scan_start_time = None

        self.init_ui()
        self.setWindowTitle("局域网端口扫描器 v1.0")
        self.setGeometry(100, 100, 1400, 900)
        self.center_window()

    def center_window(self):
        """窗口居中"""
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )

    def init_ui(self):
        """初始化界面"""
        # 主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # 主布局
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)

        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # 左侧配置面板
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)

        # 右侧结果面板
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)

        # 设置分割比例
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        # 设置样式
        self.set_styles()

    def create_left_panel(self):
        """创建左侧配置面板"""
        panel = QWidget()
        layout = QVBoxLayout()
        panel.setLayout(layout)

        # 标题
        title = QLabel("🔍 端口扫描器")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("快速 · 隐蔽 · 准确")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: gray;")
        layout.addWidget(subtitle)

        layout.addSpacing(20)

        # 网络配置组
        network_group = QGroupBox("📡 网络配置")
        network_layout = QVBoxLayout()
        network_group.setLayout(network_layout)

        # 网络段
        net_layout = QHBoxLayout()
        net_layout.addWidget(QLabel("网络段:"))
        self.network_input = QLineEdit(get_local_network())
        self.network_input.setPlaceholderText("192.168.1")
        net_layout.addWidget(self.network_input)
        net_layout.addWidget(QLabel(".0/24"))

        detect_btn = QPushButton("🔄")
        detect_btn.setMaximumWidth(40)
        detect_btn.clicked.connect(self.auto_detect_network)
        detect_btn.setToolTip("自动检测网络")
        net_layout.addWidget(detect_btn)
        network_layout.addLayout(net_layout)

        # 主机范围
        host_layout = QHBoxLayout()
        host_layout.addWidget(QLabel("主机范围:"))
        self.host_start_spin = QSpinBox()
        self.host_start_spin.setRange(1, 254)
        self.host_start_spin.setValue(1)
        host_layout.addWidget(self.host_start_spin)
        host_layout.addWidget(QLabel("-"))
        self.host_end_spin = QSpinBox()
        self.host_end_spin.setRange(1, 254)
        self.host_end_spin.setValue(254)
        host_layout.addWidget(self.host_end_spin)
        network_layout.addLayout(host_layout)

        layout.addWidget(network_group)

        # 端口配置组
        port_group = QGroupBox("🔌 端口配置")
        port_layout = QVBoxLayout()
        port_group.setLayout(port_layout)

        self.port_button_group = QButtonGroup()

        self.common_radio = QRadioButton("常用端口 (18个)")
        self.common_radio.setChecked(True)
        self.port_button_group.addButton(self.common_radio, 1)
        port_layout.addWidget(self.common_radio)

        self.top100_radio = QRadioButton("Top 100 端口")
        self.port_button_group.addButton(self.top100_radio, 2)
        port_layout.addWidget(self.top100_radio)

        self.custom_radio = QRadioButton("自定义端口")
        self.port_button_group.addButton(self.custom_radio, 3)
        port_layout.addWidget(self.custom_radio)

        self.custom_ports_input = QLineEdit("80,443,8080,3306,3389")
        self.custom_ports_input.setPlaceholderText("如: 80,443,8080 或 1-1000")
        self.custom_ports_input.setEnabled(False)
        port_layout.addWidget(self.custom_ports_input)

        hint = QLabel("提示: 用逗号分隔，支持范围")
        hint.setStyleSheet("color: gray; font-size: 9px;")
        port_layout.addWidget(hint)

        self.custom_radio.toggled.connect(
            lambda checked: self.custom_ports_input.setEnabled(checked)
        )

        layout.addWidget(port_group)

        # 扫描参数组
        param_group = QGroupBox("⚙️ 扫描参数")
        param_layout = QVBoxLayout()
        param_group.setLayout(param_layout)

        # 并发数
        concurrent_layout = QHBoxLayout()
        concurrent_layout.addWidget(QLabel("并发连接数:"))
        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setRange(10, 500)
        self.concurrent_spin.setValue(100)
        self.concurrent_spin.setSingleStep(10)
        concurrent_layout.addWidget(self.concurrent_spin)
        param_layout.addLayout(concurrent_layout)

        # 超时时间
        timeout_layout = QHBoxLayout()
        timeout_layout.addWidget(QLabel("超时时间(秒):"))
        self.timeout_spin = QDoubleSpinBox()
        self.timeout_spin.setRange(0.5, 10.0)
        self.timeout_spin.setValue(1.0)
        self.timeout_spin.setSingleStep(0.5)
        timeout_layout.addWidget(self.timeout_spin)
        param_layout.addLayout(timeout_layout)

        # 隐蔽模式
        self.stealth_check = QCheckBox("🕵️ 启用隐蔽模式（推荐）")
        self.stealth_check.setChecked(True)
        param_layout.addWidget(self.stealth_check)

        layout.addWidget(param_group)

        # 控制按钮
        self.scan_btn = QPushButton("🚀 开始扫描")
        self.scan_btn.setMinimumHeight(50)
        self.scan_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.scan_btn.clicked.connect(self.start_scan)
        layout.addWidget(self.scan_btn)

        self.stop_btn = QPushButton("⏹️ 停止扫描")
        self.stop_btn.setMinimumHeight(50)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_scan)
        layout.addWidget(self.stop_btn)

        # 进度信息
        self.progress_label = QLabel("就绪")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setStyleSheet("color: #2196F3; font-weight: bold;")
        layout.addWidget(self.progress_label)

        # 统计信息
        stats_group = QGroupBox("📊 统计信息")
        stats_layout = QVBoxLayout()
        stats_group.setLayout(stats_layout)

        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(100)
        self.stats_text.setPlainText("活跃主机: 0\n开放端口: 0\n扫描耗时: 0.00 秒\n扫描状态: 就绪")
        stats_layout.addWidget(self.stats_text)

        layout.addWidget(stats_group)

        layout.addStretch()

        return panel

    def create_right_panel(self):
        """创建右侧结果面板"""
        panel = QWidget()
        layout = QVBoxLayout()
        panel.setLayout(layout)

        # 工具栏
        toolbar = QHBoxLayout()

        title = QLabel("扫描结果")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        toolbar.addWidget(title)

        toolbar.addStretch()

        copy_btn = QPushButton("📋 复制")
        copy_btn.clicked.connect(self.copy_results)
        toolbar.addWidget(copy_btn)

        export_btn = QPushButton("💾 导出")
        export_btn.clicked.connect(self.export_results)
        toolbar.addWidget(export_btn)

        clear_btn = QPushButton("🗑️ 清空")
        clear_btn.clicked.connect(self.clear_results)
        toolbar.addWidget(clear_btn)

        layout.addLayout(toolbar)

        # 结果表格
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(6)
        self.result_table.setHorizontalHeaderLabels([
            "IP地址", "端口", "状态", "服务", "Banner", "时间"
        ])

        # 设置表格属性
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.result_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # 设置列宽
        header = self.result_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

        # 双击查看详情
        self.result_table.doubleClicked.connect(self.show_detail)

        layout.addWidget(self.result_table)

        # 状态栏
        self.status_label = QLabel("就绪 - 等待开始扫描")
        self.status_label.setStyleSheet("padding: 5px; background-color: #f0f0f0;")
        layout.addWidget(self.status_label)

        return panel

    def set_styles(self):
        """设置全局样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                padding: 5px 15px;
                border-radius: 3px;
                border: 1px solid #ddd;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox {
                padding: 5px;
                border: 1px solid #ddd;
                border-radius: 3px;
            }
            QTableWidget {
                border: 1px solid #ddd;
                gridline-color: #e0e0e0;
            }
            QHeaderView::section {
                background-color: #2196F3;
                color: white;
                padding: 5px;
                border: none;
                font-weight: bold;
            }
        """)

    def auto_detect_network(self):
        """自动检测网络"""
        network = get_local_network()
        self.network_input.setText(network)
        QMessageBox.information(self, "检测成功", f"检测到网络段: {network}.0/24")

    def get_ports(self):
        """获取要扫描的端口列表"""
        if self.common_radio.isChecked():
            return COMMON_PORTS
        elif self.top100_radio.isChecked():
            return TOP_100_PORTS
        else:
            try:
                ports_str = self.custom_ports_input.text()
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
                QMessageBox.critical(self, "错误", "端口格式错误！\n支持格式: 80,443,8080 或 1-1000")
                return []

    def start_scan(self):
        """开始扫描"""
        # 获取参数
        network = self.network_input.text().strip()
        host_start = self.host_start_spin.value()
        host_end = self.host_end_spin.value()
        concurrent = self.concurrent_spin.value()
        timeout = self.timeout_spin.value()
        stealth = self.stealth_check.isChecked()

        if not network:
            QMessageBox.warning(self, "警告", "请输入网络段！")
            return

        if host_start > host_end:
            QMessageBox.warning(self, "警告", "起始主机不能大于结束主机！")
            return

        ports = self.get_ports()
        if not ports:
            return

        # 确认大规模扫描
        host_count = host_end - host_start + 1
        total_scans = host_count * len(ports)

        if total_scans > 10000:
            reply = QMessageBox.question(
                self, "确认扫描",
                f"将扫描 {host_count} 个主机的 {len(ports)} 个端口\n"
                f"总计 {total_scans} 次连接尝试\n\n是否继续？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return

        # 更新 UI
        self.scan_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_label.setText("🔄 扫描中...")
        self.status_label.setText(f"正在扫描 {network}.{host_start}-{host_end}，端口数: {len(ports)}")
        self.result_table.setRowCount(0)
        self.scan_start_time = datetime.now()

        # 创建并启动扫描线程
        self.scan_thread = ScanThread(
            network, host_start, host_end, ports, concurrent, timeout, stealth
        )
        self.scan_thread.finished.connect(self.on_scan_finished)
        self.scan_thread.error.connect(self.on_scan_error)
        self.scan_thread.progress.connect(self.on_scan_progress)
        self.scan_thread.start()

    def stop_scan(self):
        """停止扫描"""
        if self.scan_thread and self.scan_thread.isRunning():
            reply = QMessageBox.question(
                self, "确认停止",
                "确定要停止当前扫描吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.scan_thread.terminate()
                self.scan_thread.wait()
                self.scan_finished()
                self.status_label.setText("⏹️ 扫描已停止")

    def on_scan_progress(self, message):
        """扫描进度更新"""
        self.progress_label.setText(message)

    def on_scan_finished(self, results):
        """扫描完成"""
        self.scan_results = results
        total_hosts = len(results)
        total_ports = sum(len(ports) for ports in results.values())

        # 更新表格
        for ip, ports in sorted(results.items()):
            for result in ports:
                row = self.result_table.rowCount()
                self.result_table.insertRow(row)

                self.result_table.setItem(row, 0, QTableWidgetItem(result.ip))
                self.result_table.setItem(row, 1, QTableWidgetItem(str(result.port)))
                self.result_table.setItem(row, 2, QTableWidgetItem(result.state))
                self.result_table.setItem(row, 3, QTableWidgetItem(result.service))
                self.result_table.setItem(row, 4, QTableWidgetItem(result.banner[:60] if result.banner else ""))
                self.result_table.setItem(row, 5, QTableWidgetItem(result.timestamp.strftime('%H:%M:%S')))

                # 设置行颜色
                if result.state == "open":
                    for col in range(6):
                        self.result_table.item(row, col).setBackground(QColor(232, 245, 233))

        # 更新统计
        elapsed = (datetime.now() - self.scan_start_time).total_seconds()
        self.update_stats(total_hosts, total_ports, elapsed)

        self.status_label.setText(f"✅ 扫描完成！发现 {total_hosts} 个活跃主机，{total_ports} 个开放端口")
        self.scan_finished()

    def on_scan_error(self, error_msg):
        """扫描错误"""
        QMessageBox.critical(self, "扫描错误", f"扫描过程中发生错误:\n{error_msg}")
        self.scan_finished()

    def scan_finished(self):
        """扫描结束清理"""
        self.scan_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_label.setText("✅ 就绪")

    def update_stats(self, hosts, ports, elapsed):
        """更新统计信息"""
        self.stats_text.setPlainText(
            f"活跃主机: {hosts}\n"
            f"开放端口: {ports}\n"
            f"扫描耗时: {elapsed:.2f} 秒\n"
            f"扫描状态: 完成"
        )

    def show_detail(self, index):
        """显示详细信息"""
        row = index.row()
        ip = self.result_table.item(row, 0).text()
        port = self.result_table.item(row, 1).text()
        state = self.result_table.item(row, 2).text()
        service = self.result_table.item(row, 3).text()
        banner = self.result_table.item(row, 4).text()
        time = self.result_table.item(row, 5).text()

        detail_text = f"""
扫描详情
{'='*50}

IP 地址:    {ip}
端口:       {port}
状态:       {state}
服务:       {service}
扫描时间:   {time}

Banner 信息:
{banner if banner else '(无)'}
        """

        QMessageBox.information(self, "端口详情", detail_text)

    def copy_results(self):
        """复制结果到剪贴板"""
        if self.result_table.rowCount() == 0:
            QMessageBox.information(self, "提示", "没有可复制的结果")
            return

        text = "IP地址\t端口\t状态\t服务\tBanner\t时间\n"
        for row in range(self.result_table.rowCount()):
            for col in range(6):
                text += self.result_table.item(row, col).text() + "\t"
            text += "\n"

        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "复制成功", "结果已复制到剪贴板")

    def export_results(self):
        """导出结果"""
        if self.result_table.rowCount() == 0:
            QMessageBox.information(self, "提示", "没有可导出的结果")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "导出结果",
            f"scan_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON文件 (*.json);;CSV文件 (*.csv);;所有文件 (*.*)"
        )

        if not filename:
            return

        try:
            import json
            results = []
            for row in range(self.result_table.rowCount()):
                results.append({
                    "ip": self.result_table.item(row, 0).text(),
                    "port": self.result_table.item(row, 1).text(),
                    "state": self.result_table.item(row, 2).text(),
                    "service": self.result_table.item(row, 3).text(),
                    "banner": self.result_table.item(row, 4).text(),
                    "time": self.result_table.item(row, 5).text()
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

            QMessageBox.information(self, "导出成功", f"结果已导出到:\n{filename}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出过程中发生错误:\n{str(e)}")

    def clear_results(self):
        """清空结果"""
        if self.result_table.rowCount() > 0:
            reply = QMessageBox.question(
                self, "确认清空",
                "确定要清空所有扫描结果吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.result_table.setRowCount(0)
                self.scan_results = {}
                self.status_label.setText("🗑️ 结果已清空")
                self.update_stats(0, 0, 0)


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # 使用 Fusion 风格，跨平台一致

    window = ModernScannerGUI()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
