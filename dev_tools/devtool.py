# 添加模块导入
import sys
from tkinter import filedialog, messagebox
import pyperclip
import customtkinter as ctk
import cv2
import json
import numpy as np
import os
import re
import subprocess
from PIL import Image, ImageTk
from datetime import datetime

"""
坐标系统统一说明：
- 画布坐标系与图像坐标系完全一致
- 不再使用4像素偏移
- 所有坐标直接对应图像上的像素位置
- ROI格式为 (x, y, width, height)
"""

# 将当前目录加入系统路径，以便导入项目模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 尝试导入项目模块
try:
    from module.atom.image import RuleImage
    from module.atom.ocr import RuleOcr
    MODULE_AVAILABLE = True
except ImportError:
    MODULE_AVAILABLE = False
    print("无法导入项目模块，部分功能将不可用")

# 添加对 mask_generator 的导入
try:
    from mask_generator import MaskGenerator
    MASK_GENERATOR_AVAILABLE = True
except ImportError:
    MASK_GENERATOR_AVAILABLE = False
    print("无法导入蒙版生成器模块")


class EmulatorComboBox(ctk.CTkComboBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.refresh_callback = None
        # 重新绑定鼠标点击事件
        self.bind("<Button-1>", self._on_click, add="+")
        # 重新绑定下拉箭头的点击事件
        self._canvas.bind("<Button-1>", self._on_click, add="+")

    def set_refresh_callback(self, callback):
        """设置刷新回调函数"""
        self.refresh_callback = callback

    def _on_click(self, event):
        """处理点击事件"""
        if self.refresh_callback:
            self.refresh_callback()


class DevTool(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.last_selected_image = None
        self.last_selected_folder = None
        self.np_image = None  # 截图的 NumPy 图像
        self.current_image = None  # 当前显示的图像
        self.rect = {"x1": 0, "y1": 0, "x2": 0, "y2": 0}  # 矩形框
        self.img_info = None  # 保存图片信息
        self.image_files = []  # 存储当前文件夹中的图片文件列表
        self.current_image_index = -1  # 当前显示的图片在列表中的索引
        # 创建窗口
        self.geometry("1730x780")  # 增加窗口宽度和高度
        self.title("DevTool")
        self.resizable(False, False)

        # 设置默认路径
        self.screenshots_path = r"D:\共享文件夹\Screenshots"
        self.save_img_path = r"D:\共享文件夹\Screenshots"
        self.python_executable = r"F:\Python3.10\VENV\Scripts\pythonw.exe"
        self.mumu_manager_path = r"E:\MuMuPlayer-12.0\shell\MuMuManager.exe"

        # 确保默认路径存在
        self._ensure_directory_exists(self.screenshots_path)
        self._ensure_directory_exists(self.save_img_path)

        # 创建主框架以支持更好的布局
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 配置网格权重以支持调整大小
        # 保持画布区域固定尺寸
        self.main_frame.grid_columnconfigure(0, weight=0)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        # 创建画布框架
        self.canvas_frame = ctk.CTkFrame(self.main_frame)
        self.canvas_frame.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="")

        # 创建画布
        self.screen_canvas = ctk.CTkCanvas(self.canvas_frame, width=1280, height=720, bg="white")  # 调整为图像实际尺寸
        self.screen_canvas.configure(borderwidth=2, relief="solid")
        self.screen_canvas.bind("<Enter>", self.in_canvas)
        self.screen_canvas.bind("<Leave>", self.out_canvas)
        self.screen_canvas.bind("<Button-1>", self.on_click)
        self.screen_canvas.bind("<B1-Motion>", self.on_move)
        self.screen_canvas.bind("<ButtonRelease-1>", self.on_release)
        # 使用固定尺寸，确保画布保持1280x720（与图像尺寸一致）
        self.screen_canvas.grid(row=0, column=0, padx=10, pady=10)
        self.mouse_is_in_canvas = False

        # 右侧控制面板框架
        self.control_frame = ctk.CTkFrame(self.main_frame, width=300)
        self.control_frame.grid(row=0, column=1, padx=0, pady=0, sticky="nsew")
        self.control_frame.grid_propagate(False)  # 防止框架根据子控件调整大小
        self.control_frame.grid_columnconfigure(0, weight=1)
        self.control_frame.grid_rowconfigure(10, weight=1)

        # "上一张"和"下一张"按钮控制面板框架
        self.image_button_frame = ctk.CTkFrame(self.control_frame)
        self.image_button_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=0, sticky="nsew")
        self.image_button_frame.grid_rowconfigure(0, weight=1)
        self.image_button_frame.grid_columnconfigure(0, weight=1)
        self.image_button_frame.grid_columnconfigure(1, weight=1)
        self.image_button_frame.grid_columnconfigure(2, weight=1)  # 新增：让3列均分空间

        # 添加"上一张"和"下一张"按钮
        self.prev_image_button = ctk.CTkButton(self.image_button_frame, text="← 上一张", width=105, command=self.load_prev_image)
        self.prev_image_button.grid(row=0, column=0, padx=(20, 0), pady=(0, 0), sticky="w")

        self.next_image_button = ctk.CTkButton(self.image_button_frame, text="下一张 →", width=105, command=self.load_next_image)
        self.next_image_button.grid(row=0, column=1, padx=(0, 10), pady=(0, 0), sticky="w")

        # 创建选项卡视图
        self.tabview = ctk.CTkTabview(self.control_frame, width=200, height=100)
        self.tabview.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="nsew")

        # 添加三个选项卡
        self.screenshot_tab = self.tabview.add("截图工具")
        self.template_tab = self.tabview.add("模板匹配")
        self.ocr_tab = self.tabview.add("OCR工具")
        self.tools_tab = self.tabview.add("工具")  # 添加新选项卡
        
        # 配置各选项卡的网格权重
        self.screenshot_tab.grid_columnconfigure(0, weight=1)
        self.screenshot_tab.grid_rowconfigure(10, weight=1)
        self.template_tab.grid_columnconfigure(0, weight=1)
        self.template_tab.grid_columnconfigure(1, weight=0)  # 第1列保持固定
        self.template_tab.grid_columnconfigure(2, weight=0)  # 第2列保持固定
        self.template_tab.grid_rowconfigure(10, weight=1)
        self.ocr_tab.grid_columnconfigure(0, weight=1)
        self.ocr_tab.grid_rowconfigure(10, weight=1)
        self.tools_tab.grid_columnconfigure(0, weight=1)  # 配置新选项卡
        self.tools_tab.grid_rowconfigure(10, weight=1)

        # 在截图工具选项卡中添加控件
        # 文件夹路径输入框
        self.folder_path_entry = ctk.CTkEntry(self.screenshot_tab, placeholder_text="请选择保存图片文件夹", width=260, justify="center")
        self.folder_path_entry.grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="ew")
        # 选择文件夹按钮
        self.choese_folder_button = ctk.CTkButton(self.screenshot_tab, text="保存目录", width=20, command=self.choose_folder)
        self.choese_folder_button.grid(row=0, column=2, padx=(5, 10), pady=(10, 5), sticky="w")

        # 图片名称输入框
        self.img_name = ctk.CTkEntry(self.screenshot_tab, placeholder_text="请选择加载的图片", width=260, justify="center")
        self.img_name.grid(row=1, column=0, columnspan=2, padx=10, pady=(5, 5), sticky="ew")
        # 读取图片按钮
        self.load_image_button = ctk.CTkButton(self.screenshot_tab, text="加载图片", width=20, command=self.load_image)
        self.load_image_button.grid(row=1, column=2, padx=(5, 10), pady=(5, 5), sticky="w")

        # 请输入保存图片名称
        self.save_name_entry = ctk.CTkEntry(self.screenshot_tab, placeholder_text="请输入保存图片的名字", width=260, justify="center")
        self.save_name_entry.grid(row=2, column=0, columnspan=2, padx=10, pady=(5, 5), sticky="ew")
        # 保存按钮
        self.save_and_fmt_button = ctk.CTkButton(self.screenshot_tab, text="保存图片", width=20, command=self.save_img)
        self.save_and_fmt_button.grid(row=2, column=2, padx=(5, 10), pady=(5, 5), sticky="w")

        # 框选坐标显示框
        self.rect_info = ctk.CTkEntry(self.screenshot_tab, placeholder_text="矩形框坐标", width=260, justify="center")
        self.rect_info.grid(row=3, column=0, columnspan=2, padx=10, pady=(5, 5), sticky="ew")
        # 绑定回 enter 键事件，当在坐标输入框按回车时显示矩形框
        self.rect_info.bind("<KeyRelease>", self.show_rectangle_from_entry)
        # 复制按钮
        self.copy_button = ctk.CTkButton(self.screenshot_tab, width=20, text="复制坐标", command=lambda: self.copy_to_clipboard(str(self.coordinates)))
        self.copy_button.grid(row=3, column=2, padx=(5, 10), pady=(5, 5), sticky="w")

        # 添加模拟器选择下拉框（点击时自动刷新）
        self.emulator_selector = EmulatorComboBox(self.screenshot_tab, values=["请选择模拟器"], width=260, command=self.on_emulator_selected)
        self.emulator_selector.set("请选择模拟器")
        self.emulator_selector.grid(row=4, column=0, columnspan=2, padx=10, pady=(5, 5), sticky="ew")
        # 设置刷新回调
        self.emulator_selector.set_refresh_callback(self.refresh_emulators)
        
        # 模拟器截图按钮
        self.capture_emulator_button = ctk.CTkButton(self.screenshot_tab, text="木木截图", width=20, command=self.capture_emulator_screenshot)
        self.capture_emulator_button.grid(row=4, column=2, padx=(5, 10), pady=(5, 5), sticky="w")

        # log显示框（放在控制面板框架内，在选项卡下方）
        self.log_frame = ctk.CTkFrame(self.control_frame)
        self.log_frame.grid(row=5, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        self.log_frame.grid_rowconfigure(0, weight=1)
        self.log_frame.grid_columnconfigure(0, weight=1)

        # 添加标题标签
        self.log_title_label = ctk.CTkLabel(
            self.log_frame,
            text="操作日志",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.log_title_label.grid(row=0, column=0, padx=(10, 0), pady=(10, 0), sticky="w")

        # 添加清空日志按钮到标题栏右侧
        self.clear_log_button = ctk.CTkButton(
            self.log_frame,
            text="清除日志",
            width=60,
            height=20,
            command=self.clear_log
        )
        self.clear_log_button.grid(row=0, column=0, padx=(0, 10), pady=(10, 0), sticky="e")

        # 添加日志文本框
        self.log_box = ctk.CTkTextbox(
            self.log_frame,
            bg_color="#dadada",
            fg_color="#000000",
            text_color="#48BB31",
            width=120,
            height=420
        )
        self.log_box.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        
        # 配置日志框的颜色标签
        self.log_box.tag_config("success", foreground="#48BB31")  # 绿色
        self.log_box.tag_config("error", foreground="#FF4136")    # 红色
        
        # 在模板匹配选项卡中添加控件
        if MODULE_AVAILABLE:
            # 匹配方式选择标签和下拉框
            self.match_method_label = ctk.CTkLabel(self.template_tab, text="匹配方式:")
            self.match_method_label.grid(row=0, column=0, padx=(10, 5), pady=5, sticky="w")
            
            self.match_method_combo = ctk.CTkComboBox(
                self.template_tab,
                values=["模板匹配", "图片匹配"],
                width=200,
                command=self.on_match_method_change
            )
            self.match_method_combo.set("模板匹配")  # 默认选择
            self.match_method_combo.grid(row=0, column=1, padx=5, pady=5, sticky="e")

            # 模板匹配参数输入框 (用于RuleImage或RuleOcr匹配)
            self.rule_param_entry = ctk.CTkEntry(self.template_tab, placeholder_text="请输入RuleImage或RuleOcr匹配", width=260)
            self.rule_param_entry.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

            # 模板路径显示 (用于图片匹配)
            self.template_path_label = ctk.CTkLabel(self.template_tab, text="未选择模板")
            self.template_path_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
            self.template_path_label.grid_remove()  # 默认隐藏
            # 选择模板按钮 (用于图片匹配)
            self.select_template_button = ctk.CTkButton(self.template_tab, text="选择模板", width=20, command=self.select_template)
            self.select_template_button.grid(row=1, column=1, padx=5, pady=10, sticky="e")
            self.select_template_button.grid_remove()  # 默认隐藏
            # 阈值显示 (用于图片匹配)
            self.threshold_label = ctk.CTkLabel(self.template_tab, text="匹配阈值: 0.80")
            self.threshold_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")
            self.threshold_label.grid_remove()  # 默认隐藏
            # 阈值滑块 (用于图片匹配)
            self.threshold_slider = ctk.CTkSlider(self.template_tab, from_=0.1, to=1.0, number_of_steps=90, command=self.update_threshold_label)
            self.threshold_slider.set(0.8)
            self.threshold_slider.grid(row=3, column=1, padx=10, pady=10, sticky="ew")
            self.threshold_slider.grid_remove()  # 默认隐藏

            # 模板匹配按钮
            self.template_match_button = ctk.CTkButton(self.template_tab, text="模板匹配", width=30, command=self.perform_template_match)
            self.template_match_button.grid(row=4, column=1, padx=5, pady=10, sticky="e")

        # 在OCR工具选项卡中添加控件
        if MODULE_AVAILABLE:
            # OCR结果文本框
            self.ocr_result_textbox = ctk.CTkTextbox(self.ocr_tab, height=100, width=260)
            self.ocr_result_textbox.grid(row=0, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
            self.ocr_result_textbox.insert("0.0", "OCR结果将显示在这里")

            # OCR按钮
            self.ocr_button = ctk.CTkButton(self.ocr_tab, text="执行OCR", width=20, command=self.perform_ocr)
            self.ocr_button.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="ew")

        # 在工具选项卡中添加控件
        # 添加检查画布尺寸按钮
        self.check_canvas_button = ctk.CTkButton(
            self.tools_tab,
            text="检查画布尺寸",
            width=260,
            command=self.check_canvas_size
        )
        self.check_canvas_button.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")

        # 如果蒙版生成器可用，添加相应按钮到工具选项卡
        if MASK_GENERATOR_AVAILABLE:
            # 蒙版生成器按钮
            self.mask_generator_button = ctk.CTkButton(
                self.tools_tab,
                text="蒙版生成器",
                width=260,
                command=self.open_mask_generator
            )
            self.mask_generator_button.grid(row=1, column=0, padx=10, pady=(5, 10), sticky="ew")

        # 执行 assets_extract 按钮
        self.assets_extract_button = ctk.CTkButton(
            self.tools_tab,
            text="执行 assets_extract",
            width=260,
            command=self.run_assets_extract
        )
        self.assets_extract_button.grid(row=2, column=0, padx=10, pady=(5, 10), sticky="ew")

        # 当前选中模板路径
        self.current_template_path = None

        # 初始化保存路径输入框为默认保存路径
        self.folder_path_entry.insert(0, self.save_img_path)

        # 用于矩形拖动功能的变量
        self.is_dragging = False  # 是否正在拖动矩形
        self.drag_start_offset_x = 0  # 拖动起始点与矩形左上角的偏移
        self.drag_start_offset_y = 0  # 拖动起始点与矩形左上角的偏移
        # 用于新矩形绘制的变量
        self.is_drawing = False  # 是否正在绘制新矩形
        self.new_rect_start_x = 0  # 新矩形的起始点x坐标
        self.new_rect_start_y = 0  # 新矩形的起始点y坐标

        # 初始化时自动加载模拟器列表
        # 使用更长的延迟来提高启动速度
        self.after(100, self.refresh_emulators)

        # 添加：启动时自动扫描并加载最新图片
        # 使用更长的延迟来提高启动速度
        self.after(200, self.load_latest_image_at_startup)
        
        # 初始化画布滚动区域
        self.screen_canvas.configure(scrollregion=(0, 0, 1280, 720))

    def _ensure_directory_exists(self, path):
        """确保目录存在，如果不存在则创建"""
        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except:
                # 如果创建失败，不修改任何属性
                pass

    def log_print(self, text, color=None):
        if color:
            self.log_box.insert("end", f"{text}\n", color)
        else:
            self.log_box.insert("end", f"{text}\n")
        self.log_box.update()
        self.log_box.see("end")

    def copy_to_clipboard(self, text):
        # 修改这里：改变复制到剪贴板的坐标格式
        x1, y1, x2, y2 = self.coordinates
        # 统一坐标系统：现在画布坐标和图像坐标一致，无需偏移
        formatted_text = f"{x1},{y1},{x2-x1},{y2-y1}"
        # 彻底清理所有空白字符
        formatted_text = re.sub(r'\s+', '', formatted_text)

        # 使用更可靠的剪贴板方法
        pyperclip.copy(formatted_text)
        self.log_print(f"复制坐标 {formatted_text} 到剪贴板")

    def choose_folder(self):
        # 使用上次选择的路径或默认路径作为初始目录
        initial_dir = self.last_selected_folder or self.save_img_path
        folder_path = filedialog.askdirectory(initialdir=initial_dir)
        if folder_path:  # 如果选择了文件夹
            self.last_selected_folder = folder_path  # 记住选择的路径
            self.folder_path_entry.delete(0, "end")
            self.folder_path_entry.insert(0, folder_path)
            self.log_print(folder_path)

    def choose_image_file(self):
        """打开文件对话框选择PNG图片文件"""
        # 使用上次选择的路径或默认路径作为初始目录
        initial_dir = self.last_selected_image or self.screenshots_path
        file_path = filedialog.askopenfilename(
            initialdir=initial_dir,
            title="选择PNG图片",
            filetypes=(("PNG图片", "*.png"), ("所有文件", "*.*"))
        )
        if file_path:  # 如果选择了文件
            self.last_selected_image = os.path.dirname(file_path)  # 记住文件所在目录
            # 更新图片文件列表和当前索引
            self.update_image_files(file_path, is_file_path=True)
        return file_path

    def load_prev_image(self):
        """加载上一张图片"""
        if not self.image_files or self.current_image_index <= 0:
            self.log_print("已经是第一张图片或没有图片可加载", "error")
            return
            
        self.current_image_index -= 1
        self.load_image_by_path(self.image_files[self.current_image_index])

    def load_next_image(self):
        """加载下一张图片"""
        if not self.image_files or self.current_image_index >= len(self.image_files) - 1:
            self.log_print("已经是最后一张图片或没有图片可加载", "error")
            return
            
        self.current_image_index += 1
        self.load_image_by_path(self.image_files[self.current_image_index])

    def load_image_by_path(self, image_path):
        """通过指定路径加载PNG图片"""
        self.log_print(f"加载图片: {os.path.basename(image_path)}")
        try:
            # 使用cv2读取图片
            self.np_image = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), cv2.IMREAD_COLOR)

            # 检查图片是否存在
            if self.np_image is None:
                self.log_print("无法读取图片文件", "error")
                return

            # 检查图片尺寸
            height, width = self.np_image.shape[:2]
            if width != 1280 or height != 720:
                self.log_print(f"警告: 图片尺寸为 {width}x{height}，不是1280x720", "error")

            # 转换为PIL Image并显示
            pil_image = Image.fromarray(cv2.cvtColor(self.np_image, cv2.COLOR_BGR2RGB))
            self.current_image = ImageTk.PhotoImage(pil_image)
            # 直接在画布的(0,0)位置显示图像，确保完全填充画布
            self.screen_canvas.create_image(0, 0, anchor="nw", image=self.current_image)

            # 配置画布的滚动区域，确保与图像尺寸一致
            self.screen_canvas.configure(scrollregion=(0, 0, width, height))

            # 设置图片名称为文件名（不含扩展名）
            img_name = os.path.splitext(os.path.basename(image_path))[0]
            self.img_name.delete(0, "end")
            self.img_name.insert(0, img_name)

            # 设置默认保存名称为加载图片名_1（仅当保存名称为空或与图片名称输入框内容不同时）
            current_save_name = self.save_name_entry.get().strip()
            if not current_save_name or current_save_name == self.name:
                self.save_name_entry.delete(0, "end")
                self.save_name_entry.insert(0, f"{img_name}_1")

            # 自动填充文件夹路径为默认保存路径
            self.folder_path_entry.delete(0, "end")
            self.folder_path_entry.insert(0, self.save_img_path)

            # 重新绘制矩形框（如果存在）
            if self.rect["x1"] != self.rect["x2"] and self.rect["y1"] != self.rect["y2"]:
                self.draw_rectangle()

        except Exception as e:
            self.log_print(f"加载图片时出错: {e}", "error")

    def load_image(self):
        """通过文件对话框加载PNG图片"""
        image_path = self.choose_image_file()
        if not image_path:  # 用户取消选择
            return

        self.load_image_by_path(image_path)

    @property
    def coordinates(self):
        x1, y1, x2, y2 = self.rect.values()
        return x1, y1, x2, y2

    @property
    def name(self):
        return self.img_name.get()

    @property
    def file_path(self):
        base_path = self.folder_path_entry.get()
        img_name = self.name
        # 检查文件名是否合法
        if not img_name or not img_name.strip():
            self.log_print("图片名称不能为空", "error")
            return None

        # 检查目录是否存在
        if not os.path.exists(base_path):
            self.log_print("保存路径不存在", "error")
            return None
        timestamp = datetime.now().strftime("%H%M%S")
        path = os.path.relpath(base_path, start=os.curdir) + "/" + img_name + f"_{timestamp}.png"  # 保存路径x
        path = path.replace("\\", "/")  # 路径格式化

        return path

    def save_img(self):
        # 检查是否已加载图片
        if self.np_image is None:
            self.log_print("请先加载图片", "error")
            return

        # 检查是否已选择有效区域
        x1, y1, x2, y2 = self.coordinates
        if not (x1 != x2 and y1 != y2):  # 检查是否已选择区域
            self.log_print("请先选择要保存的区域", "error")
            return

        # 获取保存名称输入框的内容作为文件名
        save_name = self.save_name_entry.get().strip()

        # 如果输入框为空，使用加载的图片名称作为基础名称
        if not save_name:
            base_name = self.name.strip()
            if base_name:
                save_name = f"{base_name}_1"
            else:
                self.log_print("保存图片的名字不能为空", "error")
                return

        path = os.path.join(self.folder_path_entry.get(), f"{save_name}.png")

        # 检查文件是否已存在
        if os.path.exists(path):
            # 弹窗提示用户文件已存在，提供三个选项
            result = messagebox.askyesno(
                "文件已存在",
                f"文件 {save_name}.png 已存在，是否要覆盖该文件？\n\n '是' 覆盖文件\n '否' 取消保存"
            )

            if not result:  # 用户选择否，取消保存
                self.log_print("取消保存操作", "error")
                return
            else:  # 用户选择是，覆盖文件
                self.log_print(f"将覆盖文件: {save_name}.png")

        # 确保 np_image 和矩形框有效
        if self.np_image is not None and any(self.rect.values()):
            x1, y1, x2, y2 = self.coordinates
            # 检查裁剪框的有效性
            # if not (0 <= x1 < x2 <= self.np_image.shape[1] and 0 <= y1 < y2 <= self.np_image.shape[0]):
            #     self.log_print("裁剪框的坐标无效", "error")
            #     return
            try:
                # 统一坐标系统：现在画布坐标和图像坐标一致，无需偏移
                cropped_image = self.np_image[y1 : y2, x1 : x2]
                cv2.imencode(".png", cropped_image)[1].tofile(path)
                self.log_print(f"{save_name}.png 保存成功", "success")
                # 新增：保存图片信息到 image.json
                self.save_image_info(save_name, path, x1, y1, x2, y2)
            except Exception as e:
                self.log_print(f"保存图像时出错: {e}", "error")

    def save_image_info(self, save_name, path, x1, y1, x2, y2):
        """保存图片信息到 image.json"""
        json_file_path = os.path.join(self.folder_path_entry.get(), "image.json")
        # 统一坐标系统：现在画布坐标和图像坐标一致，无需偏移
        roi_front_back = f"{x1},{y1},{x2-x1},{y2-y1}"
        image_data = {
            "itemName": save_name,
            "imageName": f"{save_name}.png",
            "roiFront": roi_front_back,
            "roiBack":  roi_front_back,
            "method": "Template matching",
            "threshold": 0.8,
            "description": save_name
        }

        formatted_json = json.dumps(image_data, ensure_ascii=False, indent=2)
        self.log_print(formatted_json)

        # 统一坐标系统：现在画布坐标和图像坐标一致，无需偏移
        roi = x1, y1, x2-x1, y2-y1
        self.log_print(f"rule_image = RuleImage(roi_front={roi}, roi_back={roi}, threshold=0.8, method=\"Template matching\", file=\"{self.folder_path_entry.get()}\\{save_name}.png\")")

        # 读取现有数据或初始化为空列表
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                try:
                    data = json.load(file)
                except json.JSONDecodeError:
                    data = []
        except FileNotFoundError:
            data = []

        # 检查是否已存在相同的 itemName
        item_exists = False
        for item in data:
            if item["itemName"] == save_name:
                # 更新现有条目
                item.update(image_data)
                item_exists = True
                break

        # 如果不存在，则追加新数据
        if not item_exists:
            data.append(image_data)

        # 写回文件
        with open(json_file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
            self.log_print(f"图片信息已保存到: {json_file_path}")

    def format_img(self, fmt_type):
        x1, y1, x2, y2 = self.coordinates
        # 统一坐标系统：现在画布坐标和图像坐标一致，无需偏移
        fmt_map = {
            "image": f"{self.name}=['{self.file_path}', [{x1}, {y1}, {x2}, {y2}], '{self.name}']",
            "page": f"{self.name}=Page('{self.name}',['{self.file_path}', [{x1}, {y1}, {x2}, {y2}], '{self.name}'])",
            "coor": f"{self.name}=({x1}, {y1}, {x2}, {y2})"
        }
        return fmt_map.get(fmt_type, "")

    def write_to_file(self, save_type):
        try:
            self._img_info = self.format_img(save_type)
            self.log_print(self._img_info)
            if self._img_info:
                file_path = os.path.join(self.folder_path_entry.get(), "img_info_auto_create.py")
                if not os.path.exists(file_path):
                    with open(file_path, "w") as file:
                        file.write(f"# this file is auto created by devtool at {datetime.now()}\n\n")  # 写入内容
                        self.log_print("创建文件成功")

                with open(file_path, "a") as f:
                    f.write(str(self._img_info) + "\n")  # 写入内容
                    self.log_print("写入文件成功")
            else:
                self.log_print("没有图像信息或图像名称", "error")
        except Exception as e:
            self.log_print(f"写入文件时出错: {e}", "error")

    def in_canvas(self, event):
        self.mouse_is_in_canvas = True

    def out_canvas(self, event):
        self.mouse_is_in_canvas = False

    def on_click(self, event):
        if self.mouse_is_in_canvas:
            # 检查是否点击在现有矩形内
            x1, y1, x2, y2 = self.rect["x1"], self.rect["y1"], self.rect["x2"], self.rect["y2"]
            # 确保矩形有效（有面积）
            if x1 != x2 and y1 != y2:
                # 标准化矩形坐标（处理从右下到左上的绘制情况）
                left = min(x1, x2)
                right = max(x1, x2)
                top = min(y1, y2)
                bottom = max(y1, y2)
                
                # 判断点击是否在矩形内部
                if left <= event.x <= right and top <= event.y <= bottom:
                    self.is_dragging = True
                    self.drag_start_offset_x = event.x - x1
                    self.drag_start_offset_y = event.y - y1
                    return
            
            # 如果不在矩形内，则准备开始新的绘制（但不立即开始）
            self.is_dragging = False
            self.is_drawing = False
            # 注意：这里不立即改变矩形坐标，只记录点击位置用于后续可能的绘制
            self.new_rect_start_x = event.x
            self.new_rect_start_y = event.y

    def on_move(self, event):
        if self.mouse_is_in_canvas:
            if self.is_dragging:
                # 拖动矩形 - 平移整个矩形
                # 计算新位置
                new_x1 = event.x - self.drag_start_offset_x
                new_y1 = event.y - self.drag_start_offset_y
                
                # 保持矩形大小不变
                width = self.rect["x2"] - self.rect["x1"]
                height = self.rect["y2"] - self.rect["y1"]
                
                # 更新矩形坐标
                self.rect["x1"] = new_x1
                self.rect["y1"] = new_y1
                self.rect["x2"] = new_x1 + width
                self.rect["y2"] = new_y1 + height
                
                self.draw_rectangle()
            else:
                # 准备绘制新矩形或正在绘制新矩形
                if not self.is_drawing:
                    # 开始绘制新矩形
                    self.is_drawing = True
                    # 设置矩形的起始点和结束点
                    self.rect["x1"] = self.new_rect_start_x
                    self.rect["y1"] = self.new_rect_start_y
                    self.rect["x2"] = event.x
                    self.rect["y2"] = event.y
                else:
                    # 更新矩形的结束点
                    self.rect["x2"] = event.x
                    self.rect["y2"] = event.y
                self.draw_rectangle()

    def on_release(self, event):
        if self.mouse_is_in_canvas:
            if self.is_dragging:
                # 完成拖动
                self.is_dragging = False
                # 更新坐标显示
                x1, y1, x2, y2 = self.coordinates
                # 统一坐标系统：现在画布坐标和图像坐标一致，无需偏移
                self.log_print(f"矩形框坐标：{x1},{y1},{x2-x1},{y2-y1}")
                self.dyn_creat_info()
            else:
                # 处理新矩形绘制
                if self.is_drawing:
                    # 完成新矩形绘制
                    self.rect["x2"] = event.x
                    self.rect["y2"] = event.y
                    # 检查是否实际拉出了矩形框（即起点和终点不同）
                    if self.rect["x1"] != self.rect["x2"] and self.rect["y1"] != self.rect["y2"]:
                        self.draw_rectangle()
                        # 统一坐标系统：现在画布坐标和图像坐标一致，无需偏移
                        x1, y1, x2, y2 = self.coordinates
                        self.log_print(f"矩形框坐标：{x1},{y1},{x2-x1},{y2-y1}")
                        self.dyn_creat_info()
                # 重置绘制状态
                self.is_drawing = False
                self.new_rect_start_x = 0
                self.new_rect_start_y = 0

    def dyn_creat_info(self, *args, **kwargs):
        # 修改这里：改变矩形框坐标显示框中的格式
        x1, y1, x2, y2 = self.coordinates
        # 统一坐标系统：现在画布坐标和图像坐标一致，无需偏移
        self.rect_info.delete(0, "end")
        self.rect_info.insert(0, f"{x1},{y1},{x2-x1},{y2-y1}")

    def draw_rectangle(self):
        self.screen_canvas.delete("rect")
        # 使用统一的坐标系统，直接绘制矩形
        self.screen_canvas.create_rectangle(
            self.rect["x1"], 
            self.rect["y1"], 
            self.rect["x2"], 
            self.rect["y2"], 
            outline="red", 
            tags="rect"
        )

    def show_rectangle_from_entry(self, event=None):
        """从坐标输入框获取坐标并在画布上显示矩形框"""
        coord_text = self.rect_info.get().strip()
        # 去掉所有空格，并将中文逗号替换为英文逗号
        coord_text = coord_text.replace(" ", "").replace("，", ",")
        if not coord_text:
            return

        try:
            # 解析坐标格式 x,y,w,h
            coords = [float(x.strip()) for x in coord_text.split(',')]
            if len(coords) == 2:
                coords.extend([10, 10])  # 使用extend替代多次append
            if len(coords) != 4:
                return  # 不完整的坐标不处理

            x, y, w, h = coords
            # 统一坐标系统：现在画布坐标和图像坐标一致，无需偏移
            x1 = int(x)
            y1 = int(y)
            x2 = x1 + int(w)
            y2 = y1 + int(h)

            # 检查坐标是否在图像范围内
            if self.np_image is not None:
                if not (0 <= x1 < x2 <= self.np_image.shape[1] and 0 <= y1 < y2 <= self.np_image.shape[0]):
                    # 坐标超出范围时不绘制，但不清除现有矩形
                    return

            # 更新矩形坐标
            self.rect.update({"x1": x1, "y1": y1, "x2": x2, "y2": y2})

            # 绘制矩形
            self.draw_rectangle()

        except ValueError:
            # 输入非数字时不处理
            pass
        except Exception:
            # 其他异常也不处理
            pass

    # 新增功能：OCR识别
    def perform_ocr(self):
        """执行OCR识别"""
        if not MODULE_AVAILABLE:
            self.log_print("项目模块不可用，无法执行OCR", "error")
            return
            
        if self.np_image is None:
            self.log_print("请先加载图片", "error")
            return

        if not self.is_rect_valid():
            self.log_print("请先选择有效区域", "error")
            return

        try:
            # 获取选区坐标
            x1, y1, x2, y2 = self.coordinates
            # 统一坐标系统：现在画布坐标和图像坐标一致，无需偏移
            # x1, y1, x2, y2 = x1 - 4, y1 - 4, x2 - 4, y2 - 4
            
            # 确保坐标有效
            x1, x2 = sorted([x1, x2])
            y1, y2 = sorted([y1, y2])
            
            if x1 < 0 or y1 < 0 or x2 > self.np_image.shape[1] or y2 > self.np_image.shape[0]:
                self.log_print("选区超出图片范围", "error")
                return
                
            # 创建RuleOcr对象
            ocr_rule = RuleOcr(roi=(x1, y1, x2-x1, y2-y1), area=(x1, y1, x2-x1, y2-y1), mode="Single", method="Default", keyword="", name="devtool_ocr")

            # 转换图片格式
            rgb_image = cv2.cvtColor(self.np_image, cv2.COLOR_BGR2RGB)
            
            # 执行OCR
            ocr_result = ocr_rule.detect_and_ocr(rgb_image)

            # 显示结果
            if ocr_result:
                self.ocr_result_textbox.delete("0.0", "end")
                if isinstance(ocr_result, list):
                    for result in ocr_result:
                        self.ocr_result_textbox.insert("end", f"{result}\n")
                else:
                    self.ocr_result_textbox.insert("end", str(ocr_result))
                self.log_print(f"OCR识别完成: {ocr_result}")
            else:
                self.ocr_result_textbox.delete("0.0", "end")
                self.ocr_result_textbox.insert("0.0", "未识别到文本")
                self.log_print("OCR未识别到文本", "error")
                
        except Exception as e:
            self.log_print(f"OCR执行出错: {str(e)}", "error")

    # 新增功能：选择模板
    def select_template(self):
        """选择模板图片"""
        if not MODULE_AVAILABLE:
            self.log_print("项目模块不可用", "error")
            return
            
        template_path = filedialog.askopenfilename(
            title="选择模板图片",
            filetypes=(("PNG图片", "*.png"), ("所有文件", "*.*"))
        )
        
        if template_path:
            self.current_template_path = template_path
            # 显示文件名
            filename = os.path.basename(template_path)
            self.template_path_label.configure(text=filename)
            self.log_print(f"已选择模板: {filename}")

    # 新增功能：匹配方式改变处理
    def on_match_method_change(self, choice):
        """处理匹配方式选择改变"""
        if choice == "图片匹配":
            # 隐藏模板匹配参数输入框
            self.rule_param_entry.grid_remove()
            # 显示模板选择控件
            self.template_path_label.grid()
            self.select_template_button.grid()
            self.threshold_label.grid()
            self.threshold_slider.grid()
        else:
            # 隐藏模板选择控件
            self.template_path_label.grid_remove()
            self.select_template_button.grid_remove()
            self.threshold_label.grid_remove()
            self.threshold_slider.grid_remove()
            # 显示模板匹配参数输入框
            self.rule_param_entry.grid()

        self.log_print(f"匹配方式已更改为: {choice}")

    # 新增功能：模板匹配
    def perform_template_match(self):
        """执行模板匹配"""
        if not MODULE_AVAILABLE:
            self.log_print("项目模块不可用，无法执行模板匹配", "error")
            return
            
        if self.np_image is None:
            self.log_print("请先加载图片", "error")
            return

        # 获取当前选择的匹配方式
        match_method = self.match_method_combo.get()
        
        if match_method == "图片匹配":
            if not self.current_template_path:
                self.log_print("请先选择模板图片", "error")
                return

            if not self.is_rect_valid():
                self.log_print("请先选择有效区域", "error")
                return
            try:
                # 获取选区坐标
                x1, y1, x2, y2 = self.coordinates
                # 统一坐标系统：现在画布坐标和图像坐标一致，无需偏移
                # x1, y1, x2, y2 = x1 - 4, y1 - 4, x2 - 4, y2 - 4

                # 确保坐标有效
                x1, x2 = sorted([x1, x2])
                y1, y2 = sorted([y1, y2])

                if x1 < 0 or y1 < 0 or x2 > self.np_image.shape[1] or y2 > self.np_image.shape[0]:
                    self.log_print("选区超出图片范围", "error")
                    return

                # 获取当前阈值
                threshold = self.threshold_slider.get()

                # 执行图片匹配逻辑
                self._perform_image_match(x1, y1, x2, y2, threshold)

            except Exception as e:
                self.log_print(f"模板匹配执行出错: {str(e)}", "error")

        else:
            param = self.rule_param_entry.get().strip()

            if "RuleImage" in param and param.endswith(")"):
                # 执行RuleImage匹配逻辑
                self._perform_ruleimage_match(param)

            elif "RuleOcr" in param and param.endswith(")"):
                # 执行RuleOCR匹配逻辑
                self._perform_ruleocr_match(param)


    def _perform_image_match(self, x1, y1, x2, y2, threshold):
        """执行图片匹配"""
        # 统一坐标系统：现在画布坐标和图像坐标一致，无需偏移
        # 创建RuleImage对象
        template_rule = RuleImage(
            roi_front=(x1, y1, x2-x1, y2-y1),
            roi_back=(x1, y1, x2-x1, y2-y1),
            threshold=threshold,
            method="Template matching",
            file=self.current_template_path
        )
        print(f"Template matching: {template_rule.roi_front}")
        self._perform_match(template_rule)

    def _perform_ruleocr_match(self, ruleocr_param):
        """执行RuleOcr匹配"""
        try:
            print(f"使用RuleOcr参数: {ruleocr_param}")

            # 解析字符串参数并创建RuleOcr对象
            # 假设输入格式为: RuleOcr(roi=(40,319,41,23), area=(40,319,41,23), mode="Digit", method="Default", keyword="", name="sca_number_orochi")
            if "RuleOcr" in ruleocr_param and ruleocr_param.endswith(")"):
                # 提取参数部分
                params_str = ruleocr_param[9:-1]  # 去掉"RuleOcr("和最后的")"

                # 使用正则表达式一次性提取所有参数
                roi_match = re.search(r'roi=\(([^)]+)\)', params_str)
                area_match = re.search(r'area=\(([^)]+)\)', params_str)
                mode_match = re.search(r'mode=([\'"])([^\'"]+)\1', params_str)
                method_match = re.search(r'method=([\'"])([^\'"]+)\1', params_str)
                keyword_match = re.search(r'keyword=([\'"])([^\'"]*)\1', params_str)
                name_match = re.search(r'name=([\'"])([^\'"]+)\1', params_str)

                if not all([roi_match, area_match, mode_match, method_match, keyword_match, name_match]):
                    self.log_print("RuleOcr参数格式不正确", "error")
                    return

                roi = tuple(map(int, roi_match.group(1).split(',')))
                area = tuple(map(int, area_match.group(1).split(',')))
                mode = mode_match.group(2)
                method = method_match.group(2)
                keyword = keyword_match.group(2)
                name = name_match.group(2)

                # 创建RuleOcr对象
                ocr_rule = RuleOcr(
                    roi=roi,
                    area=area,
                    mode=mode,
                    method=method,
                    keyword=keyword,
                    name=name
                )

                self._perform_ocr_match(ocr_rule)
            else:
                self.log_print("RuleOcr参数格式不正确", "error")

        except Exception as e:
            self.log_print(f"RuleOcr参数解析出错: {str(e)}", "error")

    def _perform_ocr_match(self, ocr_rule):
        """执行OCR匹配"""
        try:
            print(f"RuleOcr: {ocr_rule}")
            # 转换图片格式
            rgb_image = cv2.cvtColor(self.np_image, cv2.COLOR_BGR2RGB)

            # 在画布上绘制OCR区域
            self.screen_canvas.delete("ocr_result")
            roi = ocr_rule.roi
            # 统一坐标系统：现在画布坐标和图像坐标一致，无需偏移
            canvas_x1, canvas_y1 = roi[0], roi[1]
            canvas_x2, canvas_y2 = roi[2], roi[3]
            self.screen_canvas.create_rectangle(
                canvas_x1, canvas_y1, canvas_x1 + canvas_x2, canvas_y1 + canvas_y2,
                outline="green", width=1, tags="ocr_result"  # 使用蓝色区分OCR结果
            )

            # 执行OCR识别
            ocr_result = ocr_rule.ocr(rgb_image)

            # 在日志中显示结果
            self.log_print(f"OCR识别结果: {ocr_result}")

        except Exception as e:
            self.log_print(f"OCR匹配执行出错: {str(e)}", "error")

    def _perform_ruleimage_match(self, ruleimage_param):
        """执行RuleImage匹配"""
        try:
            # 获取RuleImage参数
            print(f"RuleImage: {ruleimage_param}")

            # 解析字符串参数并创建RuleImage对象
            # 假设输入格式为: RuleImage(roi_front=(176,148,144,108), roi_back=(128,142,902,449), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/special/special_sp_buy_low.png")
            if "RuleImage" in ruleimage_param and ruleimage_param.endswith(")"):
                # 提取参数部分
                params_str = ruleimage_param[10:-1]  # 去掉"RuleImage("和最后的")"

                # 使用正则表达式一次性提取所有参数
                roi_front_match = re.search(r'roi_front=\(([^)]+)\)', params_str)
                roi_back_match = re.search(r'roi_back=\(([^)]+)\)', params_str)
                threshold_match = re.search(r'threshold=([\d.]+)', params_str)
                method_match = re.search(r'method=([\'"])([^\'"]+)\1', params_str)
                file_match = re.search(r'file=([\'"])([^\'"]+)\1', params_str)
                
                if not all([roi_front_match, roi_back_match, threshold_match, method_match, file_match]):
                    self.log_print("RuleImage参数格式不正确", "error")
                    return
                
                roi_front = tuple(map(int, roi_front_match.group(1).split(',')))
                roi_back = tuple(map(int, roi_back_match.group(1).split(',')))
                threshold = float(threshold_match.group(1))
                method = method_match.group(2)
                file = file_match.group(2)

                # 创建RuleImage对象
                template_rule = RuleImage(
                    roi_front=roi_front,
                    roi_back=roi_back,
                    threshold=threshold,
                    method=method,
                    file=file
                )

                self._perform_match(template_rule)
            else:
                self.log_print("RuleImage参数格式不正确", "error")

        except Exception as e:
            self.log_print(f"RuleImage参数解析出错: {str(e)}", "error")

    def _perform_match(self, template_rule):
        try:
            print(f"RuleImage: {template_rule}")
            # 转换图片格式
            rgb_image = cv2.cvtColor(self.np_image, cv2.COLOR_BGR2RGB)

            # 在画布上绘制匹配结果
            self.screen_canvas.delete("match_result")
            roi = template_rule.roi_back
            # 统一坐标系统：现在画布坐标和图像坐标一致，无需偏移
            canvas_x1, canvas_y1 = roi[0], roi[1]
            canvas_x2, canvas_y2 = roi[2], roi[3]
            self.screen_canvas.create_rectangle(
                canvas_x1, canvas_y1, canvas_x1 + canvas_x2, canvas_y1 + canvas_y2,
                outline="blue", width=1, tags="match_result"  # 使用不同颜色区分
            )

            # 执行模板匹配
            match_result, max_val = template_rule.match_test(rgb_image)

            # 显示结果
            if match_result:
                # 在画布上绘制匹配结果
                self.screen_canvas.delete("match_result")
                roi = template_rule.roi_front
                # 统一坐标系统：现在画布坐标和图像坐标一致，无需偏移
                canvas_x1, canvas_y1 = roi[0], roi[1]
                canvas_x2, canvas_y2 = roi[2], roi[3]
                self.screen_canvas.create_rectangle(
                    canvas_x1, canvas_y1, canvas_x1 + canvas_x2, canvas_y1 + canvas_y2,
                    outline="green", width=1, tags="match_result"  # 使用不同颜色区分
                )
                self.log_print(f"匹配成功 {roi} 置信度 [{max_val}]")
            else:
                self.log_print(f"匹配失败 置信度 [{max_val}]", "error")
        except Exception as e:
            self.log_print(f"匹配执行出错: {str(e)}", "error")

    def open_mask_generator(self):
        """打开蒙版生成器"""
        try:
            # 构建命令行参数
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mask_generator.py")
            # 启动子进程
            subprocess.Popen([self.python_executable, script_path])
        except Exception as e:
            self.log_print(f"启动蒙版生成器时出错: {str(e)}", "error")

    def run_assets_extract(self):
        """生成 assets"""
        try:
            # 构建命令行参数
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets_extract.py")
            # 启动子进程
            subprocess.Popen([self.python_executable, script_path])
            self.log_print("执行 assets_extract 成功", "success")
        except Exception as e:
            self.log_print(f"执行 assets_extract 出错: {str(e)}", "error")

    def check_canvas_size(self):
        """检查画布实际尺寸"""
        canvas_width = self.screen_canvas.winfo_width()
        canvas_height = self.screen_canvas.winfo_height()
        requested_width = self.screen_canvas.cget("width")
        requested_height = self.screen_canvas.cget("height")
        self.log_print(f"画布请求尺寸: {requested_width}x{requested_height}")
        self.log_print(f"画布实际尺寸: {canvas_width}x{canvas_height}")
        # 同时检查Canvas的配置
        self.log_print(f"Canvas配置: width={self.screen_canvas['width']}, height={self.screen_canvas['height']}")
        # 检查Canvas的边界框
        bbox = self.screen_canvas.bbox("all")
        if bbox:
            self.log_print(f"Canvas内容边界: {bbox}")
        else:
            self.log_print("Canvas中没有内容")
        
        # 检查父容器尺寸
        frame_width = self.canvas_frame.winfo_width()
        frame_height = self.canvas_frame.winfo_height()
        self.log_print(f"父容器尺寸: {frame_width}x{frame_height}")
        
        # 输出当前坐标系统信息
        self.log_print(f"当前坐标系统: 画布尺寸{requested_width}x{requested_height}，图像尺寸应为1280x720")
        
    # 辅助方法：检查矩形是否有效
    def is_rect_valid(self):
        """检查当前选择的矩形是否有效"""
        x1, y1, x2, y2 = self.coordinates
        return x1 != x2 and y1 != y2

    # 新增功能：更新阈值标签
    def update_threshold_label(self, value):
        """更新阈值标签显示"""
        self.threshold_label.configure(text=f"匹配阈值: {float(value):.2f}")

    def clear_log(self):
        """清空日志框内容"""
        self.log_box.delete("0.0", "end")

    def refresh_emulators(self):
        """刷新模拟器列表"""
        try:
            # 检查MuMuManager是否存在
            if not self.mumu_manager_path:
                self.log_print("未找到MuMuManager.exe，请检查安装路径", "error")
                return
            
            # 隐藏CMD窗口执行命令
            startupinfo = None
            if os.name == 'nt':  # Windows系统
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            # 执行命令获取模拟器信息
            self.log_print("正在获取模拟器列表...")
            result = subprocess.run(
                [self.mumu_manager_path, "info", "-v", "all"],
                capture_output=True, 
                text=True, 
                timeout=10,
                startupinfo=startupinfo,
                encoding='utf-8'  # 明确指定编码
            )
            
            if result.returncode != 0:
                self.log_print(f"获取模拟器列表失败: {result.stderr}", "error")
                return
            
            # 解析JSON输出
            try:
                emulators_info = json.loads(result.stdout)
                emulator_list = []
                self.emulator_info_dict = {}  # 保存模拟器信息用于后续选择
                
                # 处理每个模拟器实例
                for index, emulator in emulators_info.items():
                    # 跳过非模拟器信息的条目（如版本信息等）
                    if not isinstance(emulator, dict):
                        continue
                        
                    name = emulator.get("name", f"模拟器{index}")
                    adb_port = emulator.get("adb_port", None)
                    
                    # adb_port存在即代表模拟器已启动
                    if adb_port is not None:
                        display_name = f"{name} ({adb_port})"
                        emulator_list.append(display_name)
                        self.emulator_info_dict[display_name] = {
                            "name": name,
                            "adb_port": adb_port,
                            "index": index
                        }
                
                if not emulator_list:
                    emulator_list = ["未找到已启动的模拟器"]
                    self.log_print("未找到已启动的模拟器")
                else:
                    self.log_print(f"找到 {emulator_list} 模拟器")
                
                # 更新下拉框
                self.emulator_selector.configure(values=emulator_list)
                # 只有在当前没有有效选择时才设置默认值
                current_value = self.emulator_selector.get()
                if current_value in ["请选择模拟器", "未找到已启动的模拟器"] or current_value not in emulator_list:
                    self.emulator_selector.set(emulator_list[0])
                
            except json.JSONDecodeError as e:
                self.log_print(f"解析模拟器信息失败: {e}", "error")
                self.log_print(f"原始输出: {result.stdout}", "error")
                
        except subprocess.TimeoutExpired:
            self.log_print("获取模拟器列表超时", "error")
        except Exception as e:
            self.log_print(f"刷新模拟器列表时出错: {str(e)}", "error")

    def on_emulator_selected(self, choice):
        """当选择模拟器时的回调函数"""
        if choice != "请选择模拟器" and choice != "未找到已启动的模拟器" and choice in self.emulator_info_dict:
            self.log_print(f"已选择模拟器: {choice}")

    def capture_emulator_screenshot(self):
        """从模拟器截取画面"""
        try:
            # 获取从下拉框选择的模拟器信息
            selected_emulator = self.emulator_selector.get()
            if selected_emulator in ["请选择模拟器", "未找到已启动的模拟器"]:
                self.log_print("请先选择一个模拟器", "error")
                return
                
            if selected_emulator not in self.emulator_info_dict:
                self.log_print("选择的模拟器信息无效", "error")
                return
                
            # 从选择的模拟器中获取端口号
            adb_port = self.emulator_info_dict[selected_emulator]["adb_port"]
            device_address = f"127.0.0.1:{adb_port}"
            
            # 构建ADB路径
            adb_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "toolkit", "Lib", "site-packages", "adbutils", "binaries", "adb.exe")
            if not os.path.exists(adb_path):
                # 如果指定路径不存在，则使用系统PATH中的adb
                adb_path = "adb"
                self.log_print("使用系统PATH中的ADB工具")
            else:
                self.log_print(f"使用ADB路径: {adb_path}")
            
            # 隐藏CMD窗口执行ADB命令
            startupinfo = None
            if os.name == 'nt':  # Windows系统
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            # 连接设备
            self.log_print(f"正在连接设备: {device_address}")
            connect_result = subprocess.run(
                [adb_path, "connect", device_address], 
                capture_output=True, 
                text=True, 
                timeout=10,
                startupinfo=startupinfo
            )
            
            if connect_result.returncode != 0:
                self.log_print(f"连接设备失败: {connect_result.stderr}", "error")
                return
                
            self.log_print(f"设备连接成功: {device_address}")
            
            # 获取屏幕截图
            self.log_print("正在获取屏幕截图...")
            screenshot_result = subprocess.run(
                [adb_path, "-s", device_address, "shell", "screencap", "-p"], 
                capture_output=True, 
                timeout=30,
                startupinfo=startupinfo
            )
            
            if screenshot_result.returncode != 0:
                self.log_print(f"截图命令执行失败: {screenshot_result.stderr}", "error")
                return
                
            # 检查是否有截图数据
            if not screenshot_result.stdout:
                self.log_print("截图命令没有返回数据", "error")
                return
                
            # 处理截图数据
            screenshot_data = screenshot_result.stdout
            
            if os.name == 'nt':  # Windows系统
                screenshot_data = screenshot_data.replace(b'\r\n', b'\n')
                
            # 将截图数据转换为numpy数组
            nparr = np.frombuffer(screenshot_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                self.log_print("无法解码截图数据", "error")
                return
                
            # 检查图片尺寸并调整（如果需要）
            if img.shape[1] != 1280 or img.shape[0] != 720:
                self.log_print(f"截图尺寸 {img.shape[1]}x{img.shape[0]} 不符合1280x720", "error")
                return

            # 保存截图到文件
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            filename = f"MuMu12-{timestamp}.png"
            save_path = os.path.join(self.save_img_path, filename)
            
            # 确保目录存在
            self._ensure_directory_exists(self.save_img_path)
            
            # 检查图像数据
            if img is None:
                self.log_print("图像数据为空", "error")
                return
                
            # 直接使用PIL保存
            try:
                pil_image = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
                pil_image.save(save_path, 'PNG')
            except Exception as e:
                self.log_print(f"PIL截图保存失败: {str(e)}", "error")
                return
            
            # 加载截图到界面
            self.load_image_by_path(save_path)
            self.log_print(f"模拟器截图已保存: {filename}", "success")
            
            # 更新图片列表，将新截图加入列表
            self.update_image_files(self.save_img_path)

        except subprocess.TimeoutExpired:
            self.log_print("截图操作超时", "error")
        except FileNotFoundError:
            self.log_print("未找到ADB工具，请确保已安装并添加到系统路径或使用项目自带的ADB", "error")
        except Exception as e:
            self.log_print(f"截取模拟器画面时出错: {str(e)}", "error")

    def load_latest_image_at_startup(self):
        """启动时自动扫描目录并加载最新图片"""
        folder_path = self.screenshots_path  # 使用默认目录

        # 检查目录是否存在
        if not os.path.exists(folder_path):
            self.log_print(f"目录不存在: {folder_path}", "error")
            return

        # 扫描目录中的1280x720 PNG文件
        self.update_image_files(folder_path, is_file_path=False)

        # 如果找到图片，加载最新的
        if self.image_files:
            latest_image_path = self.image_files[-1]  # 最后一张是最新图片
            self.load_image_by_path(latest_image_path)
        else:
            self.log_print("目录中没有符合条件的1280x720 PNG图片", "error")

    def _get_valid_images_from_folder(self, folder_path):
        """获取文件夹中所有1280x720的PNG图片文件"""
        all_files = []
        for f in os.listdir(folder_path):
            if f.lower().endswith('.png'):
                # 检查图片尺寸是否为1280x720
                img_path = os.path.join(folder_path, f)
                try:
                    img = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), cv2.IMREAD_COLOR)
                    if img is not None and img.shape[1] == 1280 and img.shape[0] == 720:
                        all_files.append(f)
                except Exception:
                    continue
        return all_files

    def update_image_files(self, folder_path_or_file_path, is_file_path=False):
        """
        更新图片文件列表
        :param folder_path_or_file_path: 文件夹路径或文件路径
        :param is_file_path: 是否为文件路径，如果是则需要根据当前文件设置索引
        """
        if is_file_path:
            folder_path = os.path.dirname(folder_path_or_file_path)
            current_filename = os.path.basename(folder_path_or_file_path)
        else:
            folder_path = folder_path_or_file_path
            current_filename = None

        all_files = self._get_valid_images_from_folder(folder_path)

        # 按修改时间排序
        all_files.sort(key=lambda x: os.path.getmtime(os.path.join(folder_path, x)))

        self.image_files = [os.path.join(folder_path, f) for f in all_files]

        if is_file_path and current_filename:
            # 直接通过文件名比较来确定当前图片索引
            self.current_image_index = -1
            for i, img_path in enumerate(self.image_files):
                if os.path.basename(img_path) == current_filename:
                    self.current_image_index = i
                    break
        else:
            # 设置当前索引为最后一张图片（最新图片）
            if self.image_files:
                self.current_image_index = len(self.image_files) - 1
            else:
                self.current_image_index = -1


if __name__ == "__main__":
    app = DevTool()
    app.mainloop()
