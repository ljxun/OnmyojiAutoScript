# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
from module.logger import logger
from tasks.ActivityCommon.challenge import ScriptTask as Challenge
from tasks.ActivityCommon.config import ActiveType
from tasks.ActivityCommon.delegate import ScriptTask as Delegate
from tasks.ActivityCommon.script_task import ScriptTask as ActivityCommonScriptTask


class ScriptTask(ActivityCommonScriptTask):
    """ 活动通用2 """
    def __init__(self, config):
        super().__init__(config)
        self.Challenge = Challenge(self.config)
        self.Delegate = Delegate(self.config)

    def run(self):
        config = self.config.activity_common_2
        battle_active_type = config.activity_common_config.active_type
        if battle_active_type == ActiveType.battle:
            folder = 'ActivityCommon2'
        else:
            folder = 'ActivityCommon'
        # 加载图片
        goto_challenge_folder = f"./tasks/{folder}/{battle_active_type}"
        battle_folder = "./tasks/ActivityCommon/战斗中"

        logger.hr(f"开始执行 {battle_active_type} 任务", 2)
        self.Challenge.run_config(config, goto_challenge_folder, battle_folder)


if __name__ == '__main__':
    from module.config.config import Config

    c = Config('du')
    t = ScriptTask(c)

    t.run()
