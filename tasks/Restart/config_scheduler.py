# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
from datetime import time
from pydantic import Field
from tasks.Component.config_scheduler import Scheduler


class RestartScheduler(Scheduler):
    enable: bool = Field(default=True, description='enable_help')
    priority: int = Field(default=0, description='priority_help')
    server_update: time = Field(default=time(hour=9, minute=5, second=0), description='server_update_help')

