# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
import sys

import logging
import os
from datetime import date
from io import TextIOBase
from logging.handlers import TimedRotatingFileHandler
from rich.console import Console, ConsoleOptions, ConsoleRenderable, NewLine, RenderResult
from rich.highlighter import NullHighlighter
from rich.logging import RichHandler
from rich.rule import Rule
from typing import Callable, List


def empty_function(*args, **kwargs):
    pass


# Ensure running in Alas root folder
os.chdir(os.path.join(os.path.dirname(__file__), '../'))
# cnocr will set root logger in cnocr.utils
# Delete logging.basicConfig to avoid logging the same message twice.
logging.basicConfig = empty_function
logging.raiseExceptions = True  # Set True if wanna see encode errors on console

# Remove HTTP keywords (GET, POST etc.)
# RichHandler.KEYWORDS = []


# def show_handlers(handlers):
#     # 获取并打印日志记录器中处理器的信息
#     for handler in logger.handlers:
#         # 获取处理器的类名
#         handler_class = handler.__class__.__name__
#         print(f"Handler class: {handler_class}")
#
#         # 获取处理器的级别
#         handler_level = logging.getLevelName(handler.level)
#         print(f"Handler level: {handler_level}")
#
#         # 获取处理器的格式化器
#         formatter = handler.formatter
#         if formatter is not None:
#             formatter_class = formatter.__class__.__name__
#             print(f"Formatter class: {formatter_class}")
#
#         # 其他处理器的属性和方法，根据需要进行获取和打印
#         print()  # 打印空行，用于分隔处理器的信息


# Logger init
logger_debug = False
logger = logging.getLogger('oas')
logger.setLevel(logging.DEBUG if logger_debug else logging.INFO)
logging.addLevelName(logging.WARNING, "WARN")
file_formatter = logging.Formatter(
    fmt='%(asctime)s.%(msecs)03d|%(filename)14.14s:%(lineno)03d|%(levelname)4s| %(message)s',
    datefmt='%Y%m%d %H:%M:%S')
console_formatter = logging.Formatter(
    fmt='%(asctime)s.%(msecs)03d │ %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
flutter_formatter = logging.Formatter(
    fmt='%(levelname)1s | %(asctime)s.%(msecs)03d | %(message)s', datefmt='%H:%M:%S')

# ======================================================================================================================
#            Set console logger
# ======================================================================================================================
console_hdlr = RichHandler(
    console=Console(
        width=120
    ),
    show_path=False,
    show_time=False,
    rich_tracebacks=True,
    tracebacks_show_locals=True,
    tracebacks_extra_lines=3,
    tracebacks_width=160
)
console_hdlr.setFormatter(console_formatter)
logger.addHandler(console_hdlr)
# logger.py

log_path = r'.\log'
# 使用 os.path.join 进行路径拼接，确保跨平台兼容性
backup_path = os.path.join(log_path, 'backup')
week_path = os.path.join(log_path, '每周任务')
error_path = os.path.join(log_path, 'error')

delete_path = os.path.join(backup_path, 'delete_home')
old_path = os.path.join(backup_path, 'old_folder')


def get_filename(config_name):
    datetime_now = datetime.now()
    today_date = datetime_now.strftime('%Y-%m-%d')
    today_time = format_chinese_time(datetime_now)
    today_weekday = datetime.now().strftime("%A")
    filename = f"{config_name} {today_date} {today_time}"
    return filename


from datetime import datetime


def get_time_period(hour: int) -> str:
    """智能匹配中文时间段（支持自定义规则）"""
    periods = [
        (0, "凌晨"),
        (6, "早晨"),
        (9, "上午"),
        (12, "中午"),
        (13, "下午"),
        (18, "傍晚"),
        (20, "晚上")
    ]
    # 逆序匹配第一个符合条件的时间段
    return next((name for threshold, name in reversed(periods) if hour >= threshold), "凌晨")


def format_chinese_time(dt: datetime = None) -> str:
    """生成带秒数的中文时间描述"""
    dt = dt or datetime.now()
    hour = dt.hour
    period = get_time_period(hour)
    hour_12 = 12 if (h := hour % 12) == 0 else h  # 海象运算符简化代码
    time_str = f"{period} {hour_12}点{dt.minute:02d}分{dt.second:02d}"
    return time_str


class Logger:
    def __init__(self):
        self.log_file_path = log_path

    def log(self, message):
        with open(self.log_file_path, 'a') as file:
            file.write(message + '\n')


# ======================================================================================================================
#            Set file
# ======================================================================================================================
class RichFileHandler(RichHandler):
    # Rename
    pass


class SafeTimedRotatingFileHandler(TimedRotatingFileHandler):
    def doRollover(self):
        if self.stream:
            self.stream.close()  # 显式关闭当前文件流
        super().doRollover()


# Add file logger
pyw_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]

