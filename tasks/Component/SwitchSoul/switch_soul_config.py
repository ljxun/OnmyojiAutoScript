# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
from pydantic import BaseModel, Field


class SwitchSoulConfig(BaseModel):
    # 是否启动 御魂切换
    enable: bool = Field(default=False)
    # 是否启动 预设队伍上阵 todo
    # preset_enable: bool = Field(default=False, description='preset_enable_help')
    switch_group_team: str = Field(default='-1,-1', description='switch_group_team_help')

    # 是否启动  OCR切换御魂
    enable_switch_by_name: bool = Field(default=False, description='enable_switch_by_name_help')
    group_name: str = Field(default='')
    team_name: str = Field(default='')
