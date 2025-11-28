from module.config.config import Config
from module.device.device import Device
from module.logger import logger
from tasks.Component.SwitchAccount.assets import SwitchAccountAssets
from tasks.Component.SwitchAccount.exit_game import ExitGame
from tasks.Component.SwitchAccount.login_account import LoginAccount
from tasks.Component.SwitchAccount.switch_account_config import AccountInfo
from tasks.GameUi.game_ui import GameUi
from tasks.GameUi.page import page_main, page_login
from tasks.Restart.login import LoginHandler


class SwitchAccount(LoginAccount, ExitGame, GameUi, SwitchAccountAssets):

    def __init__(self, config: Config, to: AccountInfo, frm: AccountInfo = None):
        """

        @param config:
        @type config:
        @param device:
        @type device:
        @param to: 要登录的账号信息
        @type to:
        @param frm: 上一个账号信息 ,避免关键字from
        @type frm:
        """
        super().__init__(config)
        self.to_account_info = to
        self.from_account_info = frm

    def switchAccount(self):
        logger.info("[角色] 开始切换 %s-%s",  self.to_account_info.svr, self.to_account_info.character)
        # 判断所处界面
        curPage = self.ui_get_current_page()

        if curPage != page_login and curPage != page_main:
            self.ui_goto_page(page_main)
            curPage = self.ui_get_current_page()
        if curPage == page_main:
            self.exitGame()

        # 处于登录界面
        if not self.login(self.to_account_info):
            return False
        logger.info("[角色] %s-%s 登陆成功!", self.to_account_info.svr, self.to_account_info.character)
        # 处理位于登录界面各种奇葩弹窗
        login_handler = LoginHandler(config=self.config)
        login_handler.set_specific_usr(self.to_account_info.svr)
        login_handler.app_handle_login()

        return True


if __name__ == '__main__':
    config = Config('4399')
    device = Device(config)
    account_list = [
        # AccountInfo(account="178****7164", account_alias="178****7164", apple_or_android=True, character="浙沥沥、下雨", svr="全球国际区"),
        # AccountInfo(account="187****4867", account_alias="187****4867", apple_or_android=True, character="紫芪", svr="破晓之樱"),
        AccountInfo(account="xilili1", account_alias="xilili1", password="ljx112757", enable_wy=False, apple_or_android=True, character="下雨1", svr="樱之华"),
        AccountInfo(account="xilili2s", account_alias="xilili2s", password="ljx112757", enable_wy=False, apple_or_android=True, character="下雨2", svr="樱之华"),
        AccountInfo(account="xilili3", account_alias="xilili3", password="ljx112757", enable_wy=False, apple_or_android=True, character="下雨3", svr="樱之华"),
        AccountInfo(account="xilili4", account_alias="xilili4", password="ljx112757", enable_wy=False, apple_or_android=True, character="下雨4", svr="樱之华"),
        AccountInfo(account="xilili5", account_alias="xilili5", password="ljx112757", enable_wy=False, apple_or_android=True, character="下雨5", svr="樱之华"),
        AccountInfo(account="xilili6", account_alias="xilili6", password="ljx112757", enable_wy=False, apple_or_android=True, character="下雨6", svr="樱之华"),
        AccountInfo(account="xilili7s", account_alias="xilili7s", password="ljx112757", enable_wy=False, apple_or_android=True, character="下雨7", svr="樱之华"),
        AccountInfo(account="xilili8", account_alias="xilili8", password="ljx112757", enable_wy=False, apple_or_android=True, character="下雨8", svr="樱之华"),
        AccountInfo(account="xilili9", account_alias="xilili9", password="ljx112757", enable_wy=False, apple_or_android=True, character="下雨9", svr="樱之华"),
        AccountInfo(account="xilili10", account_alias="xilili10", password="ljx112757", enable_wy=False, apple_or_android=True, character="下雨10", svr="樱之华"),


        # AccountInfo(account="187****4867", account_alias="187****4867", apple_or_android=True, character="三千菟", svr="樱之华"),
        # AccountInfo(account="150****7970", account_alias="150****7970", apple_or_android=True, character="落地反弹", svr="樱之华"),
        # AccountInfo(account="sui94044@163.com", account_alias="sui94044", apple_or_android=True, character="阿岁啊", svr="樱之华"),
        # AccountInfo(account="178****7164", account_alias="178****7164", apple_or_android=True, character="浙沥沥、下雨", svr="破晓之樱"),
        #
        # AccountInfo(account="150****7970", account_alias="150****7970", apple_or_android=True, character="落地反弹", svr="网易一两情相悦"),
        # AccountInfo(account="187****4867", account_alias="187****4867", apple_or_android=True, character="三千卍", svr="旧友新朋"),
        # AccountInfo(account="187****4867", account_alias="187****4867", apple_or_android=True, character="唳莅", svr="灵狐愿"),
        # AccountInfo(account="187****4867", account_alias="187****4867", apple_or_android=True, character="夜玖幻", svr="游梦迷蝶"),
    ]

    for toAccount in account_list:
        sa = SwitchAccount(config, toAccount)
        sa.switchAccount()
