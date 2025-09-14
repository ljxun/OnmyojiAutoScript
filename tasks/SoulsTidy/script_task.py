# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
from time import sleep
from datetime import timedelta, datetime, time
from cached_property import cached_property

from module.exception import TaskEnd
from module.logger import logger
from module.base.timer import Timer

from tasks.GameUi.game_ui import GameUi
from tasks.GameUi.page import page_main, page_shikigami_records
from tasks.SoulsTidy.assets import SoulsTidyAssets
from tasks.SoulsTidy.config import SimpleTidy

""" 整理御魂 """
class ScriptTask(GameUi, SoulsTidyAssets):
    click_num = 0

    def run(self):
        self.ui_get_current_page()
        self.ui_goto(page_shikigami_records)
        con = self.config.souls_tidy

        # 进入到御魂的主界面
        self.goto_souls()

        # 贪吃鬼
        if con.simple_tidy.only_greed:
            self.greed()
        # 奉纳御魂
        if con.simple_tidy.only_maneki:
            self.maneki()

        # 退回到式神录
        self.back_records()

        self.ui_get_current_page()
        self.ui_goto(page_main)
        self.set_next_run(task='SoulsTidy', success=True, finish=False)
        raise TaskEnd('SoulsTidy')

    def goto_souls(self):
        """
        进入到御魂的主界面
        :return:
        """
        while 1:
            self.screenshot()
            if self.appear(self.I_ST_GREED) and self.appear(self.I_ST_TIDY):
                break

            if self.appear_then_click(self.I_ST_REPLACE, interval=1):
                continue
            if self.appear_then_click(self.I_ST_SOULS, interval=1):
                continue
            if self.click(self.C_ST_DETAIL, interval=1.5):
                continue
        # 御魂超过上限的提示
        self.ocr_appear_click(self.O_ST_OVERFLOW)
        logger.info('Enter souls page')

    def back_records(self):
        """
        退回到式神录
        :return:
        """
        self.ui_click(self.I_UI_BACK_YELLOW, self.I_CHECK_RECORDS)

    def greed(self):
        """
        贪吃鬼
        :return:
        """
        # 先是贪吃鬼
        logger.hr('Greed Ghost')
        self.ui_click(self.I_ST_GREED, self.I_ST_GREED_HABIT)
        self.ui_click(self.I_ST_GREED_HABIT, self.I_ST_FEED_NOW)
        logger.info('Feed greed ghost')
        while 1:
            self.screenshot()
            if self.appear(self.I_UI_CONFIRM):
                self.ui_click_until_disappear(self.I_UI_CONFIRM, interval=1)
                break
            if self.appear_then_click(self.I_ST_FEED_NOW, interval=3.5):
                continue
        logger.info('Feed greed ghost done')
        # 关闭贪吃鬼, 进入奉纳
        while 1:
            self.screenshot()
            if self.appear(self.I_ST_CAT):
                # 出现招财猫
                break
            if self.appear_then_click(self.I_ST_GREED_CLOSE, interval=1):
                continue
            if self.appear_then_click(self.I_ST_BONGNA, interval=1, threshold=0.6):
                continue
        logger.hr('Enter bongna')


    def maneki(self):
        """
        奉纳御魂
        :return:
        """
        while 1:
            self.screenshot()
            if self.appear(self.I_ST_CAT):
                # 出现招财猫
                break
            if self.appear_then_click(self.I_ST_BONGNA, interval=1, threshold=0.6):
                continue
        # 确保是按照等级来排序的
        while 1:
            self.screenshot()
            if self.ocr_appear(self.O_ST_SORT_LEVEL_1):
                break
            if self.ocr_appear_click(self.O_ST_SORT_LEVEL_2, interval=0.6):
                continue
            if self.ocr_appear_click(self.O_ST_SORT_TIME, interval=2):
                continue
            if self.ocr_appear_click(self.O_ST_SORT_TYPE, interval=2):
                continue
            if self.ocr_appear_click(self.O_ST_SORT_LOCATION, interval=2):
                continue
        logger.info('Sort by level')
        # 开始奉纳
        while 1:
            self.screenshot()
            firvel = self.O_ST_FIRSET_LEVEL.ocr(self.device.image)
            if firvel != '古' and firvel != '+0':
                # 问就是 把 +0 识别成了 古
                logger.info('No zero level, bongna done')
                break
            # !!!!!!  这里没有检查金币是否足够
            # 长按
            while 1:
                self.screenshot()
                self.click(self.L_ONE, interval=2.5)
                self.click_num += 1
                gold_amount = self.O_ST_GOLD.ocr(self.device.image)
                if not isinstance(gold_amount, int):
                    logger.warning('Gold amount not int, skip')
                    continue
                if gold_amount > 0:
                    self.click_num = 0
                    break
                if self.click_num >= 3:
                    logger.warning(f'长按选中弃置御魂次数：{self.click_num},结束')
                    return

            # 点击奉纳收取奖励
            if not self.appear(self.I_ST_DONATE):
                logger.warning('Donate button not appear, skip')
                continue
            while 1:
                self.screenshot()
                if self.appear_then_click(self.I_UI_CONFIRM, interval=0.5):
                    continue
                # 如果奉纳少就不是神赐而是获得奖励
                if self.ui_reward_appear_click():
                    break
                # 出现神赐, 就点击然后消失，
                if self.appear(self.I_ST_GOD_PRESENT) or self.appear(self.I_ST_GOD_LUCKY):
                    logger.info('God present appear')
                    sleep(0.5)
                    self.screenshot()
                    if not (self.appear(self.I_ST_GOD_PRESENT) or self.appear(self.I_ST_GOD_LUCKY)):
                        continue
                    while 1:
                        self.screenshot()
                        if not (self.appear(self.I_ST_GOD_PRESENT) or self.appear(self.I_ST_GOD_LUCKY)):
                            logger.info('God present disappear')
                            break
                        if self.click(self.C_ST_GOD_PRSENT, interval=1):
                            continue
                    sleep(0.5)
                    break
                if self.appear_then_click(self.I_ST_DONATE, interval=5.5):
                    continue
            logger.info('Donate one')

        logger.info('Bongna done')








if __name__ == '__main__':
    from module.config.config import Config
    from module.device.device import Device
    c = Config('du')
    d = Device(c)
    t = ScriptTask(c, d)
    t.screenshot()


    # t.greed_maneki()
    t.run()

