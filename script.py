# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
import time

import cv2
import inflection
import json
import re
import zerorpc
import zmq
from cached_property import cached_property
from datetime import datetime, timedelta
from module.base.decorator import del_cached_property
from module.base.utils import load_module
from module.config.config import Config
from module.config.utils import convert_to_underscore
from module.device.device import Device
from module.device.device_manager import DeviceManager
from module.exception import *
from module.logger import logger, error_path, get_filename
from module.server.i18n import I18n
from multiprocessing.queues import Queue
from pathlib import Path
from pydantic import ValidationError
from threading import Thread
from typing import Callable
from module.device.emulator_manager import EmulatorManager


class Script:
    def __init__(self, config_name: str = 'oas') -> None:
        self.team_running = False
        self.server = None
        self.state_queue: Queue = None
        self.gui_update_task: Callable = None  # 回调函数, gui进程注册当每次config更新任务的时候更新gui的信息
        self.config_name = config_name
        self.failure_record = {}
        # 运行loop的线程
        self.loop_thread: Thread = None
        self.start_loop_count = 1

    @cached_property
    def config(self) -> "Config":
        try:
            from module.config.config import Config
            config = Config(config_name=self.config_name)
            # 将state_queue传递给config实例
            config.state_queue = self.state_queue
            return config
        except RequestHumanTakeover:
            logger.critical('Request human takeover')
            exit(1)
        except Exception as e:
            logger.exception(e)
            exit(1)

    @property
    def emulator(self) -> "EmulatorManager":
        return EmulatorManager(config=self.config)

    @property
    def device(self) -> "Device":
        # 使用全局设备管理器获取共享设备实例
        return DeviceManager.get_device(config=self.config)

    @property
    def device_status(self) -> bool:
        # 使用全局设备管理器获取设备状态
        return DeviceManager.get_device_status()
    
    @device_status.setter
    def device_status(self, value: bool):
        # 使用全局设备管理器设置设备状态
        DeviceManager.set_device_status(value)

    def reset_device(self):
        # 重置共享设备实例
        del_cached_property(self, 'config')
        logger.debug('[清理] config 清理工作已完成')
        DeviceManager.reset_device()

    @cached_property
    def checker(self):
        """
        占位函数，在alas中是检查服务器是否正常的
        :return:
        """
        return None

    def save_error_log(self, task='taskname', error_type='Error'):
        """
        Save last 60 screenshots in ./log/error/<timestamp>
        Save logs to ./log/error/<timestamp>/log.txt
        """
        from module.base.utils import save_image
        from module.handler.sensitive_info import (handle_sensitive_image,
                                                   handle_sensitive_logs)
        if self.config.script.error.save_error:
            # 账号切换任务配置
            con = self.config.switch_account_config.config
            config_name = self.config.config_name.upper()

            if con.enable:
                name = con.account_name
                config_name = f"{config_name}_{name}"

            folder = f'{error_path}/{error_type}/{task}/{config_name}'
            filename = get_filename(config_name)
            error_path_base = f'{folder}/{filename}'
            error_log_path = f'{error_path_base}.log'
            error_image_path = f'{error_path_base}.png'
            Path(folder).mkdir(parents=True, exist_ok=True)
            logger.info(f"保存错误日志到: {error_log_path}")
            logger.info(f"保存错误截图到: {error_image_path}")

            with open(logger.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                start = 0
                for index, line in enumerate(lines):
                    line = line.strip(' \r\t\n')
                    if re.match('^═{15,}$', line):
                        start = index
                lines = lines[start - 2:]
                lines = handle_sensitive_logs(lines)
            with open(error_log_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)

            image = ''
            if self.emulator.is_emulator_running():
                if hasattr(self.device, 'image') and self.device.image is not None:
                    try:
                        save_image(self.device.image, error_image_path)
                        image = self.device.image
                    except Exception as e:
                        logger.warning(f"保存错误截图失败: {str(e)}")

            # asyncio.run(self.config.pushtg.telegram_send(title, error_path_image, error_path_log))
            if con.enable:
                name = con.account_name
                logger.info(f"已开启小号任务，拼接[{name}]，发送通知")
                task = f"{name}▪{I18n.trans_zh_cn(task)}"
            self.config.notifier.send_push(f"❌ {I18n.trans_zh_cn(task)}", error_type, image, error_log_path)

    def init_server(self, port: int) -> int:
        """
        初始化zerorpc服务，返回端口号
        :return:
        """
        self.server = zerorpc.Server(self)
        try:
            self.server.bind(f'tcp://127.0.0.1:{port}')
            return port
        except zmq.error.ZMQError:
            logger.error(f"Ocr server cannot bind on port {port}")
            return False

    def run_server(self) -> None:
        """
        启动zerorpc服务
        :return:
        """
        self.server.run()

    def gui_args(self, task: str) -> str:
        """
        获取给gui显示的参数
        :return:
        """
        return self.config.gui_args(task=task)

    def gui_menu(self) -> str:
        """
        获取给gui显示的菜单
        :return:
        """
        return self.config.gui_menu

    def gui_task(self, task: str) -> str:
        """
        获取给gui显示的任务 的参数的具体值
        :return:
        """
        return self.config.model.gui_task(task=task)

    def gui_set_task(self, task: str, group: str, argument: str, value) -> bool:
        """
        设置给gui显示的任务 的参数的具体值
        :return:
        """
        # 验证参数
        task = convert_to_underscore(task)
        group = convert_to_underscore(group)
        argument = convert_to_underscore(argument)
        # pandtic验证
        if isinstance(value, str):
            if len(value) == 8:
                try:
                    value = datetime.strptime(value, '%H:%M:%S').time()
                except ValueError:
                    pass

        path = f'{task}.{group}.{argument}'
        task_object = getattr(self.config.model, task, None)
        group_object = getattr(task_object, group, None)
        argument_object = getattr(group_object, argument, None)

        if argument_object is None:
            logger.error(f'Set arg {task}.{group}.{argument}.{value} failed')
            return False

        try:
            setattr(group_object, argument, value)
            argument_object = getattr(group_object, argument, None)
            logger.info(f'Set arg {task}.{group}.{argument}.{argument_object}')
            self.config.save()  # 我是没有想到什么方法可以使得属性改变自动保存的
            return True
        except ValidationError as e:
            logger.error(e)
            return False

    @zerorpc.stream
    def gui_mirror_image(self):
        """
        获取给gui显示的镜像
        :return: cv2的对象将 numpy 数组转换为字节串。接下来MsgPack 进行序列化发送方将图像数据转换为字节串
        """
        # return msgpack.packb(cv2.imencode('.jpg', self.device.screenshot())[1].tobytes())
        img = cv2.cvtColor(self.device.screenshot(), cv2.COLOR_RGB2BGR)
        self.device.stuck_record_clear()
        ret, buffer = cv2.imencode('.jpg', img)
        yield buffer.tobytes()

    def _gui_update_tasks(self) -> None:
        """
        获取更新任务后 pending waiting 的任务 和 当前的任务的数据。打包给gui显示
        :return:
        """
        data = {}
        pending = []
        waiting = []
        task = {}
        if self.config.task is not None and self.config.task.next_run < datetime.now():
            task["name"] = self.config.task.command
            task["next_run"] = str(self.config.task.next_run)
        data["task"] = task

        for p in self.config.pending_task[1:]:
            item = {"name": p.command, "next_run": str(p.next_run)}
            pending.append(item)

        for w in self.config.waiting_task:
            item = {"name": w.command, "next_run": str(w.next_run)}
            waiting.append(item)

        data["pending"] = pending
        data["waiting"] = waiting

        if self.gui_update_task is not None:
            self.gui_update_task(data)

    def _gui_set_status(self, status: str) -> None:
        """
        设置给gui显示的状态
        :param status: 可以在gui中显示的状态 有 "Init", "Empty"(不显示), "Run"(运行中), "Error", "Free"(空闲)
        :return:
        """
        data = {"status": status}
        if self.gui_update_task is not None:
            self.gui_update_task(data)

    def gui_task_list(self) -> str:
        """
        获取给gui显示的任务列表
        :return:
        """
        result = {}
        for key, value in self.config.model.dict().items():
            if isinstance(value, str):
                continue
            if key == "restart":
                continue
            if "scheduler" not in value:
                continue

            scheduler = value["scheduler"]
            item = {"enable": scheduler["enable"],
                    "next_run": str(scheduler["next_run"])}
            key = self.config.model.type(key)
            result[key] = item
        return json.dumps(result)

    def wait_until(self, future):
        """
        Wait until a specific time.

        Args:
            future (datetime):

        Returns:
            bool: True if wait finished, False if config changed.
        """
        future = future + timedelta(seconds=1)
        self.config.start_watching()
        while 1:
            if datetime.now() > future:
                return True

            time.sleep(5)

            if self.config.should_reload():
                return False

    def get_next_task(self) -> str:
        """获取下一个任务名(大驼峰格式)"""
        while True:
            # 准备任务配置
            task = self.config.get_next()
            self.config.task = task
            if self.state_queue:
                self.state_queue.put({"schedule": self.config.get_schedule_data()})

            now = datetime.now()
            if task.next_run <= now:
                break

            # 处理等待策略
            opt = self.config.script.optimization
            wait_duration = task.next_run - now

            # 转换关闭时间为时间差
            def to_delta(t):
                delta = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
                return delta if delta.total_seconds() > 0 else None

            # 策略判断条件
            close_emu_delta = to_delta(opt.close_emulator_time)
            close_game_delta = to_delta(opt.close_game_time)
            should_close_emu = close_emu_delta and wait_duration > close_emu_delta
            should_close_game = close_game_delta and wait_duration > close_game_delta

            is_emulator_running = self.emulator.is_emulator_running()

            # 执行等待策略
            if opt.do_noting:
                logger.warning("不关闭游戏, 等待下一个任务")
            elif should_close_emu:
                if is_emulator_running:
                    logger.warning("模拟器关闭前, 等待30秒...")
                    if not self.check_wait_until(datetime.now() + timedelta(seconds=30)):
                        continue
                    self.emulator.stop_emulator()
                    is_emulator_running = False
                    DeviceManager.reset_device()
            elif should_close_game:
                if is_emulator_running and self.emulator.is_app_running():
                    logger.warning("游戏关闭前, 等待10秒...")
                    if not self.check_wait_until(datetime.now() + timedelta(seconds=10)):
                        continue
                    self.emulator.app_stop()
                    DeviceManager.reset_device()

            # 执行等待操作
            logger.hr(f"模拟器状态 {is_emulator_running}", level=1)
            wait_info = f'{I18n.trans_zh_cn(task.command)}({task.next_run.strftime("%H:%M:%S")})'
            delta_str = str(task.next_run - now).split('.')[0]
            logger.info(f'🕒 等待任务 | {wait_info} | 剩余时长: {delta_str}')

            # 等待下个任务循环5秒检查一次
            if not self.check_wait_until(task.next_run):
                continue

        return task.command

    def check_wait_until(self, future_time):
        if self.wait_until(future_time):
            return True
        else:
            logger.warning("检测到配置变更，重新加载任务配置")
            del_cached_property(self, 'config')
            return False

    def run(self, command: str) -> bool:
        """
        :param command:  大写驼峰命名的任务名字
        :return:
        """
        try:
            module_name = 'script_task'
            module_path = str(Path.cwd() / 'tasks' / command / (module_name + '.py'))
            logger.info(f'module_path: {module_path}, module_name: {module_name}')
            task_module = load_module(module_name, module_path)
            task_module.ScriptTask(config=self.config).run()
        except TaskEnd:
            return True
        except GameNotRunningError as e:
            logger.warning(e)
            self.config.task_call('Restart')
            return True
        except Exception as e:
            # 特别处理OpenCV模板匹配异常
            if isinstance(e, cv2.error) and "Assertion failed" in str(e) and "corr.rows <= img.rows" in str(e):
                logger.error(f"模板匹配失败: 模板尺寸大于目标图像尺寸")
                logger.error(f"详细错误: {str(e)}")
                error_type = "TemplateMatchError"
            else:
                error_type = type(e).__name__  # 获取异常类型名称

            result = False
            if isinstance(e, (GameWaitTooLongError, GameTooManyClickError, GamePageUnknownError, GameStuckError, GameBugError, FileNotFoundError)):
                logger.error(e)
                logger.warning(f'{error_type}, Game will be restarted in 10 seconds')
                self.save_error_log(task=command, error_type=error_type)
                time.sleep(10)
                self.config.task_call('Restart')
                return result
            elif isinstance(e, ScriptError):
                logger.critical(e)
            elif isinstance(e, RequestHumanTakeover):
                if "screenshot error" in str(e):
                    logger.error("截图异常，模拟器可能未启动")
                    return False
                logger.error(e)
                logger.critical(e)
                result = 'exit'
            elif isinstance(e, SwitchAccountError):
                error_type = str(e)
                logger.warning(error_type)
            else:
                logger.exception(e)
            self.save_error_log(task=command, error_type=error_type)
            return result

    def loop(self):
        """
        调度器主循环
        """
        # 初始化日志
        logger.set_file_logger(self.config_name)

        # 重置状态
        logger.info(f'[准备] 正在重置状态...')
        self.failure_record = {}
        is_first_task = True
        stop_requested = False
        self.config.model.running_task = ""

        logger.info(f'[启动] 调度器循环开始 | 配置: {self.config_name}')
        try:
            while not stop_requested:
                try:
                    # ------------------------- 获取任务 -------------------------
                    task = self.get_next_task()
                    task_chinese_name = I18n.trans_zh_cn(task)
                    logger.info(f'[任务] 获取到任务 | {task_chinese_name}')

                    # ------------------------- 跳过首次重启任务 -------------------------
                    if is_first_task and task == 'Restart':
                        logger.info('[任务] 跳过第一次启动时的重启任务')
                        self.config.task_delay(task='Restart', success=True, server=True)
                        del_cached_property(self, 'config')
                        is_first_task = False
                        continue

                    # ------------------------- 任务执行 -------------------------
                    logger.hr(f'{task_chinese_name} Start', 0)
                    self.config.model.running_task = task
                    success = self.run(inflection.camelize(task))
                    self.config.model.running_task = ""
                    logger.hr(f'{task_chinese_name} End', 0)
                    is_first_task = False
                    del_cached_property(self, 'config')

                    # ------------------------- 失败处理 -------------------------
                    if success == 'exit':
                        logger.info('[错误] RequestHumanTakeover 异常,退出调度器 error')
                        stop_requested = True
                        exit(1)

                    if success:
                        self.start_loop_count = 1
                        self.failure_record[task] = 0
                        continue
                    else:
                        failed = self.failure_record.get(task, 0) + 1
                        self.failure_record[task] = failed
                        MAX_FAIL_COUNT = 3

                        logger.info(f'[任务统计] 任务: {task_chinese_name} | 累计失败次数: {failed}/{MAX_FAIL_COUNT}')

                        if failed >= MAX_FAIL_COUNT:
                            logger.critical(f'[错误] 任务连续失败超过阈值 | 任务: {task_chinese_name} | 次数: {failed}/{MAX_FAIL_COUNT}')

                            # 失败次数超限，关闭任务
                            # task_name = convert_to_underscore(task)
                            # task_object = getattr(self.config.model, task_name, None)
                            # scheduler = getattr(task_object, 'scheduler', None)
                            # scheduler.enable = False
                            # self.config.save()

                            self.config.notifier.push(title=f"❌❌❌ {task_chinese_name}", content=f"任务连续失败{failed}次, 按照任务成功处理")
                            # 任务连续失败, 按照执行成功处理
                            self.config.task_delay(task, success=True, server=True)

                            logger.error('[错误] 退出调度器')
                            stop_requested = True
                            exit(1)
    
                except Exception as e:
                    error_type = type(e).__name__  # 获取异常类型名称
                    logger.error(f'[异常] 循环运行崩溃: {error_type} | {str(e)}', exc_info=True)
                    self.config.notifier.push(title="❌❌❌ 循环崩溃", content=str(e))
                    stop_requested = True
                finally:
                    if stop_requested:
                        self.reset_device()
        finally:
            self.reset_device()
            exit(1)
    
    def start_loop(self):
        """
        循环启动控制器
        """
        # 初始化日志
        logger.set_file_logger(self.config_name)

        logger.info('[启动] 启动循环守护线程')
        max_start_loop_count = 3

        while self.start_loop_count <= max_start_loop_count:
            # 启动新线程
            self.loop_thread = Thread(target=self.loop)
            self.loop_thread.start()
            logger.info(f'[线程] 工作线程已启动 | 启动次数: {self.start_loop_count}/{max_start_loop_count}')

            # 等待线程结束（无限等待，确保线程完成）
            self.loop_thread.join()

            # 线程结束后准备启动
            self.start_loop_count += 1

            # 检查是否超过最大启动次数
            if self.start_loop_count > max_start_loop_count:
                break

        # 达到最大启动次数后的处理
        logger.error('[终止] 达到最大启动次数，系统退出')
        self.config.notifier.push(title='❌❌❌ 系统退出',content=f"[终止] 达到最大启动次数，系统退出")
        time.sleep(5)
        exit(1)


if __name__ == "__main__":
    # logger.info(f'✅ {res_type}卡确认成功，重置状态')
    # logger.warning(f'❌ {res_type}卡确认失败，重置状态')
    script = Script("mi")
    script.start_loop()
    # while 1:
    # script = Script("oas3")
    # device = Device("oas3")
    # device.app_start()
    # time.sleep(10)
    # logger.info('Start app')
    # device.app_stop()
    # logger.info('Stop app')
    # time.sleep(5)
    # device.emulator_stop()
    # time.sleep(5)
    # del_cached_property(script, 'device')
    # del_cached_property(script, 'config')
    # script.start_loop()
    # script.save_error_log(title='ad')
    # locale.setlocale(locale.LC_TIME, 'chinese')
    # today = datetime.now()
    # date = today.strftime('%Y-%m-%d %A')
    # print(locale.windows_locale.values())  # Windows
    # print(date)
    # print(script.gui_task_list())
    # print(script.config.gui_menu)