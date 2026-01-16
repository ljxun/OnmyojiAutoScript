import aiohttp
import asyncio
import os
import yaml
from aiohttp import FormData
from aiohttp_socks import ProxyConnector
from module.logger import logger


class PushTg:
    def __init__(self, _config: str, enable: bool = False) -> None:
        self.config_name: str = ""
        self.enable: bool = enable

        if not self.enable:
            return
        config = {}
        try:
            for item in yaml.safe_load_all(_config):
                config.update(item)
        except Exception as e:
            logger.error("Fail to load onepush config, skip sending")
            return
        self.config = config
        try:
            self.proxy: str = self.config.pop("proxy", "")
            if self.proxy == "":
                logger.info("No proxy specified, skip sending")
                return
            self.token: str = self.config.pop("token", "")
            if self.token == "":
                logger.info("No token specified, skip sending")
                return
            self.chat_id: str = self.config.pop("chat_id", "")
            if self.chat_id == "":
                logger.info("No chat_id specified, skip sending")
                return
        except Exception as e:
            logger.error(e)
            return

    async def send_text_message(self,
                                token: str,
                                chat_id: str,
                                text: str,
                                proxy: str = None,
                                timeout: int = 10
                                ) -> bool:
        """发送纯文本消息"""
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": text}

        try:
            connector = None
            if proxy and proxy.startswith("socks"):
                connector = ProxyConnector.from_url(proxy)

            async with aiohttp.ClientSession(connector=connector) as session:
                kwargs = {"proxy": proxy} if proxy and not connector else {}

                async with session.post(
                        url,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=timeout),
                        **kwargs
                ) as response:
                    result = await response.json()
                    return result.get("ok", False)

        except Exception as e:
            logger.error(f"发送文本失败: {str(e)}")
            return False

    async def send_media(self,
                         token: str,
                         chat_id: str,
                         file_path: str,
                         file_type: str,
                         caption: str = "",
                         proxy: str = None,
                         timeout: int = 30
                         ) -> bool:
        """通用媒体文件发送函数"""
        api_methods = {
            "photo": "sendPhoto",
            "document": "sendDocument"
        }

        if file_type not in api_methods:
            raise ValueError(f"不支持的文件类型: {file_type}")

        url = f"https://api.telegram.org/bot{token}/{api_methods[file_type]}"

        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")

            data = FormData()
            data.add_field("chat_id", chat_id)
            data.add_field("caption", caption)
            data.add_field(
                file_type,
                open(file_path, "rb"),
                filename=os.path.basename(file_path)
            )

            connector = None
            if proxy and proxy.startswith("socks"):
                connector = ProxyConnector.from_url(proxy)

            async with aiohttp.ClientSession(connector=connector) as session:
                kwargs = {"proxy": proxy} if proxy and not connector else {}

                async with session.post(
                        url,
                        data=data,
                        timeout=aiohttp.ClientTimeout(total=timeout),
                        **kwargs
                ) as response:
                    result = await response.json()
                    return result.get("ok", False)

        except Exception as e:
            logger.error(f"发送媒体失败: {str(e)}")
            return False

    async def send_message(self,
                           token: str,
                           chat_id: str,
                           text: str = None,
                           image_path: str = None,
                           file_path: str = None,
                           proxy: str = None,
                           timeout: int = 30
                           ) -> bool:
        """
        支持三种消息模式：
        1. 纯文本
        2. 文本+图片
        3. 文本+图片+文件
        """
        success = True

        try:
            # 情况1：仅文本
            if text and not image_path and not file_path:
                return await self.send_text_message(token, chat_id, text, proxy, timeout)

            # 处理媒体发送
            media_to_send = []
            if image_path:
                media_to_send.append(("photo", image_path))
            if file_path:
                media_to_send.append(("document", file_path))

            # 使用文本作为第一个媒体的描述
            caption = text or ""

            # 依次发送媒体
            for idx, (file_type, path) in enumerate(media_to_send):
                current_caption = caption if idx == 0 else ""
                success &= await self.send_media(
                    token=token,
                    chat_id=chat_id,
                    file_path=path,
                    file_type=file_type,
                    caption=current_caption,
                    proxy=proxy,
                    timeout=timeout
                )

            return success

        except Exception as e:
            logger.error(f"消息发送失败: {str(e)}")
            return False

    async def telegram_send(self, caption, img_path=None, file_path=None):

        if not self.enable:
            return False
        PROXY = self.proxy
        TOKEN = self.token
        CHAT_ID = str(self.chat_id)
        kwargs = {
            'text': caption,
            'proxy': PROXY
        }
        try:
            if img_path is not None:
                kwargs['image_path'] = img_path
            if file_path is not None:
                kwargs['file_path'] = file_path

            await self.send_message(TOKEN, CHAT_ID, **kwargs)
        except Exception as e:
            # 异常捕获并记录详细错误日志
            logger.error(f"消息发送失败: {str(e)}", exc_info=True)
            # 可以在这里添加失败消息的重试逻辑或错误上报
        finally:
            logger.info("消息发送流程结束")


if __name__ == '__main__':
    from module.config.config import Config

    config = Config('du')
    # device = Device(config)
    # config.notifier.push(title='契灵之境', content='契灵数量已达上限500，请及时处理')

    # 测试不同传参方式
    # asyncio.run(main("纯文本"))  # 仅caption
    # asyncio.run(main("带图片", img_path="/path/to/img.png"))  # caption+img
    # asyncio.run(main("带文件", file_path="/data/file.zip"))  # caption+file
    asyncio.run(config.pushtg.telegram_send
                ("全部参数", r"D:\OnmyojiAutoScript\ljxun\log\error\MI 12-36-43 (2025-03-09).png",
                 r"D:\OnmyojiAutoScript\ljxun\log\error\MI 12-36-43 (2025-03-09).log"))
    # asyncio.run(push.main("全部参数", r"D:\OnmyojiAutoScript\ljxun\log\error\MI 12-36-43 (2025-03-09).png",
    #                       r"D:\OnmyojiAutoScript\ljxun\log\error\MI 12-36-43 (2025-03-09).log"))  # 全参数
