"""
高级蒙版生成器 - 提供多种蒙版生成方式和手动编辑功能

这个工具提供了一个图形界面，允许用户：
1. 加载图像文件
2. 选择不同的蒙版生成方式
3. 调整各种参数
4. 手动编辑蒙版细节
5. 实时预览原图和应用蒙版后的效果
6. 保存生成的蒙版
"""

from tkinter import filedialog, Canvas

import customtkinter as ctk

import cv2
import numpy as np
import os
from PIL import Image, ImageTk
from numpy import fromfile


class MaskGenerator(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 配置窗口
        self.title("高级蒙版生成器")
        self.geometry("1200x800")
        ctk.set_appearance_mode("dark")

        # 初始化变量
        self.current_image = None
        self.current_image_path = None
        self.mask = None
        self.editing = False
        self.last_x = None
        self.last_y = None
        self.edit_mode = "draw"  # "draw" or "erase"
        self.shape_mode = "free"  # "free", "rectangle", "circle", "ellipse"
        self.shape_start_pos = None
        self.temp_shape_id = None
        self.brush_size = 10
        self.scale_factor = 1.0
        self.image_position = (0, 0)
        self.brush_indicators = []  # 存储所有画笔指示器的ID

        # 参数变量
        self.method_var = ctk.StringVar(value="threshold")
        self.threshold_var = ctk.IntVar(value=127)
        self.block_size_var = ctk.IntVar(value=11)
        self.c_var = ctk.IntVar(value=2)
        self.blur_size_var = ctk.IntVar(value=5)
        self.canny_low_var = ctk.IntVar(value=100)
        self.canny_high_var = ctk.IntVar(value=200)
        self.hue_low_var = ctk.IntVar(value=0)
        self.hue_high_var = ctk.IntVar(value=180)
        self.sat_low_var = ctk.IntVar(value=0)
        self.sat_high_var = ctk.IntVar(value=255)
        self.val_low_var = ctk.IntVar(value=0)
        self.val_high_var = ctk.IntVar(value=255)
        self.invert_var = ctk.BooleanVar(value=False)
        self.blur_enabled_var = ctk.BooleanVar(value=False)

        # 创建UI元素
        self.create_widgets()

    def create_widgets(self):
        # 主布局
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 左侧控制面板
        control_frame = ctk.CTkFrame(main_frame)
        control_frame.pack(side="left", fill="y", padx=10, pady=10)

        # 标题
        title_label = ctk.CTkLabel(control_frame, text="高级蒙版生成器", font=ctk.CTkFont(size=20, weight="bold"))
        title_label.pack(pady=10)

        # 文件操作框架
        file_frame = ctk.CTkFrame(control_frame)
        file_frame.pack(pady=10, fill="x")

        # 文件选择按钮
        self.select_btn = ctk.CTkButton(file_frame, text="选择图片", command=self.select_image, width=100)
        self.select_btn.pack(side="left", padx=5, pady=5)

        # 保存按钮
        self.quick_save_btn = ctk.CTkButton(file_frame, text="保存蒙版", command=self.quick_save_mask, width=100)
        self.quick_save_btn.pack(side="right", padx=5, pady=5)

        # 文件名标签
        self.file_label = ctk.CTkLabel(control_frame, text="未选择文件")
        self.file_label.pack(pady=5)

        # 编辑工具框架
        edit_frame = ctk.CTkFrame(control_frame)
        edit_frame.pack(pady=10, fill="x")

        ctk.CTkLabel(edit_frame, text="编辑工具:").pack(pady=5)

        # 工具选择按钮
        tools_frame = ctk.CTkFrame(edit_frame)
        tools_frame.pack(fill="x", padx=5)

        ctk.CTkButton(tools_frame, text="绘制", width=60, command=lambda: self.set_edit_mode("draw")).pack(side="left", padx=2)

        ctk.CTkButton(tools_frame, text="擦除", width=60, command=lambda: self.set_edit_mode("erase")).pack(side="left", padx=2)

        ctk.CTkButton(tools_frame, text="撤销", width=60, command=self.undo_edit).pack(side="right", padx=2)

        # 形状选择
        shape_frame = ctk.CTkFrame(edit_frame)
        shape_frame.pack(fill="x", pady=5)
        ctk.CTkButton(shape_frame, text="自由绘制", width=80, command=lambda: self.set_shape_mode("free")).pack(side="left", padx=2)
        ctk.CTkButton(shape_frame, text="矩形", width=60, command=lambda: self.set_shape_mode("rectangle")).pack(side="left", padx=2)
        ctk.CTkButton(shape_frame, text="椭圆", width=60, command=lambda: self.set_shape_mode("ellipse")).pack(side="left", padx=2)
        ctk.CTkButton(shape_frame, text="正圆", width=60, command=lambda: self.set_shape_mode("circle")).pack(side="left", padx=2)

        # 画笔大小调节
        brush_frame = ctk.CTkFrame(edit_frame)
        brush_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(brush_frame, text="画笔大小:").pack(side="left", padx=5)

        self.brush_size_label = ctk.CTkLabel(brush_frame, text=str(self.brush_size))
        self.brush_size_label.pack(side="right", padx=5)

        brush_slider = ctk.CTkSlider(edit_frame, from_=1, to=50, command=self.update_brush_size)
        brush_slider.pack(fill="x", padx=10, pady=5)
        brush_slider.set(self.brush_size)

        # 方法选择（使用下拉框）
        method_frame = ctk.CTkFrame(control_frame)
        method_frame.pack(pady=10, fill="x")

        ctk.CTkLabel(method_frame, text="蒙版生成方式:").pack(pady=5)

        methods = {"简单阈值": "threshold", "Otsu阈值": "otsu", "自适应阈值": "adaptive", "Canny边缘检测": "canny", "颜色范围": "color"}

        method_menu = ctk.CTkOptionMenu(method_frame, values=list(methods.keys()), command=lambda x: self.change_method(methods[x]))
        method_menu.pack(pady=5, fill="x", padx=10)
        method_menu.set("简单阈值")  # 设置默认值

        # 预处理选项
        preprocess_frame = ctk.CTkFrame(control_frame)
        preprocess_frame.pack(pady=10, fill="x")

        ctk.CTkLabel(preprocess_frame, text="预处理选项:").pack(pady=5)

        ctk.CTkCheckBox(preprocess_frame, text="启用模糊", variable=self.blur_enabled_var, command=self.update_image).pack(pady=2)

        # 参数调节区域（使用滚动框）
        param_canvas = ctk.CTkScrollableFrame(control_frame, height=300)
        param_canvas.pack(pady=10, fill="x")

        # 简单阈值参数
        self.threshold_frame = ctk.CTkFrame(param_canvas)
        ctk.CTkLabel(self.threshold_frame, text="阈值:").pack()
        ctk.CTkSlider(self.threshold_frame, from_=0, to=255, variable=self.threshold_var, command=lambda x: self.update_image()).pack(fill="x", padx=10)

        # 自适应阈值参数
        self.adaptive_frame = ctk.CTkFrame(param_canvas)
        ctk.CTkLabel(self.adaptive_frame, text="块大小:").pack()
        ctk.CTkSlider(self.adaptive_frame, from_=3, to=99, variable=self.block_size_var, command=lambda x: self.update_image()).pack(fill="x", padx=10)
        ctk.CTkLabel(self.adaptive_frame, text="C值:").pack()
        ctk.CTkSlider(self.adaptive_frame, from_=0, to=20, variable=self.c_var, command=lambda x: self.update_image()).pack(fill="x", padx=10)

        # Canny边缘检测参数
        self.canny_frame = ctk.CTkFrame(param_canvas)
        ctk.CTkLabel(self.canny_frame, text="低阈值:").pack()
        ctk.CTkSlider(self.canny_frame, from_=0, to=255, variable=self.canny_low_var, command=lambda x: self.update_image()).pack(fill="x", padx=10)
        ctk.CTkLabel(self.canny_frame, text="高阈值:").pack()
        ctk.CTkSlider(self.canny_frame, from_=0, to=255, variable=self.canny_high_var, command=lambda x: self.update_image()).pack(fill="x", padx=10)

        # 颜色范围参数
        self.color_frame = ctk.CTkFrame(param_canvas)
        ctk.CTkLabel(self.color_frame, text="色调范围:").pack()
        ctk.CTkSlider(self.color_frame, from_=0, to=180, variable=self.hue_low_var, command=lambda x: self.update_image()).pack(fill="x", padx=10)
        ctk.CTkSlider(self.color_frame, from_=0, to=180, variable=self.hue_high_var, command=lambda x: self.update_image()).pack(fill="x", padx=10)
        ctk.CTkLabel(self.color_frame, text="饱和度范围:").pack()
        ctk.CTkSlider(self.color_frame, from_=0, to=255, variable=self.sat_low_var, command=lambda x: self.update_image()).pack(fill="x", padx=10)
        ctk.CTkSlider(self.color_frame, from_=0, to=255, variable=self.sat_high_var, command=lambda x: self.update_image()).pack(fill="x", padx=10)
        ctk.CTkLabel(self.color_frame, text="亮度范围:").pack()
        ctk.CTkSlider(self.color_frame, from_=0, to=255, variable=self.val_low_var, command=lambda x: self.update_image()).pack(fill="x", padx=10)
        ctk.CTkSlider(self.color_frame, from_=0, to=255, variable=self.val_high_var, command=lambda x: self.update_image()).pack(fill="x", padx=10)

        # 模糊参数
        self.blur_frame = ctk.CTkFrame(param_canvas)
        ctk.CTkLabel(self.blur_frame, text="模糊大小:").pack()
        ctk.CTkSlider(self.blur_frame, from_=1, to=21, variable=self.blur_size_var, command=lambda x: self.update_image()).pack(fill="x", padx=10)

        # 反转选项
        ctk.CTkCheckBox(param_canvas, text="反转蒙版", variable=self.invert_var, command=self.update_image).pack(pady=10)

        # 创建右侧图像显示区域
        display_frame = ctk.CTkFrame(main_frame)
        display_frame.pack(side="right", padx=10, pady=10, expand=True, fill="both")

        # 原图显示
        original_frame = ctk.CTkFrame(display_frame)
        original_frame.pack(side="left", expand=True, fill="both", padx=5, pady=5)

        ctk.CTkLabel(original_frame, text="原图").pack(pady=5)

        self.original_canvas = Canvas(original_frame, width=400, height=500, bg="#1a1a1a", highlightthickness=0)
        self.original_canvas.pack(expand=True, fill="both", padx=5, pady=5)

        # 效果显示
        result_frame = ctk.CTkFrame(display_frame)
        result_frame.pack(side="right", expand=True, fill="both", padx=5, pady=5)

        ctk.CTkLabel(result_frame, text="效果预览（可编辑）").pack(pady=5)

        self.result_canvas = Canvas(result_frame, width=400, height=500, bg="#1a1a1a", highlightthickness=0)
        self.result_canvas.pack(expand=True, fill="both", padx=5, pady=5)

        # 绑定鼠标事件
        self.result_canvas.bind("<Button-1>", self.start_edit)
        self.result_canvas.bind("<B1-Motion>", self.edit)
        self.result_canvas.bind("<ButtonRelease-1>", self.stop_edit)
        # 添加鼠标移动事件
        self.result_canvas.bind("<Motion>", self.update_brush_indicator)
        self.result_canvas.bind("<Leave>", self.hide_brush_indicator)
        self.result_canvas.bind("<Enter>", self.show_brush_indicator)

        # 绑定窗口大小变化事件
        self.bind("<Configure>", self.on_resize)

        # 更新参数框架显示
        self.update_param_frames()

        # 初始化编辑历史
        self.edit_history = []
        self.max_history = 10

    def clear_brush_indicators(self):
        """清除所有画笔指示器"""
        for indicator_id in self.brush_indicators:
            self.result_canvas.delete(indicator_id)
        self.brush_indicators = []

    def update_brush_indicator(self, event):
        """更新画笔指示器位置和大小"""
        if self.mask is None or self.shape_mode != "free":
            self.clear_brush_indicators()
            return

        # 清除所有旧的画笔指示器
        self.clear_brush_indicators()

        # 计算画笔实际大小（考虑缩放）
        brush_radius = self.brush_size * self.scale_factor / 2

        # 创建新的画笔指示器
        x, y = event.x, event.y

        # 根据模式选择颜色
        if self.edit_mode == "draw":
            outline_color = "#00ff00"  # 绿色
        else:
            outline_color = "#ff0000"  # 红色

        # 创建外部轮廓
        outer_circle = self.result_canvas.create_oval(x - brush_radius, y - brush_radius, x + brush_radius, y + brush_radius, outline=outline_color, width=1)
        self.brush_indicators.append(outer_circle)

        # 添加内部轮廓
        inner_circle = self.result_canvas.create_oval(x - brush_radius + 1, y - brush_radius + 1, x + brush_radius - 1, y + brush_radius - 1, outline="#ffffff", width=1)
        self.brush_indicators.append(inner_circle)

    def hide_brush_indicator(self, event):
        """隐藏画笔指示器"""
        self.clear_brush_indicators()

    def show_brush_indicator(self, event):
        """显示画笔指示器"""
        if self.shape_mode == "free":
            self.update_brush_indicator(event)

    def change_method(self, method):
        """切换蒙版生成方式"""
        self.method_var.set(method)
        self.update_param_frames()
        self.update_image()

    def set_edit_mode(self, mode):
        """设置编辑模式（绘制或擦除）"""
        self.edit_mode = mode
        # 更新画笔指示器颜色
        if self.last_x is not None and self.last_y is not None:
            self.result_canvas.event_generate("<Motion>", x=self.last_x, y=self.last_y)

    def set_shape_mode(self, mode):
        """设置形状绘制模式"""
        self.shape_mode = mode
        if self.temp_shape_id:
            self.result_canvas.delete(self.temp_shape_id)
            self.temp_shape_id = None

        if mode != "free":
            self.clear_brush_indicators()
        elif self.last_x is not None:
            self.result_canvas.event_generate("<Motion>", x=self.last_x, y=self.last_y)

    def update_brush_size(self, value):
        """更新画笔大小"""
        self.brush_size = int(float(value))
        self.brush_size_label.configure(text=str(self.brush_size))
        # 更新画笔指示器
        if self.last_x is not None and self.last_y is not None:
            self.result_canvas.event_generate("<Motion>", x=self.last_x, y=self.last_y)

    def start_edit(self, event):
        """开始编辑"""
        if self.mask is None:
            return

        self.save_to_history()
        self.editing = True

        if self.shape_mode == "free":
            self.last_x = event.x
            self.last_y = event.y
            self.edit(event)  # 立即绘制一个点
        else:
            self.shape_start_pos = (event.x, event.y)

    def edit(self, event):
        """编辑蒙版"""
        if not self.editing or self.mask is None:
            return

        if self.shape_mode == "free":
            x, y = event.x, event.y
            img_x = int((x - self.image_position[0]) / self.scale_factor)
            img_y = int((y - self.image_position[1]) / self.scale_factor)
            last_img_x = int((self.last_x - self.image_position[0]) / self.scale_factor)
            last_img_y = int((self.last_y - self.image_position[1]) / self.scale_factor)

            h, w = self.mask.shape
            if 0 <= img_x < w and 0 <= img_y < h:
                color = 255 if self.edit_mode == "draw" else 0
                cv2.line(self.mask, (last_img_x, last_img_y), (img_x, img_y), color, self.brush_size)
                self.update_image(update_mask=False)

            self.last_x, self.last_y = x, y

        elif self.shape_mode in ["rectangle", "ellipse", "circle"]:
            if self.temp_shape_id:
                self.result_canvas.delete(self.temp_shape_id)

            start_x, start_y = self.shape_start_pos
            end_x, end_y = event.x, event.y
            outline_color = "#00ff00" if self.edit_mode == "draw" else "#ff0000"

            if self.shape_mode == "rectangle":
                self.temp_shape_id = self.result_canvas.create_rectangle(start_x, start_y, end_x, end_y, outline=outline_color, width=1)
            elif self.shape_mode == "ellipse":
                self.temp_shape_id = self.result_canvas.create_oval(start_x, start_y, end_x, end_y, outline=outline_color, width=1)
            elif self.shape_mode == "circle":
                center_x, center_y = self.shape_start_pos
                current_x, current_y = event.x, event.y
                radius = int(((current_x - center_x) ** 2 + (current_y - center_y) ** 2) ** 0.5)
                self.temp_shape_id = self.result_canvas.create_oval(center_x - radius, center_y - radius, center_x + radius, center_y + radius, outline=outline_color, width=1)

    def stop_edit(self, event):
        """停止编辑"""
        if not self.editing:
            return
        self.editing = False

        if self.temp_shape_id:
            self.result_canvas.delete(self.temp_shape_id)
            self.temp_shape_id = None

        if self.shape_mode in ["rectangle", "ellipse", "circle"] and self.shape_start_pos:
            start_x_canvas, start_y_canvas = self.shape_start_pos
            end_x_canvas, end_y_canvas = event.x, event.y

            if self.shape_mode in ["rectangle", "ellipse"]:
                start_x_img = int((min(start_x_canvas, end_x_canvas) - self.image_position[0]) / self.scale_factor)
                start_y_img = int((min(start_y_canvas, end_y_canvas) - self.image_position[1]) / self.scale_factor)
                end_x_img = int((max(start_x_canvas, end_x_canvas) - self.image_position[0]) / self.scale_factor)
                end_y_img = int((max(start_y_canvas, end_y_canvas) - self.image_position[1]) / self.scale_factor)

                if self.shape_mode == "rectangle":
                    if self.edit_mode == "draw":
                        self.mask = np.zeros(self.current_image.shape[:2], dtype=np.uint8)
                        cv2.rectangle(self.mask, (start_x_img, start_y_img), (end_x_img, end_y_img), 255, -1)
                    else:
                        cv2.rectangle(self.mask, (start_x_img, start_y_img), (end_x_img, end_y_img), 0, -1)
                elif self.shape_mode == "ellipse":
                    center = ((start_x_img + end_x_img) // 2, (start_y_img + end_y_img) // 2)
                    axes = ((end_x_img - start_x_img) // 2, (end_y_img - start_y_img) // 2)
                    if self.edit_mode == "draw":
                        self.mask = np.zeros(self.current_image.shape[:2], dtype=np.uint8)
                        cv2.ellipse(self.mask, center, axes, 0, 0, 360, 255, -1)
                    else:
                        cv2.ellipse(self.mask, center, axes, 0, 0, 360, 0, -1)

            elif self.shape_mode == "circle":
                center_x_canvas, center_y_canvas = self.shape_start_pos
                radius_canvas = int(((end_x_canvas - center_x_canvas) ** 2 + (end_y_canvas - center_y_canvas) ** 2) ** 0.5)
                center_x_img = int((center_x_canvas - self.image_position[0]) / self.scale_factor)
                center_y_img = int((center_y_canvas - self.image_position[1]) / self.scale_factor)
                radius_img = int(radius_canvas / self.scale_factor)

                if self.edit_mode == "draw":
                    self.mask = np.zeros(self.current_image.shape[:2], dtype=np.uint8)
                    cv2.circle(self.mask, (center_x_img, center_y_img), radius_img, 255, -1)
                else:
                    cv2.circle(self.mask, (center_x_img, center_y_img), radius_img, 0, -1)

            self.shape_start_pos = None
            self.update_image(update_mask=False)

    def save_to_history(self):
        """保存当前状态到历史记录"""
        if self.mask is not None:
            self.edit_history.append(self.mask.copy())
            if len(self.edit_history) > self.max_history:
                self.edit_history.pop(0)

    def undo_edit(self):
        """撤销上一次编辑"""
        if self.edit_history:
            self.mask = self.edit_history.pop()
            self.update_image(update_mask=False)

    def update_param_frames(self, *args):
        """根据选择的方法显示/隐藏相应的参数设置"""
        method = self.method_var.get()

        # 隐藏所有参数框架
        for frame in [self.threshold_frame, self.adaptive_frame, self.canny_frame, self.color_frame]:
            frame.pack_forget()

        # 显示相应的参数框架
        if method == "threshold" or method == "otsu":
            self.threshold_frame.pack(fill="x", pady=5)
        elif method == "adaptive":
            self.adaptive_frame.pack(fill="x", pady=5)
        elif method == "canny":
            self.canny_frame.pack(fill="x", pady=5)
        elif method == "color":
            self.color_frame.pack(fill="x", pady=5)

        # 模糊参数框架根据是否启用显示
        if self.blur_enabled_var.get():
            self.blur_frame.pack(fill="x", pady=5)
        else:
            self.blur_frame.pack_forget()

    def select_image(self):
        """选择图像文件"""
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif")])
        if file_path:
            self.current_image_path = file_path
            self.file_label.configure(text=os.path.basename(file_path))
            self.current_image = cv2.imdecode(fromfile(file_path, dtype=np.uint8), -1)
            self.edit_history = []  # 清空编辑历史
            self.update_image()

    def generate_mask(self):
        """根据选择的方法生成蒙版"""
        if self.current_image is None:
            return None

        # 转换为灰度图
        gray = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2GRAY)

        # 预处理 - 模糊
        if self.blur_enabled_var.get():
            blur_size = self.blur_size_var.get()
            if blur_size % 2 == 0:  # 确保是奇数
                blur_size += 1
            gray = cv2.GaussianBlur(gray, (blur_size, blur_size), 0)

        method = self.method_var.get()

        if method == "threshold":
            _, mask = cv2.threshold(gray, self.threshold_var.get(), 255, cv2.THRESH_BINARY)
        elif method == "otsu":
            _, mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        elif method == "adaptive":
            block_size = self.block_size_var.get()
            if block_size % 2 == 0:  # 确保是奇数
                block_size += 1
            mask = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, block_size, self.c_var.get())
        elif method == "canny":
            mask = cv2.Canny(gray, self.canny_low_var.get(), self.canny_high_var.get())
        elif method == "color":
            # 转换为HSV颜色空间
            hsv = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2HSV)
            # 创建颜色范围
            lower = np.array([self.hue_low_var.get(), self.sat_low_var.get(), self.val_low_var.get()])
            upper = np.array([self.hue_high_var.get(), self.sat_high_var.get(), self.val_high_var.get()])
            # 创建蒙版
            mask = cv2.inRange(hsv, lower, upper)

        # 反转蒙版
        if self.invert_var.get():
            mask = cv2.bitwise_not(mask)

        return mask

    def update_image(self, *args, update_mask=True):
        """更新显示的图像"""
        if self.current_image is None:
            return

        # 生成或更新蒙版
        if update_mask:
            self.mask = self.generate_mask()
        if self.mask is None:
            return

        # 创建应用蒙版后的效果图
        result = self.current_image.copy()
        result[self.mask == 0] = 0

        # 转换图像格式用于显示
        original_rgb = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2RGB)
        result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)

        original_pil = Image.fromarray(original_rgb)
        result_pil = Image.fromarray(result_rgb)

        # 显示图像
        self.display_image(original_pil, self.original_canvas)
        self.display_image(result_pil, self.result_canvas)

    def display_image(self, img, canvas):
        """在指定画布上显示图像"""
        # 获取画布尺寸
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()

        # 确保画布尺寸有效
        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width = 400
            canvas_height = 500

        # 计算缩放比例
        img_width, img_height = img.size
        scale = min(canvas_width / img_width, canvas_height / img_height)
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)

        # 保存缩放比例和图像位置（用于编辑功能）
        self.scale_factor = scale
        self.image_position = ((canvas_width - new_width) // 2, (canvas_height - new_height) // 2)

        # 缩放图像
        img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # 转换为PhotoImage并保存引用
        photo = ImageTk.PhotoImage(img_resized)
        if canvas == self.original_canvas:
            self.original_photo = photo
        else:
            self.result_photo = photo

        # 清除画布并显示新图像
        canvas.delete("all")
        canvas.create_image(canvas_width // 2, canvas_height // 2, image=photo, anchor="center")

    def on_resize(self, event):
        """当窗口大小变化时更新图像"""
        if self.current_image is not None:
            self.update_image(update_mask=False)

    def quick_save_mask(self):
        """快速保存蒙版到原图所在目录"""
        if self.mask is None or self.current_image_path is None:
            return

        # 生成保存路径
        dir_path = os.path.dirname(self.current_image_path)
        file_name = os.path.splitext(os.path.basename(self.current_image_path))[0]
        save_path = os.path.join(dir_path, f"{file_name}_mask.png")

        # 保存蒙版
        # result = cv2.imwrite(save_path, self.mask)
        result = cv2.imencode('.png', self.mask)[1].tofile(save_path)
        save_label = ctk.CTkLabel(self, text=f"已保存至: {os.path.basename(save_path)}", fg_color=("green", "#2D5"))
        save_label.place(relx=0.5, rely=0.9, anchor="center")

        # 2秒后移除消息
        self.after(2000, save_label.destroy)


if __name__ == "__main__":
    app = MaskGenerator()
    app.mainloop()
