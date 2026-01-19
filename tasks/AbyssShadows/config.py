# This Python file uses the following encoding: utf-8
# @brief    Configurations for Ryou Dokan Toppa (阴阳竂道馆突破配置)
# @author   jackyhwei
# @note     draft version without full test
# github    https://github.com/roarhill/oas

from enum import Enum
from pydantic import Field
from tasks.Component.GeneralBattle.config_general_battle import GeneralBattleConfig
from tasks.Component.SwitchSoul.switch_soul_config import SwitchSoulConfig
from tasks.Component.config_base import ConfigBase
from tasks.Component.config_scheduler import Scheduler


class BattleOrder(str, Enum):
    ELITE_GENERAL_BOSS = "精英→副将→首领"
    ELITE_BOSS_GENERAL = "精英→首领→副将"
    GENERAL_ELITE_BOSS = "副将→精英→首领"
    GENERAL_BOSS_ELITE = "副将→首领→精英"
    BOSS_ELITE_GENERAL = "首领→精英→副将"
    BOSS_GENERAL_ELITE = "首领→副将→精英"


class AbyssShadowsBossType(ConfigBase):
    open: bool = Field(default=False, description='寮管理开启狭间')
    dragon: bool = Field(default=False, description='神龙暗域')
    peacock: bool = Field(default=False, description='孔雀暗域')
    fox: bool = Field(default=False, description='白藏主暗域')
    leopard: bool = Field(default=False, description='黑豹暗域')
    attack_order: BattleOrder = Field(default=BattleOrder.ELITE_GENERAL_BOSS, description='攻击顺序')


class AbyssShadows(ConfigBase):
    scheduler: Scheduler = Field(default_factory=Scheduler)
    abyss_shadows_boss_type: AbyssShadowsBossType = Field(default_factory=AbyssShadowsBossType)
    general_battle_config: GeneralBattleConfig = Field(default_factory=GeneralBattleConfig)
    switch_soul_config: SwitchSoulConfig = Field(default_factory=SwitchSoulConfig)
