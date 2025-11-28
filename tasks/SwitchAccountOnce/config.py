# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
from pydantic import BaseModel, Field
from tasks.Component.config_base import ConfigBase, Time
from tasks.Component.config_scheduler import Scheduler


class OnceConfig(BaseModel):
    accounts_file: str = Field(default='', description='需要切换账号的文件名：比如（accounts.json）')
    limit_task_time: Time = Field(default=Time(19, 0, 0), description='限时任务开始时间')
    # enable_notify: bool = Field(default=False, description='消息通知')
    # enable_save_img: bool = Field(default=False, description='截图保存')


class SwitchAccountOnce(ConfigBase):
    scheduler: Scheduler = Field(default_factory=Scheduler)
    once_config: OnceConfig = Field(default_factory=OnceConfig)
