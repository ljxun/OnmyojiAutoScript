# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
from pydantic import BaseModel, Field
from tasks.Component.config_base import ConfigBase
from tasks.Component.config_scheduler import Scheduler


class BackUpConfig(BaseModel):
    # 备份日志标志
    backup_flag: bool = Field(title='Backup Flag', default=False, description='备份日志')
    backup_date: str = Field(default='', description='完成备份任务日期')


class BackUp(ConfigBase):
    scheduler: Scheduler = Field(default_factory=Scheduler)
    back_up_config: BackUpConfig = Field(default_factory=BackUpConfig)
