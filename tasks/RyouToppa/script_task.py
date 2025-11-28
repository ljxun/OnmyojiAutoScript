# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
import time

import random
from datetime import datetime, timedelta
from module.atom.image_grid import ImageGrid
from module.base.utils import point2str
from module.exception import TaskEnd
from module.logger import logger
from tasks.Component.GeneralBattle.general_battle import GeneralBattle
from tasks.Component.SwitchSoul.switch_soul import SwitchSoul
from tasks.Component.config_base import Time
from tasks.GameUi.page import page_kekkai_toppa
from tasks.RealmRaid.assets import RealmRaidAssets
from tasks.RyouToppa.assets import RyouToppaAssets

""" 寮突破 """

area_map = (
    {
        "fail_sign": (RyouToppaAssets.I_AREA_1_IS_FAILURE_NEW, RyouToppaAssets.I_AREA_1_IS_FAILURE),
        "rule_click": RyouToppaAssets.C_AREA_1,
        "finished_sign": (RyouToppaAssets.I_AREA_1_FINISHED, RyouToppaAssets.I_AREA_1_FINISHED_NEW)
    },
    {
        "fail_sign": (RyouToppaAssets.I_AREA_2_IS_FAILURE_NEW, RyouToppaAssets.I_AREA_2_IS_FAILURE),
        "rule_click": RyouToppaAssets.C_AREA_2,
        "finished_sign": (RyouToppaAssets.I_AREA_2_FINISHED, RyouToppaAssets.I_AREA_2_FINISHED_NEW)
    },
    {
        "fail_sign": (RyouToppaAssets.I_AREA_3_IS_FAILURE_NEW, RyouToppaAssets.I_AREA_3_IS_FAILURE),
        "rule_click": RyouToppaAssets.C_AREA_3,
        "finished_sign": (RyouToppaAssets.I_AREA_3_FINISHED, RyouToppaAssets.I_AREA_3_FINISHED_NEW)
    },
    {
        "fail_sign": (RyouToppaAssets.I_AREA_4_IS_FAILURE_NEW, RyouToppaAssets.I_AREA_4_IS_FAILURE),
        "rule_click": RyouToppaAssets.C_AREA_4,
        "finished_sign": (RyouToppaAssets.I_AREA_4_FINISHED, RyouToppaAssets.I_AREA_4_FINISHED_NEW)
    },
    {
        "fail_sign": (RyouToppaAssets.I_AREA_5_IS_FAILURE_NEW, RyouToppaAssets.I_AREA_5_IS_FAILURE),
        "rule_click": RyouToppaAssets.C_AREA_5,
        "finished_sign": (RyouToppaAssets.I_AREA_5_FINISHED, RyouToppaAssets.I_AREA_5_FINISHED_NEW)
    },
    {
        "fail_sign": (RyouToppaAssets.I_AREA_6_IS_FAILURE_NEW, RyouToppaAssets.I_AREA_6_IS_FAILURE),
        "rule_click": RyouToppaAssets.C_AREA_6,
        "finished_sign": (RyouToppaAssets.I_AREA_6_FINISHED, RyouToppaAssets.I_AREA_6_FINISHED_NEW)
    },
    # {
    #     "fail_sign": (RyouToppaAssets.I_AREA_7_IS_FAILURE_NEW, RyouToppaAssets.I_AREA_7_IS_FAILURE),
    #     "rule_click": RyouToppaAssets.C_AREA_7,
    #     "finished_sign": (RyouToppaAssets.I_AREA_7_FINISHED, RyouToppaAssets.I_AREA_7_FINISHED_NEW)
    # },
    # {
    #     "fail_sign": (RyouToppaAssets.I_AREA_8_IS_FAILURE_NEW, RyouToppaAssets.I_AREA_8_IS_FAILURE),
    #     "rule_click": RyouToppaAssets.C_AREA_8,
    #     "finished_sign": (RyouToppaAssets.I_AREA_8_FINISHED, RyouToppaAssets.I_AREA_8_FINISHED_NEW)
    # }
)


