# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey

from datetime import datetime, timedelta
from module.exception import TaskEnd
from module.logger import logger
from tasks.SwitchAccountOnce.base_channel_task import BaseChannelTask, TaskType

""" 小号切换 """


class ScriptTask(BaseChannelTask):
    # 跳过的任务
    skip_task = ['Restart', 'BackUp', 'SwitchAccountLoop']
    # 周任务只在周一 运行
    week_task = ['RichMan', 'WeeklyTrifles']
    # 限时任务 晚上7点后运行
    limit_task = ['Hunt', 'DemonEncounter', 'Duel', 'AreaBoss', 'CollectiveMissions']
    # 协站50运行的任务
    assist50_run_task = ['DailyTrifles', 'EvoZone']
    # 总是运行的任务
    always_run_task = ['CourtyardAffairs','KekkaiUtilize', 'TalismanPass']
    task_type_name = ''
    account_info = ''

    def run_task(self, con, current_account_data, index, task_type):
        # 初始化任务信息
        self.task_type_name = self.get_task_type_name(task_type)
        self.account_info = f"{current_account_data.get('svr')}-{current_account_data.get('character')}"

        # 检查任务完成时间信息
        taskCompleteTime = current_account_data.get(f"{task_type}")
        if taskCompleteTime is None:
            logger.info(f"[角色] {self.account_info}, 没有[{self.task_type_name}]信息, 跳过")
            return

        # 协战任务特殊处理
        is_only_assist50 = bool(current_account_data.get('isAssist50'))
        if is_only_assist50 and task_type != TaskType.assist50:
            logger.info(f"[角色] {self.account_info}, 只做 [协战任务], [{self.task_type_name}], 跳过")
            return
        elif not is_only_assist50 and task_type == TaskType.assist50:
            logger.info(f"[角色] {self.account_info}, 不做 [{self.task_type_name}], 跳过")
            return

        # 任务完成情况检查
        now = datetime.now()
        if self._is_task_completed(task_type, taskCompleteTime, now):
            logger.info(f"[角色] {self.account_info}, 已完成[{self.task_type_name}], 跳过")
            return

        # 限时任务时间检查
        if task_type == TaskType.limitTask:
            self._handle_limit_task_wait(now, self.task_type_name)

        # 执行任务
        logger.info(f"[角色] {self.account_info}, 上次 [{self.task_type_name}] 完成时间: {taskCompleteTime}")
        self.switch_account(con, current_account_data, index, task_type)
        self.set_task(con, current_account_data, index, task_type)
        # 本次任务设置为一分钟后
        self.set_next_run(target=datetime.now() + timedelta(minutes=1))
        raise TaskEnd

    def set_task(self, con, current_account_data, index, task_type):
        logger.info(f"[角色] {self.account_info}, 开始调起任务")

        target_time = datetime(2000, 1, 1)
        match task_type:
            # 日常任务
            case TaskType.dailyTask:
                for task in self.config.waiting_task:
                    if task.command in set(self.skip_task) | set(self.week_task) | set(self.limit_task):
                        continue
                    self.set_next_run(task=task.command, target=target_time)
            # 限时任务
            case TaskType.limitTask:
                self._set_batch_tasks(self.limit_task, target_time)
                self._set_batch_tasks(self.always_run_task, target_time)
            # 周任务
            case TaskType.weekTask:
                self._set_batch_tasks(self.week_task, target_time)
            # 协站50任务
            case TaskType.assist50:
                self._set_batch_tasks(self.assist50_run_task, target_time)

        # 更新数据和通知
        self.update_account_data(con.once_config.accounts_file, current_account_data, index, task_type)
        # self.push_notify(content=f"{self.account_info} [{self.task_type_name}]创建")
