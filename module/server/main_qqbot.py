import aiohttp
import os
import requests
import yaml
from datetime import datetime
from module.logger import logger
from module.notify.notify import Notifier


class MainQQBotManager():
    # def __init__(self):
    #     # 使用全局日志记录器 'oas'
    #     self.logger = logging.getLogger('oas')  # 使用全局日志记录器
    #     self.logger.setLevel(logging.INFO)  # 设置日志级别
    #
    #     # 如果需要独立日志文件，可以保留以下代码
    #     log_dir = "log"  # 日志文件夹
    #     os.makedirs(log_dir, exist_ok=True)
    #     log_file = os.path.join(log_dir, "main_qqbot.log")  # 定义日志文件路径
    #
    #     file_handler = TimedRotatingFileHandler(
    #         log_file,
    #         when="midnight",
    #         interval=1,
    #         backupCount=7,
    #         encoding="utf-8"
    #     )
    #     file_handler.setLevel(logging.INFO)
    #     file_handler.setFormatter(file_formatter)
    #
    #     # 将独立日志处理器添加到日志记录器
    #     self.logger.addHandler(file_handler)

    async def received(self, data):
        try:
            print(f"Received data:{data}")  # 打印接收到的数据

            # QQ群号码
            group_id = data.get("group_id")
            group_name = data.get("group_name")
            # QQ号
            user_id = data.get("sender").get("user_id")
            nickname = data.get("sender").get("nickname")
            # 消息内容
            raw_message = data.get("raw_message")

            # 判断是否满足条件
            condition_met = False
            if str(group_id) == "1045504603" and str(user_id) == "2210814203":
                condition_met = True
            elif str(group_id) == "1059103834" and str(user_id) == "596090280":
                condition_met = True
            if not condition_met:
                print("条件未满足，退出处理")
                return
            logger.info(f"接收到重要数据: {group_name}-{nickname}-{raw_message}")  # 打印接收到的数据
            if "qq=all" not in raw_message:
                return

            send_info = ("下面是一段关于一个游戏中道馆是否建立的消息通知，我需要你分析下面的通知消息判断是否建立，结果只要True或者False,其余内容不要返回."
                         "---以下为信息内容---"
                         f"{raw_message}"
                         "---信息内容结束---")
            # 获取配置参数
            config = load_qqbot_config()

            # 调用硅基流动 API
            api_key = config["api"]["api_key"]
            model_name = config["api"]["model_name"]
            result = call_silicon_flow_api(api_key, model_name, send_info).strip()
            logger.info(f"返回结果:{result}")

            # 验证返回结果
            if result.lower() == "true":
                logger.info("福利道馆已经创建")
                # 提取 notifier 配置
                notifier_config = config["notifier"]
                yaml_notifier = yaml.dump(notifier_config, allow_unicode=True, sort_keys=False)

                try:
                    # 调用 Notifier.push 方法
                    notifier = Notifier(yaml_notifier, "", True, False)
                    success = notifier.push(title="QQBot", content="福利道馆已经创建")
                    if not success:
                        logger.warning("通知推送失败，请检查 Notifier 配置")
                except Exception as e:
                    # 捕获异常并记录日志
                    logger.error(f"通知推送过程中出现异常: {e}")

                # 异步调用 send_team_task
                await send_team_task("DU", "Dokan")
                await send_team_task("MI", "Dokan")

            elif result.lower() == "false":
                logger.warning("福利道馆未创建")
            else:
                logger.error(f"API 返回无效结果:{result}")

        except KeyError as ke:
            logger.error(f"数据解析错误，缺少字段: {ke}")
        except AttributeError as ae:
            logger.error(f"数据访问错误，可能是嵌套字段不存在: {ae}")
        except requests.RequestException as re:
            logger.error(f"网络请求失败: {re}")
        except Exception as e:
            logger.error(f"未知错误: {e}")


def send_test(test):
    """
    发送PUT请求到指定URL
    """
    ip = "http://127.0.0.1:22288"

    # 请求URL - 注意路径末尾是 "/value"
    url = f"{ip}/{test}/"

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
        response = requests.get(url, params=params, headers=headers)

        # 输出请求信息
        logger.info(f"请求URL: {url}")
        logger.info(f"请求方法: PUT")
        logger.info(f"请求参数: {params}")
        logger.info(f"状态码: {response.status_code}")
        logger.info(f"响应内容: {response.text}")

        # 检查请求是否成功
        if response.status_code == 200:
            logger.info(f"✅ 成功")
        else:
            logger.warning(f"请求失败，状态码: {response.status_code}")
            if response.status_code == 404:
                logger.warning("请检查URL路径是否正确")

    except requests.exceptions.RequestException as e:
        logger.error(f"请求发生错误: {e}")


