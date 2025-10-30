# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
import copy
import datetime
import operator
import threading
import random

from datetime import datetime, timedelta
from cached_property import cached_property
from module.server.i18n import I18n
from threading import Lock

from module.base.filter import Filter
from module.config.config_updater import ConfigUpdater
from module.config.config_manual import ConfigManual
from module.config.config_watcher import ConfigWatcher
from module.config.config_menu import ConfigMenu
from module.config.config_model import ConfigModel
from module.config.config_state import ConfigState
from module.config.scheduler import TaskScheduler
from module.config.utils import *
from module.notify.notify import Notifier
from module.notify.pushtg import PushTg

from module.exception import RequestHumanTakeover, ScriptError
from module.logger import logger
from multiprocessing.queues import Queue


class Function:
    def __init__(self, key: str, data: dict):
        """
        输入的是每一个ConfigModel的一个字段对象
        :param data:
        """
        if isinstance(data, dict) is False:
            self.enable = False
            self.command = "Unknown"
            self.next_run = DEFAULT_TIME
            return
        if data.get("scheduler") is None:
            self.enable = False
            self.command = "Unknown"
            self.next_run = DEFAULT_TIME
            return

        self.enable: bool = data['scheduler']['enable']
        self.command: str = ConfigModel.type(key)
        next_run = data['scheduler']['next_run']
        if isinstance(next_run, str):
            next_run = datetime.strptime(next_run, "%Y-%m-%d %H:%M:%S")
        self.next_run: datetime = next_run
        priority = data['scheduler']['priority']
        if isinstance(priority, str):
            priority = int(priority)
        self.priority: int = priority
        if not isinstance(self.priority, int):
            logger.error(f"Invalid priority: {self.priority}")

        # self.enable = deep_get(data, keys="Scheduler.Enable", default=False)
        # self.command = deep_get(data, keys="Scheduler.Command", default="Unknown")
        # self.next_run = deep_get(data, keys="Scheduler.NextRun", default=DEFAULT_TIME)

    def __str__(self):
        enable = "Enable" if self.enable else "Disable"
        return f"{self.command} ({enable}, {self.priority}, {str(self.next_run)})"

    __repr__ = __str__

    def __eq__(self, other):
        if not isinstance(other, Function):
            return False

        if self.command == other.command and self.next_run == other.next_run:
            return True
        else:
            return False


def name_to_function(name):
    """
    Args:
        name (str):

    Returns:
        Function:
    """
    function = Function({})
    function.command = name
    function.enable = True
    return function


