# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey

import json
from datetime import datetime
from module.exception import TaskEnd
from module.logger import logger
from tasks.Component.SwitchAccount.switch_account import SwitchAccount
from tasks.Component.SwitchAccount.switch_account_config import AccountInfo
from tasks.SwitchAccountOnce.base_channel_task import BaseChannelTask, TaskType
from tasks.SwitchAccountOnce.channel4399 import ScriptTask as ScriptTask4399
from tasks.SwitchAccountOnce.channelwy import ScriptTask as ScriptTaskWY

""" 账号切换 """


class ScriptTask(BaseChannelTask):
    def __init__(self, config):
        super().__init__(config)
        self.task_wy = ScriptTaskWY(self.config)
        self.task_4399 = ScriptTask4399(self.config)

    def run(self):
        con = self.config.switch_account_once

        # ===== 日常任务 =====
        self.run_start(con, TaskType.dailyTask)
    
        # ===== 协战任务 =====
        self.run_start(con, TaskType.assist50)
    
        # ===== 限时任务 =====
        self.run_start(con, TaskType.limitTask)

        # ===== 周任务 =====
        self.run_start(con, TaskType.weekTask)

        # 所有角色任务均已完成
        self.set_wait_task_time()
        self.set_next_run(task=self.config.task.command, success=True, finish=True)
        self.push_notify(content="✅ 所有角色任务均已完成")
        raise TaskEnd
        
    def run_start(self, con, task_type):

        accounts_file = con.once_config.accounts_file

        # 加载所有账号数据
        with open(f'config/SwitchAccount/{accounts_file}', 'r', encoding='utf-8') as file:
            all_accounts_data = json.load(file)

        task_type_name = self.get_task_type_name(task_type)
        logger.hr(task_type_name, 1)

        for index, current_account_data in enumerate(all_accounts_data):
            if current_account_data.get("enable_wy", True):
                # 网易渠道
                self.task_wy.run_task(con, current_account_data, index, task_type)
            else:
                # 4399渠道
                self.task_4399.run_task(con, current_account_data, index, task_type)


def run_task(config):
    t = ScriptTask(config)
    t.run()


def set_task_time(config):
    # 批量修改任务时间
    config.get_next()
    target_time = datetime(2099, 1, 1)
    for task in config.pending_task:
        config.task_delay(task=task.command, target=target_time)
    config.task_delay(task="SwitchAccountOnce", target=datetime.now())


def switch_account(config):
    account_list = [
        # AccountInfo(account="178****7164", account_alias="178****7164", apple_or_android=True, character="浙沥沥、下雨", svr="全球国际区"),
        # AccountInfo(account="187****4867", account_alias="187****4867", apple_or_android=True, character="紫芪", svr="破晓之樱"),

        AccountInfo(account="187****4867", account_alias="187****4867", apple_or_android=True, character="三千菟", svr="樱之华"),
        AccountInfo(account="150****7970", account_alias="150****7970", apple_or_android=True, character="落地反弹", svr="樱之华"),
        AccountInfo(account="sui94044@163.com", account_alias="sui94044", apple_or_android=True, character="阿岁啊", svr="樱之华"),
        AccountInfo(account="178****7164", account_alias="178****7164", apple_or_android=True, character="浙沥沥、下雨", svr="破晓之樱"),

        AccountInfo(account="150****7970", account_alias="150****7970", apple_or_android=True, character="落地反弹", svr="网易一两情相悦"),
        AccountInfo(account="187****4867", account_alias="187****4867", apple_or_android=True, character="三千卍", svr="旧友新朋"),
        AccountInfo(account="187****4867", account_alias="187****4867", apple_or_android=True, character="唳莅", svr="灵狐愿"),
        AccountInfo(account="187****4867", account_alias="187****4867", apple_or_android=True, character="夜玖幻", svr="游梦迷蝶"),
    ]

    for toAccount in account_list:
        sa = SwitchAccount(config, toAccount)
        sa.switchAccount()


def switch_qd_account(config):

    account_list = [
        AccountInfo(account="xilili1", account_alias="xilili1", password="ljx112757", enable_wy=False, apple_or_android=True, character="下雨1", svr="樱之华"),
        AccountInfo(account="xilili2s", account_alias="xilili2s", password="ljx112757", enable_wy=False, apple_or_android=True, character="下雨2、", svr="樱之华"),
        AccountInfo(account="xilili3", account_alias="xilili3", password="ljx112757", enable_wy=False, apple_or_android=True, character="下雨3", svr="樱之华"),
        AccountInfo(account="xilili4", account_alias="xilili4", password="ljx112757", enable_wy=False, apple_or_android=True, character="下雨4、", svr="樱之华"),
        AccountInfo(account="xilili5", account_alias="xilili5", password="ljx112757", enable_wy=False, apple_or_android=True, character="下雨5", svr="樱之华"),
        AccountInfo(account="xilili6", account_alias="xilili6", password="ljx112757", enable_wy=False, apple_or_android=True, character="下雨6、", svr="樱之华"),
        AccountInfo(account="xilili7s", account_alias="xilili7s", password="ljx112757", enable_wy=False, apple_or_android=True, character="下雨7", svr="樱之华"),
        AccountInfo(account="xilili8", account_alias="xilili8", password="ljx112757", enable_wy=False, apple_or_android=True, character="下雨8", svr="樱之华"),
        AccountInfo(account="xilili9", account_alias="xilili9", password="ljx112757", enable_wy=False, apple_or_android=True, character="下雨9", svr="樱之华"),
        AccountInfo(account="xilili10", account_alias="xilili10", password="ljx112757", enable_wy=False, apple_or_android=True, character="下雨10", svr="樱之华"),
    ]
    for toAccount in account_list:
        sa = SwitchAccount(config, toAccount)
        sa.switchAccount()


if __name__ == '__main__':
    from module.config.config import Config
    # from module.device.device import Device

    config = Config('4399')
    # device = Device(config)
    # 运行任务
    # run_task(config)
    # 设置时间
    # set_task_time(config)
    # 切换账号
    # switch_account(config)
    switch_qd_account(config)

