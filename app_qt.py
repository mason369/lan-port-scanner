#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
局域网端口扫描器 - PyQt6 现代化图形界面
深色主题 + 实时结果更新
"""

import asyncio
import json
import csv
import sys
from datetime import datetime
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QSpinBox, QDoubleSpinBox,
    QRadioButton, QCheckBox, QTableWidget, QTableWidgetItem,
    QGroupBox, QMessageBox, QFileDialog, QHeaderView, QProgressBar,
    QTextEdit, QButtonGroup, QSplitter, QFrame, QComboBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QFont, QColor, QIcon, QPalette, QLinearGradient, QPainter

from scanner import StealthScanner, get_local_network, COMMON_PORTS, TOP_100_PORTS, ScanResult


class ScanThread(QThread):
    """扫描线程 - 支持实时结果回调"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    result_found = pyqtSignal(object)

    def __init__(self, network, host_start, host_end, ports,
                 concurrent, timeout, stealth):
        super().__init__()
        self.network = network
        self.host_start = host_start
        self.host_end = host_end
        self.ports = ports
        self.concurrent = concurrent
        self.timeout = timeout
        self.stealth = stealth
        self._scanner = None

    def run(self):
        try:
            self.progress.emit("正在初始化扫描器...")

            def on_result(result):
                self.result_found.emit(result)

            def on_progress(msg):
                self.progress.emit(msg)

            self._scanner = StealthScanner(
                max_concurrent=self.concurrent,
                timeout=self.timeout,
                delay_range=(0.005, 0.02) if self.stealth else (0, 0),
                randomize=self.stealth,
                on_result=on_result,
                on_progress=on_progress,
            )

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(
                self._scanner.scan_network(
                    network_prefix=self.network,
                    ports=self.ports,
                    host_range=(self.host_start, self.host_end),
                )
            )
            loop.close()
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        if self._scanner:
            self._scanner.stop()


# ─── 深色主题样式 ───────────────────────────────────────────
DARK_STYLE = """
QMainWindow {
    background-color: #1a1b2e;
}
QWidget {
    color: #e0e0e0;
    font-family: "Segoe UI", "Microsoft YaHei", "PingFang SC", sans-serif;
    font-size: 13px;
}
QGroupBox {
    background-color: #232442;
    border: 1px solid #3a3b5c;
    border-radius: 10px;
    margin-top: 14px;
    padding: 16px 12px 12px 12px;
    font-weight: bold;
    font-size: 13px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 16px;
    padding: 0 8px;
    color: #8b8ec7;
}
QLabel {
    color: #c0c3e0;
}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #2a2b4a;
    border: 1px solid #3a3b5c;
    border-radius: 6px;
    padding: 6px 10px;
    color: #e0e0e0;
    selection-background-color: #5c6bc0;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #7c4dff;
}
QRadioButton, QCheckBox {
    color: #c0c3e0;
    spacing: 6px;
}
QRadioButton::indicator, QCheckBox::indicator {
    width: 16px; height: 16px;
}
QRadioButton::indicator:checked {
    background-color: #7c4dff;
    border: 2px solid #7c4dff;
    border-radius: 9px;
}
QCheckBox::indicator:checked {
    background-color: #7c4dff;
    border: 2px solid #7c4dff;
    border-radius: 4px;
}
QPushButton {
    background-color: #2a2b4a;
    border: 1px solid #3a3b5c;
    border-radius: 8px;
    padding: 8px 18px;
    color: #c0c3e0;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #353660;
    border-color: #7c4dff;
}
QPushButton:pressed {
    background-color: #7c4dff;
}
QPushButton:disabled {
    background-color: #1e1f38;
    color: #555;
    border-color: #2a2b4a;
}
QTableWidget {
    background-color: #1e1f38;
    alternate-background-color: #232442;
    border: 1px solid #3a3b5c;
    border-radius: 8px;
    gridline-color: #2a2b4a;
    selection-background-color: #3949ab;
    color: #e0e0e0;
}
QHeaderView::section {
    background-color: #2a2b4a;
    color: #8b8ec7;
    padding: 8px 6px;
    border: none;
    border-bottom: 2px solid #7c4dff;
    font-weight: bold;
    font-size: 12px;
}
QProgressBar {
    background-color: #2a2b4a;
    border: none;
    border-radius: 6px;
    height: 8px;
    text-align: center;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #7c4dff, stop:1 #448aff);
    border-radius: 6px;
}
QTextEdit {
    background-color: #2a2b4a;
    border: 1px solid #3a3b5c;
    border-radius: 6px;
    color: #c0c3e0;
    padding: 6px;
}
QScrollBar:vertical {
    background: #1e1f38;
    width: 8px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #3a3b5c;
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #7c4dff;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QSplitter::handle {
    background-color: #3a3b5c;
    width: 2px;
}
"""