class Config(ConfigState, ConfigManual, ConfigWatcher, ConfigMenu):

    def __init__(self, config_name: str, task=None) -> None:
        """

        :param config_name:
        :param task:
        """
        super().__init__(config_name)  # 调用 ConfigState 的初始化方法
        super(ConfigManual, self).__init__()
        super(ConfigWatcher, self).__init__()
        super(ConfigMenu, self).__init__()
        self.model = ConfigModel(config_name=config_name)
        self.state_queue: Queue = None
        self.scheduler_update_dt = None # 调度器更新时间

    def __getattr__(self, name):
        """
        一开始是打算直接继承ConfigModel的，但是pydantic会接管所有的变量
        故而选择持有ConfigModel
        :param name:
        :return:
        """
        try:
            return getattr(self.model, name)
        except AttributeError:
            # 这个导致 大量的无用log
            # logger.error(f'can not ask this variable {name}')
            return None  # 或者抛出异常，或者返回其他默认值

    @cached_property
    def lock_config(self) -> Lock:
        return Lock()

    def gui_args(self, task: str) -> str:
        """
        获取给gui显示的参数
        :return:
        """
        return self.model.gui_args(task=task)

    def get_arg(self, task: str, group: str, argument: str):
        """

        :param task:
        :param group:
        :param argument:
        :return: str/int/float
        """
        try:
            return self.data[task][group][argument]
        except:
            logger.exception(f'have no arg {task}.{group}.{argument}')

    def set_arg(self, task: str, group: str, argument: str, value) -> None:
        """

        :param task:
        :param group:
        :param argument:
        :param value:
        :return:
        """
        try:
            self.data[task][group][argument] = value
        except:
            logger.exception(f'have no arg {task}.{group}.{argument}')

    def reload(self):
        self.model = ConfigModel(config_name=self.config_name)

    def safe_save(self, update_func=None):
        """
        安全保存配置，避免覆盖其他地方的修改
        1.先重新加载配置 2.修改参数 3.保存配置
        Args:
            update_func: 可选的更新函数，在重新加载后执行特定更新操作
        """
        logger.info(f'safe save config {self.config_name}')
        with self.lock_config:
            self.reload()  # 确保数据最新
            if update_func:
                update_func()
            self.save()

    def save(self) -> None:
        """
        保存配置文件
        :return:
        """
        # logger.info(f'save config {self.config_name}')
        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                self.model.write_json(self.config_name, self.model.dict())
                return
            except PermissionError as e:
                if attempt < max_retries - 1:
                    logger.warning(f"保存配置文件权限被拒绝，{retry_delay}秒后重试 (第{attempt + 1}次): {e}")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # 指数退避
                else:
                    logger.error(f"保存配置文件失败，已重试{max_retries}次仍无法访问: {e}")
                    raise
            except Exception as e:
                logger.error(f"保存配置文件时发生未知错误: {e}")
                raise

    def update_scheduler(self) -> None:
        """
        更新调度器， 设置pending_task and waiting_task
        :return:
        """
        pending_task = []
        waiting_task = []
        error = []
        self.scheduler_update_dt = datetime.now()
        for key, value in self.model.dict().items():
            func = Function(key, value)
            if not func.enable:
                continue
            if not isinstance(func.next_run, datetime):
                error.append(func)
            elif func.next_run < self.scheduler_update_dt:
                pending_task.append(func)
            else:
                waiting_task.append(func)

        # f = Filter(regex=r"(.*)", attr=["command"])
        # f.load(self.SCHEDULER_PRIORITY)
        if pending_task:
            # 先按照过滤器排序
            pending_task = TaskScheduler.filter.apply(pending_task)
            # logger.info(f'过滤器排序 pending_task: {pending_task}')

            # 再按照优先级排序
            pending_task = TaskScheduler.priority(pending_task)
            # logger.info(f'优先级排序 pending_task: {pending_task}')

            self.first_priority_task = pending_task[0].command

            # pending_task = TaskScheduler.schedule(rule=self.model.script.optimization.schedule_rule,
            #                                       pending=pending_task)
            running_task = self.model.running_task
            if running_task and pending_task:
                try:
                    # 若首位已经是目标，直接跳过后续循环
                    if pending_task[0].command != running_task:
                        for i, f in enumerate(pending_task):
                            if f.command == running_task:
                                # 移除并插入到首位
                                task = pending_task.pop(i)
                                pending_task.insert(0, task)
                                break  # 仅处理第一个匹配项

                except (ValueError, IndexError) as e:
                    logger.error(f"Error processing task: {e}, Current task list: {pending_task}")

        if waiting_task:
            # waiting_task = f.apply(waiting_task)
            # waiting_task = TaskScheduler.schedule(rule=self.model.script.optimization.schedule_rule,
            #                                       pending=waiting_task)

            # 先按照过滤器排序
            waiting_task = TaskScheduler.filter.apply(waiting_task)
            # logger.info(f'过滤器排序 waiting_task: {waiting_task}')

            # 再按照优先级排序
            waiting_task = TaskScheduler.priority(waiting_task)
            # logger.info(f'优先级排序 waiting_task: {waiting_task}')

            # 最后按照执行时间排序
            waiting_task = sorted(waiting_task, key=operator.attrgetter("next_run"))
            # logger.info(f'时间排序 waiting_task: {waiting_task}')

        if error:
            pending_task = error + pending_task

        self.pending_task = pending_task
        self.waiting_task = waiting_task

    def get_next(self) -> Function:
        """
        获取下一个要执行的任务
        :return:
        """
        self.update_scheduler()

        if self.pending_task:
            # logger.info(f"Pending tasks: {[f.command for f in self.pending_task]}")
            task = self.pending_task[0]
            self.task = task
            # logger.attr("Task", task)
            return task

        # 哪怕是没有任务，也要返回一个任务，这样才能保证调度器正常运行
        if self.waiting_task:
            logger.info("No task pending")
            task = copy.deepcopy(self.waiting_task[0])
            # task.next_run = (task.next_run + self.hoarding).replace(microsecond=0)
            logger.attr("Task", task)
            return task
        else:
            logger.critical("No task waiting or pending")
            logger.critical("Please enable at least one task")
            raise RequestHumanTakeover

    def get_schedule_data(self) -> dict[str, dict]:
        """
        获取调度器的数据， 但是你必须使用update_scheduler来更新信息
        :return:
        """
        # 根据调度器更新时间来判断是否有可运行的任务,保证逻辑一致性
        scheduler_update_dt = getattr(self, 'scheduler_update_dt', datetime.now())
        running = {}
        if self.task is not None and self.task.next_run < scheduler_update_dt:
            running = {"name": self.task.command, "next_run": str(self.task.next_run)}

        pending = []
        for p in self.pending_task[1:]:
            item = {"name": p.command, "next_run": str(p.next_run)}
            pending.append(item)

        waiting = []
        for w in self.waiting_task:
            item = {"name": w.command, "next_run": str(w.next_run)}
            waiting.append(item)

        data = {"running": running, "pending": pending, "waiting": waiting}
        return data

    def task_call(self, task: str = None, force_call=True):
        """
        回调任务，这会是在任务结束后调用
        :param task: 调用的任务的大写名称
        :param force_call:
        :return:
        """
        # 重置运行任务
        self.model.running_task = ""

        task = convert_to_underscore(task)
        if self.model.deep_get(self.model, keys=f'{task}.scheduler.next_run') is None:
            raise ScriptError(f"Task to call: `{task}` does not exist in user config")

        task_enable = self.model.deep_get(self.model, keys=f'{task}.scheduler.enable')
        if force_call or task_enable:
            next_run = datetime.now().replace(
                microsecond=0
            )
            logger.info(f"回调任务: [{task}]")
            self.model.deep_set(self.model, keys=f'{task}.scheduler.next_run', value=next_run)
            self.save()
            return True
        else:
            logger.info(f"Task call: {task} (skipped because disabled by user)")
            return False

    def task_delay(self, task: str = None, start_time: datetime = None,
                   success: bool = None, server: bool = True, target: datetime = None) -> None:
        """
        设置下次运行时间  当然这个也是可以重写的
        :param target: 可以自定义的下次运行时间
        :param server: True
        :param success: 判断是成功的还是失败的时间间隔
        :param task: 任务名称，大驼峰的
        :param finish: 是完成任务后的时间为基准还是开始任务的时间为基准
        :return:
        """
        next_run = None

        # 加载配置文件
        self.reload()
        # 任务预处理
        if not task:
            task = self.task.command
        task_name = task
        # 驼峰形式的字符串转换为下划线形式的字符串
        task = convert_to_underscore(task)
        task_object = getattr(self.model, task, None)
        if not task_object:
            logger.warning(f'No task named {task}')
            return
        scheduler = getattr(task_object, 'scheduler', None)
        if not scheduler:
            logger.warning(f'No scheduler in {task}')
            return

        # 任务开始时间
        if not start_time:
            start_time = datetime.now().replace(microsecond=0)

        if target is not None:
            target = [target] if not isinstance(target, list) else target
            next_run = nearest_future(target)

        elif success is not None:
            interval = (
                scheduler.success_interval
                if success
                else scheduler.failure_interval
            )
            if isinstance(interval, str):
                interval = timedelta(interval)

            # 如果间隔时间大于1天, 则将下次运行时间设置为固定时间加间隔天数
            if interval.days > 1:
                days_num = interval.days
                next_days_time = datetime.now() + timedelta(days=interval.days)
                next_run = datetime.combine(next_days_time, scheduler.server_update)
            else:
                # 如果间隔时间小于等于1天, 则将下次运行时间设置为当前时间加间隔时间
                days_num = 1
                next_run = start_time + interval

            if server and hasattr(scheduler, 'server_update'):
                # 如果有强制运行时间 并且运行成功 并且间隔时间小于等于一天
                if target is None and success and days_num == 1:
                    if scheduler.server_update != time(hour=9):
                        # 如果固定时间是不是9点 则将下次运行时间设置为明天的固定时间
                        next_run = parse_tomorrow_server(scheduler.server_update)

        # 总结
        # 如果间隔时间大于1天, 则将下次运行时间设置为固定时间加间隔天数
        # 如果间隔时间小于等于1天,并且固定时间是9点 则将下次运行时间设置为当前时间加间隔时间
        # 如果间隔时间小于等于1天,并且固定时间是不是9点 则将下次运行时间设置为明天的固定时间

        # 保证线程安全的
        self.lock_config.acquire()
        next_run = next_run.replace(microsecond=0)
        try:
            scheduler.next_run = next_run
            self.save()
        finally:
            self.lock_config.release()

        # 广播调度更新
        if next_run <= datetime.now():
            if self.state_queue is not None:
                try:
                    self.update_scheduler()
                    self.state_queue.put({"schedule": self.get_schedule_data()})
                    # logger.info("已广播调度更新")
                except Exception as e:
                    logger.warning(f"广播调度更新失败: {e}")
            else:
                logger.warning("state_queue 未设置，跳过广播")

        # 设置
        try:
            logger.hr(f'设置任务（`{I18n.trans_zh_cn(task_name)}` | {next_run}）执行', 2)
        except Exception as e:
            logger.warning(f"设置任务失败: {e}")

    # @cached_property
    # def notifier(self):
    #     notifier = Notifier(self.model.script.error.notify_config, enable=self.model.script.error.notify_enable)
    #     notifier.config_name = self.config_name.upper()
    #     logger.info(f'Notifier: {notifier.config_name}')
    #     return notifier

    @cached_property
    def notifier(self):
        notifier = Notifier(self.model.script.error.notify_config, self.model.script.error.pushtg_config, enable=self.model.script.error.notify_enable, enable_tg=self.model.script.error.pushtg_enable)
        notifier.config_name = self.config_name.upper()
        logger.info(f'Notifier: {notifier.config_name}')
        return notifier

    @cached_property
    def pushtg(self):
        pushtg = PushTg(self.model.script.error.pushtg_config, enable=self.model.script.error.pushtg_enable_error)
        pushtg.config_name = self.config_name.upper()
        logger.info(f'PushTg: {pushtg.config_name}')
        return pushtg


if __name__ == '__main__':
    config = Config(config_name='oas1')
    # print(config.model.running_task)
    # print(type(config.model.running_task))
    # if config.model.running_task is None:
    #     print('None')
    # if config.model.running_task == "Restart":
    # config.save()
    # config.update_scheduler()
    # print(config.pending_task)
    # config = Config(config_name='mi')
    # config.update_scheduler()
    # print(config.pending_task)

    print(config.get_next())
