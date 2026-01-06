# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
from enum import Enum
from pydantic import BaseModel, Field
from tasks.Component.config_base import ConfigBase
from tasks.Component.config_scheduler import Scheduler


class SummonType(str, Enum):
    default = '普通召唤'
    recall = '今忆召唤'


class DailyTriflesConfig(BaseModel):
    one_summon: bool = Field(title='One Summon', default=False)
    # 召唤类型
    # summon_type: SummonType = Field(default=SummonType.default, description='召唤类型')
    broken_amulet: int = Field(title='Broken Amulet', default=0, description='trifles_broken_amulet_help')
    friend_love: bool = Field(title='Friend Love', default=False)
    luck_msg: bool = Field(title='Luck Msg', default=False)
    store_sign: bool = Field(title='Store Sign', default=False, description='store_sign_help')
    # 每天购买体力数量
    buy_sushi_count: int = Field(title='Buy Sushi Count', default=-1)
    recruit_members: bool = Field(title='Mecruit Members', default=False, description='招募寮成员')
    lottery_box: bool = Field(title='Lottery Box', default=True, description='抽奖箱抽奖')


class DailyTrifles(ConfigBase):
    scheduler: Scheduler = Field(default_factory=Scheduler)
    trifles_config: DailyTriflesConfig = Field(default_factory=DailyTriflesConfig)
