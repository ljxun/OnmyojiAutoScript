# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey

import random
from datetime import datetime, timedelta
from module.base.timer import Timer
from module.exception import TaskEnd
from module.logger import logger
from tasks.ActivityShikigami.assets import ActivityShikigamiAssets
from tasks.AutoCake.assets import AutoCakeAssets
from tasks.Component.GeneralBattle.general_battle import GeneralBattle
from tasks.Component.SwitchSoul.switch_soul import SwitchSoul
from tasks.GameUi.page import page_main


class ScriptTask(SwitchSoul, GeneralBattle,  AutoCakeAssets, ActivityShikigamiAssets):
    """ 活动挂饼 """
    def run(self) -> None:
        self.start_time = datetime.now()
        config = self.config.auto_cake
        # 切换御魂
        if config.switch_soul_config.enable:
            self.run_switch_soul(config.switch_soul_config.switch_group_team)
        if config.switch_soul_config.enable_switch_by_name:
            self.run_switch_soul_by_name(
                config.switch_soul_config.group_name,
                config.switch_soul_config.team_name
            )

        self.ui_goto_page(page_main)

        # 进入活动
        self.home_main()

        # 自动战斗
        self.automatic_battle()
        self.push_notify(content="战斗结束！")

        # 回到庭院
        self.ui_goto_page(page_main)

        if config.auto_cake_config.active_souls_clean:
            self.set_next_run(task='SoulsTidy', success=False, finish=False, target=datetime.now())

        self.set_next_run(task='AutoCake', success=True, finish=True)
        raise TaskEnd("AutoCake")

    def automatic_battle(self):
        config = self.config.auto_cake.auto_cake_config

        self.limit_time: timedelta = timedelta(hours=config.limit_time.hour, minutes=config.limit_time.minute,
                                               seconds=config.limit_time.second)

        #  进入活动界面，必须锁定阵容
        if self.appear(self.I_IS_REACH):
            while 1:
                self.screenshot()
                if self.appear_then_click(self.I_UNLOCK, interval=1):
                    continue
                if self.appear(self.I_LOCK):
                    break

        # 任务开启
        swipe_timer = Timer(270)
        swipe_timer.start()
        ocr_count = 0
        while 1:
            self.screenshot()
            # 时间结束判断
            if datetime.now() - self.start_time >= self.limit_time:
                # 任务执行时间超过限制时间，退出
                logger.info('Auto cake task is over time')
                break
            # 攻打次数上限判断
            if self.appear(self.I_IS_OVER):
                logger.info('Auto cake task is over count')
                break
            # 检测门票数量
            if self.appear(self.I_IS_REACH, interval=10):
                if self.appear_rgb(self.I_IS_CLOSE):
                    logger.info('开启樱饼')
                    self.appear_then_click(self.I_IS_CLOSE, interval=1)
                    self.device.stuck_record_add('BATTLE_STATUS_S')
                res, score = self.O_REMAIN_AP_ACTIVITY2.ocr(self.device.image, return_score=True)
                ocr_count += 1
                if score > 0.6:
                    if res <= 0:
                        logger.warning(f'门票数量：{res}, 任务结束')
                        break
                else:
                    if ocr_count > 5:
                        self.save_image(content=f'ocr识别多次，置信度过低：{score}，结束任务', push_flag=True, image_type=True, wait_time=0)
                        return
                    self.save_image(content=f'置信度过低：{score}', push_flag=True, image_type=True, wait_time=0)
            # 定时重置状态
            if swipe_timer.reached():
                swipe_timer.reset()
                self.device.stuck_record_clear()
                self.device.stuck_record_add('BATTLE_STATUS_S')

    def home_main(self) -> bool:
        """
        从庭院到活动的爬塔界面，统一入口
        :return:
        """
        logger.hr("Enter Shikigami", 2)
        while 1:
            self.screenshot()
            self.C_RANDOM_LEFT.name = "BATTLE_RANDOM"
            self.C_RANDOM_RIGHT.name = "BATTLE_RANDOM"
            self.C_RANDOM_TOP.name = "BATTLE_RANDOM"
            self.C_RANDOM_BOTTOM.name = "BATTLE_RANDOM"
            if self.appear(self.I_IS_REACH):
                break
            if self.appear_then_click(self.I_SHI, interval=1):
                continue
            if self.appear_then_click(self.I_TOGGLE_BUTTON, interval=3):
                continue
            if self.appear_then_click(self.I_SKIP_BUTTON, interval=1.5):
                continue
            # 如果出现了 “获得奖励”
            reward_click = random.choice(
                [self.C_RANDOM_LEFT, self.C_RANDOM_RIGHT, self.C_RANDOM_TOP, self.C_RANDOM_BOTTOM])
            if self.appear_then_click(self.I_UI_REWARD, action=reward_click, interval=1.3):
                continue
            if self.appear_then_click(self.I_RED_EXIT, interval=1.5):
                continue
            if self.appear_then_click(self.I_STEP_2, interval=2):
                continue


if __name__ == '__main__':
    from module.config.config import Config
    from module.device.device import Device

    c = Config('du')
    d = Device(c)
    t = ScriptTask(c, d)

    t.run()
