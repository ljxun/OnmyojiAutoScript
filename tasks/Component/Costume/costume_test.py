# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey

from module.logger import logger
from tasks.Component.GeneralBattle.general_battle import GeneralBattle
from tasks.Component.SwitchSoul.switch_soul import SwitchSoul
from tasks.Pets.assets import PetsAssets


class ScriptTask(GeneralBattle, SwitchSoul, PetsAssets):

    def run(self):
        # 町中测试
        self.ui_click(self.I_MAIN_GOTO_TOWN, self.I_CHECK_TOWN)
        self.ui_click(self.I_TOWN_GOTO_MAIN, self.I_CHECK_MAIN)
        # 探索测试
        self.ui_click(self.I_MAIN_GOTO_EXPLORATION, self.I_CHECK_EXPLORATION)
        self.ui_click(self.I_BACK_BLUE, self.I_CHECK_MAIN)
        # 召唤测试
        self.ui_click(self.I_MAIN_GOTO_SUMMON, self.I_CHECK_SUMMON)
        self.ui_click(self.I_SUMMON_GOTO_MAIN, self.I_CHECK_MAIN)
        # 宠物屋测试
        self.ui_click(self.I_PET_HOUSE, self.I_PET_CLAW)
        self.ui_click(self.I_PET_EXIT, self.I_CHECK_MAIN)
        logger.info('Test Success')


if __name__ == '__main__':
    from module.config.config import Config

    c = Config('du')
    t = ScriptTask(c)
    t.run()

