import sys
import sys
import time

import cv2
import json
import os
from PIL import Image
from PyQt5.QtCore import Qt, QRect
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QComboBox, QListWidget,
                             QTextEdit, QFrame, QScrollArea, QGridLayout, QLineEdit,
                             QCheckBox, QSpinBox, QDoubleSpinBox, QFileDialog,
                             QMessageBox, QSplitter, QGroupBox)
from dev_tools.rule_edit_gui import ADB
from dev_tools.rule_edit_gui.PreviewWindow import PreviewWindow
from dev_tools.rule_edit_gui.ThemeManager import ThemeManager


class ImageCanvas(QLabel):
    """自定义图片画布，支持绘制矩形选择框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("border: 1px solid #ccc;")
        self.setAlignment(Qt.AlignCenter)

        # 图片相关
        self.original_pixmap = None
        self.scaled_pixmap = None
        self.scale_factor = 1.0

        # 选择框相关
        self.red_rect = None
        self.green_rect = None
        self.drawing_red = False
        self.drawing_green = False
        self.start_point = None
        self.end_point = None
        self.mode = "normal"  # normal 或 include

        # 父窗口引用
        self.parent_window = None

    def set_parent_window(self, parent_window):
        """设置父窗口引用"""
        self.parent_window = parent_window

    def set_image(self, image_path):
        """设置显示的图片"""
        try:
            self.original_pixmap = QPixmap(image_path)
            self._scale_and_display()
            return True
        except Exception as e:
            print(f"加载图片失败: {e}")
            return False

    def _scale_and_display(self):
        """缩放并显示图片"""
        if not self.original_pixmap:
            return

        # 计算缩放比例
        canvas_size = self.size()
        img_size = self.original_pixmap.size()

        # 确保画布有足够的空间
        if canvas_size.width() <= 0 or canvas_size.height() <= 0:
            return

        scale_x = canvas_size.width() / img_size.width()
        scale_y = canvas_size.height() / img_size.height()
        self.scale_factor = min(scale_x, scale_y, 1.0)

        # 缩放图片
        scaled_size = img_size * self.scale_factor
        self.scaled_pixmap = self.original_pixmap.scaled(
            scaled_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )

        self.setPixmap(self.scaled_pixmap)

        # 如果有父窗口，重新计算现有的ROI框位置
        if self.parent_window and self.parent_window.selected_item_index is not None:
            items = self.parent_window.get_items_list()
            if self.parent_window.selected_item_index < len(items):
                item_data = items[self.parent_window.selected_item_index]
                self.parent_window.update_roi_display(item_data)

    def resizeEvent(self, event):
        """窗口大小改变事件"""
        super().resizeEvent(event)
        # 当画布大小改变时，重新缩放图片
        if self.original_pixmap:
            self._scale_and_display()

    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if not self.scaled_pixmap:
            return

        if event.button() == Qt.LeftButton:
            self.drawing_red = True
            self.start_point = event.pos()
            if self.mode == "include":
                self.green_rect = None
        elif event.button() == Qt.RightButton and self.mode != "include":
            self.drawing_green = True
            self.start_point = event.pos()

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if not self.scaled_pixmap:
            return

        # 更新坐标显示
        if self.parent_window:
            image_coords = self._canvas_to_image_coords(event.pos())
            self.parent_window.update_coord_display(image_coords)

        # 绘制矩形
        if self.drawing_red or self.drawing_green:
            self.end_point = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if not self.scaled_pixmap or not self.start_point:
            return

        end_pos = event.pos()

        if self.drawing_red:
            self.drawing_red = False
            self.red_rect = self._normalize_rect(self.start_point, end_pos)

            if self.mode == "include":
                # 在include模式下，绿框向外扩展1px
                self.green_rect = self._expand_rect(self.red_rect, 1)

            # 更新父窗口的坐标显示
            if self.parent_window:
                self.parent_window.update_red_label(self.red_rect)
                # 更新配置字段中的roiFront
                red_coords = self.get_red_coords()
                if red_coords:
                    x, y, w, h = red_coords
                    roi_str = f"{x},{y},{w},{h}"
                    self.parent_window.update_field_value("roiFront", roi_str)

                if self.mode == "include" and self.green_rect:
                    self.parent_window.update_green_label(self.green_rect)
                    # 更新配置字段中的roiBack
                    green_coords = self.get_green_coords()
                    if green_coords:
                        x, y, w, h = green_coords
                        roi_str = f"{x},{y},{w},{h}"
                        self.parent_window.update_field_value("roiBack", roi_str)

        elif self.drawing_green:
            self.drawing_green = False
            self.green_rect = self._normalize_rect(self.start_point, end_pos)

            # 更新父窗口的坐标显示
            if self.parent_window:
                self.parent_window.update_green_label(self.green_rect)
                # 更新配置字段中的roiBack
                green_coords = self.get_green_coords()
                if green_coords:
                    x, y, w, h = green_coords
                    roi_str = f"{x},{y},{w},{h}"
                    self.parent_window.update_field_value("roiBack", roi_str)

        self.start_point = None
        self.end_point = None
        self.update()

    def paintEvent(self, event):
        """绘制事件"""
        super().paintEvent(event)

        if not self.scaled_pixmap:
            return

        painter = QPainter(self)

        # 绘制现有的矩形
        if self.red_rect:
            painter.setPen(QPen(QColor("red"), 2))
            painter.drawRect(self.red_rect)

        if self.green_rect:
            painter.setPen(QPen(QColor("green"), 2))
            painter.drawRect(self.green_rect)

        # 绘制正在拖拽的矩形
        if self.start_point and self.end_point:
            if self.drawing_red:
                painter.setPen(QPen(QColor("red"), 2))
                rect = self._normalize_rect(self.start_point, self.end_point)
                painter.drawRect(rect)

                if self.mode == "include":
                    painter.setPen(QPen(QColor("green"), 2))
                    expanded_rect = self._expand_rect(rect, 1)
                    painter.drawRect(expanded_rect)

            elif self.drawing_green:
                painter.setPen(QPen(QColor("green"), 2))
                rect = self._normalize_rect(self.start_point, self.end_point)
                painter.drawRect(rect)

    def _normalize_rect(self, start, end):
        """标准化矩形（确保左上角和右下角正确）"""
        x1, y1 = start.x(), start.y()
        x2, y2 = end.x(), end.y()

        left = min(x1, x2)
        top = min(y1, y2)
        width = abs(x2 - x1)
        height = abs(y2 - y1)

        return QRect(left, top, width, height)

    def _expand_rect(self, rect, pixels):
        """扩展矩形"""
        return QRect(
            max(0, rect.x() - pixels),
            max(0, rect.y() - pixels),
            rect.width() + 2 * pixels,
            rect.height() + 2 * pixels
        )

    def _canvas_to_image_coords(self, canvas_pos):
        """将画布坐标转换为原图坐标"""
        if not self.scaled_pixmap or self.scale_factor == 0:
            return (0, 0)

        # 获取图片在画布中的偏移
        pixmap_rect = self.scaled_pixmap.rect()
        widget_rect = self.rect()

        offset_x = (widget_rect.width() - pixmap_rect.width()) // 2
        offset_y = (widget_rect.height() - pixmap_rect.height()) // 2

        # 计算相对于图片的坐标
        img_x = canvas_pos.x() - offset_x
        img_y = canvas_pos.y() - offset_y

        # 转换为原图坐标
        orig_x = int(img_x / self.scale_factor)
        orig_y = int(img_y / self.scale_factor)

        return (orig_x, orig_y)

    def get_red_coords(self):
        """获取红色框的原图坐标"""
        if not self.red_rect:
            return None
        return self._rect_to_image_coords(self.red_rect)

    def get_green_coords(self):
        """获取绿色框的原图坐标"""
        if not self.green_rect:
            return None
        return self._rect_to_image_coords(self.green_rect)

    def _rect_to_image_coords(self, rect):
        """将画布矩形转换为原图坐标"""
        if not rect or self.scale_factor == 0:
            return None

        # 获取图片在画布中的偏移
        if not self.scaled_pixmap:
            return None

        pixmap_rect = self.scaled_pixmap.rect()
        widget_rect = self.rect()

        offset_x = (widget_rect.width() - pixmap_rect.width()) // 2
        offset_y = (widget_rect.height() - pixmap_rect.height()) // 2

        # 转换为原图坐标
        x = int((rect.x() - offset_x) / self.scale_factor)
        y = int((rect.y() - offset_y) / self.scale_factor)
        w = int(rect.width() / self.scale_factor)
        h = int(rect.height() / self.scale_factor)

        return (x, y, w, h)

    def clear_selections(self):
        """清除所有选择框"""
        self.red_rect = None
        self.green_rect = None
        self.update()

    def set_mode(self, mode):
        """设置模式"""
        self.mode = mode
        if mode == "include":
            self.green_rect = None
        self.update()

class CustomWindowTitleBar(QFrame):
    """自定义窗口标题栏"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setFixedHeight(35)  # 增加高度以适应更美观的设计
        self.setObjectName("titleBar")  # 设置对象名称以便样式定位

        # 创建布局
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 0, 10, 0)
        self.layout.setSpacing(8)

        # 应用图标（可选）
        # self.app_icon = QLabel(self)
        # self.app_icon.setFixedSize(20, 20)
        # self.app_icon.setAlignment(Qt.AlignCenter)
        # self.app_icon.setText("📸")  # 使用emoji图标，可以后续替换为实际图标
        # self.layout.addWidget(self.app_icon)

        # 标题标签
        self.title_label = QLabel("Rule Editor", self)
        self.title_label.setObjectName("titleLabel")
        self.layout.addWidget(self.title_label)

        self.layout.addStretch()

        # 窗口控制按钮容器
        self.button_container = QWidget()
        self.button_layout = QHBoxLayout(self.button_container)
        self.button_layout.setContentsMargins(0, 0, 0, 0)
        self.button_layout.setSpacing(1)

        # 最小化按钮
        self.min_button = QPushButton("🗕", self)
        self.min_button.setFixedSize(32, 26)
        self.min_button.setObjectName("minButton")
        self.min_button.clicked.connect(self.on_minimize)
        self.min_button.setToolTip("最小化")
        self.button_layout.addWidget(self.min_button)

        # 最大化/还原按钮
        self.max_button = QPushButton("🗖", self)
        self.max_button.setFixedSize(32, 26)
        self.max_button.setObjectName("maxButton")
        self.max_button.clicked.connect(self.on_maximize)
        self.max_button.setToolTip("最大化")
        self.button_layout.addWidget(self.max_button)

        # 关闭按钮
        self.close_button = QPushButton("🗙", self)
        self.close_button.setFixedSize(32, 26)
        self.close_button.setObjectName("closeButton")
        self.close_button.clicked.connect(self.on_close)
        self.close_button.setToolTip("关闭")
        self.button_layout.addWidget(self.close_button)

        self.layout.addWidget(self.button_container)

        # 拖动相关
        self.dragging = False
        self.drag_start_pos = None

        # 记录窗口状态
        self.is_maximized = False

    def apply_theme(self, theme_data):
        """应用主题样式"""
        # 获取主题颜色
        title_bg = theme_data.get('title_bg', '#2b2b2b')
        title_fg = theme_data.get('title_fg', '#ffffff')
        button_bg = theme_data.get('button_bg', '#404040')
        button_hover_bg = theme_data.get('button_hover_bg', '#505050')
        close_hover_bg = theme_data.get('close_hover_bg', '#e81123')

        # 设置标题栏样式
        self.setStyleSheet(f"""
            QFrame#titleBar {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 {title_bg}, stop: 1 {self._darken_color(title_bg, 0.1)});
                border-bottom: 1px solid {self._darken_color(title_bg, 0.2)};
                color: {title_fg};
            }}
            
            QLabel#titleLabel {{
                color: {title_fg};
                font-weight: bold;
                font-size: 13px;
                padding-left: 5px;
            }}
            
            QPushButton#minButton, QPushButton#maxButton {{
                background-color: transparent;
                border: none;
                color: {title_fg};
                font-size: 12px;
                font-family: "Segoe MDL2 Assets", "Arial";
                border-radius: 0px;
            }}
            
            QPushButton#minButton:hover, QPushButton#maxButton:hover {{
                background-color: {button_hover_bg};
            }}
            
            QPushButton#closeButton {{
                background-color: transparent;
                border: none;
                color: {title_fg};
                font-size: 12px;
                font-family: "Segoe MDL2 Assets", "Arial";
                border-radius: 0px;
            }}
            
            QPushButton#closeButton:hover {{
                background-color: {close_hover_bg};
                color: white;
            }}
            
            QPushButton:pressed {{
                background-color: {self._darken_color(button_hover_bg, 0.2)};
            }}
        """)

    def _darken_color(self, color_hex, factor):
        """使颜色变暗"""
        try:
            color_hex = color_hex.lstrip('#')
            r = int(color_hex[0:2], 16)
            g = int(color_hex[2:4], 16)
            b = int(color_hex[4:6], 16)

            r = max(0, int(r * (1 - factor)))
            g = max(0, int(g * (1 - factor)))
            b = max(0, int(b * (1 - factor)))

            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return color_hex

    def on_minimize(self):
        """最小化窗口"""
        if self.parent_window:
            self.parent_window.showMinimized()

    def on_maximize(self):
        """最大化/还原窗口"""
        if self.parent_window:
            if self.is_maximized:
                self.parent_window.showNormal()
                self.max_button.setText("🗖")
                self.max_button.setToolTip("最大化")
                self.is_maximized = False
            else:
                self.parent_window.showMaximized()
                self.max_button.setText("🗗")
                self.max_button.setToolTip("还原")
                self.is_maximized = True

    def on_close(self):
        """关闭窗口"""
        if self.parent_window:
            self.parent_window.close()

    def set_title(self, title):
        """设置标题"""
        self.title_label.setText(title)

    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_start_pos = event.globalPos() - self.parent_window.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self.dragging and event.buttons() & Qt.LeftButton and not self.is_maximized:
            new_pos = event.globalPos() - self.drag_start_pos
            self.parent_window.move(new_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            event.accept()

    def mouseDoubleClickEvent(self, event):
        """双击标题栏最大化/还原"""
        if event.button() == Qt.LeftButton:
            self.on_maximize()
            event.accept()

class RuleEditGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        # self.setWindowTitle("截图工具")
        # 隐藏默认标题栏
        self.setWindowFlags(Qt.FramelessWindowHint)
        # 设置自定义标题栏
        self.title_bar = CustomWindowTitleBar(self)
        self.setMenuWidget(self.title_bar)

        self.setGeometry(100, 100, 1600, 900)
        self.setMinimumSize(1200, 900)
        self.helper_texts = {
            "imageRule": "红色的框(Roi front)表示这一个项要匹配的图片，绿色的框(Roi back)表示匹配的范围。",
            "ocrRule": "红色的框(Roi front = roi)表示这一个项OCR识别的默认范围，绿色的框(Roi Back = area)表示如果识别到会点击的的范围。",
            "clickRule": "红色的框(Roi front)表示这一个项点击的默认范围，绿色的框(Roi back)表示备用的范围。",
            "swipeRule": "红色的框(Roi front)表示滑动的起始范围，绿色的框(Roi back)表示滑动的停止范围。",
            "longClickRule": "红色的框(Roi front)表示这一个项点击的默认范围，绿色的框(Roi back)表示备用的范围。",
            "listRule": "红色的框(Roi front)表示这一个项要匹配的图片，绿色的框(Roi back)表示匹配的范围。",
        }

        # 数据相关
        self.current_rule_type = None
        self.current_json_data = []
        self.current_json_file = None
        self.selected_item_index = None
        self.image_path = None

        # 主题管理器
        self.theme_manager = ThemeManager()

        # 配置字段缓存
        self.config_widgets = {}

        self._build_ui()
        self.apply_theme()



    def _build_ui(self):
        """构建用户界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        # 顶部工具栏
        self._create_toolbar(main_layout)

        # 主要内容区域
        self._create_main_area(main_layout)

        # 底部状态栏
        self._create_statusbar(main_layout)

    def _create_toolbar(self, parent_layout):
        """创建顶部工具栏"""
        toolbar = QHBoxLayout()

        # 图片操作按钮
        select_image_btn = QPushButton("选择图片")
        select_image_btn.clicked.connect(self.select_image)
        toolbar.addWidget(select_image_btn)

        clear_btn = QPushButton("清除所有选择")
        clear_btn.clicked.connect(self.clear_all)
        toolbar.addWidget(clear_btn)

        toolbar.addSpacing(20)

        # 主题选择
        toolbar.addWidget(QLabel("主题:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(self.theme_manager.get_theme_names())
        self.theme_combo.setCurrentText(self.theme_manager.current_theme)
        self.theme_combo.currentTextChanged.connect(self.on_theme_change)
        toolbar.addWidget(self.theme_combo)

        toolbar.addSpacing(20)

        # 灰度图选择
        self.grayscale_checkbox = QCheckBox("灰度图")
        self.grayscale_checkbox.stateChanged.connect(self.on_grayscale_change)
        toolbar.addWidget(self.grayscale_checkbox)

        toolbar.addSpacing(20)

        # 模式选择
        toolbar.addWidget(QLabel("模式:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["normal", "include"])
        self.mode_combo.currentTextChanged.connect(self.on_mode_change)
        toolbar.addWidget(self.mode_combo)

        toolbar.addSpacing(20)

        # 坐标显示
        self.red_label = QLabel("红色框: 未选择")
        self.red_label.setStyleSheet("color: red;")
        toolbar.addWidget(self.red_label)

        self.green_label = QLabel("绿色框: 未选择")
        self.green_label.setStyleSheet("color: green;")
        toolbar.addWidget(self.green_label)

        toolbar.addStretch()

        parent_layout.addLayout(toolbar)

    def _create_main_area(self, parent_layout):
        """创建主要内容区域"""
        splitter = QSplitter(Qt.Horizontal)

        # 左侧区域
        left_widget = self._create_left_area()
        splitter.addWidget(left_widget)

        # 右侧区域
        right_widget = self._create_right_area()
        splitter.addWidget(right_widget)

        # 设置分割比例
        splitter.setSizes([1000, 400])

        parent_layout.addWidget(splitter)

    def get_screenshot(self):
        """通过adb获取截图"""
        adb_address = self.adb_input.text().strip()
        if not adb_address:
            QMessageBox.warning(self, "警告", "请填写ADB地址")
            return

        try:
            # 连接ADB设备
            ADB.set_adb_target(adb_address)
            connect_num = 0
            while not ADB.check_adb_device():
                connect_num += 1
                if connect_num > 3:
                    raise Exception("连接ADB设备失败，请检查地址和模拟器状态")
                ADB.adb_reconnect()
                time.sleep(2)

            # 获取截图
            img = ADB.adb_screenshot()
            # 保存到临时路径
            path='./temp_path'
            if not os.path.exists(path):
                os.makedirs(path)
            # 文件名为年月日时分秒
            date_time_str=time.strftime("%Y-%m-%d %H-%M-%S")
            print(date_time_str)
            file_name=f"{date_time_str}.png"
            temp_path = os.path.join(path, file_name)
            cv2.imwrite(temp_path, img)
            self.image_path = temp_path
            if not self.canvas.set_image(temp_path):
                QMessageBox.critical(self, "错误", "加载截图失败")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"获取截图失败: {str(e)}")
    def _create_left_area(self):
        """创建左侧区域"""
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # 图片画布容器
        canvas_container = QFrame()
        canvas_container.setFrameStyle(QFrame.StyledPanel)
        canvas_layout = QVBoxLayout(canvas_container)
        # 在画布上方增加一个toolbar
        toolbar_layout = QHBoxLayout()
        canvas_layout.addLayout(toolbar_layout)

        # 增加一个adb地址的输入框
        self.adb_input = QLineEdit()
        self.adb_input.setPlaceholderText("ADB地址 (可选)")
        self.adb_input.setText("127.0.0.1:16384")
        self.adb_input.setMaximumWidth(200)
        toolbar_layout.addWidget(self.adb_input)

        # 增加一个获取截图按钮
        get_screenshot_btn = QPushButton("获取模拟器截图")
        get_screenshot_btn.clicked.connect(self.get_screenshot)
        toolbar_layout.addWidget(get_screenshot_btn)
        toolbar_layout.addSpacing(20)

        save_btn = QPushButton("保存框选截图")
        save_btn.clicked.connect(self.save_roi)
        toolbar_layout.addWidget(save_btn)
        # 填充右侧
        toolbar_layout.addStretch()


        # 图片画布
        self.canvas = ImageCanvas()
        self.canvas.set_parent_window(self)
        canvas_layout.addWidget(self.canvas)
        canvas_container.setMinimumSize(800, 600)

        # 保存按钮

        # canvas_layout.addWidget(save_btn, alignment=Qt.AlignRight)

        left_layout.addWidget(canvas_container)

        # 底部区域
        bottom_splitter = QSplitter(Qt.Horizontal)

        # 规则类型选择
        rule_group = QGroupBox("规则类型")
        rule_layout = QVBoxLayout(rule_group)

        self.rule_type_list = QListWidget()
        self.rule_type_list.addItems([
            "imageRule", "ocrRule", "clickRule",
            "swipeRule", "longClickRule", "listRule"
        ])
        self.rule_type_list.itemClicked.connect(self.on_rule_type_select)
        rule_layout.addWidget(self.rule_type_list)
        bottom_splitter.addWidget(rule_group)

        # 提示信息区域
        help_group = QGroupBox("提示信息")
        help_layout = QVBoxLayout(help_group)

        self.help_text = QTextEdit()
        self.help_text.setReadOnly(True)
        self.help_text.setMaximumHeight(150)
        help_layout.addWidget(self.help_text)

        bottom_splitter.addWidget(help_group)
        bottom_splitter.setSizes([200, 600])

        left_layout.addWidget(bottom_splitter)

        # 默认选择第一个规则类型
        # self.update_help_text("请先选择规则类型，然后选择或创建JSON文件")
        self.on_rule_type_select(self.rule_type_list.item(0))
        self.rule_type_list.setCurrentRow(0)
        return left_widget

    def _create_right_area(self):
        """创建右侧区域"""
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # JSON文件选择区域
        json_group = QGroupBox("JSON文件")
        json_layout = QVBoxLayout(json_group)

        json_btn_layout = QHBoxLayout()
        select_json_btn = QPushButton("选择JSON文件")
        select_json_btn.clicked.connect(self.select_json_file)
        json_btn_layout.addWidget(select_json_btn)

        new_json_btn = QPushButton("新建JSON文件")
        new_json_btn.clicked.connect(self.create_new_json)
        json_btn_layout.addWidget(new_json_btn)

        json_layout.addLayout(json_btn_layout)

        self.json_file_label = QLabel("未选择文件")
        self.json_file_label.setStyleSheet("color: gray;")
        json_layout.addWidget(self.json_file_label)

        right_layout.addWidget(json_group)

        # Item列表区域
        item_group = QGroupBox("Item列表")
        item_layout = QVBoxLayout(item_group)

        item_btn_layout = QHBoxLayout()
        add_item_btn = QPushButton("新增")
        add_item_btn.clicked.connect(self.add_item)
        item_btn_layout.addWidget(add_item_btn)

        delete_item_btn = QPushButton("删除")
        delete_item_btn.clicked.connect(self.delete_item)
        item_btn_layout.addWidget(delete_item_btn)

        item_layout.addLayout(item_btn_layout)

        self.item_list = QListWidget()
        self.item_list.itemClicked.connect(self.on_item_select)
        item_layout.addWidget(self.item_list)

        right_layout.addWidget(item_group)

        # 预览截图窗口
        preview_group = QGroupBox("截图预览")
        preview_layout = QVBoxLayout(preview_group)

        self.preview_window = PreviewWindow()
        self.preview_window.set_parent_window(self)
        preview_layout.addWidget(self.preview_window)

        right_layout.addWidget(preview_group)

        # 配置区域
        config_group = QGroupBox("配置")
        config_layout = QVBoxLayout(config_group)


        # 滚动区域
        self.config_scroll = QScrollArea()
        self.config_scroll.setWidgetResizable(True)
        self.config_widget = QWidget()
        self.config_layout = QVBoxLayout(self.config_widget)
        self.config_scroll.setWidget(self.config_widget)

        config_layout.addWidget(self.config_scroll)

        right_layout.addWidget(config_group)
        # 设置最小高度，防止过小
        config_group.setMinimumHeight(280)

        # 保存JSON按钮
        save_json_btn = QPushButton("保存JSON")
        save_json_btn.clicked.connect(self.save_json)
        right_layout.addWidget(save_json_btn)

        return right_widget

    def _create_statusbar(self, parent_layout):
        """创建底部状态栏"""
        self.coord_label = QLabel("坐标: -,-")
        parent_layout.addWidget(self.coord_label, alignment=Qt.AlignLeft)

    def apply_theme(self, theme_name: str = None):
        """应用主题"""
        if theme_name:
            self.theme_manager.set_theme(theme_name)

        theme = self.theme_manager.get_theme()

        # 应用自定义标题栏主题
        if hasattr(self, 'title_bar'):
            self.title_bar.apply_theme(theme)

        # 应用样式表
        style_sheet = f"""
        QMainWindow {{
            background-color: {theme['bg']};
            color: {theme['fg']};
        }}
        QWidget {{
            background-color: {theme['frame_bg']};
            color: {theme['label_fg']};
        }}
        QPushButton {{
            background-color: {theme['button_bg']};
            color: {theme['button_fg']};
            border: {theme['borderwidth']}px solid #ccc;
            padding: 5px;
            border-radius: 3px;
        }}
        QPushButton:hover {{
            background-color: {theme['button_active_bg']};
        }}
        QLineEdit, QTextEdit, QComboBox {{
            background-color: {theme['entry_bg']};
            color: {theme['entry_fg']};
            border: {theme['borderwidth']}px solid #ccc;
            padding: 3px;
        }}
        QListWidget {{
            background-color: {theme['listbox_bg']};
            color: {theme['listbox_fg']};
            border: {theme['borderwidth']}px solid #ccc;
        }}
        QListWidget::item:selected {{
            background-color: {theme['select_bg']};
            color: {theme['select_fg']};
        }}
        QGroupBox {{
            font-weight: bold;
            border: 2px solid #ccc;
            border-radius: 5px;
            margin-top: 1ex;
            padding-top: 10px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }}
        QWidget {{
            background-color: {theme['frame_bg']};
        }}
        """
        self.setStyleSheet(style_sheet)

    def on_theme_change(self, theme_name):
        """主题改变事件"""
        self.apply_theme(theme_name)

    def on_mode_change(self, mode):
        """模式改变事件"""
        self.canvas.set_mode(mode)
        self.clear_all()

    def on_grayscale_change(self, state):
        """灰度图选择改变事件"""
        is_grayscale = state == Qt.Checked

        # 更新预览窗口的灰度模式
        if hasattr(self, 'preview_window'):
            self.preview_window.set_grayscale_mode(is_grayscale)
            # 如果当前有选中的红色框，更新预览
            red_coords = self.canvas.get_red_coords()
            if red_coords and self.image_path:
                self.preview_window.update_preview(self.image_path, red_coords)

        # 如果需要，可以在这里添加主画布的灰度显示功能
        # 但通常主画布保持原色，只在预览和导出时应用灰度

    def update_coord_display(self, coords):
        """更新坐标显示"""
        x, y = coords
        self.coord_label.setText(f"坐标: {x},{y}")

    def update_red_label(self, rect):
        """更新红色框标签"""
        if rect:
            coords = self.canvas._rect_to_image_coords(rect)
            if coords:
                x, y, w, h = coords
                self.red_label.setText(f"红色框: {x},{y},{w},{h}")
                # 更新预览窗口
                if hasattr(self, 'preview_window') and self.image_path:
                    self.preview_window.update_preview(self.image_path, coords)
        else:
            self.red_label.setText("红色框: 未选择")
            # 清除预览
            if hasattr(self, 'preview_window'):
                self.preview_window.clear_preview()

    def update_green_label(self, rect):
        """更新绿色框标签"""
        if rect:
            coords = self.canvas._rect_to_image_coords(rect)
            if coords:
                x, y, w, h = coords
                self.green_label.setText(f"绿色框: {x},{y},{w},{h}")
        else:
            self.green_label.setText("绿色框: 未选择")

    def update_help_text(self, text):
        """更新提示信息"""
        self.help_text.setPlainText(text)

    def select_image(self):
        """选择图片"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图片", "",
            "图片文件 (*.png *.jpg *.jpeg *.bmp *.gif)"
        )

        if file_path:
            self.image_path = file_path
            if self.canvas.set_image(file_path):
                self.clear_all()

    def clear_all(self):
        """清除所有选择"""
        self.canvas.clear_selections()
        self.update_red_label(None)
        self.update_green_label(None)

    def on_rule_type_select(self, item):
        """规则类型选择事件"""
        self.current_rule_type = item.text()
        self.update_help_text(f"已选择规则类型: {self.current_rule_type}\n\n"
                              f"{self.helper_texts.get(self.current_rule_type, '')}\n\n"
                              f"请选择或创建JSON文件")

    def select_json_file(self):
        """选择JSON文件"""
        if not self.current_rule_type:
            QMessageBox.warning(self, "警告", "请先选择规则类型")
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择JSON文件", "", "JSON文件 (*.json)"
        )

        if file_path:
            self.load_json_file(file_path)

    def create_new_json(self):
        """创建新的JSON文件"""
        if not self.current_rule_type:
            QMessageBox.warning(self, "警告", "请先选择规则类型")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "创建新JSON文件", "", "JSON文件 (*.json)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump([], f, indent=2, ensure_ascii=False)
                self.load_json_file(file_path)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"创建文件失败: {str(e)}")

    def load_json_file(self, file_path):
        """加载JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 验证数据格式
            if isinstance(data, list):
                self.current_json_data = data
            elif isinstance(data, dict) and "list" in data:
                # 处理listRule格式
                self.current_json_data = data
            else:
                self.current_json_data = []

            self.current_json_file = file_path
            self.selected_item_index = None

            # 更新界面
            self.json_file_label.setText(os.path.basename(file_path))
            self.json_file_label.setStyleSheet("color: black;")
            self.update_item_list()
            self.clear_config_fields()

            items_count = len(self.get_items_list())
            self.update_help_text(
                f"已加载文件: {os.path.basename(file_path)}\n"
                f"包含 {items_count} 个项目\n\n选择项目可编辑其属性。"
            )

        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载文件失败: {str(e)}")

    def get_items_list(self):
        """获取items列表"""
        if self.current_rule_type == "listRule" and isinstance(self.current_json_data, dict):
            return self.current_json_data.get("list", [])
        else:
            return self.current_json_data if isinstance(self.current_json_data, list) else []

    def update_item_list(self):
        """更新ItemName列表"""
        self.item_list.clear()
        items = self.get_items_list()
        for item in items:
            item_name = item.get("itemName", "[无名称]")
            self.item_list.addItem(item_name)

    def clear_config_fields(self):
        """清空配置区域"""
        # 清除所有子控件
        while self.config_layout.count():
            child = self.config_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.config_widgets.clear()

    def on_item_select(self, item):
        """选中Item时的处理"""
        row = self.item_list.row(item)
        self.selected_item_index = row

        # 更新配置区域
        items = self.get_items_list()
        if row < len(items):
            item_data = items[row]
            self.show_item_config(item_data)
            # 更新ROI显示
            self.update_roi_display(item_data)

    def update_roi_display(self, item_data):
        """更新ROI框显示"""
        self.canvas.red_rect = None
        self.canvas.green_rect = None

        # 显示红色框
        if "roiFront" in item_data and item_data["roiFront"]:
            roi_front = item_data["roiFront"]
            if isinstance(roi_front, str) and roi_front:
                parts = roi_front.split(',')
                if len(parts) == 4:
                    try:
                        x, y, w, h = map(int, parts)
                        # 转换为画布坐标
                        x_scaled = int(x * self.canvas.scale_factor)
                        y_scaled = int(y * self.canvas.scale_factor)
                        w_scaled = int(w * self.canvas.scale_factor)
                        h_scaled = int(h * self.canvas.scale_factor)

                        # 计算画布偏移
                        if self.canvas.scaled_pixmap:
                            pixmap_rect = self.canvas.scaled_pixmap.rect()
                            widget_rect = self.canvas.rect()
                            offset_x = (widget_rect.width() - pixmap_rect.width()) // 2
                            offset_y = (widget_rect.height() - pixmap_rect.height()) // 2

                            x_scaled += offset_x
                            y_scaled += offset_y

                            self.canvas.red_rect = QRect(x_scaled, y_scaled, w_scaled, h_scaled)
                            self.update_red_label(self.canvas.red_rect)
                    except ValueError:
                        pass

        # 显示绿色框
        if "roiBack" in item_data and item_data["roiBack"]:
            roi_back = item_data["roiBack"]
            if isinstance(roi_back, str) and roi_back:
                parts = roi_back.split(',')
                if len(parts) == 4:
                    try:
                        x, y, w, h = map(int, parts)
                        # 转换为画布坐标
                        x_scaled = int(x * self.canvas.scale_factor)
                        y_scaled = int(y * self.canvas.scale_factor)
                        w_scaled = int(w * self.canvas.scale_factor)
                        h_scaled = int(h * self.canvas.scale_factor)

                        # 计算画布偏移
                        if self.canvas.scaled_pixmap:
                            pixmap_rect = self.canvas.scaled_pixmap.rect()
                            widget_rect = self.canvas.rect()
                            offset_x = (widget_rect.width() - pixmap_rect.width()) // 2
                            offset_y = (widget_rect.height() - pixmap_rect.height()) // 2

                            x_scaled += offset_x
                            y_scaled += offset_y

                            self.canvas.green_rect = QRect(x_scaled, y_scaled, w_scaled, h_scaled)
                            self.update_green_label(self.canvas.green_rect)
                    except ValueError:
                        pass

        # 如果没有ROI信息，清除标签显示
        if not self.canvas.red_rect:
            self.update_red_label(None)
        if not self.canvas.green_rect:
            self.update_green_label(None)

        self.canvas.update()

    def show_item_config(self, item_data):
        """显示项目配置"""
        self.clear_config_fields()

        # 创建配置表单
        form_layout = QGridLayout()
        row = 0

        for key, value in item_data.items():
            label = QLabel(f"{key}:")
            form_layout.addWidget(label, row, 0)

            # 根据值类型创建不同的控件
            if isinstance(value, bool):
                widget = QCheckBox()
                widget.setChecked(value)
                widget.stateChanged.connect(
                    lambda state, k=key: self.update_field_value(k, state == Qt.Checked)
                )
            elif key == "threshold":
                # threshold字段使用文本框
                widget = QLineEdit()
                widget.setText(str(value))
                widget.textChanged.connect(
                    lambda text, k=key: self.update_field_value(k, text)
                )
            elif isinstance(value, int):
                widget = QSpinBox()
                widget.setRange(-999999, 999999)
                widget.setValue(value)
                widget.valueChanged.connect(
                    lambda v, k=key: self.update_field_value(k, v)
                )
            elif isinstance(value, float):
                widget = QDoubleSpinBox()
                widget.setRange(-999999.0, 999999.0)
                widget.setValue(value)
                widget.valueChanged.connect(
                    lambda v, k=key: self.update_field_value(k, v)
                )
            else:
                widget = QLineEdit()
                widget.setText(str(value))
                widget.textChanged.connect(
                    lambda text, k=key: self.update_field_value(k, text)
                )

            form_layout.addWidget(widget, row, 1)
            self.config_widgets[key] = widget
            row += 1

        # 添加表单到布局
        form_widget = QWidget()
        form_widget.setLayout(form_layout)
        self.config_layout.addWidget(form_widget)
        self.config_layout.addStretch()

    def update_field_value(self, key, value):
        """更新字段值"""
        if self.selected_item_index is not None:
            items = self.get_items_list()
            if self.selected_item_index < len(items):
                current_item = items[self.selected_item_index]
                old_value = current_item.get(key)

                # 更新字段值
                current_item[key] = value

                # 特殊处理：当修改ROI字段时，动态更新画布显示
                if key in ["roiFront", "roiBack"]:
                    self.update_roi_from_field(key, value)

                # 特殊处理：当修改itemName时，同时更新imageName（仅对imageRule和listRule）
                if key == "itemName" and self.current_rule_type in ["imageRule", "listRule"]:
                    if "imageName" in current_item and old_value != value:
                        # 获取当前imageName的扩展名
                        old_image_name = current_item.get("imageName", "")
                        if old_image_name:
                            # 提取文件扩展名
                            if '.' in old_image_name:
                                extension = '.' + old_image_name.split('.')[-1]
                            else:
                                extension = '.png'  # 默认扩展名
                        else:
                            extension = '.png'

                        # 更新imageName
                        new_image_name = f"{value}{extension}"
                        current_item["imageName"] = new_image_name

                        # 更新UI中对应的imageName控件
                        if "imageName" in self.config_widgets:
                            image_widget = self.config_widgets["imageName"]
                            if isinstance(image_widget, QLineEdit):
                                image_widget.setText(new_image_name)

                # 同时更新UI中对应的控件显示
                if key in self.config_widgets:
                    widget = self.config_widgets[key]
                    if isinstance(widget, QLineEdit):
                        if widget.text() != str(value):
                            widget.setText(str(value))
                    elif isinstance(widget, QCheckBox):
                        widget.setChecked(bool(value))
                    elif isinstance(widget, QSpinBox):
                        widget.setValue(int(value))
                    elif isinstance(widget, QDoubleSpinBox):
                        widget.setValue(float(value))

                # 如果修改的是itemName，还需要更新列表显示
                if key == "itemName":
                    self.item_list.item(self.selected_item_index).setText(str(value))

    def update_roi_from_field(self, field_name, value):
        """根据字段更新对应的ROI框显示"""
        if not isinstance(value, str) or not value.strip():
            # 如果值为空，清除对应的ROI框
            if field_name == "roiFront":
                self.canvas.red_rect = None
                self.update_red_label(None)
            elif field_name == "roiBack":
                self.canvas.green_rect = None
                self.update_green_label(None)
            self.canvas.update()
            return

        # 解析ROI字符串
        parts = value.split(',')
        if len(parts) != 4:
            return

        try:
            x, y, w, h = map(int, parts)

            # 转换为画布坐标
            x_scaled = int(x * self.canvas.scale_factor)
            y_scaled = int(y * self.canvas.scale_factor)
            w_scaled = int(w * self.canvas.scale_factor)
            h_scaled = int(h * self.canvas.scale_factor)

            # 计算画布偏移
            if self.canvas.scaled_pixmap:
                pixmap_rect = self.canvas.scaled_pixmap.rect()
                widget_rect = self.canvas.rect()
                offset_x = (widget_rect.width() - pixmap_rect.width()) // 2
                offset_y = (widget_rect.height() - pixmap_rect.height()) // 2

                x_scaled += offset_x
                y_scaled += offset_y

                # 更新对应的ROI框
                if field_name == "roiFront":
                    self.canvas.red_rect = QRect(x_scaled, y_scaled, w_scaled, h_scaled)
                    self.update_red_label(self.canvas.red_rect)
                elif field_name == "roiBack":
                    self.canvas.green_rect = QRect(x_scaled, y_scaled, w_scaled, h_scaled)
                    self.update_green_label(self.canvas.green_rect)

                # 刷新画布显示
                self.canvas.update()

        except ValueError:
            # 如果解析失败，清除对应的ROI框
            if field_name == "roiFront":
                self.canvas.red_rect = None
                self.update_red_label(None)
            elif field_name == "roiBack":
                self.canvas.green_rect = None
                self.update_green_label(None)
            self.canvas.update()

    def get_default_item_by_type(self):
        """根据规则类型获取默认项目"""
        base_item = {
            "itemName": "new_item",
            "roiFront": "0,0,100,100",
            "roiBack": "0,0,100,100",
            "description": "description"
        }

        if self.current_rule_type == "imageRule":
            base_item.update({
                "imageName": "new_item.png",
                "method": "Template matching",
                "threshold": 0.8
            })
        elif self.current_rule_type == "ocrRule":
            base_item.update({
                "mode": "Single",
                "method": "Default",
                "keyword": ""
            })
        elif self.current_rule_type == "swipeRule":
            base_item.update({
                "mode": "default"
            })
        elif self.current_rule_type == "longClickRule":
            base_item.update({
                "duration": 1500
            })
        elif self.current_rule_type == "listRule":
            # listRule只需要基本字段，不需要roiBack
            del base_item["roiBack"]
            del base_item["description"]

        return base_item

    def add_item(self):
        """新增项目"""
        if not self.current_json_file:
            QMessageBox.warning(self, "警告", "请先选择或创建JSON文件")
            return

        # 根据规则类型创建默认Item
        new_item = self.get_default_item_by_type()

        # 添加到当前数据
        if self.current_rule_type == "listRule" and isinstance(self.current_json_data, dict):
            if "list" not in self.current_json_data:
                self.current_json_data["list"] = []
            self.current_json_data["list"].append(new_item)
        else:
            if not isinstance(self.current_json_data, list):
                self.current_json_data = []
            self.current_json_data.append(new_item)

        # 刷新Item列表
        self.update_item_list()

        # 选中新添加的项
        items_count = len(self.get_items_list())
        self.item_list.setCurrentRow(items_count - 1)

        # 显示配置
        self.selected_item_index = items_count - 1
        self.show_item_config(new_item)

    def delete_item(self):
        """删除选中的项目"""
        if self.selected_item_index is None:
            QMessageBox.warning(self, "警告", "请先选择要删除的项目")
            return

        reply = QMessageBox.question(
            self, "确认删除", "确定要删除选中的项目吗？",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            items = self.get_items_list()
            if self.selected_item_index < len(items):
                # 删除项目
                if self.current_rule_type == "listRule" and isinstance(self.current_json_data, dict):
                    del self.current_json_data["list"][self.selected_item_index]
                else:
                    del self.current_json_data[self.selected_item_index]

                # 更新界面
                self.selected_item_index = None
                self.update_item_list()
                self.clear_config_fields()

    def save_roi(self):
        """保存ROI截图"""
        red_coords = self.canvas.get_red_coords()
        if not red_coords or not self.image_path:
            QMessageBox.warning(self, "警告", "请先选择图片和红色框区域")
            return

        if not self.current_json_file or self.selected_item_index is None:
            QMessageBox.warning(self, "警告", "请先选择JSON文件和要保存的项目")
            return

        items = self.get_items_list()
        if self.selected_item_index >= len(items):
            QMessageBox.warning(self, "警告", "选中的项目无效")
            return

        current_item = items[self.selected_item_index]
        item_name = current_item.get("itemName", "unnamed")

        # 获取JSON文件所在目录
        json_dir = os.path.dirname(self.current_json_file)

        # 生成保存路径
        filename = f"{item_name}.png"
        save_path = os.path.join(json_dir, filename)

        try:
            x, y, w, h = red_coords
            # 使用PIL截取图片
            img = Image.open(self.image_path)
            roi = img.crop((x, y, x + w, y + h))

            # 检查是否需要保存为灰度图
            is_grayscale = self.grayscale_checkbox.isChecked()
            if is_grayscale:
                roi = roi.convert('L')  # 转换为灰度图
                # 如果选择了灰度图，在文件名中添加标识
                filename = f"{item_name}_gray.png"
                save_path = os.path.join(json_dir, filename)

            roi.save(save_path)

            # 如果是imageRule，自动更新imageName
            if self.current_rule_type == "imageRule" and "imageName" in current_item:
                relative_path = os.path.relpath(save_path, json_dir)
                current_item["imageName"] = relative_path
                # 刷新配置显示
                self.show_item_config(current_item)

            # 显示成功消息，包含是否为灰度图的信息
            mode_text = "灰度图" if is_grayscale else "彩色图"
            QMessageBox.information(self, "成功", f"已保存{mode_text}到: {save_path}")

            # 更新提示信息
            if self.current_rule_type in ["imageRule", "listRule"]:
                self.update_help_text(
                    f"截图已保存: {os.path.basename(save_path)} ({mode_text})\n"
                    f"图片路径已自动更新到配置中\n\n记得保存JSON文件以应用更改。"
                )

        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存图片失败: {str(e)}")

    def save_json(self):
        """保存JSON文件"""
        if not self.current_json_file:
            QMessageBox.warning(self, "警告", "请先选择JSON文件")
            return

        try:
            with open(self.current_json_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_json_data, f, indent=2, ensure_ascii=False)

            QMessageBox.information(self, "成功", "JSON文件已保存")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存JSON文件失败: {str(e)}")




def main():
    app = QApplication(sys.argv)

    # 设置应用程序属性
    app.setApplicationName("规则编辑器")
    app.setApplicationVersion("1.0")

    # 创建主窗口
    window = RuleEditGUI()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
