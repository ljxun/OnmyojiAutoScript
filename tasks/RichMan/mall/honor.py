# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
import time

from module.logger import logger
from tasks.RichMan.config import HonorRoom
from tasks.RichMan.mall.special import Special


class Honor(Special):

    def execute_honor(self, con: HonorRoom = None):
        logger.hr('荣誉商店', 2)
        if not con:
            con = self.config.rich_man.honor_room
        if not con.enable:
            logger.info('Honor is not enable')
            return
        self._enter_honor()
        self._honor_mystery_amulet(con.mystery_amulet, con.check_money)
        self._honor_black_daruma_scrap(con.black_daruma_scrap, con.check_money)
        self.save_image()

    def _honor_mystery_amulet(self, enable: bool = False, check_money: bool = True):
        logger.hr('荣誉点购买蓝票', 3)
        if not enable:
            logger.info('Buy mystery amulet is disabled')
            return

        self.screenshot()
        if not self.appear(self.I_HONOR_BLUE):
            logger.warning('No appear mystery amulet')
            return
        # 检查剩余数量
        # remain_number = self.O_HONOR_BLUE.ocr(self.device.image)
        remain_number = self._special_check_remain(self.I_HONOR_BLUE)
        if not isinstance(remain_number, int):
            logger.warning('Can not get remain number')
            return
        if remain_number == 0:
            logger.warning(f'No blue honor {remain_number}')
            return
        if check_money:
            if not self.mall_check_money(4, 1500):
                logger.warning('No enough money')
                return
        # 点击购买
        self.buy_more(self.I_HONOR_BLUE)
        time.sleep(1)

    def _honor_black_daruma_scrap(self, enable: bool = False, check_money: bool = True):
        logger.hr('荣誉点购买黑碎', 3)
        if not enable:
            logger.info('Buy black daruma scrap is disabled')
            return

        self.screenshot()
        if not self.appear(self.I_HONOR_BLACK):
            logger.warning('No appear black daruma scrap')
            return
        # 检查剩余数量
        # remain_number = self.O_HONOR_BLACK.ocr(self.device.image)
        remain_number = self._special_check_remain(self.I_HONOR_BLACK)
        if not isinstance(remain_number, int):
            logger.warning('Can not get remain number')
            return
        if remain_number == 0:
            logger.warning(f'No black daruma scrap {remain_number}')
            return
        if check_money:
            if not self.mall_check_money(4, 540):
                logger.warning('No enough money')
                return
        # 点击购买
        self.buy_more(self.I_HONOR_BLACK)
        time.sleep(0.5)


if __name__ == '__main__':
    from module.config.config import Config

    c = Config('mi')
    t = Honor(c)

    t._honor_mystery_amulet(True)
