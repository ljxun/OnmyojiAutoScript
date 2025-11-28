# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
from enum import Enum
from pydantic import Field

from tasks.Component.config_base import ConfigBase


class Week(str, Enum):
    mon = '周一'
    tue = '周二'
    wed = '周三'
    thu = '周四'
    fri = '周五'
    sat = '周六'
    sun = '周日'


class SwitchWeek(ConfigBase):
    next_week_day: Week = Field(default=Week.mon, description='选择下周周几运行')
