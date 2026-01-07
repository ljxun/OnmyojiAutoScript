# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey

from module.exception import TaskEnd
from tasks.ActivityCommon.challenge import ScriptTask as Challenge
from tasks.ActivityCommon.delegate import ScriptTask as Delegate
from tasks.Component.GeneralBattle.general_battle import GeneralBattle
from tasks.Component.SwitchSoul.switch_soul import SwitchSoul
from tasks.ActivityCommon.config import ActiveType


class ScriptTask(SwitchSoul, GeneralBattle):
    """ 活动通用 """
    def __init__(self, config):
        super().__init__(config)
        self.Delegate = Delegate(self.config)
        self.Challenge = Challenge(self.config)

    def run(self):
        config = self.config.activity_common.activity_common_config
        if config.active_type == '委派':
            self.Delegate.run()
        else:
            self.run1()

    def run1(self):
        config = self.config.activity_common
        battle_active_type = config.activity_common_config.active_type
        goto_challenge_folder = f"./tasks/ActivityCommon/{battle_active_type}"
        # 战斗图片路径
        battle_folder = "./tasks/ActivityCommon/战斗中"

        self.Challenge.run_config(config, goto_challenge_folder, battle_folder)


if __name__ == '__main__':
    from module.config.config import Config

    c = Config('du')
    t = ScriptTask(c)

    t.run()
