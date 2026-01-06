# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
import time

import random
from datetime import datetime
from enum import Enum
from module.base.timer import Timer
from module.exception import TaskEnd, RequestHumanTakeover
from module.logger import logger
from tasks.CollectiveMissions.assets import CollectiveMissionsAssets
from tasks.CollectiveMissions.config import MissionsType
from tasks.GameUi.game_ui import GameUi
from tasks.GameUi.page import page_guild


class MC(str, Enum):
    BL = '契灵'
    AW1 = '觉醒一'
    AW2 = '觉醒二'
    AW3 = '觉醒三'
    GR1 = '御灵一'
    GR2 = '御灵二'
    GR3 = '御灵三'
    SO1 = '御魂一'
    SO2 = '御魂二'
    FRIEND = '结伴同行'
    UNKNOWN = '未知'
    FEED = '养成'  # 喂N卡


class ScriptTask(GameUi, CollectiveMissionsAssets):
    """ 集体任务 """
    missions: list = []  # 用于记录三个的任务的种类

    def run(self):

        missions_type = self.config.collective_missions.missions_config.missions_type

        target = MC.GR3
        target_1 = MC.GR1
        match missions_type:
            case MissionsType.AW:
                logger.info('Selecting 觉醒三')
                target = MC.AW3
                target_1 = MC.AW1
            case MissionsType.GR:
                logger.info('Selecting 御灵三')
                target = MC.GR3
                target_1 = MC.GR1
            case MissionsType.SO:
                logger.info('Selecting 御魂一')
                target = MC.SO1
                target_1 = MC.SO2
            case MissionsType.FEED:
                logger.info('Selecting N卡')
                target = MC.FEED
                target_1 = None

        remain = self.goto_cm_main()

        self.select_gr(target)
        if not self._donate_all(0, target, 1, remain):
            if target_1:
                self.ui_click(self.I_BACK_RED, self.I_CM_RECORDS)
                self.select_gr(target_1)
                if not self._donate_all(0, target_1, 3, remain):
                    self.save_image(wait_time=0, push_flag=True, content=f'⚠️{target_1.value} 材料不足')

        # 设置任务结束
        self.next_run_task()

    def check_cm_number(self):
        logger.info('Checking CM number')
        # 判断今天是否已经完成了， 还是多少次数的任务
        self.screenshot()
        current, remain, total = self.O_CM_NUMBER.ocr(self.device.image)
        if current == total == 30:
            logger.warning('Today\'s missions have been completed')

            check_timer = Timer(3)
            check_timer.start()
            while 1:
                self.screenshot()
                if self.ui_reward_appear_click(True):
                    check_timer.reset()
                    continue
                if self.appear_then_click(self.I_CM_REWARDS, interval=1):
                    check_timer.reset()
                    continue
                if check_timer.reached():
                    break

            # 设置任务结束
            self.next_run_task()
            return None
        else:
            return remain

    def goto_cm_main(self):
        self.ui_goto_page(page_guild)
        time.sleep(1)
        self.ui_click(self.I_CM_SHRINE, self.I_CM_CM)
        self.ui_click(self.I_CM_CM, self.I_CM_RECORDS)
        logger.info('Start to detect missions')
        return self.check_cm_number()

    def next_run_task(self):

        def update_config():
            self.config.collective_missions.missions_config.task_date = str(datetime.now().date())
        self.config.safe_save(update_config)

        self.screenshot()
        current, remain, total = self.O_CM_NUMBER.ocr(self.device.image)
        if not (current == total == 30):
            self.push_notify(content=f'❌ 集体任务未完成 | {current}/{total}')

        self.set_next_run(task='CollectiveMissions', success=True, finish=True)
        raise TaskEnd('CollectiveMissions')

    def select_gr(self, target):
        last_result = None       # 记录上一次的OCR识别结果（初始为None）
        consecutive_count = 0    # 记录连续相同结果的次数（初始为0）
        total_count = 0
        consecutive_count_max = 5
        while True:              # 无限循环（用True更易读）
            self.screenshot()     # 截取当前屏幕
            current_result = self.O_CM_2.ocr(self.device.image)  # 执行OCR识别，获取当前结果

            # 核心逻辑：比较当前结果与上一次结果
            if current_result == last_result:
                consecutive_count += 1  # 连续次数+1
                # 当连续次数≥ consecutive_count_max时，退出循环（阈值可根据需求调整）
                if consecutive_count >= consecutive_count_max:
                    message = f"连续{consecutive_count}次识别结果均为：{current_result}，触发退出条件"
                    self.push_notify(content=message)
                    # 设置任务结束
                    self.next_run_task()
            else:
                # 结果不同，重置计数器和上一次结果
                consecutive_count = 1       # 当前结果作为新的连续起点（首次出现）
                last_result = current_result  # 更新上一次结果为当前结果
            # ------------------------------------------------------------------

            # 原有核心逻辑：识别到目标文本则返回
            if current_result == target:
                logger.info(f"识别到目标'{target}'，返回对应结果")
                return

            # 原有逻辑：点击刷新按钮并等待（避免频繁点击）
            if self.appear_then_click(self.I_CM_FLUSH, interval=1):
                total_count += 1
                if total_count > 30:
                    self.save_image(wait_time=0, push_flag=True, content=f'⚠️刷新次数已超过30次,结束任务')
                    self.next_run_task()
                self.device.click_record_clear()
                time.sleep(1)  # 等待页面刷新完成（根据实际加载时间调整）

    def _donate_all(self, index: int, target: MissionsType, num: int, incomplete_num: int):
        """
        捐赠材料
        :param index: 0, 1, 2 三个任务的位置
        :return:
        """
        match_click = {
            0: self.C_CM_1,
            1: self.C_CM_2,
            2: self.C_CM_3,
        }
        while 1:
            while 1:
                self.screenshot()
                if self.appear(self.I_CM_PRESENT):
                    break
                if self.click(match_click[index], interval=1.5):
                    continue
            # 开始捐材料
            logger.info('Start to donate')
            # 判断哪一个的材料最多
            self.screenshot()
            max_index = 0
            max_number = 0
            total_number = 0
            for i, ocr in enumerate([self.O_CM_1_MATTER, self.O_CM_2_MATTER,
                                     self.O_CM_3_MATTER, self.O_CM_4_MATTER]):
                curr, remain, total = ocr.ocr(self.device.image)
                total_number += total
                if total > max_number:
                    max_number = total
                    max_index = i
            # 综合判断是否需要推送
            logger.info(f'{target.value} 需要数量: {num * incomplete_num}')
            self.screenshot()
            if total_number < num * incomplete_num:
                return False
            else:
                logger.info(f'{target.value} 总量剩余{total_number}')
                self._swipe_cm(max_index)
                incomplete_num = self.check_cm_number()

    def _swipe_cm(self, max_index: int):
        match_swipe = {
            0: self.S_CM_MATTER_1,
            1: self.S_CM_MATTER_2,
            2: self.S_CM_MATTER_3,
            3: self.S_CM_MATTER_4,
        }
        match_image = {
            0: self.I_CM_ADD_1,
            1: self.I_CM_ADD_2,
            2: self.I_CM_ADD_3,
            3: self.I_CM_ADD_4,
        }
        # 滑动到最多的材料
        random_click = [self.I_CM_ADD_1, self.I_CM_ADD_2, self.I_CM_ADD_3, self.I_CM_ADD_4]
        window_control = self.config.script.device.control_method == 'window_message'
        swipe_count = 0
        click_count = 0
        while 1:
            self.screenshot()
            if self.appear(self.I_CM_MATTER):
                break
            if not window_control and self.swipe(match_swipe[max_index], interval=2.5):
                swipe_count += 1
                time.sleep(1.5)
                continue

            # 为什么使用window_message无法滑动
            if window_control and click_count > 30:
                logger.info('Swipe to the most matter failed')
                logger.info('Please check your game resolution')
                break
            if window_control and self.click(random.choice(random_click), interval=0.7):
                click_count += 1
                continue

            if not window_control and swipe_count >= 5:
                logger.info('Swipe to the most matter failed')
                logger.info('Please check your game resolution')
                raise RequestHumanTakeover

        logger.info('Swipe to the most matter')
        # 还有一点很重要的，捐赠会有双倍的，需要领两次
        reward_number = 0
        timer = Timer(3)
        timer.start()
        while 1:
            self.screenshot()
            if timer.reached():
                break
            if reward_number >= 2:
                break
            if self.ui_reward_appear_click(False):
                timer.reset()
                reward_number += 1
                continue
            if self.appear_then_click(self.I_CM_PRESENT, interval=1):
                timer.reset()
                continue
        self.ui_reward_appear_click(True)
        logger.info('Donate finished')
        return True


if __name__ == '__main__':
    from module.config.config import Config

    c = Config('mi')
    t = ScriptTask(c)
    t.screenshot()
    t.run()

