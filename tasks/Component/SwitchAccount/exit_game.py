from module.logger import logger
from tasks.Component.SwitchAccount.assets import SwitchAccountAssets
from tasks.base_task import BaseTask


class ExitGame(BaseTask, SwitchAccountAssets):

    def exitGame(self):
        logger.info("start game exit")
        # 打开该页面比较慢 如果interval短 将发生异常
        self.ui_click(self.C_SA_EG_PROFILE_PHOTO, self.I_SA_USER_CENTER_PROFILE, 3)
        while 1:
            self.screenshot()
            if self.appear(self.I_CHECK_LOGIN_FORM):
                logger.info("[角色] 退出游戏")
                break
            if self.appear_then_click(self.I_SA_USER_CENTER, interval=2):
                continue
            if self.appear_then_click(self.I_SA_SWITCH_ACCOUNT_BTN, interval=2):
                continue
            if self.appear_then_click(self.I_CHANGE_ACCOUNT, interval=2):
                continue
