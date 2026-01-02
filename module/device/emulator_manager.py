# -*- coding: utf-8 -*-
"""
用于管理模拟器的模块，不依赖ADB连接
通过模拟器管理器直接控制模拟器的启动、关闭等操作
"""
import os

from deploy.process import ProcessManager
from module.device.execute_util import execute_emulator, execute_show_window
from module.logger import logger
from module.server.setting import State
from tasks.Script.config_device import EmulatorWindow
from tasks.Script.config_device import PackageName
from module.device.app_control import AppControl
from module.device.platform2.emulator_windows import EmulatorManager as EmulatorManagerOld


class EmulatorManager:
    def __init__(self, config=None):
        """
        初始化模拟器管理器
        """
        self.config = config
        # 获取模拟器Serial
        self.serial = config.script.device.serial
        # 获取模拟器句柄
        self.handle = config.script.device.handle


        # 获取模拟器管理器路径
        # MuMu-5     E:/MuMuPlayer-12.0/nx_main/MuMuManager.exe
        # MuMu-4.12  E:/MuMuPlayer-12.0/shell/MuMuPlayer.exe    E:/MuMuPlayer-12.0/shell/MuMuManager.exe

        # 首先尝试使用已保存的路径
        self.manager_path = config.script.device.emulatorinfo_path
        # 如果路径无效，获取新的路径
        logger.info(f"模拟器管理器路径: {self.manager_path}")
        if not self.manager_path or not os.path.isfile(self.manager_path):
            logger.warning("模拟器管理器路径无效, 根据端口获取")
            emulator_manager_old = EmulatorManagerOld()
            emulator_instance = emulator_manager_old.get_emulator_instance_by_serial(self.serial)
            self.manager_path = emulator_instance.path
            # 赋值路径
            self.config.script.device.emulatorinfo_path = self.manager_path
            self.config.script.device.emulatorinfo_name = emulator_instance.name
        self.manager_path = self.manager_path.replace("MuMuNxMain.exe", "MuMuManager.exe")
        self.manager_path = self.manager_path.replace("MuMuPlayer.exe", "MuMuManager.exe")
        self.player_path = self.manager_path.replace("MuMuManager.exe","MuMuPlayer.exe")
        if not os.path.isfile(self.player_path):
            self.player_path = self.manager_path

        # 获取模拟器实例ID
        self.vmindex = self.get_vmindex_by_name(self.handle)
        # 获取模拟器启动的app
        self.package_name = self.get_package_name()

        # 获取模拟器启动启动后窗口操作
        self.emulator_window = config.script.device.emulator_window

    def get_emulator_info(self, vmindex):
        """
        获取模拟器信息
        """
        cmd = [self.manager_path, "info", "-v", str(vmindex)]
        return execute_emulator(cmd)

    def get_package_name(self):
        """
        获取正确的包名
        """
        package = self.config.script.device.package_name
        if package == PackageName.AUTO:
            package = "com.netease.onmyoji.wyzymnqsd_cps"  # 默认包名
        elif isinstance(package, PackageName):
            package = package.value
        return package

    def get_vmindex_by_name(self, handle):
        """
        根据模拟器名称获取索引
        """
        cmd = [self.manager_path, "info", "-v", "all"]
        result = execute_emulator(cmd)
        try:
            # 处理每个模拟器实例
            for index, emulator in result.items():
                # 跳过非模拟器信息的条目（如版本信息等）
                if not isinstance(emulator, dict):
                    continue
                name = emulator.get("name", f"模拟器{index}")
                if name.lower() == handle.lower():
                    # logger.info(f"模拟器名称: {name} 索引: {index}")
                    return str(index)  # 确保返回字符串类型
        except Exception as e:
            logger.error(f'根据模拟器名称获取索引时出错: {handle} 错误: {e}')

    def start_emulator(self):
        """
        启动模拟器
        MuMuPlayer.exe  可以隐藏窗口启动
        MuMuManager.exe 不能隐藏窗口启动
        """
        if self.emulator_window == EmulatorWindow.default:
            show_window = True
        else:
            show_window = False

        cmd = [self.player_path, "control", "-v", self.vmindex, "launch"]
        result = execute_show_window(cmd, show_window)
        if result:
            logger.info("模拟器开始启动")
        else:
            logger.error("模拟器启动失败")

    def stop_emulator(self):
        """
        关闭模拟器
        """
        if not self.is_emulator_running():
            logger.info("无需关闭模拟器")
        else:
            cmd = [self.manager_path, "control", "-v", self.vmindex, "shutdown"]
            result = execute_emulator(cmd)
            if result:
                logger.info("模拟器关闭成功")
                self.stop_ocr_server()
            else:
                logger.error(f"模拟器关闭失败 {result}")

    def stop_ocr_server(self):
        """
        所有模拟器关闭的情况下,关闭OCR服务
        """
        if State.deploy_config.UseOcrServer:
            cmd = [self.manager_path, "info", "-v", "all"]
            all_emulators_info = execute_emulator(cmd)

            for index, emulator_data in all_emulators_info.items():
                # 跳过非模拟器信息的条目
                if isinstance(emulator_data, dict):
                    is_process_started = emulator_data.get("is_process_started", False)
                    name = emulator_data.get("name", f"模拟器{index}")
                    # logger.info(f"模拟器 {name} 状态: {is_process_started}")
                    if is_process_started:
                        return
            logger.info("所有模拟器已关闭, 关闭OCR服务")
            port = State.deploy_config.OcrServerPort
            process_manager = ProcessManager()
            process_manager.stop_process_tree_by_port(port=port)

    def app_start(self):
        """
        启动app
        """
        mode = ["app", "launch"]
        cmd = [self.manager_path, "control", "-v", self.vmindex, *mode, "-pkg", self.package_name]
        result = execute_emulator(cmd)
        if result:
            logger.info(f"{self.package_name}启动成功")
        else:
            logger.error(f"{self.package_name}启动失败 {result}")

    def app_stop(self):
        """
        关闭游戏
        """
        cmd = [self.manager_path, "control", "-v", self.vmindex, "app", "close", "-pkg", self.package_name]
        result = execute_emulator(cmd)
        if result:
            logger.info("游戏关闭成功")
        else:
            logger.error("游戏关闭失败")

    def get_app_status(self):
        """
        获取游戏状态
        """
        cmd = [self.manager_path, "control", "-v", self.vmindex, "app", "info", "-pkg", self.package_name]
        result = execute_emulator(cmd)
        if result:
            game_state = result.get("state", None)
            return game_state
        else:
            logger.error(f"获取游戏状态失败 {result}")
            return None

    def is_app_running(self):
        """
        检查游戏是否已启动
        """
        # E:\MuMuPlayer-12.0\shell\MuMuManager.exe control -v all app  info -pkg com.netease.onmyoji.wyzymnqsd_cps
        # E:\MuMuPlayer-12.0\shell\MuMuManager.exe control -v 3   app  info -pkg com.netease.onmyoji.m4399

        # app_control = AppControl(self.config)
        # return app_control.app_is_running()

        state = self.get_app_status()
        is_running = state == "running"
        logger.info(f"游戏运行状态: {is_running}")
        return is_running

    def is_emulator_running(self):
        """
        检查模拟器是否已启动
        """
        res = self.get_emulator_info(self.vmindex)
        if res is None:
            return False
        player_state = res.get("player_state", False)
        is_start_finished = player_state == "start_finished"
        return is_start_finished
        # is_process_started = res.get("is_process_started", False)
        # logger.info(f"模拟器运行状态: {is_process_started}")
        # return bool(is_process_started)

    def hide_window(self):
        """
        隐藏模拟器窗口
        """
        cmd = [self.manager_path, "control", "-v", self.vmindex, "hide_window"]
        result = execute_emulator(cmd)
        if result:
            logger.info("模拟器窗口已隐藏")
        else:
            logger.error("模拟器窗口隐藏失败")

    def show_window(self):
        """
        显示模拟器窗口
        """
        cmd = [self.manager_path, "control", "-v", self.vmindex, "show_window"]
        result = execute_emulator(cmd)
        if result:
            logger.info("模拟器窗口已显示")
        else:
            logger.error("模拟器窗口显示失败")


if __name__ == "__main__":
    from module.config.config import Config

    config = Config('du')
    # 创建模拟器管理器实例
    manager = EmulatorManager(config)
    manager.get_vmindex_by_name('du')

    # # 检查模拟器状态
    # if manager.is_emulator_running():
    #     print("模拟器正在运行")
    #     manager.stop_ocr_server()
    #     # manager.get_emulator_info(1)
    #     # manager.hide_window()
    # else:
    #     print("模拟器未运行")
