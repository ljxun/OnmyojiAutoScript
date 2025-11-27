# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey

from time import sleep

import random
from datetime import datetime, timedelta
from module.atom.animate import RuleAnimate
from module.atom.click import RuleClick
from module.atom.gif import RuleGif
from module.atom.image import RuleImage
from module.atom.list import RuleList
from module.atom.long_click import RuleLongClick
from module.atom.ocr import RuleOcr
from module.atom.swipe import RuleSwipe
from module.base.timer import Timer
from module.config.config import Config
from module.config.utils import convert_to_underscore
from module.device.device import Device
from module.device.device_manager import DeviceManager
from module.device.emulator_manager import EmulatorManager
from module.exception import ScriptError
from module.logger import logger
from module.ocr.base_ocr import OcrMode
from tasks.Component.Costume.costume_base import CostumeBase
from tasks.Component.config_base import Time
from tasks.Component.config_switch_week import Week
from tasks.GlobalGame.assets import GlobalGameAssets
from tasks.GlobalGame.config_emergency import FriendInvitation
from typing import Union


class BaseTaskParent(GlobalGameAssets, CostumeBase):
    config: Config = None
    _device: Device = None

    limit_time: timedelta = None  # 限制运行的时间，是软时间，不是硬时间
    limit_count: int = None  # 限制运行的次数
    current_count: int = None  # 当前运行的次数

    def __init__(self, config: Config) -> None:
        """
        :rtype: object
        """
        self.config = config
        self._device = None

        self.interval_timer = {}  # 这个是用来记录每个匹配的运行间隔的，用于控制运行频率
        self.start_time = datetime.now()  # 启动的时间
        self.check_costume(self.config.global_game.costume_config)
        # 战斗次数相关
        self.current_count = 0  # 战斗次数

    @property
    def device(self) -> Device:
        # 使用全局设备管理器获取共享设备实例
        return DeviceManager.get_device(config=self.config)

    @property
    def emulator(self) -> "EmulatorManager":
        return EmulatorManager(config=self.config)

    @property
    def device_status(self) -> bool:
        # 使用全局设备管理器获取设备状态
        return DeviceManager.get_device_status()

    def _burst(self) -> bool:
        """
        游戏界面突发异常检测
        :return: 没有出现返回False, 其他True
        """
        appear_invitation = self.appear(self.I_G_ACCEPT)
        if not appear_invitation:
            return False
        logger.info('检测到悬赏邀请')
        invite_type = self.config.global_game.emergency.friend_invitation
        detect_record = self.device.detect_record
        match invite_type:
            case FriendInvitation.ACCEPT:
                # logger.info(f"接受全部邀请")
                click_button = self.I_G_ACCEPT
            case FriendInvitation.REJECT:
                # logger.info(f"拒绝全部邀请")
                click_button = self.I_G_REJECT
            case FriendInvitation.IGNORE:
                # logger.info(f"忽略全部邀请")
                click_button = self.I_G_IGNORE
            case FriendInvitation.ONLY_JADE:
                # logger.info(f"仅接受勾玉邀请")
                if self.appear(self.I_G_JADE):
                    click_button = self.I_G_ACCEPT
                else:
                    click_button = self.I_G_IGNORE
            case FriendInvitation.JADE_SUSHI_FOOD:
                # logger.info(f"接受勾协/体协/粮协邀请")
                if self.appear(self.I_G_JADE) or self.appear(self.I_G_CAT_FOOD) or self.appear(self.I_G_DOG_FOOD) or self.appear(self.I_G_SUSHI):
                    click_button = self.I_G_ACCEPT
                else:
                    click_button = self.I_G_IGNORE
            case _:
                raise ScriptError(f'未知的好友邀请类型: {invite_type}')
        if not click_button:
            raise ScriptError(f'未知的点击按钮类型: {invite_type}')
        while 1:
            self.device.screenshot()
            if not self.appear(target=click_button):
                # logger.info('悬赏邀请处理完成')
                break
            if self.appear_then_click(click_button, interval=0.8):
                continue
        # 长战斗场景处理（点击后可能取消战斗状态）
        self.device.detect_record = detect_record
        # 接受邀请后立即执行悬赏任务
        if click_button == self.I_G_ACCEPT:
            logger.warning('已接受悬赏邀请')
            self.set_next_run(task='WantedQuests', target=datetime.now().replace(microsecond=0))
            if 17 == datetime.now().hour:
                self.push_notify("已接到悬赏邀请,记得去做呢", "接到悬赏")
        else:
            logger.warning(f"已忽略悬赏邀请")
        return True

    def screenshot(self):
        """
        截图 引入中间函数的目的是 为了解决如协作的这类突发的事件
        :return:
        """
        self.device.screenshot()
        # 判断勾协
        self._burst()

        return self.device.image

    def maybe_screenshot(self, soft_skip: bool = False):
        """
        可能截图
        :param soft_skip: True跳过截图(但保证设备一定有图才跳过,否则依然截图)
        :return:
        """
        if not soft_skip or not self.exist_image():
            return self.screenshot()
        return self.device.image

    def exist_image(self) -> bool:
        """
        判断当前设备是否有图片
        :return: 有返回True，没有返回False
        """
        return hasattr(self.device, 'image') and self.device.image is not None

    def appear(self,
               target: RuleImage,
               interval: float = None,
               threshold: float = None):
        """

        :param target: 匹配的目标可以是RuleImage, 也可以是RuleOcr
        :param interval:
        :param threshold:
        :return:
        """
        if not isinstance(target, RuleImage):
            return False

        if interval:
            if target.name in self.interval_timer:
                if self.interval_timer[target.name].limit != interval:
                    self.interval_timer[target.name] = Timer(interval)
            else:
                self.interval_timer[target.name] = Timer(interval)
            if not self.interval_timer[target.name].reached():
                return False

        appear = target.match(self.device.image, threshold=threshold)

        if appear and interval:
            self.interval_timer[target.name].reset()

        return appear

    def appear_then_click(self,
                          target: RuleImage | RuleGif,
                          action: Union[RuleClick, RuleLongClick] = None,
                          interval: float = None,
                          threshold: float = None,
                          duration: float = None):
        """
        出现了就点击，默认点击图片的位置，如果添加了click参数，就点击click的位置
        :param duration: 如果是长按，可以手动指定duration，不指定默认.单位是ms！！！！
        :param action: 可以是RuleClick, 也可以是RuleLongClick
        :param target: 可以是RuleImage后续支持RuleOcr
        :param interval:
        :param threshold:
        :return: True or False
        """
        if not isinstance(target, RuleImage):
            return False

        appear = self.appear(target, interval=interval, threshold=threshold)
        if appear and not action:
            x, y = target.coord()
            self.device.click(x, y, control_name=target.name)

        elif appear and action:
            x, y = action.coord()
            if isinstance(action, RuleLongClick):
                if duration is None:
                    self.device.long_click(x, y, duration=action.duration / 1000, control_name=target.name)
                else:
                    self.device.long_click(x, y, duration=duration / 1000, control_name=target.name)
            elif isinstance(action, RuleClick):
                self.device.click(x, y, control_name=target.name)

        return appear

    def wait_until_appear(self,
                          target: RuleImage,
                          skip_first_screenshot=False,
                          wait_time: int = None) -> bool:
        """
        等待直到出现目标
        :param wait_time: 等待时间，单位秒
        :param target:
        :param skip_first_screenshot:
        :return:
        """
        wait_timer = None
        if wait_time:
            wait_timer = Timer(wait_time)
            wait_timer.start()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.screenshot()
            if wait_timer and wait_timer.reached():
                logger.warning(f"Wait until appear {target.name} timeout")
                return False
            if self.appear(target):
                return True

    def wait_until_appear_then_click(self,
                                     target: RuleImage,
                                     wait_time: int = None) -> bool:
        """
        等待直到出现目标，然后点击
        :param target:
        :param wait_time:
        :return:
        """
        if self.wait_until_appear(target, wait_time=wait_time):
            x, y = target.coord()
            self.device.click(x=x, y=y, control_name=target.name)
            return True
        else:
            return False

    def wait_until_disappear(self, target: RuleImage) -> None:
        while 1:
            self.screenshot()
            if not self.appear(target):
                break

    def wait_until_stable(self,
                          target: RuleImage,
                          timer=Timer(0.3, count=1),
                          timeout=Timer(5, count=10),
                          skip_first_screenshot=True):
        """
        等待目标稳定，即连续多次匹配成功
        :param target:
        :param timer:
        :param timeout:
        :param skip_first_screenshot:
        :return:
        """
        target._match_init = False
        timeout.reset()
        while 1:
            if skip_first_screenshot:
                skip_first_screenshot = False
            else:
                self.screenshot()

            if target._match_init:
                if target.match(self.device.image):
                    if timer.reached():
                        break
                else:
                    # button.load_color(self.device.image)
                    timer.reset()
            else:
                # target.load_color(self.device.image)
                target._match_init = True

            if timeout.reached():
                logger.warning(f'Wait_until_stable({target}) timeout')
                break

    def wait_animate_stable(self, rule: RuleAnimate, interval: float = None, timeout: float = None):
        """
        不同与上面的wait_until_stable，这个将会匹配连续的两帧图片的特定区域
        @param rule:
        @param interval:
        @param timeout:
        @return:
        """
        if not isinstance(rule, RuleAnimate):
            rule = RuleAnimate(rule)
        timeout_timer = Timer(timeout).start() if timeout is not None else None
        while 1:
            self.screenshot()

            if interval:
                if rule.name in self.interval_timer:
                    if self.interval_timer[rule.name].limit != interval:
                        self.interval_timer[rule.name] = Timer(interval)
                else:
                    self.interval_timer[rule.name] = Timer(interval)
                if not self.interval_timer[rule.name].reached():
                    return False

            stable = rule.stable(self.device.image)
            if stable:
                if interval:
                    self.interval_timer[rule.name].reset()
                break

            if timeout_timer and timeout_timer.reached():
                logger.info(f'Wait_animate_stable({rule}) timeout')
                break

    def wait_until_pos_stable(self, target: RuleImage, stable_time: float = 0.3, timeout: float = 2,
                              threshold: float = None, skip_first_screenshot: bool = True) -> bool:
        """
        等待直到在同一位置稳定出现
        :param skip_first_screenshot:
        :param threshold: target匹配阈值
        :param target: 目标图像
        :param stable_time: 判断是否稳定的时间
        :param timeout: 等待稳定的超时时间
        :return: timer时间内稳定出现则返回True, 否则False
        """
        logger.info(f'Wait until {target.name} position stable')
        timeout_timer = Timer(timeout).start()
        stable_timer = Timer(stable_time).start()
        pre_roi_front, cur_roi_front = None, None
        origin_roi_back = target.roi_back
        while not timeout_timer.reached():
            self.maybe_screenshot(skip_first_screenshot)
            skip_first_screenshot = False
            # 当前页面能够匹配到target
            if target.match(self.device.image, threshold=threshold):
                cur_roi_front = target.roi_front
                logger.info(f'Current:{cur_roi_front}, pre:{pre_roi_front}')
                target.roi_back = pre_roi_front
                # 上一次匹配到的位置还能匹配到target
                if pre_roi_front is not None and target.match(self.device.image, threshold=threshold):
                    # 到达稳定时间
                    if stable_timer.reached():
                        logger.info(f'{target.name} position has stabilized')
                        target.roi_back = origin_roi_back
                        return True
                else:
                    stable_timer.reset()  # 上一次匹配到的位置这次匹配不到了, 重置定时器
            else:
                stable_timer.reset()  # 当前页面都匹配不到, 重置定时器
            # 记录这一次的target位置
            pre_roi_front = cur_roi_front
            # 还原target的匹配区域
            target.roi_back = origin_roi_back
        logger.warning(f'Wait until pos stable({target}) timeout')
        return False

    def swipe(self, swipe: RuleSwipe, interval: float = None, duration: float = 0.1, wait_up_time=0) -> None:
        """

        :param interval:
        :param swipe:
        :param  duration
        :param  wait_up_time
        :return:
        """
        if not isinstance(swipe, RuleSwipe):
            return

        if interval:
            if swipe.name in self.interval_timer:
                # 如果传入的限制时间不一样，则替换限制新的传入的时间
                if self.interval_timer[swipe.name].limit != interval:
                    self.interval_timer[swipe.name] = Timer(interval)
            else:
                # 如果没有限制时间，则创建限制时间
                self.interval_timer[swipe.name] = Timer(interval)
            # 如果时间还没到达，则不执行
            if not self.interval_timer[swipe.name].reached():
                return

        x1, y1, x2, y2 = swipe.coord()
        self.device.swipe(p1=(x1, y1), p2=(x2, y2), control_name=swipe.name, duration=(duration, duration + 0.1), wait_up_time=wait_up_time)

        # 执行后，如果有限制时间，则重置限制时间
        if interval:
            # logger.info(f'Swipe {swipe.name}')
            self.interval_timer[swipe.name].reset()

    def click(self, click: Union[RuleClick, RuleLongClick, RuleOcr] = None, interval: float = None) -> bool:
        """
        点击或者长按
        :param interval:
        :param click:
        :return:
        """
        if not click:
            return False

        if interval:
            if click.name in self.interval_timer:
                # 如果传入的限制时间不一样，则替换限制新的传入的时间
                if self.interval_timer[click.name].limit != interval:
                    self.interval_timer[click.name] = Timer(interval)
            else:
                # 如果没有限制时间，则创建限制时间
                self.interval_timer[click.name] = Timer(interval)
            # 如果时间还没到达，则不执行
            if not self.interval_timer[click.name].reached():
                return False

        x, y = click.coord()
        if isinstance(click, RuleLongClick):
            self.device.long_click(x=x, y=y, duration=click.duration / 1000, control_name=click.name)
        elif isinstance(click, RuleClick) or isinstance(click, RuleImage) or isinstance(click, RuleOcr):
            self.device.click(x=x, y=y, control_name=click.name)

        # 执行后，如果有限制时间，则重置限制时间
        if interval:
            self.interval_timer[click.name].reset()
            return True
        return False

    def ocr_result(self, target: RuleOcr, interval: float = None):
        """
        执行OCR识别操作

        :param target: RuleOcr对象，包含OCR识别规则和目标信息
        :param interval: 间隔时间限制，单位为秒，默认为1秒，用于控制相同OCR操作的执行频率
        :return: OCR识别结果
        :raises ValueError: 当target不是RuleOcr类型时抛出异常
        """
        if not isinstance(target, RuleOcr):
            raise ValueError('ocr target must be RuleOcr')

        # 处理OCR操作的时间间隔限制
        if interval:
            if target.name in self.interval_timer:
                # 如果传入的限制时间不一样，则替换限制新的传入的时间
                if self.interval_timer[target.name].limit != interval:
                    self.interval_timer[target.name] = Timer(interval)
                # 如果时间还没到达，则等待
                while not self.interval_timer[target.name].reached():
                    sleep(0.1)  # 短暂休眠避免过度占用CPU
            else:
                # 如果没有限制时间，则创建限制时间
                self.interval_timer[target.name] = Timer(interval)

        # 执行OCR识别
        result = target.ocr(self.device.image)

        # 重置计时器
        if interval:
            self.interval_timer[target.name].reset()

        return result

    def ocr_appear(self, target: RuleOcr, interval: float = None) -> bool:
        """
        ocr识别目标
        :param interval:
        :param target:
        :return: 如果target有keyword或者是keyword存在，返回是True，否则返回False
                 但是没有指定keyword，返回的是匹配到的值，具体取决于target的mode
        """
        if not isinstance(target, RuleOcr):
            return False

        if interval:
            if target.name in self.interval_timer:
                # 如果传入的限制时间不一样，则替换限制新的传入的时间
                if self.interval_timer[target.name].limit != interval:
                    self.interval_timer[target.name] = Timer(interval)
            else:
                # 如果没有限制时间，则创建限制时间
                self.interval_timer[target.name] = Timer(interval)
            # 如果时间还没到达，则不执行
            if not self.interval_timer[target.name].reached():
                return False

        result = target.ocr(self.device.image)
        appear = False

        if not target.keyword or target.keyword == '':
            appear = False
        match target.mode:
            case OcrMode.FULL:  # 全匹配
                appear = result != (0, 0, 0, 0)
            case OcrMode.SINGLE:
                appear = result == target.keyword
            case OcrMode.DIGIT:
                appear = result == int(target.keyword)
            case OcrMode.DIGITCOUNTER:
                appear = result == target.ocr_str_digit_counter(target.keyword)
            case OcrMode.DURATION:
                appear = result == target.parse_time(target.keyword)

        if interval:
            self.interval_timer[target.name].reset()

        return appear

    def ocr_appear_click(self,
                         target: RuleOcr,
                         action: Union[RuleClick, RuleLongClick] = None,
                         interval: float = None,
                         duration: float = None) -> bool:
        """
        ocr识别目标，如果目标存在，则触发动作
        :param target:
        :param action:
        :param interval:
        :param duration:
        :return:
        """
        appear = self.ocr_appear(target, interval)

        if not appear:
            return False

        if action:
            x, y = action.coord()
            self.click(action, interval)
        else:
            x, y = target.coord()
            self.device.click(x=x, y=y, control_name=target.name)
        return True

    def list_find(self, target: RuleList, name: str | list[str], max_swipe: int = 10) -> bool | tuple:
        """
        会一致在列表寻找目标，找到了就退出。
        如果是图片列表会一直往下找
        如果是纯文字的，会自动识别自己的位置，根据位置选择向前还是向后翻
        :param max_swipe: 最大滑动次数
        :param target:
        :param name:
        :return:
        """
        swipe_down = False
        swipe_distance_ratio = None
        result = None
        if not target:
            return False
        appear = False
        for _ in range(max_swipe):
            self.screenshot()
            if target.is_image:
                result = target.image_appear(self.device.image, name=name)
                swipe_down = True
            elif target.is_ocr:
                result = target.ocr_appear(self.device.image, name=name)
                swipe_down = result is not None and isinstance(result, int) and result > 0
                swipe_distance_ratio = 1
            # 结果是坐标证明找到了, 非坐标都是没找到
            if result is not None and isinstance(result, tuple):
                appear = True
                break
            if swipe_distance_ratio:
                x1, y1, x2, y2 = target.swipe_pos(number=swipe_distance_ratio, after=swipe_down)
            else:
                x1, y1, x2, y2 = target.swipe_pos(after=swipe_down)
            self.device.swipe(p1=(x1, y1), p2=(x2, y2))
            sleep(random.uniform(0.8, 1.3))  # 等待滑动完成, 待优化
        if appear:
            return result
        return False

    def list_appear_click(self, target: RuleList, interval: float = None) -> bool:
        if interval:
            if target.name in self.interval_timer:
                # 如果传入的限制时间不一样，则替换限制新的传入的时间
                if self.interval_timer[target.name].limit != interval:
                    self.interval_timer[target.name] = Timer(interval)
            else:
                # 如果没有限制时间，则创建限制时间
                self.interval_timer[target.name] = Timer(interval)
            # 如果时间还没到达，则不执行
            if not self.interval_timer[target.name].reached():
                return False
        appear = self.list_find(target, name=target.array[0])
        if isinstance(appear, tuple) and interval:
            x, y = appear
            self.device.click(x, y)
            self.interval_timer[target.name].reset()
            return True
        return False

    def set_next_run(self, task: str = None, finish: bool = False,
                     success: bool = True, server: bool = True, target: datetime = None) -> None:
        """
        设置下次运行时间  当然这个也是可以重写的
        :param target: 可以自定义的下次运行时间
        :param server: True
        :param success: 判断是成功的还是失败的时间间隔
        :param task: 任务名称，大驼峰的
        :param finish: 是完成任务后的时间为基准还是开始任务的时间为基准
        :return:
        """
        if finish:
            start_time = datetime.now().replace(microsecond=0)
        else:
            start_time = self.start_time
        self.config.task_delay(task, start_time=start_time, success=success, server=server, target=target)

    def custom_next_run(self, task: str, custom_time: Time = None, time_delta: float = 1) -> None:
        """
        设置下次自定义运行时间
        :param task: 任务名称，大驼峰的
        :param custom_time: 可以自定义的下次运行时间
        :param time_delta: 下次运行日期为几天后，默认为第二天
        :return:
        """
        target_time = (datetime.now() + timedelta(days=time_delta)).replace(hour=custom_time.hour,
                                                                            minute=custom_time.minute,
                                                                            second=custom_time.second)
        self.set_next_run(task, target=target_time)

    def next_run_week(self, target_day: int = 1):
        """
        计算下一次运行的时间，目标是每周的特定一天。

        参数:
        target_day (int): 目标运行的日，取值1到7代表周一到周日，默认为1（周一）。
        """

        def convert_week_to_number(week_day: Week) -> int:
            """
            将 Week 枚举转换为对应的数字
            周一对应 1，周二对应 2，... 周日对应 7

            :param week_day: Week 枚举值
            :return: 对应的数字 (1-7)
            """
            week_map = {
                Week.mon: 1,
                Week.tue: 2,
                Week.wed: 3,
                Week.thu: 4,
                Week.fri: 5,
                Week.sat: 6,
                Week.sun: 7
            }

            return week_map.get(week_day, 0)  # 如果找不到返回0

        if isinstance(target_day, Week):
            target_day = convert_week_to_number(target_day)

        today = datetime.today()
        current_weekday = today.weekday()  # 周一为0，周日为6
        target = target_day - 1  # 将输入1-7转换为0-6
        days_diff = (target - current_weekday) % 7 or 7

        TaskName = self.config.task.command
        logger.info(f'{TaskName} done in {days_diff} days on next Week [{target_day}].')

        # 获取服务更新时间配置
        task_name = convert_to_underscore(TaskName)
        task_object = getattr(self.config.model, task_name, None)
        scheduler = getattr(task_object, 'scheduler', None)
        server_update = scheduler.server_update

        self.push_notify(content=f'任务下周{target_day}执行')

        # 调用自定义函数设置下一次运行时间
        self.custom_next_run(task=TaskName,
                             custom_time=Time(hour=server_update.hour, minute=server_update.minute,
                                              second=server_update.second),
                             time_delta=days_diff)

    #  ---------------------------------------------------------------------------------------------------------------
    #
    #  ---------------------------------------------------------------------------------------------------------------
    def ui_reward_appear_click(self, screenshot=False) -> bool:
        """
        如果出现 ‘获得奖励’ 就点击
        :return:
        """
        if screenshot:
            self.screenshot()
        return self.appear_then_click(self.I_UI_REWARD, action=self.C_UI_REWARD, interval=0.4, threshold=0.6)

    def ui_get_reward(self, click_image: RuleImage or RuleOcr or RuleClick, click_interval: float = 1):
        """
        传进来一个点击图片 或是 一个ocr， 会点击这个图片，然后等待‘获得奖励’，
        最后当获得奖励消失后 退出
        :param click_interval:
        :param click_image:
        :return:
        """
        _timer = Timer(10)
        _timer.start()
        while 1:
            self.screenshot()

            if self.ui_reward_appear_click():
                sleep(0.5)
                while 1:
                    self.screenshot()
                    # 等待动画结束
                    if not self.appear(self.I_UI_REWARD, threshold=0.6):
                        logger.info('Get reward success')
                        break

                    # 一直点击
                    if self.ui_reward_appear_click():
                        continue
                break
            if _timer.reached():
                logger.warning('Get reward timeout')
                break

            if isinstance(click_image, RuleImage):
                if self.appear_then_click(click_image, interval=click_interval):
                    continue
            elif isinstance(click_image, RuleOcr):
                if self.ocr_appear_click(click_image, interval=click_interval):
                    continue
            elif isinstance(click_image, RuleClick):
                if self.click(click_image, interval=click_interval):
                    continue

        return True

    def ui_click(self, click, stop, interval=1):
        """
        循环的一个操作，直到出现stop
        :param click:
        :param stop:
        :parm interval
        :return:
        """
        while 1:
            self.screenshot()
            if self.appear(stop):
                break
            if isinstance(click, RuleImage) and self.appear_then_click(click, interval=interval):
                continue
            if isinstance(click, RuleClick) and self.click(click, interval=interval):
                continue
            elif isinstance(click, RuleOcr) and self.ocr_appear_click(click, interval=interval):
                continue

    def ui_click_until_disappear(self, click, interval: float = 1):
        """
        点击一个按钮直到消失
        :param interval:
        :param click:
        :return:
        """
        while 1:
            self.screenshot()
            if not self.appear(click):
                break
            elif self.appear_then_click(click, interval=interval):
                continue

    def ui_click_until_smt_disappear(self, click, stop, interval: float = 1):
        """
        点击一个按钮/区域/文字直到stop消失
        """
        while 1:
            self.screenshot()
            if not self.appear(stop):
                break
            if isinstance(click, RuleImage) or isinstance(click, RuleGif):
                self.appear_then_click(click, interval=interval)
                continue
            if isinstance(click, RuleClick):
                self.click(click, interval)
                continue
            if isinstance(click, RuleOcr):
                self.click(click)
                continue

    def push_notify(self, content='', title=None):
        """
        父类中定义一个 push_notify 方法，子类可以重写它。
        默认情况下可以什么都不做，或者给出一个提示。
        """
        logger.warning(f"[BaseTaskParent] push_notify 被调用，但未在子类中具体实现。内容：{content}, 标题：{title}")
