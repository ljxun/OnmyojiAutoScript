# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
from enum import Enum
from pydantic import Field
from tasks.Component.config_base import ConfigBase, Time
from tasks.Component.config_scheduler import Scheduler


class ScrollNumber(str, Enum):
    ONE = "卷一"
    TWO = "卷二"
    THREE = "卷三"
    FOUR = "卷四"
    FIVE = "卷五"
    SIX = "卷六"


class MemoryScrollsConfig(ConfigBase):
    auto_contribute_memoryscrolls: bool = Field(default=True, description='自动贡献绘卷碎片')
    ranking: int = Field(default=80, description='排名多少前不进行贡献,0默认全部贡献')
    score: int = Field(default=200, description='一次贡献指定分数,0默认全部贡献')
    scroll_number: ScrollNumber = Field(default=ScrollNumber.ONE, description='scroll_number_help')
    close_memoryscrolls: bool = Field(default=False, description='指定绘卷结束后，关闭绘卷任务')
    close_exploration: bool = Field(default=False, description='指定绘卷结束后，关闭探索任务')
    close_goryourealm: bool = Field(default=False, description='指定绘卷结束后，关闭御灵任务')


class MemoryScrollsFinish(ConfigBase):
    # 检查小绘卷满50
    check_ms_s_50_enable: bool = Field(default=False, description='是否检查小绘卷满50')
    auto_finish_exploration: bool = Field(default=False, description='小绘卷满50后，自动结束当日探索任务')
    auto_finish_goryourealm: bool = Field(default=False, description='小绘卷满50后，自动结束当日御灵任务')
    # 当日小绘卷满50后指定探索和御灵明天运行时间
    next_run_time: Time = Field(default=Time(hour=7, minute=0, second=0), description='当日小绘卷满50后，指定探索和御灵明天运行时间')


class MemoryScrolls(ConfigBase):
    scheduler: Scheduler = Field(default_factory=Scheduler)
    memory_scrolls_config: MemoryScrollsConfig = Field(default_factory=MemoryScrollsConfig)
    memory_scrolls_finish: MemoryScrollsFinish = Field(default_factory=MemoryScrollsFinish)
