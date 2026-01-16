# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
from datetime import datetime
from module.exception import TaskEnd
from module.logger import logger
from tasks.CourtyardAffairs.assets import CourtyardAffairsAssets
from tasks.CourtyardAffairs.page import page_courtyard_affairs
from tasks.GameUi.game_ui import GameUi
from tasks.GameUi.page import page_main
from tasks.Restart.assets import RestartAssets


class ScriptTask(CourtyardAffairsAssets, GameUi):
    """ 庭院事务 """

    def run(self) -> None:
        self.courtyard_affairs()
        self.next_run_time()
        raise TaskEnd

    def courtyard_affairs(self) -> None:
        self.ui_goto_page(page_main)
        self.ui_click(self.I_REFRESH, self.I_COURTYARD_AFFAIRS_BUTTON)
        self.ui_goto_page(page_courtyard_affairs)

        click_count = 0
        while 1:
            self.screenshot()

            if click_count >= 3:
                logger.warning('庭院暂无可完成的事务!')
                # self.save_image(task_name="庭院暂无可完成的事务",image_type=True, wait_time=0)
                break
            # 点击取消
            if self.appear_then_click(RestartAssets.I_LOGIN_CANCEL_BATTLE):
                logger.info('式神满级，是否提取物经验？-点击取消')
                # self.save_image(task_name="庭院事务领取？-点击取消", push_flag=True, wait_time=0, image_type=True)
                continue
            if self.appear(self.I_SUCCESS_CLAIMED):
                # self.save_image(task_name="庭院事务完成",image_type=True)
                break
            if self.appear_then_click(self.I_COMPLETE_WITH_ONE_CLICK, interval=1):
                click_count += 1
                continue
            if self.appear_then_click(self.I_DAILY, interval=1):
                continue

    def next_run_time(self):
        time_1 = self.config.courtyard_affairs.next_task_time.run_time_1
        time_2 = self.config.courtyard_affairs.next_task_time.run_time_2

        current_time = datetime.now().time()

        if time_1 <= current_time <= time_2:
            # 当前时间在 run_time_1 到 run_time_2 范围内
            self.custom_next_run(task='CourtyardAffairs', custom_time=time_2, time_delta=0)
        elif current_time < time_1:
            # 当前时间早于 run_time_1，设置为 run_time_1
            self.custom_next_run(task='CourtyardAffairs', custom_time=time_1, time_delta=0)
        else:
            # 当前时间晚于 run_time_2，设置为明天的 run_time_1
            self.custom_next_run(task='CourtyardAffairs', custom_time=time_1, time_delta=1)



if __name__ == "__main__":
    from module.config.config import Config

    c = Config("du")
    t = ScriptTask(c)
    t.next_run_time()
