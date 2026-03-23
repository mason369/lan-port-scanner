#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
局域网端口扫描器 - PyQt6 现代化图形界面
玻璃拟态深色主题 + Dashboard 布局 + 实时图表
"""

import asyncio
import json
import csv
import sys
import math
import webbrowser
from datetime import datetime
from typing import Optional
from collections import defaultdict

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QSpinBox, QDoubleSpinBox,
    QRadioButton, QCheckBox, QTableWidget, QTableWidgetItem,
    QGroupBox, QMessageBox, QFileDialog, QHeaderView, QProgressBar,
    QTextEdit, QButtonGroup, QSplitter, QFrame, QComboBox,
    QGraphicsDropShadowEffect, QMenu, QScrollArea, QSizePolicy,
    QStyledItemDelegate, QStyle
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QTimer, QSize, QPropertyAnimation,
    QEasingCurve, pyqtProperty, QRect, QPoint, QParallelAnimationGroup
)
from PyQt6.QtGui import (
    QFont, QColor, QIcon, QPalette, QLinearGradient, QPainter,
    QBrush, QPen, QAction, QCursor, QPainterPath, QConicalGradient,
    QRadialGradient, QFontDatabase
)

from scanner import StealthScanner, get_local_network, COMMON_PORTS, TOP_100_PORTS, ScanResult

# 尝试导入可选依赖
try:
    import qtawesome as qta
    HAS_QTA = True
except ImportError:
    HAS_QTA = False

try:
    import pyqtgraph as pg
    pg.setConfigOptions(antialias=True, background=None, foreground='#e0e0e0')
    HAS_PG = True
except ImportError:
    HAS_PG = False


# ─── 服务分类 ───────────────────────────────────────────
SERVICE_CATEGORIES = {
    'Web': [80, 443, 8080, 8443, 8000, 8008, 8888, 8081, 3000],
    '数据库': [3306, 5432, 27017, 6379, 1433, 1521, 5984, 9200, 11211],
    '远程访问': [22, 23, 3389, 5900, 5800],
    '邮件': [25, 110, 143, 465, 587, 993, 995],
    '文件共享': [21, 445, 139, 2049, 873],
    '消息队列': [5672, 9092, 1883, 15672],
    '网络服务': [53, 67, 68, 123, 161, 389, 636],
    '其他': [],
}

SERVICE_CATEGORY_COLORS = {
    'Web': '#448aff',
    '数据库': '#7c4dff',
    '远程访问': '#ff5252',
    '邮件': '#ffab40',
    '文件共享': '#69f0ae',
    '消息队列': '#40c4ff',
    '网络服务': '#ff80ab',
    '其他': '#8b8ec7',
}


def classify_port(port: int) -> str:
    for cat, ports in SERVICE_CATEGORIES.items():
        if port in ports:
            return cat
    return '其他'


def get_icon(name: str, color: str = '#c0c3e0', scale_factor: float = 1.0):
    if HAS_QTA:
        try:
            return qta.icon(name, color=color, scale_factor=scale_factor)
        except Exception:
            return QIcon()
    return QIcon()


# ─── 扫描线程 ───────────────────────────────────────────
class ScanThread(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    progress_pct = pyqtSignal(int)
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
                # 解析百分比
                if '扫描进度:' in msg and '%' in msg:
                    try:
                        pct = int(msg.split('%')[0].split(':')[-1].strip())
                        self.progress_pct.emit(pct)
                    except (ValueError, IndexError):
                        pass
                elif '主机发现:' in msg:
                    try:
                        parts = msg.split('/')
                        done = int(parts[0].split(':')[-1].strip())
                        total = int(parts[1].split('，')[0].strip())
                        pct = int(done / total * 50) if total > 0 else 0
                        self.progress_pct.emit(pct)
                    except (ValueError, IndexError):
                        pass

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
            self.progress_pct.emit(100)
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        if self._scanner:
            self._scanner.stop()


# ─── 圆形进度环组件 ───────────────────────────────────────
class CircularProgress(QWidget):
    def __init__(self, parent=None, size=64, line_width=5):
        super().__init__(parent)
        self._size = size
        self._line_width = line_width
        self._value = 0
        self._max_value = 100
        self._is_complete = False
        self.setFixedSize(size, size)

    def get_value(self):
        return self._value

    def set_value(self, val):
        self._value = val
        self._is_complete = (val >= self._max_value)
        self.update()

    value = pyqtProperty(int, get_value, set_value)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(
            self._line_width, self._line_width,
            -self._line_width, -self._line_width
        )

        # 背景环
        bg_pen = QPen(QColor(255, 255, 255, 20))
        bg_pen.setWidth(self._line_width)
        bg_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(bg_pen)
        painter.drawArc(rect, 0, 360 * 16)

        # 前景环
        if self._value > 0:
            if self._is_complete:
                color = QColor('#69f0ae')
            else:
                gradient_pos = self._value / self._max_value
                r = int(124 + (68 - 124) * gradient_pos)
                g = int(77 + (138 - 77) * gradient_pos)
                b = int(255 + (255 - 255) * gradient_pos)
                color = QColor(r, g, b)

            fg_pen = QPen(color)
            fg_pen.setWidth(self._line_width)
            fg_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(fg_pen)

            span = int(-self._value / self._max_value * 360 * 16)
            painter.drawArc(rect, 90 * 16, span)

        # 中心文字
        painter.setPen(QColor('#f0f0f5'))
        font = painter.font()
        font.setPixelSize(self._size // 4)
        font.setBold(True)
        painter.setFont(font)

        if self._is_complete:
            painter.setPen(QColor('#69f0ae'))
            font.setPixelSize(self._size // 3)
            painter.setFont(font)
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "✓")
        else:
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{self._value}%")

        painter.end()


# ─── 统计卡片组件 ───────────────────────────────────────
class StatCard(QFrame):
    def __init__(self, title, icon_name, accent_color, parent=None):
        super().__init__(parent)
        self.accent_color = accent_color
        self.setFixedHeight(90)
        self.setMinimumWidth(150)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # 左侧彩色竖条
        bar = QFrame()
        bar.setFixedWidth(4)
        bar.setStyleSheet(f"background-color: {accent_color}; border-radius: 2px;")
        layout.addWidget(bar)

        # 图标
        if HAS_QTA:
            icon_label = QLabel()
            icon_label.setPixmap(get_icon(icon_name, accent_color, 1.2).pixmap(28, 28))
            icon_label.setFixedSize(32, 32)
            icon_label.setStyleSheet("background: transparent;")
            layout.addWidget(icon_label)

        # 文字区
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        self.value_label = QLabel("0")
        self.value_label.setStyleSheet(
            f"font-size: 26px; font-weight: bold; color: {accent_color};"
            "background: transparent; font-family: 'Cascadia Code', 'Consolas', 'Courier New', monospace;"
        )

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(
            "font-size: 11px; color: #6c6f94; background: transparent;"
        )

        text_layout.addWidget(self.value_label)
        text_layout.addWidget(self.title_label)
        layout.addLayout(text_layout)
        layout.addStretch()

        self.setStyleSheet(f"""
            StatCard {{
                background-color: #1a1b2e;
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 12px;
            }}
            StatCard:hover {{
                border: 1px solid rgba(255,255,255,0.12);
            }}
        """)

    def set_value(self, text):
        self.value_label.setText(str(text))


# ─── 简易饼图组件 (无 pyqtgraph 时使用) ───────────────────
class SimplePieChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = {}
        self._colors = {}
        self.setMinimumSize(200, 200)

    def set_data(self, data: dict, colors: dict):
        self._data = data
        self._colors = colors
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        margin = 10
        chart_size = min(w, h) - margin * 2
        chart_rect = QRect(
            (w - chart_size) // 2, margin,
            chart_size, chart_size
        )

        total = sum(self._data.values())
        if total == 0:
            # 空状态
            painter.setPen(QPen(QColor(255, 255, 255, 30), 2, Qt.PenStyle.DashLine))
            painter.drawEllipse(chart_rect.adjusted(20, 20, -20, -20))
            painter.setPen(QColor('#6c6f94'))
            font = painter.font()
            font.setPixelSize(13)
            painter.setFont(font)
            painter.drawText(chart_rect, Qt.AlignmentFlag.AlignCenter, "等待扫描")
            painter.end()
            return

        start_angle = 90 * 16
        for cat, count in sorted(self._data.items(), key=lambda x: -x[1]):
            if count == 0:
                continue
            span = int(count / total * 360 * 16)
            color = QColor(self._colors.get(cat, '#8b8ec7'))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawPie(chart_rect, start_angle, -span)
            start_angle -= span

        # 中心挖空(甜甜圈效果)
        hole_size = int(chart_size * 0.55)
        hole_rect = QRect(
            (w - hole_size) // 2, margin + (chart_size - hole_size) // 2,
            hole_size, hole_size
        )
        painter.setBrush(QBrush(QColor('#0d0e1a')))
        painter.drawEllipse(hole_rect)

        # 中心文字
        painter.setPen(QColor('#f0f0f5'))
        font = painter.font()
        font.setPixelSize(20)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(hole_rect, Qt.AlignmentFlag.AlignCenter, str(total))

        # 图例
        legend_y = margin + chart_size + 8
        font.setPixelSize(11)
        font.setBold(False)
        painter.setFont(font)
        x_offset = 10
        for cat, count in sorted(self._data.items(), key=lambda x: -x[1]):
            if count == 0:
                continue
            color = QColor(self._colors.get(cat, '#8b8ec7'))
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(x_offset, legend_y, 10, 10, 2, 2)
            painter.setPen(QColor('#9da0c7'))
            text = f"{cat}({count})"
            painter.drawText(x_offset + 14, legend_y + 10, text)
            x_offset += len(text) * 8 + 24
            if x_offset > w - 40:
                x_offset = 10
                legend_y += 18

        painter.end()


# ─── 简易柱状图组件 ───────────────────────────────────────
class SimpleBarChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = {}
        self._colors = {}
        self.setMinimumSize(200, 150)

    def set_data(self, data: dict, colors: dict):
        self._data = data
        self._colors = colors
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()

        sorted_data = sorted(self._data.items(), key=lambda x: -x[1])[:8]
        if not sorted_data:
            painter.setPen(QColor('#6c6f94'))
            font = painter.font()
            font.setPixelSize(13)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "等待扫描")
            painter.end()
            return

        max_val = max(v for _, v in sorted_data) or 1
        margin_left = 70
        margin_right = 40
        margin_top = 10
        margin_bottom = 10
        bar_area_w = w - margin_left - margin_right
        bar_height = min(24, (h - margin_top - margin_bottom) // max(len(sorted_data), 1) - 4)
        spacing = 4

        font = painter.font()
        font.setPixelSize(11)
        painter.setFont(font)

        for i, (cat, count) in enumerate(sorted_data):
            y = margin_top + i * (bar_height + spacing)
            bar_w = int(count / max_val * bar_area_w) if max_val > 0 else 0

            # 标签
            painter.setPen(QColor('#9da0c7'))
            painter.drawText(
                QRect(4, y, margin_left - 8, bar_height),
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                cat
            )

            # 柱子
            color = QColor(self._colors.get(cat, '#8b8ec7'))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))
            path = QPainterPath()
            path.addRoundedRect(margin_left, y, max(bar_w, 4), bar_height, 4, 4)
            painter.drawPath(path)

            # 数值
            painter.setPen(QColor('#f0f0f5'))
            painter.drawText(
                QRect(margin_left + bar_w + 6, y, 40, bar_height),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                str(count)
            )

        painter.end()


# ─── 侧边栏组件 ───────────────────────────────────────────
class CollapsibleSidebar(QFrame):
    EXPANDED_WIDTH = 300
    COLLAPSED_WIDTH = 0

    def __init__(self, parent=None):
        super().__init__(parent)
        self._expanded = True
        self._target_width = self.EXPANDED_WIDTH
        self.setFixedWidth(self.EXPANDED_WIDTH)
        self.setStyleSheet("""
            CollapsibleSidebar {
                background-color: #131429;
                border-right: 1px solid rgba(255,255,255,0.06);
            }
        """)

        self._anim = QPropertyAnimation(self, b"fixedWidth")
        self._anim.setDuration(250)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

    def get_fixed_width(self):
        return self.fixedWidth if hasattr(self, '_fw') else self.EXPANDED_WIDTH

    def set_fixed_width(self, w):
        self._fw = w
        self.setFixedWidth(w)

    fixedWidth_prop = pyqtProperty(int, get_fixed_width, set_fixed_width)

    def toggle(self):
        self._expanded = not self._expanded
        self._anim.setPropertyName(b"fixedWidth_prop")
        self._anim.setStartValue(self.width())
        self._anim.setEndValue(
            self.EXPANDED_WIDTH if self._expanded else self.COLLAPSED_WIDTH
        )
        self._anim.start()

    def collapse(self):
        if self._expanded:
            self.toggle()

    def expand(self):
        if not self._expanded:
            self.toggle()

    @property
    def is_expanded(self):
        return self._expanded


# ─── 深色主题样式 ───────────────────────────────────────────
DARK_STYLE = """
QMainWindow {
    background-color: #0d0e1a;
}
QWidget {
    color: #e0e0e0;
    font-family: "Segoe UI", "Microsoft YaHei", "PingFang SC", sans-serif;
    font-size: 13px;
}
QGroupBox {
    background-color: rgba(26, 27, 46, 0.8);
    border: 1px solid rgba(255,255,255,0.06);
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
    background: transparent;
}
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #222340;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 6px;
    padding: 7px 10px;
    color: #f0f0f5;
    selection-background-color: #5c6bc0;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #7c4dff;
    background-color: #282950;
}
QRadioButton, QCheckBox {
    color: #c0c3e0;
    spacing: 6px;
    background: transparent;
}
QRadioButton::indicator, QCheckBox::indicator {
    width: 16px; height: 16px;
}
QRadioButton::indicator:checked {
    background-color: #7c4dff;
    border: 2px solid #7c4dff;
    border-radius: 9px;
}
QRadioButton::indicator:unchecked {
    border: 2px solid #3a3b5c;
    border-radius: 9px;
    background-color: transparent;
}
QCheckBox::indicator:checked {
    background-color: #7c4dff;
    border: 2px solid #7c4dff;
    border-radius: 4px;
}
QCheckBox::indicator:unchecked {
    border: 2px solid #3a3b5c;
    border-radius: 4px;
    background-color: transparent;
}
QPushButton {
    background-color: #1a1b2e;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 8px;
    padding: 8px 18px;
    color: #c0c3e0;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #232442;
    border-color: rgba(124,77,255,0.5);
    color: #f0f0f5;
}
QPushButton:pressed {
    background-color: #7c4dff;
    color: white;
}
QPushButton:disabled {
    background-color: #0d0e1a;
    color: #4a4d6e;
    border-color: rgba(255,255,255,0.03);
}
QTableWidget {
    background-color: #111225;
    alternate-background-color: #151630;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
    gridline-color: rgba(255,255,255,0.04);
    selection-background-color: rgba(124,77,255,0.25);
    selection-color: #f0f0f5;
    color: #e0e0e0;
}
QHeaderView::section {
    background-color: #131429;
    color: #8b8ec7;
    padding: 10px 8px;
    border: none;
    border-bottom: 2px solid #7c4dff;
    font-weight: bold;
    font-size: 12px;
}
QProgressBar {
    background-color: rgba(255,255,255,0.05);
    border: none;
    border-radius: 4px;
    height: 6px;
    text-align: center;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #7c4dff, stop:1 #448aff);
    border-radius: 4px;
}
QTextEdit {
    background-color: #111225;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 8px;
    color: #9da0c7;
    padding: 8px;
    font-family: 'Cascadia Code', 'Consolas', 'Courier New', monospace;
    font-size: 11px;
}
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    border-radius: 4px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: rgba(255,255,255,0.1);
    border-radius: 4px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: rgba(124,77,255,0.5);
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background: transparent;
    height: 8px;
    border-radius: 4px;
    margin: 2px;
}
QScrollBar::handle:horizontal {
    background: rgba(255,255,255,0.1);
    border-radius: 4px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover {
    background: rgba(124,77,255,0.5);
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}
QSplitter::handle {
    background-color: rgba(255,255,255,0.04);
    width: 2px;
}
QSplitter::handle:hover {
    background-color: #7c4dff;
}
QMenu {
    background-color: #1a1b2e;
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 8px;
    padding: 4px;
}
QMenu::item {
    padding: 8px 32px 8px 16px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: rgba(124,77,255,0.25);
}
QMenu::separator {
    height: 1px;
    background-color: rgba(255,255,255,0.06);
    margin: 4px 8px;
}
QToolTip {
    background-color: #232442;
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 6px;
    padding: 6px 10px;
    color: #f0f0f5;
    font-size: 12px;
}
"""


# ─── 主界面 ─────────────────────────────────────────────
class ModernScannerGUI(QMainWindow):
    """现代化 Dashboard 风格扫描器界面"""

    def __init__(self):
        super().__init__()
        self.scan_thread: Optional[ScanThread] = None
        self.scan_results = {}
        self.scan_start_time = None
        self.total_open = 0
        self.total_hosts_found = set()
        self._category_counts = defaultdict(int)
        self._scan_progress = 0

        self.setWindowTitle("LAN Port Scanner")
        self.setMinimumSize(1200, 700)
        self.resize(1500, 900)
        self._init_ui()
        self._center_window()

    def _center_window(self):
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2,
        )

    def _init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        root_layout = QHBoxLayout()
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        main_widget.setLayout(root_layout)

        # 左侧：可折叠侧边栏
        self.sidebar = CollapsibleSidebar()
        sidebar_inner = QVBoxLayout(self.sidebar)
        sidebar_inner.setContentsMargins(12, 12, 12, 12)
        sidebar_inner.setSpacing(8)
        self._build_sidebar(sidebar_inner)
        root_layout.addWidget(self.sidebar)

        # 右侧：主内容区
        main_area = QWidget()
        main_area.setStyleSheet("background-color: #0d0e1a;")
        main_layout = QVBoxLayout(main_area)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(12)

        # 顶部：标题栏 + 统计卡片
        top_bar = self._build_top_bar()
        main_layout.addWidget(top_bar)

        # 统计卡片行
        stats_row = self._build_stats_row()
        main_layout.addLayout(stats_row)

        # 中部：结果表格 + 图表
        mid_splitter = QSplitter(Qt.Orientation.Horizontal)
        mid_splitter.setHandleWidth(3)

        # 左：结果表格区
        table_container = self._build_table_area()
        mid_splitter.addWidget(table_container)

        # 右：图表区
        charts_container = self._build_charts_area()
        mid_splitter.addWidget(charts_container)
        mid_splitter.setStretchFactor(0, 3)
        mid_splitter.setStretchFactor(1, 1)
        mid_splitter.setSizes([900, 350])
        main_layout.addWidget(mid_splitter, 1)

        # 底部：日志
        log_container = self._build_log_area()
        main_layout.addWidget(log_container)

        # 底部状态栏
        self.status_label = QLabel("就绪 - 等待开始扫描")
        self.status_label.setStyleSheet(
            "padding: 6px 14px; background-color: #131429;"
            "border-radius: 6px; color: #6c6f94; font-size: 11px;"
            "border: 1px solid rgba(255,255,255,0.04);"
        )
        main_layout.addWidget(self.status_label)

        root_layout.addWidget(main_area, 1)

    def _build_sidebar(self, layout):
        # 标题 + 折叠按钮
        header_row = QHBoxLayout()
        title = QLabel("配置面板")
        title.setStyleSheet(
            "font-size: 15px; font-weight: bold; color: #7c4dff;"
        )
        header_row.addWidget(title)
        header_row.addStretch()

        self.toggle_btn = QPushButton()
        if HAS_QTA:
            self.toggle_btn.setIcon(get_icon('mdi.chevron-left', '#8b8ec7'))
        else:
            self.toggle_btn.setText("◀")
        self.toggle_btn.setFixedSize(32, 32)
        self.toggle_btn.setStyleSheet(
            "QPushButton { border-radius: 16px; border: 1px solid rgba(255,255,255,0.08); }"
            "QPushButton:hover { background-color: rgba(124,77,255,0.2); }"
        )
        self.toggle_btn.clicked.connect(self._toggle_sidebar)
        header_row.addWidget(self.toggle_btn)
        layout.addLayout(header_row)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
            "QScrollArea > QWidget > QWidget { background: transparent; }"
        )
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(8)

        # ── 网络配置 ──
        net_group = QGroupBox()
        ng = QVBoxLayout(net_group)
        ng.setSpacing(6)

        net_title = QHBoxLayout()
        if HAS_QTA:
            icon = QLabel()
            icon.setPixmap(get_icon('mdi.lan', '#7c4dff').pixmap(18, 18))
            icon.setFixedSize(20, 20)
            net_title.addWidget(icon)
        net_title.addWidget(QLabel("网络配置"))
        net_title.addStretch()
        ng.addLayout(net_title)

        row1 = QHBoxLayout()
        lbl = QLabel("网段")
        lbl.setFixedWidth(40)
        row1.addWidget(lbl)
        self.network_input = QLineEdit(get_local_network())
        self.network_input.setPlaceholderText("如 192.168.1")
        row1.addWidget(self.network_input)
        ng.addLayout(row1)

        row2 = QHBoxLayout()
        lbl2 = QLabel("范围")
        lbl2.setFixedWidth(40)
        row2.addWidget(lbl2)
        self.host_start = QSpinBox()
        self.host_start.setRange(1, 254)
        self.host_start.setValue(1)
        row2.addWidget(self.host_start)
        dash = QLabel("—")
        dash.setFixedWidth(16)
        dash.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row2.addWidget(dash)
        self.host_end = QSpinBox()
        self.host_end.setRange(1, 254)
        self.host_end.setValue(254)
        row2.addWidget(self.host_end)
        ng.addLayout(row2)

        scroll_layout.addWidget(net_group)

        # ── 端口配置 ──
        port_group = QGroupBox()
        pg = QVBoxLayout(port_group)
        pg.setSpacing(6)

        port_title = QHBoxLayout()
        if HAS_QTA:
            icon2 = QLabel()
            icon2.setPixmap(get_icon('mdi.ethernet', '#448aff').pixmap(18, 18))
            icon2.setFixedSize(20, 20)
            port_title.addWidget(icon2)
        port_title.addWidget(QLabel("端口配置"))
        port_title.addStretch()
        pg.addLayout(port_title)

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
        scroll_layout.addWidget(port_group)

        # ── 扫描参数 ──
        param_group = QGroupBox()
        pmg = QVBoxLayout(param_group)
        pmg.setSpacing(6)

        param_title = QHBoxLayout()
        if HAS_QTA:
            icon3 = QLabel()
            icon3.setPixmap(get_icon('mdi.tune', '#69f0ae').pixmap(18, 18))
            icon3.setFixedSize(20, 20)
            param_title.addWidget(icon3)
        param_title.addWidget(QLabel("扫描参数"))
        param_title.addStretch()
        pmg.addLayout(param_title)

        r1 = QHBoxLayout()
        lbl3 = QLabel("并发数")
        lbl3.setFixedWidth(50)
        r1.addWidget(lbl3)
        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setRange(50, 2000)
        self.concurrent_spin.setValue(500)
        self.concurrent_spin.setSingleStep(50)
        r1.addWidget(self.concurrent_spin)
        pmg.addLayout(r1)

        r2 = QHBoxLayout()
        lbl4 = QLabel("超时(s)")
        lbl4.setFixedWidth(50)
        r2.addWidget(lbl4)
        self.timeout_spin = QDoubleSpinBox()
        self.timeout_spin.setRange(0.1, 5.0)
        self.timeout_spin.setValue(0.6)
        self.timeout_spin.setSingleStep(0.1)
        r2.addWidget(self.timeout_spin)
        pmg.addLayout(r2)

        self.stealth_check = QCheckBox("隐蔽模式 (随机化 + 延迟)")
        self.stealth_check.setChecked(True)
        pmg.addWidget(self.stealth_check)

        scroll_layout.addWidget(param_group)
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll, 1)

        # ── 操作按钮 ──
        self.start_btn = QPushButton()
        if HAS_QTA:
            self.start_btn.setIcon(get_icon('mdi.play-circle', '#ffffff'))
            self.start_btn.setIconSize(QSize(20, 20))
        self.start_btn.setText("  开始扫描")
        self.start_btn.setStyleSheet(
            "QPushButton { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #7c4dff, stop:1 #448aff); color: white; font-size: 14px;"
            "font-weight: bold; padding: 12px; border-radius: 10px; border: none; }"
            "QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #651fff, stop:1 #2979ff); }"
            "QPushButton:disabled { background: #1a1b2e; color: #4a4d6e; }"
        )
        self.start_btn.clicked.connect(self.start_scan)
        layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton()
        if HAS_QTA:
            self.stop_btn.setIcon(get_icon('mdi.stop-circle', '#ffffff'))
            self.stop_btn.setIconSize(QSize(18, 18))
        self.stop_btn.setText("  停止扫描")
        self.stop_btn.setStyleSheet(
            "QPushButton { background-color: rgba(198,40,40,0.8); color: white;"
            "font-weight: bold; padding: 10px; border-radius: 10px; border: none; }"
            "QPushButton:hover { background-color: #e53935; }"
            "QPushButton:disabled { background: #1a1b2e; color: #4a4d6e; }"
        )
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_scan)
        layout.addWidget(self.stop_btn)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(4)
        layout.addWidget(self.progress_bar)

        # ── 导出按钮 ──
        export_layout = QHBoxLayout()
        export_layout.setSpacing(6)

        btn_json = QPushButton()
        if HAS_QTA:
            btn_json.setIcon(get_icon('mdi.code-json', '#ffab40'))
        btn_json.setText(" JSON")
        btn_json.clicked.connect(lambda: self.export_results("json"))

        btn_csv = QPushButton()
        if HAS_QTA:
            btn_csv.setIcon(get_icon('mdi.file-delimited', '#69f0ae'))
        btn_csv.setText(" CSV")
        btn_csv.clicked.connect(lambda: self.export_results("csv"))

        export_layout.addWidget(btn_json)
        export_layout.addWidget(btn_csv)
        layout.addLayout(export_layout)

    def _build_top_bar(self):
        frame = QFrame()
        frame.setStyleSheet(
            "QFrame { background-color: #131429;"
            "border: 1px solid rgba(255,255,255,0.04);"
            "border-radius: 12px; }"
        )
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(20, 8, 20, 8)

        # 展开侧边栏按钮
        self.expand_btn = QPushButton()
        if HAS_QTA:
            self.expand_btn.setIcon(get_icon('mdi.menu', '#8b8ec7'))
        else:
            self.expand_btn.setText("☰")
        self.expand_btn.setFixedSize(36, 36)
        self.expand_btn.setStyleSheet(
            "QPushButton { border-radius: 18px; border: 1px solid rgba(255,255,255,0.08); }"
            "QPushButton:hover { background-color: rgba(124,77,255,0.2); }"
        )
        self.expand_btn.setToolTip("显示/隐藏配置面板")
        self.expand_btn.clicked.connect(self._toggle_sidebar)
        layout.addWidget(self.expand_btn)
        layout.addSpacing(12)

        # 标题
        title = QLabel("LAN Port Scanner")
        title.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #f0f0f5;"
        )
        layout.addWidget(title)

        subtitle = QLabel("快速 · 隐蔽 · 准确")
        subtitle.setStyleSheet("font-size: 11px; color: #4a4d6e;")
        layout.addWidget(subtitle)
        layout.addStretch()

        # 版本标签
        ver = QLabel("v2.0")
        ver.setStyleSheet(
            "font-size: 10px; color: #4a4d6e; padding: 2px 8px;"
            "border: 1px solid rgba(255,255,255,0.06); border-radius: 4px;"
        )
        layout.addWidget(ver)

        return frame

    def _build_stats_row(self):
        layout = QHBoxLayout()
        layout.setSpacing(12)

        self.stat_hosts = StatCard("活跃主机", "mdi.monitor-dashboard", "#7c4dff")
        self.stat_ports = StatCard("开放端口", "mdi.lan-connect", "#448aff")
        self.stat_time = StatCard("扫描耗时", "mdi.timer-outline", "#ffab40")

        layout.addWidget(self.stat_hosts)
        layout.addWidget(self.stat_ports)
        layout.addWidget(self.stat_time)

        # 圆形进度环卡片
        progress_card = QFrame()
        progress_card.setFixedHeight(90)
        progress_card.setMinimumWidth(130)
        progress_card.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        progress_card.setStyleSheet("""
            QFrame {
                background-color: #1a1b2e;
                border: 1px solid rgba(255,255,255,0.06);
                border-radius: 12px;
            }
        """)
        pc_layout = QHBoxLayout(progress_card)
        pc_layout.setContentsMargins(12, 8, 12, 8)

        self.circular_progress = CircularProgress(size=60, line_width=4)
        pc_layout.addWidget(self.circular_progress, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(progress_card)

        return layout

    def _build_table_area(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 搜索/筛选栏
        filter_row = QHBoxLayout()
        filter_row.setSpacing(8)

        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("搜索 IP / 端口 / 服务...")
        if HAS_QTA:
            self.filter_input.addAction(
                get_icon('mdi.magnify', '#6c6f94'),
                QLineEdit.ActionPosition.LeadingPosition
            )
        self.filter_input.setStyleSheet(
            "QLineEdit { padding-left: 32px; }"
        )
        self.filter_input.textChanged.connect(self._filter_table)
        filter_row.addWidget(self.filter_input)

        # 排序下拉
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["默认排序", "IP 升序", "IP 降序", "端口升序", "端口降序"])
        self.sort_combo.setFixedWidth(120)
        self.sort_combo.currentIndexChanged.connect(self._sort_table)
        filter_row.addWidget(self.sort_combo)

        layout.addLayout(filter_row)

        # 结果表格
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["IP 地址", "端口", "状态", "服务", "Banner"]
        )
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setSortingEnabled(False)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(34)

        layout.addWidget(self.table, 1)
        return container

    def _build_charts_area(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # 端口分布饼图
        pie_frame = QFrame()
        pie_frame.setStyleSheet(
            "QFrame { background-color: #111225;"
            "border: 1px solid rgba(255,255,255,0.06);"
            "border-radius: 10px; }"
        )
        pie_layout = QVBoxLayout(pie_frame)
        pie_layout.setContentsMargins(12, 8, 12, 8)

        pie_title = QLabel("端口分布")
        pie_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #8b8ec7;")
        pie_layout.addWidget(pie_title)

        self.pie_chart = SimplePieChart()
        pie_layout.addWidget(self.pie_chart, 1)
        layout.addWidget(pie_frame, 1)

        # 服务类型柱状图
        bar_frame = QFrame()
        bar_frame.setStyleSheet(
            "QFrame { background-color: #111225;"
            "border: 1px solid rgba(255,255,255,0.06);"
            "border-radius: 10px; }"
        )
        bar_layout = QVBoxLayout(bar_frame)
        bar_layout.setContentsMargins(12, 8, 12, 8)

        bar_title = QLabel("服务类型")
        bar_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #8b8ec7;")
        bar_layout.addWidget(bar_title)

        self.bar_chart = SimpleBarChart()
        bar_layout.addWidget(self.bar_chart, 1)
        layout.addWidget(bar_frame, 1)

        return container

    def _build_log_area(self):
        frame = QFrame()
        frame.setStyleSheet(
            "QFrame { background-color: #111225;"
            "border: 1px solid rgba(255,255,255,0.06);"
            "border-radius: 10px; }"
        )
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(4)

        header = QHBoxLayout()
        title = QLabel("扫描日志")
        title.setStyleSheet("font-size: 12px; font-weight: bold; color: #8b8ec7;")
        header.addWidget(title)
        header.addStretch()

        clear_btn = QPushButton("清空")
        clear_btn.setFixedSize(50, 24)
        clear_btn.setStyleSheet(
            "QPushButton { font-size: 10px; padding: 2px 8px; border-radius: 4px; }"
        )
        clear_btn.clicked.connect(lambda: self.log_text.clear())
        header.addWidget(clear_btn)
        layout.addLayout(header)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(120)
        layout.addWidget(self.log_text)

        frame.setMaximumHeight(165)
        return frame

    # ─── 交互逻辑 ─────────────────────────────────────────

    def _toggle_sidebar(self):
        self.sidebar.toggle()
        if HAS_QTA:
            if self.sidebar.is_expanded:
                self.toggle_btn.setIcon(get_icon('mdi.chevron-left', '#8b8ec7'))
            else:
                self.toggle_btn.setIcon(get_icon('mdi.chevron-right', '#8b8ec7'))

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
        color = '#6c6f94'
        if '错误' in msg or 'error' in msg.lower():
            color = '#ff5252'
        elif '完成' in msg:
            color = '#69f0ae'
        elif '发现' in msg:
            color = '#448aff'
        self.log_text.append(
            f'<span style="color:#4a4d6e">[{ts}]</span> '
            f'<span style="color:{color}">{msg}</span>'
        )

    def _filter_table(self, text):
        text = text.lower()
        for row in range(self.table.rowCount()):
            show = False
            if not text:
                show = True
            else:
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item and text in item.text().lower():
                        show = True
                        break
            self.table.setRowHidden(row, not show)

    def _sort_table(self, index):
        if index == 0:
            return
        col = 0 if index in (1, 2) else 1
        order = Qt.SortOrder.AscendingOrder if index in (1, 3) else Qt.SortOrder.DescendingOrder
        self.table.sortItems(col, order)

    def _show_context_menu(self, pos):
        row = self.table.rowAt(pos.y())
        if row < 0:
            return

        menu = QMenu(self)

        # 复制 IP
        ip_item = self.table.item(row, 0)
        port_item = self.table.item(row, 1)
        svc_item = self.table.item(row, 3)

        ip = ip_item.text() if ip_item else ""
        port = port_item.text() if port_item else ""
        service = svc_item.text() if svc_item else ""

        copy_ip = menu.addAction("复制 IP 地址")
        if HAS_QTA:
            copy_ip.setIcon(get_icon('mdi.content-copy', '#c0c3e0'))

        copy_row = menu.addAction("复制整行")
        if HAS_QTA:
            copy_row.setIcon(get_icon('mdi.table-row', '#c0c3e0'))

        menu.addSeparator()

        # HTTP 端口可以在浏览器打开
        open_browser = None
        if port and int(port) in (80, 443, 8080, 8443, 8000, 8008, 8888, 3000):
            scheme = "https" if int(port) in (443, 8443) else "http"
            open_browser = menu.addAction(f"在浏览器中打开")
            if HAS_QTA:
                open_browser.setIcon(get_icon('mdi.open-in-new', '#448aff'))

        action = menu.exec(self.table.viewport().mapToGlobal(pos))

        if action == copy_ip:
            QApplication.clipboard().setText(ip)
        elif action == copy_row:
            row_data = []
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                row_data.append(item.text() if item else "")
            QApplication.clipboard().setText("\t".join(row_data))
        elif open_browser and action == open_browser:
            scheme = "https" if int(port) in (443, 8443) else "http"
            url = f"{scheme}://{ip}:{port}"
            webbrowser.open(url)

    def _update_charts(self):
        self.pie_chart.set_data(
            dict(self._category_counts),
            SERVICE_CATEGORY_COLORS
        )
        self.bar_chart.set_data(
            dict(self._category_counts),
            SERVICE_CATEGORY_COLORS
        )

    # ─── 扫描逻辑 ─────────────────────────────────────────

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

        # 重置状态
        self.table.setRowCount(0)
        self.log_text.clear()
        self.total_open = 0
        self.total_hosts_found = set()
        self.scan_results = {}
        self._category_counts = defaultdict(int)
        self._scan_progress = 0
        self.scan_start_time = datetime.now()

        self.stat_hosts.set_value("0")
        self.stat_ports.set_value("0")
        self.stat_time.set_value("0.0s")
        self.circular_progress.set_value(0)
        self._update_charts()

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)

        # 扫描时自动收起侧边栏
        self.sidebar.collapse()

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
        self.scan_thread.progress_pct.connect(self._on_progress_pct)
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
            self.stat_time.set_value(f"{elapsed:.1f}s")

    def _on_progress(self, msg: str):
        self.status_label.setText(msg)
        self._log(msg)

    def _on_progress_pct(self, pct: int):
        self._scan_progress = pct
        self.progress_bar.setValue(pct)
        self.circular_progress.set_value(pct)

    def _on_result_found(self, result):
        self.total_open += 1
        self.total_hosts_found.add(result.ip)
        self.stat_ports.set_value(str(self.total_open))
        self.stat_hosts.set_value(str(len(self.total_hosts_found)))

        # 分类统计
        cat = classify_port(result.port)
        self._category_counts[cat] += 1

        # 更新图表 (每 5 个结果更新一次，避免频繁重绘)
        if self.total_open % 5 == 0 or self.total_open <= 5:
            self._update_charts()

        # 添加表格行
        row = self.table.rowCount()
        self.table.insertRow(row)

        ip_item = QTableWidgetItem(result.ip)
        ip_item.setForeground(QColor("#82b1ff"))
        self.table.setItem(row, 0, ip_item)

        port_item = QTableWidgetItem(str(result.port))
        port_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        port_item.setData(Qt.ItemDataRole.UserRole, result.port)
        self.table.setItem(row, 1, port_item)

        # 状态列 - 绿色圆点 + 文字
        state_item = QTableWidgetItem("● open")
        state_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        state_item.setForeground(QColor("#69f0ae"))
        self.table.setItem(row, 2, state_item)

        # 服务列 - 带颜色
        svc_item = QTableWidgetItem(result.service)
        cat_color = SERVICE_CATEGORY_COLORS.get(cat, '#8b8ec7')
        svc_item.setForeground(QColor(cat_color))
        self.table.setItem(row, 3, svc_item)

        banner_item = QTableWidgetItem(result.banner or "")
        banner_item.setForeground(QColor("#6c6f94"))
        self.table.setItem(row, 4, banner_item)

        # 保存结果
        if result.ip not in self.scan_results:
            self.scan_results[result.ip] = []
        self.scan_results[result.ip].append(result)

    def _on_finished(self, results):
        self._scan_done()
        elapsed = (datetime.now() - self.scan_start_time).total_seconds()
        self._update_charts()
        self._log(
            f"扫描完成! 耗时 {elapsed:.1f}s，"
            f"发现 {len(self.total_hosts_found)} 个主机，"
            f"{self.total_open} 个开放端口"
        )
        self.status_label.setText(
            f"扫描完成 — {len(self.total_hosts_found)} 个主机，"
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
        self.circular_progress.set_value(100)
        if hasattr(self, '_timer'):
            self._timer.stop()

    # ─── 导出 ─────────────────────────────────────────────

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
    palette.setColor(QPalette.ColorRole.Window, QColor("#0d0e1a"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#f0f0f5"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#111225"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#151630"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#f0f0f5"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#1a1b2e"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#e0e0e0"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#7c4dff"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#232442"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#f0f0f5"))
    app.setPalette(palette)

    window = ModernScannerGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
