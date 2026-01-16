# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey

from datetime import datetime, time
from module.exception import TaskEnd
from module.logger import logger
from tasks.Restart.login import LoginHandler


class ScriptTask(LoginHandler):

    def run(self) -> None:
        """
        主要就是登录的模块
        :return:
        """
        # 每日第一次启动游戏，运行日志备份
        if self.config.back_up.scheduler.enable and self.config.back_up.back_up_config.backup_date != str(datetime.now().date()):
            self.set_next_run(task='BackUp', target=datetime.now())
        # 每日第一次启动游戏，运行集体任务
        if self.config.collective_missions.missions_config.enable and self.config.collective_missions.missions_config.task_date != str(datetime.now().date()):
            self.set_next_run(task='CollectiveMissions', target=datetime.now())
        if not self.delay_pending_tasks():
            self.app_restart()
        raise TaskEnd('ScriptTask end')

    def app_restart(self):
        logger.hr('App restart')
        self.device.app_stop()
        self.device.app_start()
        self.app_handle_login()

        # 检查庭院任务运行
        self.check_running_task()

        self.set_next_run(task='Restart', success=True, finish=True, server=True)


    def check_running_task(self):
        now = datetime.now()
        # 检查当前时间是否在12:00-14:00或20:00-22:00时间段内
        now_in_time_1 = time(12, 0) <= now.time() < time(14, 0)
        now_in_time_2 = time(20, 0) <= now.time() < time(22, 0)

        if now_in_time_1 or now_in_time_2:
            # 检查庭院任务时间是否在12:00-14:00或20:00-22:00时间段内
            courtyard_affairs_time = self.config.courtyard_affairs.scheduler.next_run.time()
            task_in_time_1 = time(12, 0) <= courtyard_affairs_time < time(14, 0)
            task_in_time_2 = time(20, 0) <= courtyard_affairs_time < time(22, 0)

            if now_in_time_1 and task_in_time_1:
                self.set_next_run(task='CourtyardAffairs', target=now)
                self.push_notify(f"✅重启时间{now},与庭院任务时间{courtyard_affairs_time}，是一个时间段，执行庭院任务")
            elif now_in_time_2 and task_in_time_2:
                self.set_next_run(task='CourtyardAffairs', target=now)
                self.push_notify(f"✅重启时间{now},与庭院任务时间{courtyard_affairs_time}，是一个时间段，执行庭院任务")
            else:
                self.push_notify(f"❌重启时间{now},与庭院任务时间{courtyard_affairs_time}，不是一个时间阶段，不执行庭院任务")
        else:
            logger.warning('当前时间不在体力补给时间段内，不执行庭院任务')

    #     # 如果启用了定时领体力（每天 12-14、20-22 时内各有 20 体力）
    #     if self.config.restart.harvest_config.enable_ap:
    #         now = datetime.now()
    #         # 检查是否在12:00-14:00或20:00-22:00时间段内
    #         in_ap_time_1 = time(12, 0) <= now.time() < time(14, 0)
    #         in_ap_time_2 = time(20, 0) <= now.time() < time(22, 0)
    #
    #         # 如果当前在领体力时间段内，设置下一次重启时间为下一个时间段
    #         if in_ap_time_1 or in_ap_time_2:
    #             # 如果在12:00-14:00之间，设置为当日21:50
    #             if in_ap_time_1:
    #                 self.custom_next_run_task(Time(hour=21, minute=50, second=0), time_delta=0)
    #             # 如果在20:00-22:00之间，设置为次日13:50
    #             else:
    #                 self.custom_next_run_task(Time(hour=13, minute=50, second=0), time_delta=1)
    #         else:
    #             # 如果不在领体力时间段内，根据当前时间设置最近的重启时间
    #             # 如果时间在00:00-13:50之间则设定时间为当日 13:50 时
    #             if now.time() < time(13, 50):
    #                 self.custom_next_run_task(Time(hour=13, minute=50, second=0), time_delta=0)
    #             # 如果时间在13:50-21:50之间则设定时间为当日 21:50 时
    #             elif time(13, 50) <= now.time() < time(21, 50):
    #                 self.custom_next_run_task(Time(hour=21, minute=50, second=0), time_delta=0)
    #             # 如果时间在21:50-23:59之间则设定时间为次日 13:50 时
    #             else:
    #                 self.custom_next_run_task(Time(hour=13, minute=50, second=0), time_delta=1)
    #
    # def custom_next_run_task(self, custom_time, time_delta):
    #     self.custom_next_run(task='Restart', custom_time=custom_time, time_delta=time_delta)
    #     self.custom_next_run(task='CourtyardAffairs', custom_time=custom_time, time_delta=time_delta)

    def delay_pending_tasks(self) -> bool:
        """
        周三更新游戏的时候延迟
        @return:
        """
        datetime_now = datetime.now()
        if not (datetime_now.weekday() == 2 and 7 <= datetime_now.hour <= 8):
            return False
        logger.warning("周三游戏更新,7:00-8:59的任务延迟到9:00")
        # running 中的必然是 Restart
        for task in self.config.pending_task:
            print(task.command)
            self.set_next_run(task=task.command, target=datetime_now.replace(hour=9, minute=0, second=0, microsecond=0))
        return True


if __name__ == '__main__':
    from module.config.config import Config

    config = Config('mi')
    t = ScriptTask(config)
    # t.run()
    t.check_running_task()
    # task.config.update_scheduler()
    # task.delay_pending_tasks()
    # task.app_restart()
    # task.screenshot()
    # print(task.appear_then_click(task.I_LOGIN_SCROOLL_CLOSE, threshold=0.9))
