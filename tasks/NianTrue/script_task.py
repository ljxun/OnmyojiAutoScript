# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
from time import sleep

from cached_property import cached_property
from datetime import time
from module.base.timer import Timer
from module.exception import TaskEnd
from module.logger import logger
from tasks.Component.GeneralBattle.config_general_battle import GeneralBattleConfig
from tasks.Component.GeneralBattle.general_battle import GeneralBattle
from tasks.Component.GeneralInvite.general_invite import GeneralInvite
from tasks.Component.GeneralRoom.general_room import GeneralRoom
from tasks.GameUi.game_ui import GameUi
from tasks.GameUi.page import page_team
from tasks.NianTrue.assets import NianTrueAssets

""" 现世年兽 """


class ScriptTask(GameUi, GeneralBattle, GeneralRoom, GeneralInvite, NianTrueAssets):

    def run(self) -> None:

        while 1:

            self.ui_goto_page(page_team)

            count = 0
            while 1:
                # 进入
                self.screenshot()
                if count >= 4:
                    self.next_nian_true()

                self.check_zones('现世年兽')
                if self.appear_then_click(self.I_N_HUABEI, interval=1):
                    break
                else:
                    count += 1

            cd_count = 0
            count = 0
            while 1:
                self.screenshot()
                sleep(1)
                if self.appear(self.I_N_WAITING):
                    break
                if cd_count >= 4:
                    # 4 x 1.5 = 6秒没有进入说明是在冷却中
                    self.next_nian_true()
                if count >= 10:
                    break
                if self.appear_then_click(self.I_GR_AUTO_MATCH, interval=1.5):
                    cd_count += 1
                    continue
                else:
                    count += 1

            # 匹配个8分钟，要是八分钟还没人拿没啥了
            logger.info('Waiting for match')
            click_timer = Timer(240)
            check_timer = Timer(480)
            click_timer.start()
            check_timer.start()
            self.device.stuck_record_add('LOGIN_CHECK')
            while 1:
                self.screenshot()
                # 如果被秒开进入战斗, 被秒开不支持开启buff
                if self.check_take_over_battle(False, config=self.battle_config):
                    logger.info('NianTrue take over battle')
                    break
                # 如果进入房间
                elif self.is_in_room():
                    self.device.stuck_record_clear()
                    if self.wait_battle(wait_time=time(minute=1)):
                        self.run_general_battle(config=self.battle_config)
                        # 打完后返回庭院，记得关闭buff
                        break
                    else:
                        break
                # 如果时间到了
                if click_timer and click_timer.reached():
                    logger.warning('It has waited for 240s , but the battle has not started.')
                    logger.warning('It will be waited for 240s and try again.')
                    self.screenshot()
                    self.click(self.C_CLIC_SAFE)
                    click_timer = None
                    self.device.stuck_record_clear()
                    self.device.stuck_record_add('LOGIN_CHECK')
                    continue

                if check_timer.reached():
                    logger.warning('NianTrue match timeout')
                    while 1:
                        self.screenshot()
                        if not self.appear(self.I_N_WAITING):
                            break
                        if self.appear_then_click(self.I_UI_CONFIRM, interval=1):
                            continue
                        if self.appear_then_click(self.I_UI_CONFIRM_SAMLL, interval=1):
                            continue
                        if self.appear_then_click(self.I_N_WAITING, interval=1):
                            continue
                    logger.info('NianTrue match timeout, exit')
                    break
                # 如果还在匹配中
                if self.appear(self.I_N_WAITING):
                    continue

    def battle_wait(self) -> bool:
        # 重写
        self.device.stuck_record_add('BATTLE_STATUS_S')
        self.device.click_record_clear()
        # 战斗过程 随机点击和滑动 防封
        logger.info("NianTrue Start battle process")
        is_first = True
        while 1:
            self.screenshot()
            if self.appear(self.I_N_PAGE):
                logger.info('现世年兽来袭页面')
                return True
            if self.appear(self.I_BATTLE_OVER):
                if is_first:
                    self.save_image()
                    is_first = False
                logger.info('现世年兽战斗结束，通关奖励')
                self.click(self.C_CLIC_SAFE, interval=1)
                continue
            if self.appear(self.I_N_OK):
                self.save_image()
                self.appear_then_click(self.I_N_OK)
                logger.info('现世年兽战斗结束，已拥有物品转为金币，点击确认')
                continue

    def next_nian_true(self):
        # 退出结束
        self.set_next_run(task='NianTrue', success=True, finish=True)
        raise TaskEnd('NianTrue')

    @cached_property
    def battle_config(self) -> GeneralBattleConfig:
        conf = GeneralBattleConfig()
        return conf


if __name__ == '__main__':
    from module.config.config import Config
    from module.device.device import Device

    c = Config('test')
    d = Device(c)
    t = ScriptTask(c, d)
    t.screenshot()

    t.run()
