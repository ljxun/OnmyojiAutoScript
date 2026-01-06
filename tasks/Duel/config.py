# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
from pydantic import Field
from tasks.Component.GeneralBattle.config_general_battle import GreenMarkType
from tasks.Component.SwitchOnmyoji.config import Onmyoji
from tasks.Component.SwitchSoul.switch_soul_config import SwitchSoulConfig
from tasks.Component.config_base import ConfigBase, Time
from tasks.Component.config_scheduler import Scheduler
from tasks.Component.config_switch_week import SwitchWeek


class DuelConfig(ConfigBase):
    # 是否切换阴阳师
    switch_enabled: bool = Field(default=True, description='是否切换阴阳师')
    # 切换阴阳师
    switch_onmyoji: Onmyoji = Field(default=Onmyoji.YORIMITSU, description='切换阴阳师')
    # 一键切换斗技御魂
    switch_all_soul: bool = Field(default=False, description='switch_all_soul_help')
    # 限制时间
    limit_time: Time = Field(default=Time(minute=30), description='limit_time_help')
    # 目标分数
    target_score: int = Field(default=2000, description='target_score_help')
    # 刷满荣誉就退出
    honor_full_exit: bool = Field(default=False, description='honor_full_exit_help')
    # 是否开启绿标
    green_enable: bool = Field(default=False, description='green_enable_help')
    # 选哪一个绿标
    green_mark: GreenMarkType = Field(default=GreenMarkType.GREEN_LEFT1, description='green_mark_help')


class DuelCelebConfig(ConfigBase):
    # 是否开启名仕战斗
    celeb_battle: bool = Field(default=False, description='是否开启名仕战斗')
    # 填写第五手式神名称，如果阵容式神被办，第五手就会换式神，退出斗技
    ban_name: str = Field(default='', description='填写第五手式神名称')


class PushNotify(ConfigBase):
    enable: bool = Field(title='Enable', default=True, description='斗技是否消息通知')


class Duel(ConfigBase):
    scheduler: Scheduler = Field(default_factory=Scheduler)
    push_notify: PushNotify = Field(default_factory=PushNotify)
    duel_config: DuelConfig = Field(default_factory=DuelConfig)
    switch_week: SwitchWeek = Field(default_factory=SwitchWeek)
    duel_celeb_config: DuelCelebConfig = Field(default_factory=DuelCelebConfig)
    switch_soul: SwitchSoulConfig = Field(default_factory=SwitchSoulConfig)
