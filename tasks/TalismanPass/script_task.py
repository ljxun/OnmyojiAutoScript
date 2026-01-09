# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
import time

from module.base.timer import Timer
from module.exception import TaskEnd
from module.logger import logger
from tasks.GameUi.game_ui import GameUi
from tasks.GameUi.page import page_main
from tasks.TalismanPass.assets import TalismanPassAssets
from tasks.TalismanPass.config import TalismanConfig, LevelReward
from tasks.TalismanPass.page import page_daily, page_accomplishment

""" 花合战 """


class ScriptTask(GameUi, TalismanPassAssets):

    def run(self):
        # self.main_goto_daily()
        con: TalismanConfig = self.config.talisman_pass.talisman
        self.ui_goto_page(page_daily)

        # 收取全部奖励
        if self.in_task():
            self.get_all()
        # 收取花合战等级奖励
        self.get_flower(con.level_reward)

        if con.get_accomplishments:
            self.get_accomplishment_reward()
        if con.get_newbie:
            self.get_newbie_reward()

        self.set_next_run(task='TalismanPass', success=True, finish=True)
        raise TaskEnd('TalismanPass')

    def get_newbie_reward(self):
        """
        获取新手奖励
        :return:
        """
        self.ui_goto_page(page_main)
        self.ui_click(self.I_NEWBIE, self.I_NEWBIE_PAGE)
        self.ui_click(self.I_YC_ROAD, self.I_RESUPPLY)
        self.ui_click(self.I_RESUPPLY, self.I_RESUPPLY_PAGE)
        self.ui_get_reward(self.I_ONE_COLLECT)

        check_timer = Timer(3)
        check_timer.start()
        while 1:
            self.screenshot()
            if self.ui_reward_appear_click(True):
                break
            if check_timer.reached():
                break

        self.save_image(task_name="新手奖励", wait_time=1)


    def get_all(self):
        """
        一键收取所有的
        :return:
        """
        self.screenshot()
        if not self.appear(self.I_TP_GET_ALL):
            logger.info('No appear get all button')
        self.ui_get_reward(self.I_TP_GET_ALL)
        logger.info('Get all reward')
        time.sleep(0.5)

    def get_accomplishment_reward(self):
        """
        领取成就奖励
        :return:
        """
        self.ui_goto_page(page_accomplishment)
        # self.ui_click(self.I_ACCOMPLISHMENTS_1, self.I_ACCOMPLISHMENTS_2)
        timer = Timer(3)
        timer.start()
        while 1:
            self.screenshot()
            if timer.reached():
                logger.info('Get accomplishment reward time out')
                break
            if self.appear(self.I_ACCOMPLISHMENTS_3, interval=1):
                logger.info('Get accomplishment reward over')
                break
            if self.ui_reward_appear_click():
                self.device.click_record_clear()
                timer.reset()
                continue
            if self.click(self.C_ACCOMPLISHMENTS_3_CLICK, interval=1):
                timer.reset()
                continue

    def get_flower(self, level: LevelReward = LevelReward.TWO):
        """
        收取花合战等级奖励
        :return:
        """
        match_level = {
            LevelReward.ONE: self.I_TP_LEVEL_1,
            LevelReward.TWO: self.I_TP_LEVEL_2,
            LevelReward.THREE: self.I_TP_LEVEL_3,
        }
        self.screenshot()
        if not self.appear(self.I_RED_POINT_LEVEL):
            logger.info('No any level reward')
            return
        logger.info('Appear level reward')
        self.ui_click(self.I_RED_POINT_LEVEL, self.I_TP_GET_ALL)
        logger.info('Click level reward')
        check_timer = Timer(2)
        check_timer.start()
        while 1:
            self.screenshot()
            if self.appear_then_click(match_level[level], interval=0.8):
                logger.info(f'Select {level} reward')
                self.appear_then_click(self.I_OVERFLOW_CONFIRME)
                check_timer.reset()
                continue

            if self.ui_reward_appear_click(False):
                logger.info('Get reward')
                check_timer.reset()
                continue
            if check_timer.reached():
                logger.warning('No reward and break')
                break
            if self.appear_then_click(self.I_TP_GET_ALL, interval=2.1):
                logger.info('Get all reward')
                check_timer.reset()
                continue

    def in_task(self) -> bool:
        """
        判断是否在任务的界面
        :return:
        """
        timer = Timer(3)
        timer.start()
        while 1:
            self.screenshot()
            if timer.reached():
                logger.warning('No appear task button')
                return False
            if self.appear(self.I_TP_GOTO) or self.appear(self.I_TP_EXP):
                return True
            if self.appear_then_click(self.I_TP_TASK, interval=1):
                continue

    def main_goto_daily(self):
        """
        无法直接一步到花合战，需要先到主页，然后再到花合战
        :return:
        """
        self.ui_goto_page(page_main)

        while 1:
            self.screenshot()
            if self.appear(self.I_CHECK_DAILY):
                break
            if self.appear_then_click(self.I_TP_SKIP, interval=1):
                continue
            if self.appear_then_click(self.I_MAIN_GOTO_DAILY, interval=1):
                continue
            if self.ocr_text_threshold(self.O_CLICK_CLOSE_1, interval=2):
                self.click(self.C_CLICK_AREA)
                continue
            if self.ocr_text_threshold(self.O_CLICK_CLOSE_2, interval=2):
                self.click(self.C_CLICK_AREA)
                continue
        logger.info('Page arrive: Daily')
        time.sleep(1)
        return


import cv2
from numpy import uint8, fromfile
from pathlib import Path

def load_image(file: str):
    file = Path(file)
    img = cv2.imdecode(fromfile(file, dtype=uint8), -1)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    height, width, channels = img.shape
    if height != 720 or width != 1280:
        logger.error(f'Image size is {height}x{width}, not 720x1280')
        return None
    return img


if __name__ == '__main__':
    from module.config.config import Config

    c = Config('4399-1')
    # d = Device(c)
    t = ScriptTask(c)
    # t.screenshot()
    # d.image = load_image(r"D:\共享文件夹\Screenshots\花合战\1 (1).png")
    # t.main_goto_daily()
    t.get_newbie()
