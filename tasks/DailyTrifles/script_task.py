# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
from time import sleep

import copy
import re
from module.base.timer import Timer
from module.exception import TaskEnd
from module.logger import logger
from tasks.Component.GeneralBuff.general_buff import GeneralBuff
from tasks.Component.Summon.summon import Summon
from tasks.DailyTrifles.assets import DailyTriflesAssets
from tasks.DailyTrifles.page import page_store_sign, page_mall_special, page_summon_store, page_shikigami_debris
from tasks.GameUi.page import page_summon, page_guild, page_friends


class ScriptTask(Summon, DailyTriflesAssets, GeneralBuff):
    """ 每日琐事 """

    def run(self):
        con = self.config.daily_trifles.trifles_config
        # 每日召唤
        if con.one_summon:
            self.summon_one()
        # 厕纸
        if con.broken_amulet:
            self._broken_amulet(con.broken_amulet)
        # 集结
        self.massed_run()
        # 召唤商店
        self.run_summon_store()
        # 友情点 （现在已经可以通过庭院任务获取了）
        # if con.friend_love:
        #     self.run_friend_love()
        # 吉闻
        if con.luck_msg:
            self.run_luck_msg()
        # 商店签到
        if con.store_sign:
            self.run_store_sign()
        # 购买寿司体力
        if con.buy_sushi_count > 0:
            self.run_buy_sushi()
        # 招募寮成员
        if con.recruit_members:
            self.run_recruit_members()
        # 抽奖箱抽奖
        if con.lottery_box:
            self.check_lottery_box()
        # 召唤式神碎片
        if con.shikigami_debris:
            self.run_shikigami_debris()

        self.set_next_run('DailyTrifles', success=True, finish=False)
        raise TaskEnd('DailyTrifles')

    def run_shikigami_debris(self):
        self.ui_goto_page(page_shikigami_debris)
        self.ui_click(self.I_PAGE_SHIKIGAMI_DEBRIS, self.I_EXIT_ENSURE1)
        self.ui_click_until_disappear(self.I_EXIT_ENSURE1)

    def check_lottery_box(self):
        self.ui_goto_page(page_guild)
        while 1:
            self.screenshot()
            if self.wait_until_appear_then_click(self.I_LOTTERY_BOX, wait_time=2):
                if self.wait_until_appear(self.I_LOTTERY_BOX_PAGE, wait_time=5):
                    break
            else:
                logger.info(f'未发现抽奖箱')
                return

        while 1:
            self.screenshot()
            if self.ui_reward_appear_click():
                continue
            # 获得奖励
            cu, re, total = self.ocr_result(self.O_LOTTERY_NUMBER)
            if cu + re == total and cu != 0:
                logger.info(f'抽奖次数: [{cu}]')
                self.swipe(self.S_SWIPE_LOTTERY_BOX, interval=5)
                sleep(5)
            else:
                logger.info(f'没有可以抽奖的次数')
                return

    def run_summon_store(self):
        self.ui_goto_page(page_summon_store)
        timer = Timer(3)
        timer.start()
        while 1:
            if timer.reached():
                logger.info('not appear Summon Store')
                return
            self.screenshot()
            if self.appear(self.I_SUMMON_STORE_FREE_OVER):
                break
            if self.appear_then_click(self.I_SUMMON_STORE_FREE_1, interval=1):
                timer.reset()
                continue
            if self.appear_then_click(self.I_SUMMON_STORE_FREE, interval=1):
                sleep(1)
                timer.reset()
                continue
            if self.appear_then_click(self.I_SUMMON_STORE_LUCKY, interval=1):
                timer.reset()
                continue

        click_count = 0
        while click_count < 5:
            self.screenshot()
            if self.ui_reward_appear_click():
                click_count = 0
            if self.appear(self.I_FREE_3_OVER) and self.appear(self.I_FREE_2_OVER) and self.appear(self.I_FREE_1_OVER):
                break
            if self.appear_then_click(self.I_FREE_1, interval=1):
                click_count += 1
                continue
            if self.appear_then_click(self.I_FREE_2, interval=1):
                click_count += 1
                continue
            if self.appear_then_click(self.I_FREE_3, interval=1):
                click_count += 1
                continue
        self.save_image(wait_time=0, task_name='铜铃礼包')

    def massed_run(self):
        self.ui_goto_page(page_summon)
        if not self.appear(self.I_MASSED):
            return

        while 1:
            self.screenshot()
            if self.appear_then_click(self.I_MASSED, interval=1):
                continue
            if self.appear_then_click(self.I_AFTER_ON, interval=1):
                break
            if self.appear(self.I_BATTLE):
                break
            x, y = self.I_AFTER_ON.coord()
            self.device.click(x, y)

        click_count = 0
        while click_count <= 3:
            self.screenshot()
            if self.appear_then_click(self.I_MASSED, interval=1):
                continue
            if self.appear_then_click(self.I_AFTER_ON, interval=1):
                continue
            if self.appear_then_click(self.I_BATTLE, interval=1):
                self.device.stuck_record_add('BATTLE_STATUS_S')
                click_count += 1
                continue
            if self.appear_then_click(self.I_CLICK_ANY_POSITION, interval=1):
                continue
            if self.appear_then_click(self.I_WIN, interval=1):
                click_count = 0
                continue

    def run_luck_msg(self):
        self.ui_goto_page(page_friends)
        while 1:
            self.screenshot()
            if self.appear(self.I_LUCK_TITLE):
                break
            if self.appear_then_click(self.I_FRIENDSHIP_UP, interval=1):
                continue
            if self.appear_then_click(self.I_LUCK_MSG, interval=1):
                continue
        logger.info('Start luck msg')
        check_timer = Timer(5)
        check_timer.start()
        while 1:
            self.screenshot()

            if self.appear_then_click(self.I_CLICK_BLESS, interval=1):
                continue
            if self.appear_then_click(self.I_ONE_CLICK_BLESS, interval=1):
                continue
            if self.ui_reward_appear_click():
                logger.info('Get reward of luck msg')
                break
            if check_timer.reached():
                self.save_image(content="收取吉闻超时", wait_time=0, image_type=True, push_flag=True)
                logger.warning('There is no any luck msg')
                break

        self.ui_click(self.I_BACK_RED, self.I_CHECK_MAIN)

    def run_friend_love(self):
        self.ui_goto_page(page_friends)
        while 1:
            self.screenshot()
            if self.appear(self.I_L_LOVE):
                break
            if self.appear_then_click(self.I_FRIENDSHIP_UP, interval=1):
                continue
            if self.appear_then_click(self.I_L_FRIENDS, interval=1):
                continue
            if self.appear_then_click(self.I_L_FRIENDS_SELECT, interval=1):
                continue
        logger.info('Start friend love')
        check_timer = Timer(5)
        check_timer.start()
        while 1:
            self.screenshot()

            if self.appear_then_click(self.I_L_COLLECT, interval=1):
                continue
            if self.ui_reward_appear_click():
                logger.info('Get reward of friend love')
                break
            if check_timer.reached():
                self.save_image(content="收取友情点超时", wait_time=0, image_type=True, push_flag=True)
                logger.warning('There is no any love')
                break

        self.ui_click(self.I_BACK_RED, self.I_CHECK_MAIN)

    def run_store_sign(self):
        self.ui_goto_page(page_store_sign)
        timer = Timer(5)
        timer.start()
        while 1:
            if timer.reached():
                self.save_image(content="每日签到超时", push_flag=True, wait_time=0, image_type=True)
                return
            self.reject_invite()
            self.screenshot()
            if self.appear(self.I_GIFT_SIGN):
                break
            if self.appear_then_click(self.I_GIFT_RECOMMEND, interval=1):
                continue
        logger.info('Enter store sign')
        sleep(1)  # 等个动画
        self.reject_invite()
        self.screenshot()
        if not self.appear(self.I_GIFT_SIGN):
            logger.warning('There is no gift sign')
            self.save_image(content="未发现每日签到", push_flag=True, wait_time=0, image_type=True)
            return

        if self.ui_get_reward(self.I_GIFT_SIGN, click_interval=2.5):
            logger.info('Get reward of gift sign')

    def run_buy_sushi(self):

        # 进入Special
        self.ui_goto_page(page_mall_special)

        def detect_buy_count(base_element) -> (int, int):
            # 返回count,price
            MAX_PRICE = 9999
            MAX_COUNT = 9999
            roi = copy.deepcopy(base_element.roi_front)
            roi[0] = roi[0] + roi[2]
            roi[1] = roi[1] + roi[3] - 30
            roi[2] = 60
            roi[3] = 30
            self.O_STORE_SUSHI_PRICE.roi = roi
            _price = self.O_STORE_SUSHI_PRICE.detect_text(self.device.image)
            # 保守策略，避免OCR错误购买
            try:
                _price = int(_price)
            except Exception as e:
                _price = MAX_PRICE

            if _price < 60:
                return 0, MAX_PRICE
            _count = (_price - 60) / 20
            return _count, _price

        roi = None
        # 购买体力
        while 1:
            self.screenshot()
            # count, price = detect_buy_count(roi)
            # if count >= self.config.model.daily_trifles.trifles_config.buy_sushi_count:
            #     break
            if self.appear(self.I_STORE_COST_TYPE_JADE):
                count, price = detect_buy_count(self.I_STORE_COST_TYPE_JADE)
                if count >= self.config.daily_trifles.trifles_config.buy_sushi_count:
                    break
                self.ui_click_until_disappear(self.I_STORE_COST_TYPE_JADE, interval=2)
                logger.info(f"Buy Sushi With {price} Jade")
                continue

            if self.appear(self.I_SPECIAL_SUSHI):
                # 此处确定当前购买体力所需勾玉数量的位置,用于后续识别
                count, price = detect_buy_count(self.I_SPECIAL_SUSHI)
                if count >= self.config.daily_trifles.trifles_config.buy_sushi_count:
                    break
                self.ui_click(self.I_SPECIAL_SUSHI, stop=self.I_STORE_COST_TYPE_JADE, interval=2)
                continue
        return

    def run_recruit_members(self):
        self.ui_goto_page(page_guild)
        flush_count = 0
        timer = Timer(5)
        timer.start()
        while flush_count < 5:
            self.screenshot()
            if timer.reached():
                self.push_notify(content="招募寮成员超时，或没有管理权限")
                return
            if self.appear_then_click(self.I_POSTS):
                timer.reset()
                continue
            if self.appear_then_click(self.I_MEMBER_FLUSH, interval=1):
                flush_count += 1
                timer.reset()
                continue
            if self.appear_then_click(self.I_MEMBER_ADD, interval=0.5):
                timer.reset()
                continue
            if self.appear_then_click(self.I_RECRUIT_MEMBERS, interval=1):
                timer.reset()
                continue
            if self.appear_then_click(self.I_GUILD_MANAGEMENT_1, interval=1):
                timer.reset()
                continue
            if self.appear_then_click(self.I_GUILD_MANAGEMENT, interval=1):
                continue
            if self.appear_then_click(self.I_GUILD_INFO, interval=1):
                timer.reset()
                continue
        logger.info('Enter recruit members')

    def _broken_amulet(self, num: int):
        """

        :param num:
        :return:
        """
        if num <= 0:
            logger.warning('No broken amulet')
            return

        def click_confirm():
            self.wait_until_appear(self.I_BM_CONFIRM)
            while 1:
                self.screenshot()
                if not self.appear(self.I_BM_CONFIRM):
                    break
                else:
                    self.appear_then_click(self.I_BM_CONFIRM, interval=1)
            logger.info('Exit broken amulet')

        logger.hr('Broken amulet')
        self.ui_goto_page(page_summon)
        self.screenshot()
        number = self.O_BA_AMOUNT_1.ocr(self.device.image)
        if number == 0:
            logger.warning('No broken amulet')
            return
        num = min(number, num)
        logger.info(f'Broken amulet: {number}')
        count = 0
        self.wait_until_appear(self.I_BM_ENTER)
        while 1:
            self.screenshot()
            if not self.appear(self.I_BM_ENTER):
                break
            if self.appear_then_click(self.I_BM_ENTER, interval=1):
                continue
        count += 10
        logger.info('Enter broken amulet')
        while 1:
            self.screenshot()
            sleep(0.5)

            if not self.appear(self.I_BM_CONFIRM):
                continue
            if count >= num:
                logger.info(f'Broken amulet finished: {count}')
                click_confirm()
                break
            cu, re, total = self.O_BA_AMOUNT_2.ocr(self.device.image)
            if cu <= 10 and total == 10:
                logger.info(f'Broken amulet count: {count}. Current: {cu}. Total: {total}')
                click_confirm()
                break
            if self.appear_then_click(self.I_BM_AGAIN, interval=1):
                logger.info(f'Broken amulet count: {count}. Current: {cu}')
                self.device.click_record_clear()
                count += 10
                continue


if __name__ == '__main__':
    from module.config.config import Config

    c = Config('4399-1')
    t = ScriptTask(c)

    # t.run()
    t.run_shikigami_debris()
