# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey

from module.base.timer import Timer
from module.exception import RequestHumanTakeover, GameTooManyClickError, GameStuckError
from module.exception import TaskEnd
from module.logger import logger
from tasks.Component.GeneralBuff.general_buff import GeneralBuff
from tasks.Component.LoginHarvest.login_base import LoginBase
from tasks.Component.SwitchAccount.assets import SwitchAccountAssets
from tasks.Restart.assets import RestartAssets


class LoginHandler(LoginBase, RestartAssets, GeneralBuff):
    character: str

    def __init__(self, *wargs, **kwargs):
        super().__init__(*wargs, **kwargs)
        self.character = self.config.restart.login_character_config.character
        self.O_LOGIN_SPECIFIC_SERVE.keyword = self.character
        self.mail_harvested = 0  # 添加执行标记
        # self.specific_usr = kwargs['config'].

    def _app_handle_login(self) -> bool:
        """
        最终是在庭院界面
        :return:
        """
        logger.hr('App login')
        # self.device.stuck_record_add('LOGIN_CHECK')

        confirm_timer = Timer(1.5, count=2).start()
        orientation_timer = Timer(10)
        login_success = False

        while 1:
            if not login_success and orientation_timer.reached():
                # Screen may rotate after starting an app
                self.device.get_orientation()
                orientation_timer.reset()

            self.screenshot()
            # 渠道服登陆页面
            if self.appear(SwitchAccountAssets.I_QD_READ_AND_AGREED):
                self.set_next_run()
                raise TaskEnd

            # 4399登录会遇到活动-点击叉号
            if self.appear_then_click(self.I_LOGIN_CLOSE):
                logger.info('4399登录会遇到活动-点击叉号')
                continue
            # 是否继续刚才的战斗？-点击取消
            if self.appear_then_click(self.I_LOGIN_CANCEL_BATTLE):
                logger.info('是否继续刚才的战斗？-点击取消')
                continue
            # 确认进入庭院
            if self.appear_then_click(self.I_LOGIN_SCROOLL_CLOSE, interval=2, threshold=0.9):
                logger.info('Open scroll')
                continue
            if self.appear(self.I_LOGIN_SCROOLL_OPEN, interval=0.2):
                if confirm_timer.reached():
                    logger.info('Login to main confirm')
                    break
            else:
                confirm_timer.reset()
            # 登录成功
            if self.appear(self.I_LOGIN_SCROOLL_OPEN, interval=0.5):
                logger.info('Login success')
                login_success = True

            # 网络异常
            # if self.ocr_appear(self.O_LOGIN_NETWORK):
            #     logger.error('Network error')
            #     raise RequestHumanTakeover('Network error')

            # 跳过观看视频
            # if self.ocr_appear_click(self.O_LOGIN_SKIP_1, interval=1):
            #     continue
            # 下载插画
            if self.appear_then_click(self.I_LOGIN_LOAD_DOWN, interval=1):
                logger.info('Download inbetweening')
                continue
            # 不观看视频
            if self.appear_then_click(self.I_WATCH_VIDEO_CANCEL, interval=0.6):
                logger.info('Close video')
                continue
            # 右上角的红色的关闭
            if self.appear_then_click(self.I_LOGIN_RED_CLOSE, interval=0.6):
                logger.info('Close red close')
                continue
            # 左上角的黄色关闭
            if self.appear_then_click(self.I_LOGIN_YELLOW_CLOSE, interval=0.6):
                logger.info('Close yellow close')
                continue
            # 绑定手机号弹窗
            if self.appear_then_click(self.I_LOGIN_LOGIN_GOTO_BIND_PHONE):
                while 1:
                    self.screenshot()
                    if self.appear_then_click(self.I_LOGIN_LOGIN_CANCEL_BIND_PHONE):
                        logger.info("Close bind phone")
                        break
                continue
            # 关闭各种邀请弹窗(主要时结界卡寄养邀请)
            from tasks.Component.GeneralInvite.assets import GeneralInviteAssets as gia
            if not hasattr(self, "invite_handled"):
                if self.appear_then_click(gia.I_I_REJECT, interval=0.8):
                    logger.info("reject invites")
                    self.invite_handled = True  # 标记为已处理
                    continue
            # 点击屏幕进入游戏
            if self.appear(self.I_LOGIN_SPECIFIC_SERVE, interval=0.6) and self.ocr_appear_click(self.O_LOGIN_SPECIFIC_SERVE, interval=0.6):
                logger.info(f'多角色区服选择成功: {self.O_LOGIN_SPECIFIC_SERVE.keyword}')
                while True:
                    self.screenshot()
                    if self.appear(self.I_LOGIN_SPECIFIC_SERVE):
                        self.click(self.C_LOGIN_ENSURE_LOGIN_CHARACTER_IN_SAME_SVR, interval=2)
                        continue
                    break
                logger.info('login specific user')
                continue

            # 创建角色, 误入新区直接重启
            if self.appear(self.I_CREATE_ACCOUNT):
                logger.warning('Appear create account')
                raise GameStuckError('Appear create account')
            # 点击’进入游戏‘
            if not self.appear(self.I_LOGIN_8):
                continue
            if self.appear(self.I_CHARACTARS, interval=1):
                # https://github.com/runhey/OnmyojiAutoScript/issues/585
                self.device.click(x=246, y=535)
            if self.ocr_appear_click(self.O_LOGIN_ENTER_GAME, interval=3):
                self.wait_until_appear(self.I_LOGIN_SPECIFIC_SERVE, True, wait_time=5)
                continue

        return login_success

    def app_handle_login(self) -> bool:
        for _ in range(2):
            self.device.stuck_record_clear()
            self.device.click_record_clear()
            try:
                self._app_handle_login()
                if self.config.restart.harvest_config.enable:
                    self.check_login(self.config.global_game.costume_config)
                    self.harvest()
                return True
            except (GameTooManyClickError, GameStuckError) as e:
                logger.warning(e)
                self.device.app_stop()
                self.device.app_start()
                continue

        logger.critical('Login failed more than 3')
        logger.critical('Onmyoji server may be under maintenance, or you may lost network connection')
        raise RequestHumanTakeover

    def harvest(self):
        """
        获得奖励
        :return: 如果没有发现任何奖励后退出
        """
        logger.hr('Harvest')
        timer_harvest = Timer(3)  # 如果连续3秒没有发现任何奖励，退出
        while 1:
            self.screenshot()

            # 红色的关闭
            if self.appear_then_click(self.I_LOGIN_RED_CLOSE, interval=1):
                timer_harvest.reset()
                continue
            # 点击'获得奖励'
            if self.ui_reward_appear_click():
                timer_harvest.reset()
                continue
            # 获得奖励
            if self.appear_then_click(self.I_UI_AWARD, interval=0.2):
                timer_harvest.reset()
                continue
            # 偶尔会打开到聊天频道
            if self.appear_then_click(self.I_HARVEST_CHAT_CLOSE, interval=1):
                timer_harvest.reset()
                continue
            # 偶尔会进入其他页面
            # 左上角的黄色关闭
            if self.appear_then_click(self.I_LOGIN_YELLOW_CLOSE, interval=0.6):
                timer_harvest.reset()
                logger.info('Close yellow close')
                continue
            # 关闭宠物小屋
            if self.appear_then_click(self.I_HARVEST_BACK_PET_HOUSE, interval=0.6):
                timer_harvest.reset()
                logger.info('Close yellow close')
                continue
            # 关闭姿度出现的蒙版
            if self.appear(self.I_HARVEST_ZIDU, interval=1):
                self.I_HARVEST_ZIDU.roi_front[0] -= 200
                self.I_HARVEST_ZIDU.roi_front[1] -= 200
                if self.click(self.I_HARVEST_ZIDU, interval=2):
                    logger.info('Close zidu')
                timer_harvest.reset()
                continue
            if self.appear_then_click(self.I_LIAO_MESSAGE, interval=1):
                timer_harvest.reset()
                logger.info('关闭寮消息通知')
                continue
            # 关闭阴阳师精灵提示
            # if self.appear_then_click(self.I_LOGIN_LOGIN_ONMYOJI_GENIE):
            #     logger.info("关闭阴阳师精灵提示")
            #     continue
            # 各种邀请框
            self.reject_invite()

            # 勾玉
            if self.appear_then_click(self.I_HARVEST_JADE, interval=1.5):
                timer_harvest.reset()
                continue
            # 签到
            if self.appear_then_click(self.I_HARVEST_SIGN, interval=1.5):
                self.wait_until_appear(self.I_HARVEST_SIGN_2, wait_time=2)
                timer_harvest.reset()
                continue
            # 某些活动的特殊签到，有空看到就删掉
            if self.appear_then_click(self.I_HARVEST_SIGN_3, interval=0.7):
                timer_harvest.reset()
                continue
            if self.appear_then_click(self.I_HARVEST_SIGN_4, interval=1):
                timer_harvest.reset()
                continue
            if self.appear_then_click(self.I_HARVEST_SIGN_2, interval=1.5):
                self.wait_until_appear(self.I_LOGIN_RED_CLOSE, wait_time=2)
                timer_harvest.reset()
                continue
            # 999天的签到福袋
            if self.appear_then_click(self.I_HARVEST_SIGN_999, interval=1.5):
                timer_harvest.reset()
                continue
            # 体力
            if self.appear_then_click(self.I_HARVEST_AP, interval=1, threshold=0.7):
                timer_harvest.reset()
                continue
            # 御魂觉醒加成
            if self.appear_then_click(self.I_HARVEST_SOUL, interval=1):
                timer_harvest.reset()
                continue
            # 寮包
            if self.appear_then_click(self.I_HARVEST_GUILD_REWARD, interval=2):
                timer_harvest.reset()
                continue
            # 自选御魂
            # if self.appear(self.I_HARVEST_SOUL_1):
            #     logger.info('Select soul 1')
            #     self.ui_click(self.I_HARVEST_SOUL_1, stop=self.I_HARVEST_SOUL_2)
            #     self.ui_click(self.I_HARVEST_SOUL_2, stop=self.I_HARVEST_SOUL_3, interval=3)
            #     self.ui_click_until_disappear(click=self.I_HARVEST_SOUL_3)
            #     timer_harvest.reset()
            #     continue

            # 邮件
            # 判断是否勾选了收取邮件（不收取邮件可以查看每日收获）
            if self.config.restart.harvest_config.enable_mail:
                # 只执行一次邮件收取
                if self.mail_harvested <= 10:
                    if self.appear(self.I_MAIL_RED_DOTS, interval=1) and self.appear_then_click(self.I_HARVEST_MAIL_TOP_RIGHT, interval=1):
                        if self.wait_until_appear(self.I_HARVEST_MAIL_TITLE, wait_time=2):
                            while 1:
                                self.screenshot()
                                # 如果没有出现 ‘收取全部’ 也没有出现 ‘还未读的邮件’ 那就可以退出了
                                if not self.appear(self.I_HARVEST_MAIL_ALL) and not self.appear(self.I_HARVEST_MAIL_OPEN) and not self.appear(self.I_MAIL_CANCEL):
                                    logger.info('Mail has been harvested completed')
                                    break
                                if self.appear_then_click(self.I_MAIL_CANCEL, interval=1):
                                    continue
                                if self.appear_then_click(self.I_HARVEST_MAIL_ALL, interval=1):
                                    self.wait_until_appear_then_click(self.I_HARVEST_MAIL_CONFIRM, wait_time=2)
                                    continue
                                if self.appear_then_click(self.I_HARVEST_MAIL_OPEN, interval=1):
                                    continue
                        timer_harvest.reset()
                        self.mail_harvested += 1  # 设置标记为已执行
                        continue

            # 3秒内没有发现任何奖励，退出
            if not timer_harvest.started():
                timer_harvest.start()
            else:
                if timer_harvest.reached():
                    logger.info('No more reward')
                    return

    def set_specific_usr(self, character: str):
        self.character = character
        self.O_LOGIN_SPECIFIC_SERVE.keyword = character
