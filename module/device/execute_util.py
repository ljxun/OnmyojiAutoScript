# -*- coding: utf-8 -*-

import json
import os
import subprocess


def execute_emulator(command):
    """
    执行模拟器命令
    """
    # command_str = ' '.join(command)
    # logger.info(f'执行命令: {command_str}')
    # 隐藏CMD窗口执行命令
    startupinfo = None
    if os.name == 'nt':  # Windows系统
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=10,
        startupinfo=startupinfo,
        encoding='utf-8'  # 明确指定编码
    )
    emulators_info = json.loads(result.stdout)
    return emulators_info


def execute_show_window(command, show_window=True):
    """
    执行命令并控制窗口显示
    """
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    if not show_window:
        startupinfo.wShowWindow = 0  # SW_MINIMIZE - 不显示窗口
    else:
        startupinfo.wShowWindow = 1  # SW_SHOWNORMAL - 正常显示
    # 添加CREATE_NO_WINDOW标志以防止创建新窗口
    creationflags = subprocess.CREATE_NO_WINDOW

    # logger.info(f'Execute: {command}')
    return subprocess.Popen(
        command,
        # close_fds=True, 会造成在python进程中出现木木模拟器
        startupinfo=startupinfo,
        creationflags=creationflags,
        # 重定向标准输出和标准错误以防止弹窗
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
