# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
from enum import Enum
from pydantic import BaseModel, Field
from tasks.Component.SwitchSoul.switch_soul_config import SwitchSoulConfig
from tasks.Component.config_base import ConfigBase, Time
from tasks.Component.config_scheduler import Scheduler


class ActiveType(str, Enum):
    battle = '战斗'
    delegate = '委派'
    huanjing = '狭间幻境'
    lingran = '灵染试炼'
    yanwu = '逢魔演武'
    gua = '呱呱画室'


class ModeType(str, Enum):
    DigitCounter = 'DigitCounter'
    Digit = 'Digit'


class NumberType(str, Enum):
    Ticket = '门票数量（数值递减）'
    Battle = '战斗次数（数值递增）'


class ActivityCommonConfig(BaseModel):
    # 活动类型选择
    active_type: ActiveType = Field(default=ActiveType.battle, description='活动类型选择')

    enable: bool = Field(default=False, description='auto_enable_help')
    # 限制次数
    limit_count: int = Field(default=200, description='limit_count_help')
    # 限制时间
    limit_time: Time = Field(default=Time(minute=30), description='limit_time_help')
    # 结束后激活 御魂清理
    active_souls_clean: bool = Field(default=False, description='active_souls_clean_help')
    each_limit_second: int = Field(default=0, description='每场战斗限制秒数（0秒代表不限制)')
    enable_check_first_priority_task: bool = Field(default=False, description='是否判断更高优先级任务需要执行')


class CheckBattleConfig(ConfigBase):
    enable: bool = Field(default=False, description='是否启用 OCR 战斗次数检测')
    ocr_number_mode: ModeType = Field(default=ModeType.DigitCounter, description='OCR 战斗次数检测类型')
    ocr_number_roi: str = Field(default='', description='OCR 坐标（例如：1136,113,31,52）')
    limit_ocr_number: int = Field(default=-1, description='限制战斗次数')
    number_type: NumberType = Field(default=NumberType.Battle, description='限制战斗次数类型')


class ActivityCommon(ConfigBase):
    scheduler: Scheduler = Field(default_factory=Scheduler)
    activity_common_config: ActivityCommonConfig = Field(default_factory=ActivityCommonConfig)
    check_battle_config: CheckBattleConfig = Field(default_factory=CheckBattleConfig)
    switch_soul_config: SwitchSoulConfig = Field(default_factory=SwitchSoulConfig)
