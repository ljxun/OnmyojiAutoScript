# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey


from enum import Enum


# 可以从这儿找
# https://onmyoji.fandom.com/wiki/Items
class Item(str, Enum):
    Realm_Raid_Pass = 'RealmRaidPass'  # 突破券