# 定义常量
ignore_log_names = {'assets_test', 'assets_extract', 'script', 'script_task', 'base_task',
                    'config', 'template', 'gui', 'killOAS', 'installer', 'devtool', 'ocrServer'}


def set_file_logger(name=pyw_name):
    log_home = log_path + f''
    if name in ignore_log_names:
        return
        # log_file = os.path.join(log_home, f"{name}.log")
    elif name == 'server':
        log_file = os.path.join(log_home, "server.log")
    else:
        log_file = os.path.join(log_home, f"{date.today()}_{name}.log")
    # logger.info(f'Log file : {log_file}')
    os.makedirs(log_home, exist_ok=True)

    # 确保日志文件路径正确
    file_handler = SafeTimedRotatingFileHandler(
        filename=log_file,
        when='midnight',
        interval=1,
        backupCount=7,
        encoding='utf-8',
        utc=False,  # 使用本地时区
    )
    file_console = Console(
        file=file_handler.stream,
        no_color=True,
        highlight=False,
        width=160,
    )

    hdlr = RichFileHandler(
        console=file_console,
        show_path=False,
        show_time=False,
        show_level=False,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
        tracebacks_extra_lines=3,
        tracebacks_width=160,
        highlighter=NullHighlighter(),
    )
    hdlr.setFormatter(file_formatter)

    # 删除旧处理器时，增加调试输出
    logger.handlers = [h for h in logger.handlers if not isinstance(
        h, (logging.FileHandler, RichFileHandler))]
    # print(logger.handlers)  # 确认只剩控制台处理器
    logger.addHandler(hdlr)
    # print(logger.handlers)  # 确认只剩控制台处理器
    logger.log_file = log_file


# ======================================================================================================================
#            Set flutter
# ======================================================================================================================
class FlutterHandler(RichHandler):
    # Rename
    pass


class FlutterConsole(Console):
    """
    Force full feature console
    but not working lol :(
    """

    @property
    def options(self) -> ConsoleOptions:
        return ConsoleOptions(
            max_height=self.size.height,
            size=self.size,
            legacy_windows=False,
            min_width=1,
            max_width=self.width,
            encoding='utf-8',
            is_terminal=False,
        )


