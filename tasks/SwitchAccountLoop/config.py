
from pydantic import BaseModel, Field
from tasks.Component.config_base import ConfigBase, Time
from tasks.Component.config_scheduler import Scheduler


class LoopConfig(BaseModel):
    accounts_file: str = Field(default='', description='需要切换账号的文件名：比如（accounts.json）')
    task_start_time: Time = Field(default=Time(0, 0, 0), description='任务开始时间')
    task_end_time: Time = Field(default=Time(23, 59, 59), description='任务结束时间')
    task_interval: Time = Field(default=Time(1, 0, 0), description='每轮循环任务间隔时间')
    task_loop_interval: Time = Field(default=Time(0, 5, 0), description='每个账号循环任务间隔时间')


class SwitchAccountLoop(ConfigBase):
    scheduler: Scheduler = Field(default_factory=Scheduler)
    loop_config: LoopConfig = Field(default_factory=LoopConfig)
