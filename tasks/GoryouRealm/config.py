# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
from enum import Enum
from pydantic import Field
from tasks.Component.GeneralBattle.config_general_battle import GeneralBattleConfig
from tasks.Component.SwitchSoul.switch_soul_config import SwitchSoulConfig
from tasks.Component.config_base import ConfigBase, Time
from tasks.Component.config_scheduler import Scheduler


class GoryouClass(str, Enum):
    RANDOM = '随机',
    Dark_Divine_Dragon = '暗神龙',
    Dark_Hakuzousu = '暗白蔵主',
    Dark_Black_Panther = '暗黑豹',
    Dark_Peacock = '暗孔雀'


class GoryouConfig(ConfigBase):
    # 限制时间
    limit_time: Time = Field(default=Time(minute=30), description='limit_time_help')
    # 限制次数
    limit_count: int = Field(default=30, description='limit_count_help')
    # 类型
    goryou_class: GoryouClass = Field(default=GoryouClass.RANDOM, description='goryou_class_help')
    # 开启绘卷捐赠任务
    open_memory_scrolls: bool = Field(title='开启绘卷捐赠任务', default=False, description='开启绘卷捐赠任务')


class GoryouRealm(ConfigBase):
    scheduler: Scheduler = Field(default_factory=Scheduler)
    goryou_config: GoryouConfig = Field(default_factory=GoryouConfig)
    general_battle_config: GeneralBattleConfig = Field(default_factory=GeneralBattleConfig)
    switch_soul_config: SwitchSoulConfig = Field(default_factory=SwitchSoulConfig)

