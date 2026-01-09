# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
from pydantic import Field
from tasks.ActivityCommon.config import ActivityCommonConfig
from tasks.ActivityCommon.config import CheckBattleConfig
from tasks.Component.SwitchSoul.switch_soul_config import SwitchSoulConfig
from tasks.Component.config_base import ConfigBase
from tasks.Component.config_scheduler import Scheduler


class ActivityCommon2(ConfigBase):
    scheduler: Scheduler = Field(default_factory=Scheduler)
    activity_common_config: ActivityCommonConfig = Field(default_factory=ActivityCommonConfig)
    check_battle_config: CheckBattleConfig = Field(default_factory=CheckBattleConfig)
    switch_soul_config: SwitchSoulConfig = Field(default_factory=SwitchSoulConfig)
