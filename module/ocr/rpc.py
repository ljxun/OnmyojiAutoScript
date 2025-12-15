from module.device.ocr_manager import start_ocr_server_bat
from module.logger import logger
from module.server.setting import State


class ModelProxy:
    client = None
    online = True

    @classmethod
    def init(cls, address=State.deploy_config.OcrClientAddress, retry_count=0):
        import zerorpc

        # 限制重连次数最多3次
        if retry_count >= 3:
            logger.error("OCR server connection failed after 3 retries")
            cls.online = False
            return

        logger.info(f"Connecting to OCR server {address}")
        cls.client = zerorpc.Client(timeout=5)
        cls.client.connect(f"tcp://{address}")
        try:
            cls.client.hello()
            logger.info("Connected to OCR server True")
            cls.online = True  # 确保设置为True
        except Exception as e:
            cls.online = False
            logger.warning(f"Ocr server not running False {e}")
            start_ocr_server_bat()
            logger.info("Restarting new OCR server instance")
            # 递归调用并增加重试次数
            cls.init(address=address, retry_count=retry_count + 1)

    @classmethod
    def close(cls):
        if cls.client is not None:
            cls.client.close()
            logger.info('Disconnect to OCR server')
            cls.client = None
        else:
            logger.warning('Ocr server not connected False')

    def __init__(self, lang) -> None:
        self.lang = lang

    def ocr(self, img_fp):
        """
        Args:
            img_fp (np.ndarray):
        Returns:
        """
        if ModelProxy.online:
            img_str = img_fp.dumps()
            try:
                return self.client("ocr", img_str)
            except Exception as e:
                self._handle_ocr_disconnect(str(e))  # 使用公共方法
        from module.ocr.models import OCR_MODEL
        return OCR_MODEL.__getattribute__(self.lang).ocr(img_fp)

    def detect_and_ocr(self, img_fp, drop_score=None):
        if ModelProxy.online:
            img_str = img_fp.dumps()
            try:
                result_dicts = self.client("detect_and_ocr", img_str, drop_score)
                # Convert dictionaries back to BoxedResult objects
                if result_dicts:
                    from module.ocr.onnx_paddle_ocr import BoxedResult
                    return [BoxedResult.from_dict(result_dict) for result_dict in result_dicts]
                return []
            except Exception as e:
                self._handle_ocr_disconnect(str(e))  # 使用公共方法
        from module.ocr.models import OCR_MODEL
        return OCR_MODEL.__getattribute__(self.lang).detect_and_ocr(img_fp, drop_score)

    def ocr_lines(self, img_fp):
        if ModelProxy.online:
            img_str = img_fp.dumps()
            try:
                return self.client("ocr_lines", img_str)
            except Exception as e:
                self._handle_ocr_disconnect(str(e))  # 使用公共方法
        from module.ocr.models import OCR_MODEL
        return OCR_MODEL.__getattribute__(self.lang).ocr_lines(img_fp)

    def ocr_single_line(self, img_fp):
        if ModelProxy.online:
            img_str = img_fp.dumps()
            try:
                return self.client("ocr_single_line", img_str)
            except Exception as e:
                self._handle_ocr_disconnect(str(e))  # 使用公共方法
        from module.ocr.models import OCR_MODEL
        return OCR_MODEL.__getattribute__(self.lang).ocr_single_line(img_fp)

    def _handle_ocr_disconnect(self, error_msg: str = ""):
        """处理OCR服务断开连接的公共方法"""
        if error_msg:
            logger.warning(f"Ocr server disconnected: {error_msg}")
        else:
            logger.warning("Ocr server disconnected")
        ModelProxy.online = False
        start_ocr_server_bat()


class ModelProxyFactory:
    def __getattribute__(self, __name: str) -> ModelProxy:
        if __name in ["ch"]:
            # 处理属性访问 OCR_MODEL.ch
            if ModelProxy.client is None:
                ModelProxy.init(address=State.deploy_config.OcrClientAddress)
            return ModelProxy(lang=__name)
        elif __name == "_get_model":
            # 处理方法调用 OCR_MODEL._get_model('ch')
            def _get_model_func(lang):
                if ModelProxy.client is None:
                    ModelProxy.init(address=State.deploy_config.OcrClientAddress)
                return ModelProxy(lang=lang)
            return _get_model_func
        else:
            return super().__getattribute__(__name)

    def close(self):
        ModelProxy.close()

# def start_ocr_server(port=22268):
#     import zerorpc
#     import zmq
#     from module.ocr.models import OcrModel
#
#     class OCRServer(OcrModel):
#         def hello(self):
#             return "hello"
#
#         def ocr(self, img_fp):
#             img_fp = pickle.loads(img_fp)
#             cnocr = self.__getattribute__('ch')
#             return cnocr.ocr(img_fp)
#
#         def detect_and_ocr(self, img_fp, drop_score=None):
#             img_fp = pickle.loads(img_fp)
#             cnocr = self.__getattribute__('ch')
#             results = cnocr.detect_and_ocr(img_fp, drop_score)
#             # Convert BoxedResult objects to serializable dictionaries
#             if results:
#                 return [result.to_dict() for result in results]
#             return []
#
#         def ocr_lines(self, img_fp):
#             img_fp = pickle.loads(img_fp)
#             cnocr = self.__getattribute__('ch')
#             return cnocr.ocr_lines(img_fp)
#
#         def ocr_single_line(self, img_fp):
#             img_fp = pickle.loads(img_fp)
#             cnocr = self.__getattribute__('ch')
#             return cnocr.ocr_single_line(img_fp)
#
#     server = zerorpc.Server(OCRServer())
#     try:
#         server.bind(f"tcp://*:{port}")
#     except zmq.error.ZMQError:
#         logger.error(f"Ocr server cannot bind on port {port}")
#         return
#     logger.info(f"[OcrServer] Listening on port {port}")
#     server.run()
#
#
# def alive() -> bool:
#     global process
#     if process is not None:
#         return process.is_alive()
#     else:
#         return False
#
#
# # 脱离主进程运行
# def start_ocr_server_process(port=22268):
#     global process
#     if alive():
#         logger.warning("Ocr server process already running")
#         return
#     process = multiprocessing.Process(target=start_ocr_server, args=(port,))
#     process.start()
#     logger.info(f"Ocr server process started on port {port}")
#
#
# def stop_ocr_server_process():
#     """停止OCR server进程"""
#     global process
#     if process is not None and process.is_alive():
#         logger.info("[OcrServer] Stopping OCR server process...")
#         process.terminate()
#         process.join(timeout=5)  # 等待最多5秒
#         if process.is_alive():
#             logger.warning("[OcrServer] OCR server process didn't terminate gracefully, forcing kill")
#             process.kill()
#             process.join()
#         logger.info("[OcrServer] OCR server process stopped")
#         process = None
#     else:
#         logger.info("[OcrServer] OCR server process is not running")
#
#
# if __name__ == "__main__":
#     # Run server
#     parser = argparse.ArgumentParser(description="OAS OCR service")
#     parser.add_argument(
#         "--port",
#         type=int,
#         help="Port to listen. Default to OcrServerPort in deploy setting",
#     )
#     args, _ = parser.parse_known_args()
#     port = args.port or State.deploy_config.OcrServerPort
#     start_ocr_server(port=22268)
