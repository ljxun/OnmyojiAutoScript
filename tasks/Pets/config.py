# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
from pydantic import Field
from tasks.Component.config_base import ConfigBase
from tasks.Component.config_scheduler import Scheduler


class PetsConfig(ConfigBase):
    # 其乐融融
    pets_happy: bool = Field(default=True)
    # 大餐
    pets_feast: bool = Field(default=True)
    # 是否执行一次御魂
    orochi_enable: bool = Field(title='是否执行一次御魂', default=True, description='是否执行一次御魂')


class Pets(ConfigBase):
    scheduler: Scheduler = Field(default_factory=Scheduler)
    pets_config: PetsConfig = Field(default_factory=PetsConfig)


