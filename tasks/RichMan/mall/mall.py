# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
from module.logger import logger
from tasks.GameUi.page import page_mall
from tasks.RichMan.mall.bondlings import Bondlings
from tasks.RichMan.mall.charisma import Charisma
from tasks.RichMan.mall.consignment import Consignment
from tasks.RichMan.mall.honor import Honor
from tasks.RichMan.mall.medal import Medal
from tasks.RichMan.mall.scales import Scales


class Mall(Medal, Charisma, Honor, Consignment, Scales, Bondlings):


    def execute_mall(self):
        logger.hr('Mall', 1)
        self.ui_goto_page(page_mall, confirm_wait=2.5)

        # 寄售屋
        self.execute_consignment()
        # 蛇皮
        self.execute_scales()
        # 契灵
        self.execute_bondlings()

        # 杂货铺
        # 特殊
        self.execute_special()
        # 荣誉
        self.execute_honor()
        # 友情点
        self.execute_friendship()
        # 勋章
        self.execute_medal()
        # 魅力
        self.execute_charisma()

        # 退出
        # self.back_mall()