def random_delay(min_value: float = 1.0, max_value: float = 2.0, decimal: int = 1):
    """
    生成一个指定范围内的随机小数
    """
    random_float_in_range = random.uniform(min_value, max_value)
    return (round(random_float_in_range, decimal))


class ScriptTask(GeneralBattle, SwitchSoul, RyouToppaAssets):
    medal_grid: ImageGrid = None
    area_index = 0

    def run(self):
        """
        执行
        :return:
        """
        ryou_config = self.config.ryou_toppa
        time_limit: Time = ryou_config.raid_config.limit_time
        time_delta = timedelta(hours=time_limit.hour, minutes=time_limit.minute, seconds=time_limit.second)
        self.medal_grid = ImageGrid([RealmRaidAssets.I_MEDAL_5, RealmRaidAssets.I_MEDAL_4, RealmRaidAssets.I_MEDAL_3,
                                     RealmRaidAssets.I_MEDAL_2, RealmRaidAssets.I_MEDAL_1, RealmRaidAssets.I_MEDAL_0])

        if ryou_config.switch_soul_config.enable:
            self.run_switch_soul(ryou_config.switch_soul_config.switch_group_team)

        if ryou_config.switch_soul_config.enable_switch_by_name:
            self.run_switch_soul_by_name(ryou_config.switch_soul_config.group_name, ryou_config.switch_soul_config.team_name)

        self.ui_goto_page(page_kekkai_toppa)
        ryou_toppa_start_flag = True
        ryou_toppa_success_penetration = False
        ryou_toppa_admin_flag = False
        # 点击突破
        while 1:
            self.screenshot()
            if self.appear_then_click(RealmRaidAssets.I_REALM_RAID, interval=1):
                continue
            if self.appear(self.I_REAL_RAID_REFRESH, threshold=0.8):
                if self.appear_then_click(self.I_RYOU_TOPPA, interval=1):
                    continue
            # 攻破阴阳寮，说明寮突已开，则退出
            elif self.appear(self.I_SUCCESS_PENETRATION, threshold=0.8):
                ryou_toppa_start_flag = True
                ryou_toppa_success_penetration = True
                break
            # 出现选择寮突说明寮突未开
            elif self.appear(self.I_SELECT_RYOU_BUTTON, threshold=0.8):
                ryou_toppa_start_flag = False
                ryou_toppa_admin_flag = True
                break
            # 出现晴明说明寮突未开
            elif self.appear(self.I_NO_SELECT_RYOU, threshold=0.8):
                ryou_toppa_start_flag = False
                break
            # 出现寮奖励， 说明寮突已开
            elif self.appear(self.I_RYOU_REWARD, threshold=0.8) or self.appear(self.I_RYOU_REWARD_90, threshold=0.8):
                ryou_toppa_start_flag = True
                break

        logger.attr('寮突破开启标志', ryou_toppa_start_flag)
        logger.attr('寮突破完全攻破标志', ryou_toppa_success_penetration)
        # 寮突未开 并且有权限， 开开寮突，没有权限则标记失败
        if not ryou_toppa_start_flag:
            if ryou_config.raid_config.ryou_access and ryou_toppa_admin_flag:
                # 作为寮管理，开启今天的寮突
                logger.info("作为寮管理，尝试开启寮突破。")
                self.start_ryou_toppa()
            else:
                logger.info("寮突破未开启且您是寮成员。")
                self.set_next_run(task='RyouToppa', finish=True, server=True, success=False)
                self.set_next_run_talismanpass()

        # 100% 攻破, 第二天再执行
        if ryou_toppa_success_penetration:
            self.set_next_run(task='RyouToppa', finish=True, success=True)
            self.set_next_run_talismanpass()
        if self.config.ryou_toppa.general_battle_config.lock_team_enable:
            logger.info("锁定队伍。")
            self.ui_click(self.I_TOPPA_UNLOCK_TEAM, self.I_TOPPA_LOCK_TEAM)
        else:
            logger.info("解锁队伍。")
            self.ui_click(self.I_TOPPA_LOCK_TEAM, self.I_TOPPA_UNLOCK_TEAM)
        # --------------------------------------------------------------------------------------------------------------
        # 开始突破
        # --------------------------------------------------------------------------------------------------------------
        success = True
        while 1:
            # 判断是否有更高优先级任务，去执行新任务
            self._check_first_priority_task()
            if not self.has_ticket():
                logger.info("我们没有进攻机会了，请一小时后再试。")
                success = False
                break
            if self.current_count >= ryou_config.raid_config.limit_count:
                logger.warning("已达进攻次数上限。")
                break
            if datetime.now() >= self.start_time + time_delta:
                logger.warning("已达进攻时间上限。")
                break
            # 进攻
            res = self.attack_area(self.area_index)
            # 如果战斗失败或区域不可用，则弹出当前区域索引，开始进攻下一个
            if not res:
                self.area_index += 1
                # logger.info("切换进攻区域 [%s]" % str(self.area_index + 1))
                if self.area_index >= len(area_map):
                    logger.warning('战斗区域均失败或无法进攻,上滑战斗区域')
                    self.area_index = 0
                    self.flush_area_cache()
                continue

        if success:
            self.set_next_run(task='RyouToppa', finish=True, server=True, success=True)
        else:
            self.set_next_run(task='RyouToppa', finish=True, server=True, success=False)

        self.set_next_run_talismanpass()

    # 执行花合战
    def set_next_run_talismanpass(self):
        # self.set_next_run(task='TalismanPass', target=datetime.now())
        raise TaskEnd

    def start_ryou_toppa(self):
        """
        开启寮突破
        :return:
        """
        # 点击寮突
        while 1:
            self.screenshot()
            if self.appear_then_click(self.I_SELECT_RYOU_BUTTON, interval=1):
                break

        # 选择第一个寮
        while 1:
            self.screenshot()
            if self.appear_then_click(self.I_GUILD_ORDERS_REWARDS, action=self.C_SELECT_FIRST_RYOU, interval=1):
                break

        # 点击开始突入
        while 1:
            self.screenshot()
            if self.appear_then_click(self.I_START_TOPPA_BUTTON, interval=1):
                continue
            # 出现寮奖励， 说明寮突已开
            if self.appear(self.I_RYOU_REWARD, threshold=0.8):
                break

    def has_ticket(self) -> bool:
        """
        如果没有票了，那么就返回False
        :return:
        """
        # 21点后无限进攻机会
        now = datetime.now()
        if now.hour >= 21 or now.hour < 5:
            return True
        if now.hour == 5:
            return False
        self.wait_until_appear(self.I_TOPPA_RECORD)
        self.screenshot()
        cu, res, total = self.ocr_result(self.O_NUMBER)
        if cu == 0 and cu + res == total:
            logger.warning(f'Execute round failed, no ticket')
            return False
        return True

    def check_area(self, index: int) -> bool:
        """
        检查该区域是否攻略失败
        :return:
        """
        # logger.info('检查区域 [%s] 攻略情况' % str(index + 1))
        f1, f2 = area_map[index].get("fail_sign")
        f3, f4 = area_map[index].get("finished_sign")
        self.screenshot()
        # 如果该区域已经被攻破则退出
        # Ps: 这时候能打过的都打过了，没有能攻打的结界了, 代表任务已经完成，set_next_run time=1d
        if self.appear(f3, threshold=0.7) or self.appear(f4, threshold=0.7):
            logger.info('区域 [%s] 已经攻略, 结束任务.' % str(index + 1))
            self.set_next_run(task='RyouToppa', finish=True, success=True)
            self.set_next_run_talismanpass()
        # 如果该区域攻略失败返回 False
        if self.appear(f1, threshold=0.7) or self.appear(f2, threshold=0.7):
            logger.info('区域 [%s] 攻略失败, 跳过.' % str(index + 1))
            return False
        # self.save_image(wait_time=0, image_type=True)
        # logger.info('区域 [%s], 开始进攻.' % str(index + 1))
        return True

    def flush_area_cache(self):
        time.sleep(1)
        duration = 0.352
        # count = random.randint(1, 3)
        for i in range(1):
            # 测试过很多次 win32api, win32gui 的 MOUSEEVENTF_WHEEL, WM_MOUSEWHEEL
            # 都出现过很多次离奇的事件，索性放弃了使用以下方法，参数是精心调试的
            # 每次执行刚好刷新一组（2个）设定随机刷新 1 - 3 次
            safe_pos_x = random.randint(540, 1000)
            safe_pos_y = random.randint(320, 540)
            p1 = (safe_pos_x, safe_pos_y)
            p2 = (safe_pos_x, safe_pos_y - 101)
            logger.info('Swipe %s -> %s, %s ' % (point2str(*p1), point2str(*p2), duration))
            self.device.swipe_adb(p1, p2, duration=duration)
            time.sleep(1)

    def attack_area(self, index: int):
        """
        :return: 战斗成功(True) or 战斗失败(False) or 区域不可用（False） or 没有进攻机会（设定下次运行并退出）
        """
        # 每次进攻前检查区域可用性
        if not self.check_area(index):
            return False

        # 正式进攻会设定 2s - 10s 的随机延迟，避免攻击间隔及其相近被检测为脚本。
        # if self.config.ryou_toppa.raid_config.random_delay:
        #     delay = random_delay()
        #     time.sleep(delay)

        rcl = area_map[index].get("rule_click")
        # # 点击攻击区域，等待攻击按钮出现。
        # self.ui_click(rcl, stop=RealmRaidAssets.I_FIRE, interval=2)
        # 塔塔开！
        click_failure_count = 0
        click_rcl_count = 0
        while True:
            self.screenshot()
            if click_failure_count >= 2:
                time.sleep(1)
                self.screenshot()
                if self.appear(self.I_TOPPA_RECORD):
                    # 在点击进攻后如果未进入战斗画面则点击的安全区域
                    logger.warning("2次点击进攻后, 未进入战斗, 点击的安全区域")
                    self.click(self.C_SAFE_AREA)
                    return False
            if not self.appear(self.I_TOPPA_RECORD, threshold=0.85):
                time.sleep(1)
                self.screenshot()
                if self.appear(self.I_TOPPA_RECORD, threshold=0.85):
                    continue
                logger.info("开始进攻区域 [%s]" % str(index + 1))
                self.run_general_battle(config=self.config.ryou_toppa.general_battle_config)
                if not self.wait_until_appear(self.I_TOPPA_RECORD, wait_time=5):
                    self.screenshot()
                    self.push_notify(content='长时间未识别到寮突破界面')
                    return True

                # 战斗结束进攻区域重置为0
                self.area_index = 0
                return True

            if self.appear_then_click(RealmRaidAssets.I_FIRE, interval=1, threshold=0.8):
                click_failure_count += 1
                continue
            if self.click(rcl, interval=5):
                click_rcl_count += 1
                if click_rcl_count >= 3:
                    logger.info("区域多次点击未弹出进攻按钮，应该已击败")
                    return True
                continue

    def battle_wait(self, random_click_swipt_enable: bool) -> bool:
        # 战斗过程 随机点击和滑动 防封
        logger.info("Start battle process")
        self.device.stuck_record_clear()
        self.device.stuck_record_add('BATTLE_STATUS_S')
        while 1:
            self.screenshot()
            if self.appear(self.I_TOPPA_RECORD):
                return True
            if self.appear_then_click(self.I_WIN, interval=1):
                continue
            if self.appear_then_click(self.I_FALSE, interval=1):
                continue
            if self.appear_then_click(self.I_PREPARE_HIGHLIGHT, interval=1):
                continue
            if self.appear_then_click(self.I_REWARD, interval=1):
                continue


if __name__ == "__main__":
    from module.config.config import Config

    config = Config('MI')
    # device = Device(config)
    t = ScriptTask(config)
    # t.attack_area(1)
    t.has_ticket()
