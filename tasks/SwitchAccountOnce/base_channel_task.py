import json
from datetime import datetime, timedelta
from enum import Enum
from module.exception import TaskEnd, SwitchAccountError
from module.logger import logger
from tasks.Component.SwitchAccount.switch_account import SwitchAccount
from tasks.Component.SwitchAccount.switch_account_config import AccountInfo
from tasks.GameUi.game_ui import GameUi


class TaskType(str, Enum):
    dailyTask = 'dailyTime'
    limitTask = 'limitTime'
    weekTask = 'weekTime'
    assist50 = 'assist50Time'


class BaseChannelTask(GameUi):
    switich_account_task_list = ["SwitchAccountOnce", "SwitchAccountLoop"]

    # 提取两个子类的共同方法
    def run_task(self, con, current_account_data, index, task_type):
        pass

    def set_task(self, con, current_account_data, account_index, task_type):
        pass

    def switch_account(self, con, current_account_data, index, task_type):
        account_info = f"{current_account_data.get('svr')}-{current_account_data.get('character')}"

        logger.info(f"[角色] {account_info}, 开始切换...")

        toAccount = AccountInfo(
            account=current_account_data.get("account"),
            password=current_account_data.get("password", False),
            account_alias=current_account_data.get("accountAlias"),
            apple_or_android=current_account_data.get("appleOrAndroid", True),
            character=current_account_data.get("character"),
            svr=current_account_data.get("svr"),
            enable_wy=current_account_data.get("enable_wy", True),
        )

        sa = SwitchAccount(self.config, toAccount)
        login = sa.switchAccount()
        if login:

            def update_config():
                self.config.switch_account_config.config.account_name = account_info
            self.config.safe_save(update_config)

            logger.info(f"[角色] {account_info}, 切换完成")
        else:
            self.update_account_data(con.once_config.accounts_file, current_account_data, index, task_type)
            raise SwitchAccountError(f"[角色] {account_info}, 切换失败")

    def update_account_data(self, accounts_file, current_account_data, account_index, task_type, datetoday=None):
        # 更新当前账号的完成时间
        if datetoday is None:
            datetoday = datetime.now().strftime("%Y-%m-%d")
        current_account_data[f"{task_type}"] = datetoday

        # 重新读取完整数据
        with open(f'config/SwitchAccount/{accounts_file}', 'r', encoding='utf-8') as file:
            all_accounts_data = json.load(file)

        # 更新指定索引位置的数据
        all_accounts_data[account_index] = current_account_data

        # 保存回文件
        with open(f'config/SwitchAccount/{accounts_file}', 'w', encoding='utf-8') as file:
            json.dump(all_accounts_data, file, ensure_ascii=False, indent=4)

    def update_all_account_data(self, accounts_file, all_accounts_data, task_type, datetoday=None):
        # 更新当前账号的完成时间
        if datetoday is None:
            datetoday = datetime.now().strftime("%Y-%m-%d")

        # 遍历所有账号数据，更新每个账号的指定任务类型时间
        for account_data in all_accounts_data:
            account_data[f"{task_type}"] = datetoday

        # 保存回文件
        with open(f'config/SwitchAccount/{accounts_file}', 'w', encoding='utf-8') as file:
            json.dump(all_accounts_data, file, ensure_ascii=False, indent=4)

    def set_wait_task_time(self):
        def update_config():
            self.config.switch_account_config.config.account_name = "未知角色"
        self.config.safe_save(update_config)

        target_time = datetime(2099, 1, 1)
        for task in self.config.waiting_task:
            if task.command in self.switich_account_task_list:
                continue
            self.set_next_run(task=task.command, target=target_time)

    def get_task_type_name(self, task_type: TaskType) -> str:
        mapping = {
            TaskType.dailyTask: "日常任务",
            TaskType.limitTask: "限时任务",
            TaskType.weekTask: "周任务",
            TaskType.assist50: "协战任务"
        }
        return mapping.get(task_type, "未知任务")

    def _handle_limit_task_wait(self, now, task_type_name):
        """检查是否到达限时任务执行时间"""
        # 从配置中获取限时任务开始时间
        limit_time = self.config.switch_account_once.once_config.limit_task_time

        # 创建今天的限时任务执行时间
        limit_datetime = now.replace(hour=limit_time.hour, minute=limit_time.minute, second=limit_time.second, microsecond=0)

        if now >= limit_datetime:
            return  # 可以执行限时任务

        # 未到执行时间，设置等待
        self.set_wait_task_time()
        self.push_notify(content=f'[{task_type_name}]等待 {limit_time.hour:02d}:{limit_time.minute:02d} 运行')
        self.set_next_run(task=self.config.task.command, target=limit_datetime)
        raise TaskEnd

    def _set_batch_tasks(self, task_list, target_time):
        """批量设置任务执行时间"""
        for task in task_list:
            self.set_next_run(task=task, target=target_time)

    def _is_task_completed(self, task_type, taskCompleteTime, now):
        """检查任务是否已完成"""
        match task_type:
            case TaskType.dailyTask:
                return taskCompleteTime == str(now.date())
            case TaskType.weekTask:
                start_of_week = now.date() - timedelta(days=now.weekday())
                end_of_week = start_of_week + timedelta(days=6)
                taskCompleteTime_dt = datetime.strptime(taskCompleteTime, "%Y-%m-%d").date()
                return start_of_week <= taskCompleteTime_dt <= end_of_week
            case TaskType.limitTask:
                return taskCompleteTime == str(now.date())
            case TaskType.assist50:
                return taskCompleteTime == str(now.date())
        return False
