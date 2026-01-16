# 连接mumu模拟器adb
import cv2
import numpy as np
import os
import subprocess


def get_adb_path():
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 构建adb路径
    adb_path = os.path.join(current_dir, '', 'platform-tools', 'adb.exe')
    return adb_path

_adb_target = None  # 全局变量，存储当前目标设备ip:port

def set_adb_target(ip_port):
    """设置当前adb目标设备(ip:port)"""
    global _adb_target
    _adb_target = ip_port

def get_adb_target():
    """获取当前adb目标设备(ip:port)，未设置则为None"""
    return _adb_target

def _adb_args():
    """返回带目标设备参数的adb命令参数列表"""
    adb_path = get_adb_path()
    if _adb_target:
        return [adb_path, '-s', _adb_target]
    else:
        return [adb_path]


def check_adb_device():
    """检测是否有设备连接到adb（如设置了目标设备则只检测该设备）"""
    args = _adb_args() + ['devices']
    result = subprocess.run(args, capture_output=True, text=True)
    lines = result.stdout.strip().split('\n')
    devices = [line for line in lines[1:] if line.strip() and 'device' in line]
    if _adb_target:
        # 只检测指定设备
        return any(_adb_target in line for line in devices)
    return len(devices) > 0


def adb_screenshot():
    """通过adb获取设备截图并直接返回OpenCV格式的图像（不保存本地文件）"""

    args = _adb_args() + ['shell', 'screencap', '-p']
    result = subprocess.run(args, capture_output=True)
    img_bytes = result.stdout.replace(b'\r\n', b'\n')  # 兼容windows换行

    img = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
    return img


def adb_tap(x, y):
    """通过adb在设备上点击指定坐标"""
    args = _adb_args()
    subprocess.run(args + ['shell', 'input', 'tap', str(x), str(y)], check=True)

def adb_double_tap(x, y):
    # 模拟人手双击,随机等待时间
    import time
    wait_time = np.random.uniform(0.1, 0.3)  #
    adb_tap(x, y)
    time.sleep(wait_time)
    adb_tap(x, y)

# adb重连
def adb_reconnect():
    """重新连接adb设备"""
    # 关闭adb服务器
    args = _adb_args() + ['kill-server']
    subprocess.run(args, check=True)
    # 启动adb服务器
    args = _adb_args() + ['start-server']
    subprocess.run(args, check=True)
    # 如果设置了目标设备，则尝试连接
    if _adb_target:
        args = _adb_args() + ['connect', _adb_target]
        subprocess.run(args, check=True)