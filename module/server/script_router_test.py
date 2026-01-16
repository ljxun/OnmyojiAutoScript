import sys

import json
import requests
import threading
import urllib.parse
import websocket
from datetime import datetime
from module.logger import logger
from module.server.i18n import I18n


def send_put_request():
    """
    发送PUT请求到指定URL
    """

    script_name = "du"
    ip = "http://127.0.0.1:22288"
    # ip = "http://1a84o56629.zicp.fun"
    taskk = "Orochi"

    # 获取当前时间
    current_time = datetime.now()
    # 格式化时间为指定格式
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

    print(formatted_time)

    # 请求URL - 根据服务器端API规范构造URL
    # 服务器端API: /{script_name}/{task}/{group}/{argument}/value
    url = f"{ip}/{script_name}/{taskk}/scheduler/next_run/value"
    
    # 请求参数作为查询参数
    params = {
        'types': 'date_time',
        'value': formatted_time
    }

    # 请求头
    headers = {
        'Accept': 'application/json'
    }

    try:
        # 发送PUT请求，将参数作为查询参数传递
        response = requests.put(url, params=params, headers=headers)

        # 输出请求信息
        print(f"请求URL: {url}")
        print(f"请求方法: PUT")
        print(f"请求参数: {params}")
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        print(f"响应头: {response.headers}")

        # 检查请求是否成功
        if response.status_code == 200:
            print("请求成功!")
        else:
            print(f"请求失败，状态码: {response.status_code}")
            if response.status_code == 404:
                print("请检查URL路径是否正确")
            elif response.status_code == 500:
                print("服务器内部错误，请检查服务器日志")

    except requests.exceptions.RequestException as e:
        print(f"请求发生错误: {e}")

def fetch_today_data():
    """
    请求 https://fetchbuild.luckyancj.site/today 并接收返回消息
    """
    url = "https://fetchbuild.luckyancj.site/today"

    try:
        # 发送GET请求
        response = requests.get(url)

        # 输出请求信息
        print(f"请求URL: {url}")
        print(f"请求方法: GET")
        print(f"状态码: {response.status_code}")

        # 检查请求是否成功
        if response.status_code == 200:
            print("请求成功!")
            print(f"响应内容: {response.text}")

            # 如果返回的是JSON格式数据
            try:
                json_data = response.json()
                print(f"JSON响应: {json_data}")
            except ValueError:
                print("响应不是有效的JSON格式")

        else:
            print(f"请求失败，状态码: {response.status_code}")
            print(f"响应内容: {response.text}")

    except requests.exceptions.RequestException as e:
        print(f"请求发生错误: {e}")

    def send_team_task(self, task):
        """
        发送PUT请求到指定URL
        """
        script_name = self.config.script.team.member_script_name
        ip = self.config.script.team.member_ip

        # 请求URL - 注意路径末尾是 "/value"
        url = f"{ip}/{script_name}/{task}/scheduler/next_run/value"

        # 格式化时间为指定格式
        formatted_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 请求参数 (URL查询参数)
        params = {
            'types': 'date_time',
            'value': formatted_time
        }
        # 请求头
        headers = {
            'Accept': 'application/json'
        }

        try:
            # 发送PUT请求
            response = requests.put(url, params=params, headers=headers)

            # 输出请求信息
            logger.info(f"请求URL: {url}")
            logger.info(f"请求方法: PUT")
            logger.info(f"请求参数: {params}")
            logger.info(f"状态码: {response.status_code}")
            logger.info(f"响应内容: {response.text}")

            # 检查请求是否成功
            if response.status_code == 200:
                logger.info(f"✅ 协同任务请求成功")
            else:
                self.config.notifier.push(title=I18n.trans_zh_cn(task), content=f"❌ 协同任务请求失败")
                logger.warning(f"请求失败，状态码: {response.status_code}")
                if response.status_code == 404:
                    logger.warning("请检查URL路径是否正确")

        except requests.exceptions.RequestException as e:
            logger.error(f"请求发生错误: {e}")

    def start_websocket(self, config_name, command):
        logger.info(f"尝试连接到[{config_name}] WebSocket")
        config_name = urllib.parse.quote(config_name)
        ws = websocket.WebSocketApp(f"ws://127.0.0.1:22288/ws/{config_name}")

        # 处理 WebSocket 连接打开事件
        def on_open(ws):
            logger.info(f"[{config_name}] WebSocket连接成功!")
            ws.send(command)
            logger.info(f"已发送: {command}")

        # 处理接收到的消息
        def on_message(ws, response):
            print(f"收到响应: {response}")
            if 'state' in response:
                data = json.loads(response)
                state = data['state']
                if state == 1:
                    logger.info(f"[{config_name}] 当前运行中")
                elif state == 0:
                    logger.info(f"[{config_name}] 当前已停止")
            elif 'schedule' in response:
                data = json.loads(response)
                schedule = data['schedule']
                if 'running' in schedule and schedule['running']:
                    running_task = schedule['running']
                    logger.info(f"[{config_name}] 当前运行任务: {running_task['name']}")
                    self.team_running = True
                else:
                    logger.info(f"[{config_name}] 当前无运行任务")
                    self.team_running = False

        # 设置 WebSocket 回调函数
        ws.on_open = on_open
        ws.on_message = on_message

        # 设置超时退出
        def exit_timer():
            logger.info("超时关闭连接...")
            ws.close()
            sys.exit(0)

        timer = threading.Timer(5, exit_timer)  # 30秒后自动关闭
        timer.start()

        ws.run_forever()
        timer.cancel()  # 如果连接正常关闭，取消定时器


if __name__ == "__main__":
    # print("=== 发送PUT请求 ===")
    # send_put_request()
    print("=== 请求今日数据 ===")
    fetch_today_data()