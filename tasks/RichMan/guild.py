# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
import time

import re
from module.atom.image import RuleImage
from module.logger import logger
from tasks.Component.Buy.buy import Buy
from tasks.GameUi.game_ui import GameUi
from tasks.RichMan.assets import RichManAssets
from tasks.RichMan.page import page_medal_store, page_guid_procurement


class Guild(Buy, GameUi, RichManAssets):

    def execute_guild(self, con):

        if not con.enable:
            return
        logger.hr('功勋商店', 1)
        self.ui_goto_page(page_medal_store)

        logger.info('Enter guild store success')
        time.sleep(0.5)

        # 功勋礼包
        if con.guild_libao:
            item_info = {
                'name': '礼包',
                'image': self.I_LIAOBAO,
                'cost': 0,
                'buy_method': 'buy_more'
            }
            self._guild_item_purchase(item_info)

        # 风铃
        if con.guild_fl:
            item_info = {
                'name': '风铃',
                'image': self.I_FL,
                'cost': 0,
                'buy_method': 'buy_more',
                'double_buy': True
            }
            self._guild_item_purchase(item_info)

        # 经验手札
        if con.guild_exp:
            item_info = {
                'name': '经验御札',
                'image': self.I_EXP,
                'cost': 0,
                'buy_method': 'buy_more'
            }
            self._guild_item_purchase(item_info)

        # 御魂
        if con.guild_yuhun:
            item_info = {
                'name': '御魂',
                'image': self.I_YUHUN,
                'cost': 0,
                'buy_method': 'buy_more'
            }
            self._guild_item_purchase(item_info)

        # 蓝票
        if con.mystery_amulet:
            item_info = {
                'name': '蓝票',
                'image': self.I_GUILD_BLUE,
                'cost': 240,
                'buy_method': 'buy_more'
            }
            self._guild_item_purchase(item_info)

        # 黑碎
        if con.black_daruma_scrap:
            item_info = {
                'name': '黑碎',
                'image': self.I_GUILD_SCRAP,
                'cost': 200,
                'buy_method': 'buy_one',
                'check_image': self.I_GUILD_CHECK_SCRAP,
                'confirm_image': self.I_GUILD_BUY_SCRAP
            }
            self._guild_item_purchase(item_info)

        # 皮肤券
        if con.skin_ticket and con.skin_ticket > 0:
            item_info = {
                'name': '皮肤券',
                'image': self.I_GUILD_SKIN,
                'cost': 50,
                'buy_method': 'buy_more'
            }
            self._guild_item_purchase(item_info)
        # 保存截图
        self.save_image()

    def execute_guild_procurement(self, con):
        if not con.enable:
            return
        logger.hr('开始 寮内采办', 1)
        self.ui_goto_page(page_guid_procurement)

        logger.info('Enter guild procurement success')
        time.sleep(0.5)

        # 购买同心奖箱
        if con.buy_lottery_box:
            item_info = {
                'name': '同心奖箱',
                'image': self.I_LOTTERY_BOX,
                'cost': 0,
                'buy_method': 'buy_lottery_box',
                'check_image': self.I_LOTTERY_BOX_BUY
            }
            self._guild_item_purchase(item_info)

    def check_remain(self, image: RuleImage) -> int:
        self.O_GUILD_REMAIN.roi[0] = image.roi_front[0] - 38
        self.O_GUILD_REMAIN.roi[1] = image.roi_front[1] + 83
        logger.info(f'Image roi {image.roi_front}')
        logger.info(f'Image roi {self.O_GUILD_REMAIN.roi}')
        self.screenshot()
        result = self.O_GUILD_REMAIN.ocr(self.device.image)
        logger.warning(result)
        result = result.replace('？', '2').replace('?', '2').replace(':', '；')

        try:
            # 改进的正则表达式，增加容错性
            # 匹配包含"剩余数量"和数字的模式，允许中间有各种可能的错误字符
            patterns = [
                r'本周?剩余数量(\d+)',      # 匹配"本周剩余数量"或"本剩余数量"
                r'本[l|周]?剩余数量(\d+)',   # 匹配"本l剩余数量"或"本周剩余数量"
                r'剩余数量(\d+)',          # 直接匹配"剩余数量"
                r'本.*?剩余.*?数量(\d+)',    # 使用通配符匹配中间可能的错误字符
            ]

            found = False
            for pattern in patterns:
                match = re.search(pattern, result)
                if match:
                    result = int(match.group(1))
                    found = True
                    break

            if not found:
                # 如果所有模式都匹配失败，尝试更宽松的模式：查找"本"和"数量"之间的数字
                alt_match = re.search(r'本.*?数量(\d+)', result)
                if alt_match:
                    result = int(alt_match.group(1))
                    found = True

            if not found:
                raise ValueError(f"No matching pattern found in: {result}")

        except (IndexError, ValueError):
            self.save_image(wait_time=0, image_type=True, push_flag=True, content=f"{result}")
            result = 0

        logger.info('Remain: %s' % result)
        return int(result)

    # 整合的通用购买方法
    def _guild_item_purchase(self, item_info: dict):
        """
        通用公会物品购买函数
        """
        name = item_info.get('name', '')
        image = item_info.get('image')
        cost = item_info.get('cost', 0)
        buy_method = item_info.get('buy_method', 'buy_more')
        check_image = item_info.get('check_image')
        confirm_image = item_info.get('confirm_image')
        double_buy = item_info.get('double_buy', False)
        buy_count = item_info.get('buy_count', 1)

        logger.hr(f'开始购买{name}', 3)
        self.screenshot()

        # 检查金钱（如果有设置价格）
        if cost > 0 and not self.buy_check_money(self.O_GUILD_TOTAL, cost):
            return False

        swipe_down = True
        swipe_count = 0
        while 1:
            self.screenshot()
            # 匹配物品图标
            result = image.match(self.device.image)
            if result:
                break
            if swipe_count >= 3:
                result = False
                break
            # 功勋商店 购买皮肤券 现在问题是皮肤券作为下滑判断标志,下滑过程中roi_front[1]发生了变化,
            # 导致后续识别本周剩余数量位置偏差,现在解决方案是创建一个相同属性的I_GUILD_SKIN_CHECK 来作为判断标志
            if self.appear(self.I_GUILD_STORE_END):
                swipe_down = False
                swipe_count += 1
            if self.appear(self.I_GUILD_STORE_TOP):
                swipe_down = True
            if swipe_down and self.swipe(self.S_GUILD_STORE_DOWN, interval=1.5, duration=1, wait_up_time=1):
                continue
            if not swipe_down and self.swipe(self.S_GUILD_STORE_UP, interval=1.5, duration=1, wait_up_time=1):
                continue

        # 匹配物品图标
        if not result:
            logger.warning(f'未识别到{name}')
            self.save_image(wait_time=0, image_type=True, push_flag=True, content=f'未识别到{name}')
            return False

        # 检查剩余数量
        number = self.check_remain(image)
        if number == 0:
            logger.warning(f'{name}购买数量不足')
            return False

        # 执行购买
        if buy_method == 'buy_one':
            for _ in range(buy_count):
                self.buy_one(image, check_image, confirm_image)
                time.sleep(0.5)
        elif buy_method == 'buy_lottery_box':
            self.buy_lottery_box(image, check_image, confirm_image)
            time.sleep(0.5)
        else:
            for _ in range(buy_count):
                self.buy_more(image)
                time.sleep(0.5)

        # 特殊处理：某些物品需要购买两次
        if double_buy:
            time.sleep(0.5)
            self.buy_more(image)
            time.sleep(0.5)
        return True


if __name__ == '__main__':
    from module.config.config import Config

    c = Config('4399-1')
    # d = Device(c)
    t = Guild(c)

    # t._guild_skin_ticket(5)
    # t.execute_guild_procurement(con=c.rich_man.guild_procurement)
    t.execute_guild(c.rich_man.guild_store)
