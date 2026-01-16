# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey

from module.logger import logger

from tasks.RichMan.config import MedalRoom
from tasks.RichMan.mall.friendship_points import FriendshipPoints


class Medal(FriendshipPoints):

    def execute_medal(self, con: MedalRoom = None):
        logger.hr('勋章商店', 2)
        if not con:
            con = self.config.rich_man.medal_room
        if not con.enable:
            logger.info('Medal is not enable')
            return
        self._enter_medal()

        check_money = con.check_money

        # 黑蛋
        if con.black_daruma:
            logger.hr('勋章购买黑蛋', 3)
            self.buy_mall_one(buy_button=self.I_ME_BLACK, remain_number=False, buy_check=self.I_ME_CHECK_BLACK,
                              money_ocr=self.O_MALL_RESOURCE_3, buy_money=480, check_money=check_money)
        # 蓝票
        if con.mystery_amulet:
            logger.hr('勋章购买蓝票', 3)
            self.buy_mall_one(buy_button=self.I_ME_BLUE, remain_number=False, buy_check=self.I_ME_CHECK_BLUE,
                              money_ocr=self.O_MALL_RESOURCE_3, buy_money=180, check_money=check_money)
        # 体力100
        if con.ap_100:
            logger.hr('勋章购买体力100', 3)
            self.buy_mall_one(buy_button=self.I_ME_AP, remain_number=False, buy_check=self.I_ME_CHECK_AP,
                              money_ocr=self.O_MALL_RESOURCE_3, buy_money=120, check_money=check_money)

        # 两颗白蛋
        if con.white_daruma:
            logger.hr('勋章购买两颗白蛋', 3)
            self.buy_mall_more(buy_button=self.I_ME_WHITE, remain_number=False, money_ocr=self.O_MALL_RESOURCE_3,
                               buy_number=2, buy_max=2, buy_money=100, check_money=check_money)
        # 十张挑战券
        if con.challenge_pass:
            logger.hr('勋章购买挑战券', 3)
            self.buy_mall_more(buy_button=self.I_ME_CHALLENGE_PASS, remain_number=False,
                               money_ocr=self.O_MALL_RESOURCE_3,
                               buy_number=con.challenge_pass, buy_max=10, buy_money=30, check_money=check_money)
        # 红蛋
        if con.red_daruma:
            logger.hr('勋章购买红蛋', 3)
            self.buy_mall_more(buy_button=self.I_ME_RED, remain_number=False,
                               money_ocr=self.O_MALL_RESOURCE_3,
                               buy_number=con.red_daruma, buy_max=99, buy_money=30, check_money=check_money)
        # 破碎的咒符
        if con.broken_amulet:
            logger.hr('勋章购买破碎的咒符', 3)
            self.buy_mall_more(buy_button=self.I_ME_BROKEN, remain_number=False,
                               money_ocr=self.O_MALL_RESOURCE_3,
                               buy_number=con.broken_amulet, buy_max=99, buy_money=20, check_money=check_money)
        self.save_image()
        # 随机御魂
        if con.random_soul:
            logger.hr('勋章购买随机御魂', 3)
            self.buy_one_souls(self.I_ME_SOULS, self.I_ME_CHECK_SOULS)
            self.save_image()

    def buy_one_souls(self, start_click, check_image):
        """
        购买一个物品
        :param check_image: 购买确认时候的图片
        :param start_click: 开始点击
        :return:
        """

        logger.hr(start_click.name, 3)
        self.screenshot()
        # 检查是否出现了购买按钮
        logger.info(f'before buy_button.roi_front: {start_click.roi_front}')
        result = start_click.match(self.device.image)
        if not result:
            logger.warning(f'未匹配到目标: [{start_click}]')
            return False
        logger.info(f'after buy_button.roi_front: {start_click.roi_front}')
        if not self.appear_rgb(start_click, difference=10):
            logger.warning('Buy button is not appear')
            return False
        while 1:
            self.screenshot()

            if self.appear(check_image):
                break
            if self.appear_then_click(start_click, interval=1):
                continue
        while 1:
            self.screenshot()

            result = start_click.match_gray(self.device.image)
            if result:
                if self.appear(start_click) and not self.appear_rgb(start_click, difference=10):
                    logger.warning('Buy button end')
                    return True

            if self.click(self.C_BUY_ONE, interval=2.8):
                continue

        return True


if __name__ == '__main__':
    from module.config.config import Config

    c = Config('du')
    t = Medal(c)

    t.execute_medal()

    # t.buy_one_souls(RichManAssets.I_ME_SOULS, RichManAssets.I_ME_CHECK_SOULS)
