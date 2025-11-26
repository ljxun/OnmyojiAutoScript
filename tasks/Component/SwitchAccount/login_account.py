import time

import cv2
import random
from module.atom.click import RuleClick
from module.atom.gif import RuleGif
from module.atom.image import RuleImage
from module.atom.ocr import RuleOcr
from module.logger import logger
from tasks.Component.SwitchAccount.assets import SwitchAccountAssets
from tasks.Component.SwitchAccount.switch_account_config import AccountInfo
from tasks.Restart.assets import RestartAssets
from tasks.base_task import BaseTask


class LoginAccount(BaseTask, SwitchAccountAssets):

    def get_svr_name(self):
        self.screenshot()
        ocrRes = self.O_SA_LOGIN_FORM_SVR_NAME.ocr(self.device.image)
        return ocrRes

    def check_svr(self, svrName: str):
        logger.info(f"[区服] 需要登录的区服: [{svrName}]")
        time.sleep(1)
        while 1:
            self.screenshot()
            # self.save_image(wait_time=0, image_type=True)
            self.O_SA_LOGIN_FORM_SVR_NAME.keyword = svrName
            ocrSvrName = self.O_SA_LOGIN_FORM_SVR_NAME.ocr(self.device.image)
            # 边界检查：确保 OCR 结果不为空
            if not ocrSvrName or len(ocrSvrName) == 0:
                logger.warning("OCR 未识别到任何结果，点击空白区域...")
                self.click(self.C_SA_LOGIN_FORM_CANCEL_SVR_SELECT)
                continue
            else:
                logger.info(f"[区服] 当前登录的区服: [{ocrSvrName}]")
                if self.assess_text_threshold(svrName, ocrSvrName, 0.8):
                    return True
                else:
                    return False

    def switch_svr(self, svrName: str):
        """
            需保证账号已登录 且处于登录界面
        @param svrName:
        @type svrName:
        """
        self.screenshot()
        self.O_SA_LOGIN_FORM_SVR_NAME.keyword = svrName
        # 4399登录会遇到活动-点击叉号
        if self.wait_until_appear_then_click_center(RestartAssets.I_LOGIN_CLOSE, wait_time=1):
            logger.info('4399登录会遇到活动-点击叉号')
        self.ui_click(self.C_SA_LOGIN_FORM_SWITCH_SVR_BTN, self.I_SA_CHECK_SELECT_SVR_1, 1.5)
        # 展开底部角色列表,显示角色所属服务器
        self.screenshot()
        if self.appear(self.I_SA_CHECK_SELECT_SVR_1) and (not self.appear(self.I_SA_CHECK_SELECT_SVR_2)):
            self.click(self.O_SA_SELECT_SVR_CHARACTER_LIST)

        self.O_SA_SELECT_SVR_SVR_LIST.keyword = svrName
        found = False
        lastSvrList: tuple = ()
        while 1:
            self.screenshot()
            # 灰度图
            self.device.image = cv2.cvtColor(self.device.image, cv2.COLOR_BGR2GRAY)
            # ret, self.device.image = cv2.threshold(self.device.image, 200, 255, cv2.THRESH_OTSU)
            ret, self.device.image = cv2.threshold(self.device.image, 100, 255, cv2.THRESH_BINARY)
            # self.device.image = cv2.adaptiveThreshold(self.device.image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 25, 10)
            self.device.image = abs(255 - self.device.image)

            # RGB图
            self.device.image = cv2.cvtColor(self.device.image, cv2.COLOR_GRAY2RGB)

            ocrRes = self.O_SA_SELECT_SVR_SVR_LIST.detect_and_ocr(self.device.image)
            # 受限于图像识别文字准确率,此处对识别结果与实际服务器名字 进行检查 字重合度大于阈值 就认为查找成功
            ocrSvrList = [res.ocr_text for res in ocrRes]
            logger.info(f"识别到的区服列表：{ocrSvrList}")
            for index, ocrSvrName in enumerate(ocrSvrList):
                if len(ocrSvrName) < 3:
                    break

                if self.assess_text_threshold(svrName, ocrSvrName, 0.6):
                    found = True
                    # 确定点击位置
                    self.O_SA_SELECT_SVR_SVR_LIST.area = ocrRes[index].after_box
                    # 跳出此层for循环
                    break
            # 两次OCR结果相等表示滑动到最右侧
            if found or lastSvrList == ocrSvrList:
                break
            lastSvrList = ocrSvrList
            self.swipe(self.S_SA_SVR_SWIPE_LEFT)
            time.sleep(3)
        if found:
            self.click(self.O_SA_SELECT_SVR_SVR_LIST, interval=1.5)
            return True
        else:
            click_list = [self.C_SA_SELECT_SVR_1, self.C_SA_SELECT_SVR_2, self.C_SA_SELECT_SVR_3, self.C_SA_SELECT_SVR_4]
            # 定义权重，数字越大选中概率越大
            weights = [3, 2, 1, 1]
            # 根据权重随机选择
            selected_item = random.choices(click_list, weights=weights)[0]
            logger.info(f"[区服] '{svrName}' 未识别到, 将随机点击区服区域 [{selected_item.name}]")
            self.click(selected_item)
            time.sleep(1)
        # 没找到 点击空白区域关闭选择服务器界面
        self.click(self.C_SA_LOGIN_FORM_CANCEL_SVR_SELECT)

    def switch_character(self, characterName: str):
        """
              需保证账号已登录 且处于登录界面
        @param characterName:
        @return:
        @rtype:
        """
        logger.info(f"[角色] 开始寻找角色: [{characterName}]")
        # 4399登录会遇到活动-点击叉号
        if self.wait_until_appear_then_click_center(RestartAssets.I_LOGIN_CLOSE, wait_time=1):
            logger.info('4399登录会遇到活动-点击叉号')
        self.ui_click(self.C_SA_LOGIN_FORM_SWITCH_SVR_BTN, self.I_SA_CHECK_SELECT_SVR_1)
        # 展开底部角色列表,显示角色所属服务器
        self.screenshot()
        while (not self.appear(self.I_SA_CHECK_SELECT_SVR_2)) and self.appear(self.I_SA_CHECK_SELECT_SVR_1):
            logger.info("open svr icon")
            self.click(self.C_SA_SELECT_SVR_CHARACTER_LIST, interval=1.5)
            self.wait_until_appear(self.I_SA_CHECK_SELECT_SVR_2, False, 1)
            # self.ui_click(self.C_SA_SELECT_SVR_CHARACTER_LIST, self.I_SA_CHECK_SELECT_SVR_2, 1.5)
            self.screenshot()

        self.O_SA_SELECT_SVR_CHARACTER_LIST.keyword = characterName
        lastCharacterNameList = []
        while 1:
            self.screenshot()
            ocrRes = self.O_SA_SELECT_SVR_CHARACTER_LIST.detect_and_ocr(self.device.image)
            # 去除角色等级数字
            characterNameList = [ocrResItem.ocr_text.lstrip('1234567890 ([<>])【】（）《》') for ocrResItem in ocrRes]
            logger.info(f"识别到的角色列表：{characterNameList}")
            if characterNameList.count(characterName) > 1:
                logger.warning(f"[角色] '{characterName}' 存在多个,将使用区服查找")
                self.click(self.C_SA_LOGIN_FORM_CANCEL_SVR_SELECT, 1.5)
                return False
            for index, item in enumerate(characterNameList):
                if item != characterName:
                    continue
                # 此时 tmp 内存储的时角色名位置,而点击角色名没有反应
                # 所以需要获取到对应的服务器图标位置
                ocrRes[index].after_box[1] -= 60
                tmpClick = RuleClick(roi_front=ocrRes[index].after_box, roi_back=ocrRes[index].after_box, name="tmpClick")
                self.ui_click_until_disappear(tmpClick, stop=self.I_SA_CHECK_SELECT_SVR_2, interval=3)
                logger.info("[角色] %s 已经找到", characterName)
                return True
            if lastCharacterNameList == characterNameList:
                break
            logger.info(f'{characterName} not found,start swipe')
            lastCharacterNameList = characterNameList
            self.swipe(self.S_SA_SVR_SWIPE_LEFT)
            # 等待滑动动画完成
            time.sleep(2)

        self.click(self.C_SA_LOGIN_FORM_CANCEL_SVR_SELECT, 1.5)
        return False

    def jump2SelectAccount(self):
        """
            跳转到切换账号页面 该页面有红色登录按钮
        @return:
        @rtype:
        """
        while 1:
            if self.appear(self.I_SA_NETEASE_GAME_LOGO) and self.appear(self.I_SA_ACCOUNT_LOGIN_BTN):
                return
            if self.appear_then_click(self.I_SA_SWITCH_ACCOUNT_BTN, interval=1.5):
                continue
            if self.appear(self.I_CHECK_LOGIN_FORM):
                self.click(self.C_SA_LOGIN_FORM_USER_CENTER, 1.5)
                continue
        return

    def selectAccount(self, accountInfo: AccountInfo):
        logger.info("start selectAccount")
        self.O_SA_ACCOUNT_ACCOUNT_LIST.keyword = accountInfo.account
        self.O_SA_ACCOUNT_ACCOUNT_SELECTED.keyword = accountInfo.account
        # 正常情况一次就行,但防不住OCR搞幺蛾子 保险起见 多来几次吧 反正挂机不差这点
        for i in range(3):
            while 1:
                self.screenshot()
                if self.appear(self.I_SA_ACCOUNT_DROP_DOWN_CLOSED):
                    if self.ocr_appear(self.O_SA_ACCOUNT_ACCOUNT_SELECTED):
                        return True
                    self.ui_click_until_disappear(self.I_SA_ACCOUNT_DROP_DOWN_CLOSED, interval=1.5)
                    continue

                # 账号列表已打开状态
                ocrRes = self.O_SA_ACCOUNT_ACCOUNT_LIST.detect_and_ocr(self.device.image)
                # 找到该账号
                for index, ocr_account in enumerate([ocrResItem.ocr_text for ocrResItem in ocrRes]):
                    if not accountInfo.is_account_alias(ocr_account):
                        continue
                    self.O_SA_ACCOUNT_ACCOUNT_LIST.area = ocrRes[index].after_box
                    time.sleep(1)
                    self.click(self.O_SA_ACCOUNT_ACCOUNT_LIST)
                    logger.info("已找到账号: [ %s ]", accountInfo.account)
                    return True

                # 未找到该账号
                if self.appear(self.I_SA_ACCOUNT_DROP_DOWN_ADD_ACCOUNT):
                    break
                self.swipe(self.S_SA_ACCOUNT_LIST_UP, 1.5)
                time.sleep(0.5)
        logger.error(f"未已找到账号: [{accountInfo.account}-{accountInfo.character}]")
        return False

    # def loginSubmit(self, appleOrAndroid: bool):
    #     """
    #
    #     @param appleOrAndroid: 安卓平台还是苹果平台
    #     @type appleOrAndroid:   False           Apple
    #                             True            Android
    #     @return:
    #     @rtype:
    #     """
    #     self.screenshot()
    #     if not (self.appear(self.I_SA_ACCOUNT_LOGIN_BTN) and self.appear(self.I_SA_NETEASE_GAME_LOGO)):
    #         # 不在登录界面,返回失败
    #         return False
    #     self.ui_click(self.C_SA_LOGIN_FORM_LOGIN_BTN, self.I_SA_LOGIN_FORM_APPLE, 1)
    #     if appleOrAndroid:
    #         logger.info("APPLE selected")
    #         self.ui_click_until_disappear(self.I_SA_LOGIN_FORM_APPLE, 1)
    #     else:
    #         logger.info("ANDROID selected")
    #         self.ui_click_until_disappear(self.I_SA_LOGIN_FORM_ANDROID, 1)
    #     return True

    def login(self, accountInfo: AccountInfo) -> bool:
        """

        @param accountInfo:
        @type accountInfo:
        @return:    True    点击了"进入游戏"按钮
                    False   未找到相应角色
        @rtype:bool
        """
        self.screenshot()
        #
        if not (self.appear(self.I_CHECK_LOGIN_FORM) or self.appear(self.I_SA_NETEASE_GAME_LOGO)):
            logger.error("Unknown Page,%s %s Login Failed", accountInfo.character, accountInfo.svr)
            return False

        #
        isAccountLogon = False
        isCharacterSelected = True
        if accountInfo.enable_wy:
            isCharacterSelected = True
        else:
            while 1:
                self.screenshot()
                if self.appear(self.I_QD_READ_AND_AGREED):
                    isAccountLogon = False
                    isCharacterSelected = False
                    break
                if self.appear(self.I_SA_CHECK_SELECT_SVR_1):
                    isAccountLogon = True
                    isCharacterSelected = True
                    break
                if self.click(self.C_SA_LOGIN_FORM_SWITCH_SVR_BTN, interval=1.5):
                    continue

        self.O_SA_ACCOUNT_ACCOUNT_SELECTED.keyword = accountInfo.account
        self.O_SA_LOGIN_FORM_USER_CENTER_ACCOUNT.keyword = accountInfo.account
        while 1:
            self.screenshot()

            if self.appear_then_click(self.I_ACCEPT_AGREEMENT):
                continue

            # 处于 选择服务器界面 直接点击空白区域退出该界面 进入切换账号流程
            if self.appear(self.I_SA_CHECK_SELECT_SVR_1) or self.appear(self.I_SA_CHECK_SELECT_SVR_2):
                self.click(self.C_SA_LOGIN_FORM_CANCEL_SVR_SELECT)
                continue

            # 处于选择 苹果安卓界面
            if self.appear(self.I_SA_LOGIN_FORM_APPLE):
                btn = self.I_SA_LOGIN_FORM_ANDROID if accountInfo.apple_or_android else self.I_SA_LOGIN_FORM_APPLE
                self.ui_click_until_disappear(btn)
                isAccountLogon = True
                if self.check_svr(accountInfo.svr):
                    break
                continue
            # 处于选择账号界面
            if self.appear(self.I_SA_NETEASE_GAME_LOGO) and not self.appear(self.I_SA_LOGIN_FORM_APPLE):
                if not accountInfo.account:
                    logger.error("账号参数为空，无法切换账户")
                    return False
                # 当前选择账号不是account
                if not self.ocr_appear(self.O_SA_ACCOUNT_ACCOUNT_SELECTED):
                    # 没有找到account
                    if not self.selectAccount(accountInfo):
                        self.ui_click_until_disappear(self.C_SA_LOGIN_FORM_ACCOUNT_CLOSE_BTN, stop=self.I_SA_NETEASE_GAME_LOGO)
                        return False
                    # selectAccount 后更新图片
                    self.screenshot()
                # logger.info("[账号] 当前账号正是期望账号: [ %s ]", accountInfo.account)
                self.ui_click(self.I_SA_ACCOUNT_LOGIN_BTN, stop=self.I_SA_LOGIN_FORM_APPLE, interval=1)
                continue
            # 在用户中心界面
            if self.appear(self.I_SA_SWITCH_ACCOUNT_BTN):
                # 如果当前已登录用户就是account
                ocrRes = self.O_SA_LOGIN_FORM_USER_CENTER_ACCOUNT.ocr_single(self.device.image)
                # NOTE 由于邮箱账号@符号极易被误识别为其他,故对账号信息做预处理 便于比对
                if (accountInfo.account is None) or accountInfo.account == "" or accountInfo.is_account_alias(ocrRes):
                    logger.info("[账号] 当前账号正是期望账号: [ %s ]", ocrRes)
                    isAccountLogon = True
                    self.ui_click_until_disappear(self.C_SA_LOGIN_FORM_USER_CENTER_CLOSE_BTN, stop=self.I_SA_SWITCH_ACCOUNT_BTN, interval=1)
                    if self.check_svr(accountInfo.svr):
                        break
                    continue
                #
                if self.ui_click(self.I_SA_SWITCH_ACCOUNT_BTN, self.I_SA_NETEASE_GAME_LOGO):
                    isAccountLogon = False
                    continue
                continue
            # 在游戏登录界面 不在用户中心 不在切换账号界面
            if not (self.appear(self.I_SA_NETEASE_GAME_LOGO) or self.appear(self.I_SA_SWITCH_ACCOUNT_BTN)):
                # 判断是否已经账号登录
                if not isAccountLogon and accountInfo.enable_wy:
                    self.click(self.C_SA_LOGIN_FORM_USER_CENTER)
                    continue

                # 已登录 查找对应角色(因为有重名角色所以用下面的区服查找)
                if isCharacterSelected:
                    isCharacterSelected = self.switch_character(accountInfo.character)
                    if self.check_svr(accountInfo.svr):
                        break

            # 切换角色失败 /未找到该角色
            # 尝试使用 选择服务器方式
            if isAccountLogon and accountInfo.svr is not None and accountInfo.svr != "":
                logger.info("[区服] 选择区服登录：[%s]", accountInfo.svr)
                self.switch_svr(accountInfo.svr)
                if self.check_svr(accountInfo.svr):
                    break
            if self.appear(self.I_QD_READ_AND_AGREED):
                self.ui_click(self.I_QD_READ_AND_AGREED, stop=self.I_LOGIN_IN)
                logger.info("[协议] 渠道服点击已阅读并同意")
                self.login_qd_account(accountInfo.account, accountInfo.password)
                isAccountLogon = True
                isCharacterSelected = True

        if isAccountLogon:
            # 成功登录账号 找到角色
            # self.ui_click_until_disappear(self.C_SA_LOGIN_FORM_ENTER_GAME_BTN, stop=self.I_CHECK_LOGIN_FORM)
            logger.info("[角色] %s-%s %s %s", accountInfo.svr, accountInfo.character,
                        accountInfo.account,
                        'Android' if accountInfo.apple_or_android else 'Apple')
            return True

        logger.error("[角色] %s-%s %s %s login Failed", accountInfo.svr, accountInfo.character,
                     accountInfo.account,
                     'Android' if accountInfo.apple_or_android else 'Apple')
        return False

    def login_qd_account(self, account: str, password: str):
        """
        在登录页输入账号密码
        @param account: 账号字符串
        @param password: 密码字符串
        """
        while 1:
            self.screenshot()
            O_login_input = RuleOcr(roi=(9,74,245,295), area=(9,74,245,295), mode="Single", method="Default", keyword="", name="sa_select_svr_svr_list")
            ocrRes = O_login_input.detect_and_ocr(self.device.image)

            # 直接查找并获取 "账号" 的 OCR 结果
            account_ocr = next((res for res in ocrRes if res.ocr_text == "账号"), None)
            if not account_ocr:
                logger.error("未找到账号输入框")
                return False
            password_ocr = next((res for res in ocrRes if res.ocr_text == "密码"), None)
            if not password_ocr:
                logger.error("未找到密码输入框")
                return False

            # ocrList = [res for res in ocrRes if res.ocr_text in loginList]
            # print(account_ocr.after_box)  # 43.0, 108.0, 52.0, 32.0
            # print(password_ocr.after_box)  # 43.0, 191.0, 52.0, 32.0

            click_account_roi = account_ocr.after_box[0] + 100,account_ocr.after_box[1],account_ocr.after_box[2],account_ocr.after_box[3]
            click_password_roi = password_ocr.after_box[0] + 100,password_ocr.after_box[1],password_ocr.after_box[2],password_ocr.after_box[3]
            click_account = RuleClick(roi_front=click_account_roi, roi_back=click_account_roi, name="click_account")
            click_password = RuleClick(roi_front=click_password_roi, roi_back=click_password_roi, name="click_password")

            # clear_account_roi = 1150, account_ocr.after_box[1], 60, account_ocr.after_box[3]
            # clear_password_roi = 1150, password_ocr.after_box[1], 120, password_ocr.after_box[3]
            # self.I_QD_CLEAR_ACCOUNT_INPUT.roi_front = list(clear_account_roi)
            # self.I_QD_CLEAR_ACCOUNT_INPUT.roi_back = list(clear_account_roi)
            # logger.info(f"[坐标] clear_account_roi： {clear_account_roi}")
            # self.I_QD_CLEAR_PASSWORD_INPUT.roi_front = list(clear_password_roi)
            # self.I_QD_CLEAR_PASSWORD_INPUT.roi_back = list(clear_password_roi)
            # self.I_QD_SHOW_PASSWORD.roi_front = list(clear_password_roi)
            # self.I_QD_SHOW_PASSWORD.roi_back = list(clear_password_roi)
            # logger.info(f"[坐标] clear_password_roi： {clear_password_roi}")

            o_account_roi = account_ocr.after_box[0] + 70, account_ocr.after_box[1], account_ocr.after_box[2] + 50, account_ocr.after_box[3]
            o_password_roi = password_ocr.after_box[0] + 70, password_ocr.after_box[1], password_ocr.after_box[2] + 50, password_ocr.after_box[3]
            o_account = RuleOcr(roi=o_account_roi, area=o_account_roi, mode="Single", method="Default", keyword="账号", name="sa_select_svr_svr_list")
            o_password = RuleOcr(roi=o_password_roi, area=o_password_roi, mode="Single", method="Default", keyword="账号", name="sa_select_svr_svr_list")

            logger.info(f"开始输入账号: {account}")

            # 清空账号输入框内容
            self.ui_click_center_until_disappear(self.I_QD_CLEAR_ACCOUNT_INPUT)

            self.screenshot()
            if o_account.ocr(self.device.image) not in '请输入4399账号':
                logger.info("账号输入框没清空")
                continue

            # 定位账号输入框并点击激活
            self.click(click_account)
            time.sleep(1)

            # 输入账号
            self.device.adb.shell(f"input text {account}")
            time.sleep(1)

            self.screenshot()
            if o_account.ocr(self.device.image) not in '请输入4399账号':
                logger.info(f"账号输入成功")
            else:
                logger.warning(f"账号输入失败")
                continue

            # 定位密码输入框并点击激活
            self.click(click_password)
            time.sleep(1)

            # 清空密码输入框内容
            self.ui_click_center_until_disappear(self.I_QD_CLEAR_PASSWORD_INPUT)

            self.screenshot()
            if o_password.ocr(self.device.image) not in '请输入密码':
                logger.info("密码输入框没清空")
                continue

            # 输入密码
            self.device.adb.shell(f"input text {password}")
            time.sleep(1)

            self.screenshot()
            if o_password.ocr(self.device.image) not in '请输入密码':
                logger.info(f"密码输入成功")
                break
            else:
                logger.warning(f"密码输入失败")
                continue

        # 点击同意协议
        self.ui_click(self.I_QD_NO_AGREED, self.I_QD_AGREED, interval=1)

        # 点击登录按钮
        self.ui_click(self.I_LOGIN_IN, self.I_CHECK_LOGIN_FORM, interval=1.5)
        return None

    def ui_click_until_disappear(self, click, interval: float = 1, stop: RuleImage | RuleGif = None):
        """
        重写原ui_click_until_disappear方法,增加stop参数
        点击一个按钮直到stop消失
        如果click为RuleOcr ,直接当作RuleClick点击,不会进行ocr识别,
        @param interval:
        @param click:
        @param stop:
        @type stop:
        @return:
        """
        if (isinstance(click, RuleImage) or isinstance(click, RuleGif)) and (stop is None):
            stop = click
        while 1:
            self.screenshot()
            if not self.appear(stop):
                break
            if isinstance(click, RuleImage) or isinstance(click, RuleGif):
                self.appear_then_click(click, interval=interval)
                continue
            elif isinstance(click, RuleClick):
                self.click(click, interval)
                continue
            elif isinstance(click, RuleOcr):
                self.click(click)
                continue

    def ui_click_center_until_disappear(self, click, interval: float = 1, stop: RuleImage | RuleGif = None):
        """
        重写原ui_click_until_disappear方法,增加stop参数
        点击一个按钮直到stop消失
        如果click为RuleOcr ,直接当作RuleClick点击,不会进行ocr识别,
        @param interval:
        @param click:
        @param stop:
        @type stop:
        @return:
        """
        if (isinstance(click, RuleImage) or isinstance(click, RuleGif)) and (stop is None):
            stop = click
        while 1:
            self.screenshot()
            if not self.appear(stop):
                break
            if isinstance(click, RuleImage) or isinstance(click, RuleGif):
                if self.appear(click, interval=interval):
                    x, y = click.coord_center()
                    self.device.click(x=x, y=y, control_name=click.name)
                continue
            elif isinstance(click, RuleClick):
                self.click(click, interval)
                continue
            elif isinstance(click, RuleOcr):
                self.click(click)
                continue
