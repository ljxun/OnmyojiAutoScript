# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
from pydantic import Field
from tasks.Component.config_base import ConfigBase, Time
from tasks.Component.config_scheduler import Scheduler


class NextTaskTime(ConfigBase):
    run_time_1: Time = Field(default=Time(hour=12, minute=30, second=0), description='每天第一次执行时间')
    run_time_2: Time = Field(default=Time(hour=21, minute=0, second=0), description='每天第二次执行时间')


class CourtyardAffairs(ConfigBase):
    scheduler: Scheduler = Field(default_factory=Scheduler)
    next_task_time: NextTaskTime = Field(default_factory=NextTaskTime)
