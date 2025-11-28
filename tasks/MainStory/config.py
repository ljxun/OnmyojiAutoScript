# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
from pydantic import BaseModel, Field
from tasks.Component.config_base import ConfigBase
from tasks.Component.config_scheduler import Scheduler


class MainStoryConfig(BaseModel):
    pass


class MainStory(ConfigBase):
    scheduler: Scheduler = Field(default_factory=Scheduler)
    main_story_config: MainStoryConfig = Field(default_factory=MainStoryConfig)