async def send_team_task(script_name, task):
    """
    发送PUT请求到指定URL
    """
    ip = "http://127.0.0.1:22288"

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
        # 使用 aiohttp 发送异步 PUT 请求
        async with aiohttp.ClientSession() as session:
            async with session.put(url, params=params, headers=headers) as response:
                # 输出请求信息
                logger.info(f"请求URL: {url}")
                logger.info(f"请求方法: PUT")
                logger.info(f"请求参数: {params}")
                logger.info(f"状态码: {response.status}")
                logger.info(f"响应内容: {await response.text()}")

                # 检查请求是否成功
                if response.status == 200:
                    logger.info(f"✅ {task} 任务请求成功")
                else:
                    logger.warning(f"请求失败，状态码: {response.status}")
                    if response.status == 404:
                        logger.warning("请检查 URL 路径是否正确")

    except Exception as e:
        logger.error(f"请求发生错误: {e}")


def call_silicon_flow_api(api_key, model, prompt):
    """
    调用硅基流动API的一个例子
    :param api_key: 用户的API密钥
    :param model: 使用的模型名称
    :param prompt: 输入给API的提示信息
    :return: API返回的文本内容
    """
    url = "https://api.siliconflow.cn/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    try:
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            logger.info(f"响应内容: {response.text}")
            result = response.json()
            return result.get('choices', [{}])[0].get('message', {}).get('content', '')
        else:
            logger.warning(f"请求失败，状态码: {response.status_code}")
            logger.warning(f"响应内容: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"请求发生错误: {e}")
        return None


def load_qqbot_config(config_dir: str = "config", config_file: str = "qqbot.yaml"):
    """
    读取 config 目录下的 qqbot.yaml 文件，并获取 notifier 和 api 下的参数。

    :param config_dir: 配置文件所在目录，默认为 "config"
    :param config_file: 配置文件名，默认为 "qqbot.yaml"
    :return: 包含 notifier 和 api 参数的字典
    """
    # 构造配置文件路径
    config_path = os.path.join(config_dir, config_file)

    try:
        # 读取 YAML 文件内容
        with open(config_path, "r", encoding="utf-8") as file:
            config_data = yaml.safe_load(file)

        # 提取 notifier 和 api 参数
        notifier_config = config_data.get("notifier", {})
        api_config = config_data.get("api", {})

        return {
            "notifier": notifier_config,
            "api": api_config
        }
    except FileNotFoundError:
        print(f"配置文件未找到: {config_path}")
        return None
    except yaml.YAMLError as e:
        print(f"解析 YAML 文件时出错: {e}")
        return None
def assemble_notifier_yaml(config: dict):
    """
    将 Notifier 配置字典转换为 YAML 格式字符串。

    :param config: 包含 notifier 参数的字典
    :return: YAML 格式的字符串
    """
    # 提取 notifier 配置
    notifier_config = config.get("notifier", {})

    # 转换为 YAML 格式字符串
    yaml_string = yaml.dump(notifier_config, allow_unicode=True, sort_keys=False)
    return yaml_string


# 示例：使用 assemble_notifier_yaml 方法
if __name__ == "__main__":
    # 假设这是从 qqbot.yaml 文件中加载的配置
    config = {
        "notifier": {
            "provider": "smtp",
            "host": "smtp.qq.com",
            "user": "591692130@qq.com",
            "password": "pjanclaiezuzbfia",
            "port": 465
        },
        "api": {
            "api_key": "ipttyngedrjmmmxfnevmieiopmeslbfcgbahckasaseessyc",
            "model_name": "Qwen/QwQ-32B"
        }
    }

    # 组装 Notifier 配置为 YAML 格式
    notifier_yaml = assemble_notifier_yaml(config)

    # 打印结果
    # 打印结果
    print("Notifier YAML 格式:")
    print(notifier_yaml)

if __name__ == "__main__":
    # 假设当前工作目录是项目根目录
    config = load_qqbot_config()

    if config:
        print("API 配置:", config["api"])
        print("notifier", config.get("notifier", {}))
        print("notifier", config["notifier"])
