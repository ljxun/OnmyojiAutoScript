# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
from datetime import datetime, time
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

        now_time = datetime.now().time()
        # 检查是否在12:00-14:00或20:00-22:00时间段内
        in_ap_time_1 = time(12, 0) <= now_time < time(14, 0)
        in_ap_time_2 = time(20, 0) <= now_time < time(22, 0)

        # 如果当前在领体力时间段内，设置下一次重启时间为下一个时间段
        if in_ap_time_1 or in_ap_time_2:
            # 如果在12:00-14:00之间，设置为当日 time_2
            if in_ap_time_1:
                self.custom_next_run(task='CourtyardAffairs', custom_time=time_2, time_delta=0)
            # 如果在20:00-22:00之间，设置为次日 time_1
            else:
                self.custom_next_run(task='CourtyardAffairs', custom_time=time_1, time_delta=1)
        else:
            # 如果不在领体力时间段内，根据当前时间设置最近重启时间
            if now_time < time_1:
                # 当前时间早于 time_1，设置为 time_1
                self.custom_next_run(task='CourtyardAffairs', custom_time=time_1, time_delta=0)
            elif time_1 <= now_time < time_2:
                # 当前时间在 time_1 到 time_2 范围内
                self.custom_next_run(task='CourtyardAffairs', custom_time=time_2, time_delta=0)
            else:
                # 当前时间晚于 time_2，设置为明天的 time_1
                self.custom_next_run(task='CourtyardAffairs', custom_time=time_1, time_delta=1)



if __name__ == "__main__":
    from module.config.config import Config

    c = Config("du")
    t = ScriptTask(c)
    t.next_run_time()
