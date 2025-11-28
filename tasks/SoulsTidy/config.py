# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
from pydantic import BaseModel, Field
from tasks.Component.config_base import ConfigBase
from tasks.Component.config_scheduler import Scheduler


class SimpleTidy(BaseModel):
    # 贪吃鬼和招财猫
    # greed_maneki: bool = Field(default=False, description="greed_maneki_help")

    # 贪吃鬼
    only_greed: bool = Field(default=True, description="贪吃鬼")
    # 奉纳
    only_maneki: bool = Field(default=False, description="奉纳御魂")



class SoulsTidy(ConfigBase):
    scheduler: Scheduler = Field(default_factory=Scheduler)
    simple_tidy: SimpleTidy = Field(default_factory=SimpleTidy)

