# This Python file uses the following encoding: utf-8
# @author TripleEarth
# github https://github.com/TripleEarth
from enum import Enum
from pydantic import Field
from tasks.Component.GeneralBattle.config_general_battle import GeneralBattleConfig
from tasks.Component.GeneralInvite.config_invite import InviteConfig
from tasks.Component.SwitchSoul.switch_soul_config import SwitchSoulConfig
from tasks.Component.config_base import ConfigBase, Time
from tasks.Component.config_scheduler import Scheduler


class UserStatus(str, Enum):
    LEADER = 'leader'
    MEMBER = 'member'
    ALONE = 'alone'
    WILD = 'wild'  # 还不打算实现


class Layer(str, Enum):
    ONE = '壹层'
    TWO = '贰层'
    THREE = '叁层'
    FOUR = '肆层'
    FIVE = '伍层'
    SIX = '陆层'
    SEVEN = '柒层'
    EIGHT = '捌层'
    NINE = '玖层'
    TEN = '拾层'


class KirinType(str, Enum):
    FIREKIRIN = '火麒麟'
    WINDKIRIN = '风麒麟'
    WATERKIRIN = '水麒麟'
    LIGHTNINGKIRIN = '雷麒麟'


class EvoZoneConfig(ConfigBase):
    # 身份
    user_status: UserStatus = Field(default=UserStatus.LEADER, description='user_status_help')
    # 类型
    kirin_type: KirinType = Field(default=KirinType.LIGHTNINGKIRIN, description='kirin_type_help')
    # 层数
    layer: Layer = Field(default=Layer.TEN, description='layer_help')
    # 限制时间
    limit_time: Time = Field(default=Time(minute=30), description='limit_time_help')
    # 限制次数
    limit_count: int = Field(default=30, description='limit_count_help')
    # 是否开启觉醒加成
    soul_buff_enable: bool = Field(default=False, description='是否开启觉醒加成')


class EvoZone(ConfigBase):
    scheduler: Scheduler = Field(default_factory=Scheduler)
    evo_zone_config: EvoZoneConfig = Field(default_factory=EvoZoneConfig)
    invite_config: InviteConfig = Field(default_factory=InviteConfig)
    general_battle_config: GeneralBattleConfig = Field(default_factory=GeneralBattleConfig)
    switch_soul_config: SwitchSoulConfig = Field(default_factory=SwitchSoulConfig)
