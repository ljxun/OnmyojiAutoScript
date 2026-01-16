from PyQt5.QtCore import QObject, pyqtSignal
from typing import Dict, Any


class ThemeManager(QObject):
    """主题管理器"""

    theme_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.themes = {
            "默认": {
                "bg": "#f0f0f0",
                "fg": "#000000",
                "select_bg": "#0078d4",
                "select_fg": "#ffffff",
                "button_bg": "#e1e1e1",
                "button_fg": "#000000",
                "button_active_bg": "#d1d1d1",
                "entry_bg": "#ffffff",
                "entry_fg": "#000000",
                "frame_bg": "#f0f0f0",
                "canvas_bg": "#ffffff",
                "listbox_bg": "#ffffff",
                "listbox_fg": "#000000",
                "label_fg": "#000000",
                "text_bg": "#ffffff",
                "text_fg": "#000000",
                "scrollbar_bg": "#e1e1e1",
                "relief": "flat",
                "borderwidth": 1,
                # 标题栏主题色
                "title_bg": "#e1e1e1",
                "title_fg": "#000000",
                "button_hover_bg": "#d1d1d1",
                "close_hover_bg": "#e81123"
            },
            "深色": {
                "bg": "#2b2b2b",
                "fg": "#ffffff",
                "select_bg": "#404040",
                "select_fg": "#ffffff",
                "button_bg": "#404040",
                "button_fg": "#ffffff",
                "button_active_bg": "#505050",
                "entry_bg": "#404040",
                "entry_fg": "#ffffff",
                "frame_bg": "#2b2b2b",
                "canvas_bg": "#1e1e1e",
                "listbox_bg": "#404040",
                "listbox_fg": "#ffffff",
                "label_fg": "#ffffff",
                "text_bg": "#404040",
                "text_fg": "#ffffff",
                "scrollbar_bg": "#505050",
                "relief": "flat",
                "borderwidth": 1,
                # 标题栏主题色
                "title_bg": "#2b2b2b",
                "title_fg": "#ffffff",
                "button_hover_bg": "#505050",
                "close_hover_bg": "#e81123"
            },
            "现代蓝": {
                "bg": "#f5f7fa",
                "fg": "#2c3e50",
                "select_bg": "#3498db",
                "select_fg": "#ffffff",
                "button_bg": "#3498db",
                "button_fg": "#ffffff",
                "button_active_bg": "#2980b9",
                "entry_bg": "#ffffff",
                "entry_fg": "#2c3e50",
                "frame_bg": "#f5f7fa",
                "canvas_bg": "#ffffff",
                "listbox_bg": "#ffffff",
                "listbox_fg": "#2c3e50",
                "label_fg": "#2c3e50",
                "text_bg": "#ffffff",
                "text_fg": "#2c3e50",
                "scrollbar_bg": "#bdc3c7",
                "relief": "flat",
                "borderwidth": 0,
                # 标题栏主题色
                "title_bg": "#3498db",
                "title_fg": "#ffffff",
                "button_hover_bg": "#2980b9",
                "close_hover_bg": "#e74c3c"
            },
        }
        self.current_theme = "深色"

    def get_theme(self, theme_name: str = None) -> Dict[str, Any]:
        """获取指定主题配置"""
        if theme_name is None:
            theme_name = self.current_theme
        return self.themes.get(theme_name, self.themes["默认"])

    def get_theme_names(self) -> list:
        """获取所有主题名称"""
        return list(self.themes.keys())

    def set_theme(self, theme_name: str):
        """设置当前主题"""
        if theme_name in self.themes:
            self.current_theme = theme_name
            self.theme_changed.emit(theme_name)