class ModernScannerGUI(QMainWindow):
    """现代化深色主题扫描器界面"""

    def __init__(self):
        super().__init__()
        self.scan_thread: Optional[ScanThread] = None
        self.scan_results = {}
        self.scan_start_time = None
        self.total_open = 0
        self.total_hosts_found = set()

        self.setWindowTitle("LAN Port Scanner")
        self.setMinimumSize(1200, 780)
        self.resize(1400, 900)
        self.init_ui()
        self.center_window()

    def center_window(self):
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2,
        )

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(0)
        main_widget.setLayout(main_layout)

        # 顶部标题栏
        header = self._build_header()
        main_layout.addWidget(header)
        main_layout.addSpacing(10)

        # 内容区
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(3)
        left_panel = self._build_left_panel()
        right_panel = self._build_right_panel()
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([340, 1060])
        main_layout.addWidget(splitter, 1)

        # 底部状态栏
        self.status_label = QLabel("就绪 - 等待开始扫描")
        self.status_label.setStyleSheet(
            "padding: 8px 14px; background-color: #232442;"
            "border-radius: 6px; color: #8b8ec7; font-size: 12px;"
        )
        main_layout.addSpacing(8)
        main_layout.addWidget(self.status_label)

    def _build_header(self):
        frame = QFrame()
        frame.setStyleSheet(
            "background-color: #232442; border-radius: 10px; padding: 6px;"
        )
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(20, 10, 20, 10)

        title = QLabel("LAN Port Scanner")
        title.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #7c4dff;"
            "background: transparent;"
        )
        layout.addWidget(title)

        subtitle = QLabel("快速 · 隐蔽 · 准确")
        subtitle.setStyleSheet(
            "font-size: 12px; color: #6c6f94; background: transparent;"
        )
        layout.addWidget(subtitle)
        layout.addStretch()

        # 实时统计卡片
        for label_text, attr in [
            ("活跃主机", "_stat_hosts"),
            ("开放端口", "_stat_ports"),
            ("扫描耗时", "_stat_time"),
        ]:
            card = QFrame()
            card.setStyleSheet(
                "background-color: #2a2b4a; border-radius: 8px; padding: 4px 12px;"
            )
            cl = QVBoxLayout(card)
            cl.setContentsMargins(10, 4, 10, 4)
            cl.setSpacing(0)
            lbl = QLabel(label_text)
            lbl.setStyleSheet("font-size: 10px; color: #6c6f94; background: transparent;")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            val = QLabel("0" if "耗时" not in label_text else "0.0s")
            val.setStyleSheet(
                "font-size: 18px; font-weight: bold; color: #7c4dff;"
                "background: transparent;"
            )
            val.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cl.addWidget(lbl)
            cl.addWidget(val)
            setattr(self, attr, val)
            layout.addWidget(card)
            layout.addSpacing(6)

        return frame

    def _build_left_panel(self):
        panel = QWidget()
        panel.setFixedWidth(340)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 6, 0)
        layout.setSpacing(8)

        # ── 网络配置 ──
        net_group = QGroupBox("网络配置")
        ng = QVBoxLayout(net_group)
        ng.setSpacing(6)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("网段:"))
        self.network_input = QLineEdit(get_local_network())
        self.network_input.setPlaceholderText("如 192.168.1")
        row1.addWidget(self.network_input)
        ng.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("范围:"))
        self.host_start = QSpinBox()
        self.host_start.setRange(1, 254)
        self.host_start.setValue(1)
        row2.addWidget(self.host_start)
        row2.addWidget(QLabel("-"))
        self.host_end = QSpinBox()
        self.host_end.setRange(1, 254)
        self.host_end.setValue(254)
        row2.addWidget(self.host_end)
        ng.addLayout(row2)

        layout.addWidget(net_group)

        # ── 端口配置 ──
        port_group = QGroupBox("端口配置")
        pg = QVBoxLayout(port_group)
        pg.setSpacing(6)

        self.port_btn_group = QButtonGroup(self)
        for i, (text, val) in enumerate([
            ("常用端口 (18个)", "common"),
            ("Top 100 端口", "top100"),
            ("全端口 (1-65535)", "all"),
            ("自定义", "custom"),
        ]):
            rb = QRadioButton(text)
            rb.setProperty("port_mode", val)
            self.port_btn_group.addButton(rb, i)
            pg.addWidget(rb)
            if i == 0:
                rb.setChecked(True)

        self.custom_ports_input = QLineEdit()
        self.custom_ports_input.setPlaceholderText("如: 80,443,8080 或 1-1024")
        self.custom_ports_input.setEnabled(False)
        pg.addWidget(self.custom_ports_input)

        self.port_btn_group.idToggled.connect(self._on_port_mode_changed)
        layout.addWidget(port_group)

        # ── 扫描参数 ──
        param_group = QGroupBox("扫描参数")
        pmg = QVBoxLayout(param_group)
        pmg.setSpacing(6)

        r1 = QHBoxLayout()
        r1.addWidget(QLabel("并发数:"))
        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setRange(50, 2000)
        self.concurrent_spin.setValue(500)
        self.concurrent_spin.setSingleStep(50)
        r1.addWidget(self.concurrent_spin)
        pmg.addLayout(r1)

        r2 = QHBoxLayout()
        r2.addWidget(QLabel("超时(s):"))
        self.timeout_spin = QDoubleSpinBox()
        self.timeout_spin.setRange(0.1, 5.0)
        self.timeout_spin.setValue(0.6)
        self.timeout_spin.setSingleStep(0.1)
        r2.addWidget(self.timeout_spin)
        pmg.addLayout(r2)

        self.stealth_check = QCheckBox("隐蔽模式 (随机化 + 延迟)")
        self.stealth_check.setChecked(True)
        pmg.addWidget(self.stealth_check)

        layout.addWidget(param_group)

        # ── 操作按钮 ──
        self.start_btn = QPushButton("开始扫描")
        self.start_btn.setStyleSheet(
            "QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #7c4dff, stop:1 #448aff); color: white; font-size: 15px;"
            "font-weight: bold; padding: 12px; border-radius: 10px; border: none; }"
            "QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #651fff, stop:1 #2979ff); }"
            "QPushButton:disabled { background: #2a2b4a; color: #555; }"
        )
        self.start_btn.clicked.connect(self.start_scan)
        layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("停止扫描")
        self.stop_btn.setStyleSheet(
            "QPushButton { background-color: #c62828; color: white;"
            "font-weight: bold; padding: 10px; border-radius: 10px; border: none; }"
            "QPushButton:hover { background-color: #e53935; }"
            "QPushButton:disabled { background: #2a2b4a; color: #555; }"
        )
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_scan)
        layout.addWidget(self.stop_btn)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        layout.addWidget(self.progress_bar)

        layout.addStretch()

        # ── 导出按钮 ──
        export_layout = QHBoxLayout()
        btn_json = QPushButton("导出 JSON")
        btn_json.clicked.connect(lambda: self.export_results("json"))
        btn_csv = QPushButton("导出 CSV")
        btn_csv.clicked.connect(lambda: self.export_results("csv"))
        export_layout.addWidget(btn_json)
        export_layout.addWidget(btn_csv)
        layout.addLayout(export_layout)

        return panel

    def _build_right_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(6, 0, 0, 0)
        layout.setSpacing(8)

        # 结果表格
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["IP 地址", "端口", "状态", "服务", "Banner"]
        )
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(32)

        layout.addWidget(self.table, 1)

        # 日志区域
        log_group = QGroupBox("扫描日志")
        lg = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(140)
        self.log_text.setStyleSheet(
            "font-family: 'Consolas', 'Courier New', monospace; font-size: 11px;"
        )
        lg.addWidget(self.log_text)
        layout.addWidget(log_group)

        return panel

    def _on_port_mode_changed(self, btn_id, checked):
        if checked:
            self.custom_ports_input.setEnabled(btn_id == 3)

    def _parse_ports(self) -> list:
        btn = self.port_btn_group.checkedButton()
        mode = btn.property("port_mode") if btn else "common"
        if mode == "common":
            return COMMON_PORTS
        elif mode == "top100":
            return TOP_100_PORTS
        elif mode == "all":
            return list(range(1, 65536))
        else:
            text = self.custom_ports_input.text().strip()
            if not text:
                return COMMON_PORTS
            ports = []
            for part in text.split(","):
                part = part.strip()
                if "-" in part:
                    a, b = part.split("-", 1)
                    ports.extend(range(int(a), int(b) + 1))
                else:
                    ports.append(int(part))
            return sorted(set(p for p in ports if 1 <= p <= 65535))

    def _log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{ts}] {msg}")

    def start_scan(self):
        network = self.network_input.text().strip()
        if not network:
            QMessageBox.warning(self, "提示", "请输入网络段")
            return

        try:
            ports = self._parse_ports()
        except ValueError:
            QMessageBox.warning(self, "提示", "端口格式错误")
            return

        self.table.setRowCount(0)
        self.log_text.clear()
        self.total_open = 0
        self.total_hosts_found = set()
        self.scan_results = {}
        self.scan_start_time = datetime.now()

        self._stat_hosts.setText("0")
        self._stat_ports.setText("0")
        self._stat_time.setText("0.0s")

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setVisible(True)

        self._log(f"开始扫描 {network}.{self.host_start.value()}-{self.host_end.value()}")
        self._log(f"端口数: {len(ports)}，并发: {self.concurrent_spin.value()}")

        # 启动计时器
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_time)
        self._timer.start(100)

        self.scan_thread = ScanThread(
            network=network,
            host_start=self.host_start.value(),
            host_end=self.host_end.value(),
            ports=ports,
            concurrent=self.concurrent_spin.value(),
            timeout=self.timeout_spin.value(),
            stealth=self.stealth_check.isChecked(),
        )
        self.scan_thread.progress.connect(self._on_progress)
        self.scan_thread.result_found.connect(self._on_result_found)
        self.scan_thread.finished.connect(self._on_finished)
        self.scan_thread.error.connect(self._on_error)
        self.scan_thread.start()

    def stop_scan(self):
        if self.scan_thread:
            self.scan_thread.stop()
            self._log("正在停止扫描...")

    def _update_time(self):
        if self.scan_start_time:
            elapsed = (datetime.now() - self.scan_start_time).total_seconds()
            self._stat_time.setText(f"{elapsed:.1f}s")

    def _on_progress(self, msg: str):
        self.status_label.setText(msg)
        self._log(msg)

    def _on_result_found(self, result):
        self.total_open += 1
        self.total_hosts_found.add(result.ip)
        self._stat_ports.setText(str(self.total_open))
        self._stat_hosts.setText(str(len(self.total_hosts_found)))

        row = self.table.rowCount()
        self.table.insertRow(row)

        ip_item = QTableWidgetItem(result.ip)
        ip_item.setForeground(QColor("#82b1ff"))
        self.table.setItem(row, 0, ip_item)

        port_item = QTableWidgetItem(str(result.port))
        port_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        port_item.setForeground(QColor("#e0e0e0"))
        self.table.setItem(row, 1, port_item)

        state_item = QTableWidgetItem(result.state)
        state_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        state_item.setForeground(QColor("#69f0ae"))
        self.table.setItem(row, 2, state_item)

        svc_item = QTableWidgetItem(result.service)
        svc_item.setForeground(QColor("#ffab40"))
        self.table.setItem(row, 3, svc_item)

        banner_item = QTableWidgetItem(result.banner or "")
        banner_item.setForeground(QColor("#8b8ec7"))
        self.table.setItem(row, 4, banner_item)

        # 保存结果
        if result.ip not in self.scan_results:
            self.scan_results[result.ip] = []
        self.scan_results[result.ip].append(result)

    def _on_finished(self, results):
        self._scan_done()
        elapsed = (datetime.now() - self.scan_start_time).total_seconds()
        self._log(f"扫描完成! 耗时 {elapsed:.1f}s，"
                  f"发现 {len(self.total_hosts_found)} 个主机，"
                  f"{self.total_open} 个开放端口")
        self.status_label.setText(
            f"扫描完成 - {len(self.total_hosts_found)} 个主机，"
            f"{self.total_open} 个开放端口，耗时 {elapsed:.1f}s"
        )

    def _on_error(self, msg: str):
        self._scan_done()
        self._log(f"错误: {msg}")
        QMessageBox.critical(self, "扫描错误", msg)

    def _scan_done(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        if hasattr(self, '_timer'):
            self._timer.stop()

    def export_results(self, fmt: str):
        if not self.scan_results:
            QMessageBox.information(self, "提示", "没有可导出的结果")
            return

        if fmt == "json":
            path, _ = QFileDialog.getSaveFileName(
                self, "导出 JSON", f"scan_{datetime.now():%Y%m%d_%H%M%S}.json",
                "JSON Files (*.json)"
            )
            if path:
                data = {}
                for ip, results in self.scan_results.items():
                    data[ip] = [
                        {"port": r.port, "state": r.state,
                         "service": r.service, "banner": r.banner}
                        for r in results
                    ]
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                self._log(f"已导出 JSON: {path}")
        else:
            path, _ = QFileDialog.getSaveFileName(
                self, "导出 CSV", f"scan_{datetime.now():%Y%m%d_%H%M%S}.csv",
                "CSV Files (*.csv)"
            )
            if path:
                with open(path, "w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f)
                    writer.writerow(["IP", "端口", "状态", "服务", "Banner"])
                    for ip, results in self.scan_results.items():
                        for r in results:
                            writer.writerow([r.ip, r.port, r.state,
                                           r.service, r.banner])
                self._log(f"已导出 CSV: {path}")


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLE)
    app.setStyle("Fusion")

    # Fusion 深色调色板
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#1a1b2e"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#1e1f38"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#232442"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#2a2b4a"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#7c4dff"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)

    window = ModernScannerGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