class FlutterLogStream(TextIOBase):
    def __init__(self, *args, func: Callable[[ConsoleRenderable], None] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._func = func

    def write(self, msg: str) -> int:
        if isinstance(msg, bytes):
            msg = msg.decode("utf-8")
        self._func(msg)
        return len(msg)


def set_func_logger(func):
    stream = FlutterLogStream(func=func)
    stream_console = Console(
        file=stream,
        force_terminal=False,
        force_interactive=False,
        no_color=True,
        highlight=False,
        width=80,
    )
    hdlr = FlutterHandler(
        console=stream_console,
        show_path=False,
        show_time=False,
        show_level=False,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
        tracebacks_extra_lines=3,
        highlighter=NullHighlighter(),
    )
    hdlr.setFormatter(flutter_formatter)
    logger.addHandler(hdlr)


# ======================================================================================================================
#            Set print format
# ======================================================================================================================


def _get_renderables(
        self: Console, *objects, sep=" ", end="\n", justify=None, emoji=None, markup=None, highlight=None,
) -> List[ConsoleRenderable]:
    """
    Refer to rich.console.Console.print()
    """
    if not objects:
        objects = (NewLine(),)

    render_hooks = self._render_hooks[:]
    with self:
        renderables = self._collect_renderables(
            objects,
            sep,
            end,
            justify=justify,
            emoji=emoji,
            markup=markup,
            highlight=highlight,
        )
        for hook in render_hooks:
            renderables = hook.process_renderables(renderables)
    return renderables


def print(*objects: ConsoleRenderable, **kwargs):
    for hdlr in logger.handlers:
        if isinstance(hdlr, FlutterHandler):
            for renderable in _get_renderables(hdlr.console, *objects, **kwargs):
                hdlr.console.file._func(str(renderable))
        elif isinstance(hdlr, RichHandler):
            hdlr.console.print(*objects)


class GuiRule(Rule):
    def __rich_console__(
            self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        options.max_width = 80
        return super().__rich_console__(console, options)

    def __str__(self):
        total_width = 80
        cell_len = len(self.title) + 2
        aside_len = (total_width - cell_len) // 2
        left = self.characters * aside_len
        right = self.characters * (total_width - cell_len - aside_len)
        if self.title:
            space = ' '
        else:
            space = self.characters
        return f"{left}{space}{self.title}{space}{right}\n"

    def __repr__(self):
        return self.__str__()


def rule(title="", *, characters="─", style="rule.line", end="\n", align="center"):
    # 确保使用基本字符避免编码问题
    if characters == "":
        characters = "-"
    rule = GuiRule(title=title, characters=characters,
                   style=style, end=end)
    print(rule)


def hr(title, level=3):
    # title = str(title).upper()
    if level == 1:
        logger.rule(title, characters='═')
        # logger.info(title)
    if level == 2:
        logger.rule(title, characters='─')
        # logger.info(title)
    if level == 3:
        logger.info(f"[bold]<<< {title} >>>[/bold]", extra={"markup": True})
    if level == 0:
        logger.rule(characters='═')
        logger.rule(title, characters='─')
        logger.rule(characters='═')


def attr(name, text):
    logger.info('[%s] %s' % (str(name), str(text)))


def attr_align(name, text, front='', align=22):
    name = str(name).rjust(align)
    if front:
        name = front + name[len(front):]
    logger.info('%s: %s' % (name, str(text)))


def show():
    logger.info('INFO')
    logger.warning('WARNING')
    logger.debug('DEBUG')
    logger.error('ERROR')
    logger.critical('CRITICAL')
    logger.hr('hr0', 0)
    logger.hr('hr1', 1)
    logger.hr('hr2', 2)
    logger.hr('hr3', 3)
    logger.info(r'Brace { [ ( ) ] }')
    logger.info(r'True, False, None')
    logger.info(r'E:/path\\to/alas/alas.exe, /root/alas/, ./relative/path/log.txt')
    logger.info(
        'Tests very long strings. Tests very long strings. Tests very long strings. Tests very long strings. Tests very long strings.')
    local_var1 = 'This is local variable'
    # Line before exception
    raise Exception("Exception")
    # Line below exception


def error_convert(func):
    def error_wrapper(msg, *args, **kwargs):
        if isinstance(msg, Exception):
            msg = f'{type(msg).__name__}: {msg}'
        return func(msg, *args, **kwargs)

    return error_wrapper


logger.error = error_convert(logger.error)
logger.hr = hr
logger.attr = attr
logger.attr_align = attr_align
logger.set_file_logger = set_file_logger
logger.set_func_logger = set_func_logger
logger.rule = rule
logger.print = print
logger.log_file: str

logger.set_file_logger()
logger.hr('Start', level=0)
