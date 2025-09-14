# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
import random
from time import sleep
from datetime import time, datetime, timedelta
from module.base.timer import Timer
from module.config.utils import parse_tomorrow_server

from tasks.Component.GeneralBattle.general_battle import GeneralBattle
from tasks.Component.GeneralInvite.general_invite import GeneralInvite
from tasks.Component.GeneralBuff.general_buff import GeneralBuff
from tasks.Component.GeneralRoom.general_room import GeneralRoom
from tasks.Component.SwitchSoul.switch_soul import SwitchSoul
from tasks.GameUi.game_ui import GameUi
from tasks.GameUi.page import page_main, page_soul_zones, page_shikigami_records
from tasks.Orochi.assets import OrochiAssets
from tasks.Orochi.config import Orochi, UserStatus, Layer, Plan
from module.logger import logger
from module.exception import TaskEnd

"""八岐大蛇"""
class ScriptTask(GeneralBattle, GeneralInvite, GeneralBuff, GeneralRoom, GameUi, SwitchSoul, OrochiAssets):
    soul_full_push = True
    def run(self):

        limit_count = self.config.orochi.next_day_orochi_config.limit_count
        # 御魂层数
        layer = self.config.orochi.next_day_orochi_config.layer
        # 御魂任务选择
        plan = self.config.orochi.next_day_orochi_config.plan
        # 根据选层切换御魂
        orochi_switch_soul = self.config.orochi.switch_soul

        match plan:
            case Plan.TEN30:
                logger.info('Orochi Plan Ten 30')
                limit_count = 30
                group_team = orochi_switch_soul.ten_switch
                layer = Layer.TEN
            case Plan.ELEVEN30:
                logger.info('Orochi Plan Eleven 30')
                limit_count = 30
                group_team = orochi_switch_soul.eleven_switch
                layer = Layer.ELEVEN
            case Plan.TWELVE50:
                logger.info('Orochi Plan Twelve 50')
                limit_count = 50
                group_team = orochi_switch_soul.twelve_switch
                layer = Layer.TWELVE
            case Plan.TWELVE120:
                logger.info('Orochi Plan Twelve 120')
                limit_count = 120
                group_team = orochi_switch_soul.twelve_switch
                layer = Layer.TWELVE
            case Plan.default:
                logger.info('Orochi Plan default')
            case Plan.end:
                self.config.orochi.next_day_orochi_config.plan = Plan.TEN30
                self.config.save()
                start_time = self.config.orochi.next_day_orochi_config.start_time
                next_run = parse_tomorrow_server(start_time)
                self.set_next_run('Orochi', target=next_run)
                logger.info('Orochi Plan end')
                raise TaskEnd
            case _:
                logger.error('Unknown user plan')

        if orochi_switch_soul.auto_enable:
            # 如果是循环根据选层，换御魂
            if plan == Plan.default or plan == Plan.ONE:
                match layer:
                    case Layer.TEN:
                        group_team = orochi_switch_soul.ten_switch
                    case Layer.ELEVEN:
                        group_team = orochi_switch_soul.eleven_switch
                    case Layer.TWELVE:
                        group_team = orochi_switch_soul.twelve_switch

            self.ui_get_current_page()
            self.ui_goto(page_shikigami_records)
            self.run_switch_soul(group_team)

        limit_time = self.config.orochi.orochi_config.limit_time
        self.current_count = 0
        self.limit_count: int = limit_count
        self.limit_time: timedelta = timedelta(hours=limit_time.hour, minutes=limit_time.minute,
                                               seconds=limit_time.second)

        config: Orochi = self.config.orochi
        if not self.is_in_battle(True):
            self.ui_get_current_page()
            self.ui_goto(page_main)
            if config.orochi_config.soul_buff_enable:
                self.open_buff()
                self.soul(is_open=True)
                self.close_buff()

        success = True
        match config.orochi_config.user_status:
            case UserStatus.LEADER:
                success = self.run_leader(layer)
            case UserStatus.MEMBER:
                success = self.run_member()
            case UserStatus.ALONE:
                self.run_alone(layer)
            case _:
                logger.error('Unknown user status')

        # 记得关掉
        if config.orochi_config.soul_buff_enable:
            self.open_buff()
            self.soul(is_open=False)
            self.close_buff()

        # 下一次运行时间
        if success and plan != Plan.default:
            # 设置明天运行
            start_time = self.config.orochi.next_day_orochi_config.start_time
            next_run = parse_tomorrow_server(start_time)
            self.set_next_run('Orochi', target=next_run)
        else:
            self.set_next_run('Orochi', finish=success, success=success)

        datetime_now = datetime.now()
        # 个人突破
        self.set_next_run(task='RealmRaid', target=datetime_now)
        # 花合战
        self.set_next_run(task='TalismanPass', target=datetime_now)
        # 集体任务
        # self.set_next_run(task='CollectiveMissions', target=datetime_now)
        # 御魂整理
        if self.config.orochi.next_day_orochi_config.soulstidy_enabled or self.limit_count >= 99:
            self.set_next_run(task='SoulsTidy',target=datetime_now)

        raise TaskEnd

    def orochi_enter(self) -> bool:
        logger.info('Enter orochi')
        while True:
            self.screenshot()
            if self.appear(self.I_FORM_TEAM):
                return True
            if self.appear_then_click(self.I_OROCHI, interval=1):
                continue

    def check_layer(self, layer: str) -> bool:
        """
        检查挑战的层数, 并选中挑战的层
        :return:
        """
        pos = self.list_find(self.L_LAYER_LIST, layer)
        if pos:
            self.device.click(x=pos[0], y=pos[1])
            return True

    def check_lock(self, lock: bool = True) -> bool:
        """
        检查是否锁定阵容, 要求在八岐大蛇界面
        :param lock:
        :return:
        """
        logger.info('Check lock: %s', lock)
        if lock:
            while 1:
                self.screenshot()
                if self.appear(self.I_OROCHI_LOCK):
                    return True
                if self.appear_then_click(self.I_OROCHI_UNLOCK, interval=1):
                    continue
        else:
            while 1:
                self.screenshot()
                if self.appear(self.I_OROCHI_UNLOCK):
                    return True
                if self.appear_then_click(self.I_OROCHI_LOCK, interval=1):
                    continue

    def run_leader(self, layer):
        logger.info('Start run leader')
        self.ui_get_current_page()
        self.ui_goto(page_soul_zones)
        self.orochi_enter()
        self.check_layer(layer)
        self.check_lock(self.config.orochi.general_battle_config.lock_team_enable)
        # 创建队伍
        logger.info('Create team')
        while 1:
            self.screenshot()
            if self.appear(self.I_CHECK_TEAM):
                break
            if self.appear_then_click(self.I_FORM_TEAM, interval=1):
                continue
        # 创建房间
        self.create_room()
        self.ensure_private()
        self.create_ensure()

        # 邀请队友
        success = True
        is_first = True
        # 这个时候我已经进入房间了哦
        while 1:
            self.screenshot()
            # 无论胜利与否, 都会出现是否邀请一次队友
            # 区别在于，失败的话不会出现那个勾选默认邀请的框
            if self.check_and_invite(self.config.orochi.invite_config.default_invite):
                continue

            # 检查猫咪奖励
            if self.current_count <= 1:
                if self.appear(self.I_PET_PRESENT, interval=1):
                    self.save_image(task_name='Pets', wait_time=1)
                    if self.appear_then_click(self.I_PET_PRESENT, action=self.C_WIN_3, interval=1):
                        continue

            if self.current_count >= self.limit_count:
                if self.is_in_room():
                    logger.info('Orochi count limit out')
                    break

            if datetime.now() - self.start_time >= self.limit_time:
                if self.is_in_room():
                    logger.info('Orochi time limit out')
                    break

            # 如果没有进入房间那就不需要后面的邀请
            if not self.is_in_room():
                if self.is_room_dead():
                    logger.warning('Orochi task failed')
                    success = False
                    break
                continue

            # 点击挑战
            if not is_first:
                if self.run_invite(config=self.config.orochi.invite_config):
                    self.run_general_battle(config=self.config.orochi.general_battle_config)
                else:
                    # 邀请失败，退出任务
                    logger.warning('Invite failed and exit this orochi task')
                    success = False
                    break

            # 第一次会邀请队友
            if is_first:
                if not self.run_invite(config=self.config.orochi.invite_config, is_first=True):
                    logger.warning('Invite failed and exit this orochi task')
                    success = False
                    break
                else:
                    is_first = False
                    self.run_general_battle(config=self.config.orochi.general_battle_config)

        # 当结束或者是失败退出循环的时候只有两个UI的可能，在房间或者是在组队界面
        # 如果在房间就退出
        if self.exit_room():
            pass
        # 如果在组队界面就退出
        if self.exit_team():
            pass

        self.ui_get_current_page()
        self.ui_goto(page_main)

        return success

    def run_member(self):
        logger.info('Start run member')
        self.ui_get_current_page()

        # 开始等待队长拉人
        wait_time = self.config.orochi.invite_config.wait_time
        wait_timer = Timer(wait_time.minute * 60)
        wait_timer.start()

        success = True

        # 进入战斗流程
        self.device.stuck_record_add('BATTLE_STATUS_S')

        while 1:

            self.screenshot()

            # 等待超时
            if wait_timer.reached():
                self.push_notify(content=f"队员等待超时...")
                success = False
                return success

            if self.check_then_accept():
                break

        while 1:
            self.screenshot()

            # 检查猫咪奖励
            if self.current_count <= 1:
                if self.appear(self.I_PET_PRESENT, interval=1):
                    self.save_image(task_name='Pets', wait_time=1)
                    if self.appear_then_click(self.I_PET_PRESENT, action=self.C_WIN_3, interval=1):
                        continue

            if self.current_count >= self.limit_count:
                logger.info('Orochi count limit out')
                break
            if datetime.now() - self.start_time >= self.limit_time:
                logger.info('Orochi time limit out')
                break

            if self.check_then_accept():
                continue

            if self.is_in_room():
                self.device.stuck_record_clear()
                if self.wait_battle(wait_time=self.config.orochi.invite_config.wait_time):
                    self.run_general_battle(config=self.config.orochi.general_battle_config)
                else:
                    break
            # 队长秒开的时候，检测是否进入到战斗中
            elif self.check_take_over_battle(False, config=self.config.orochi.general_battle_config):
                continue

        while 1:
            # 有一种情况是本来要退出的，但是队长邀请了进入的战斗的加载界面
            if self.appear(self.I_GI_HOME) or self.appear(self.I_GI_EXPLORE):
                break
            # 如果可能在房间就退出
            if self.exit_room():
                pass
            # 如果还在战斗中，就退出战斗
            if self.exit_battle():
                pass

        self.ui_get_current_page()
        self.ui_goto(page_main)

        return success

    def run_alone(self, layer):
        logger.info('Start run alone')
        self.ui_get_current_page()
        self.ui_goto(page_soul_zones)
        self.orochi_enter()
        self.check_layer(layer)
        self.check_lock(self.config.orochi.general_battle_config.lock_team_enable)

        def is_in_orochi(screenshot=False) -> bool:
            if screenshot:
                self.screenshot()
            return self.appear(self.I_OROCHI_FIRE)

        while 1:
            self.screenshot()

            # 检查猫咪奖励
            if self.current_count <= 1:
                if self.appear(self.I_PET_PRESENT, interval=1):
                    self.save_image(task_name='Pets', wait_time=1)
                    if self.appear_then_click(self.I_PET_PRESENT, action=self.C_WIN_3, interval=1):
                        continue
            
            if not is_in_orochi():
                continue

            if self.current_count >= self.limit_count:
                logger.info('Orochi count limit out')
                break
            if datetime.now() - self.start_time >= self.limit_time:
                logger.info('Orochi time limit out')
                break

            # 点击挑战
            while 1:
                self.screenshot()
                if self.appear_then_click(self.I_OROCHI_FIRE, interval=1):
                    pass

                if not self.appear(self.I_OROCHI_FIRE):
                    self.run_general_battle(config=self.config.orochi.general_battle_config)
                    break

        # 回去
        while 1:
            self.screenshot()
            if not self.appear(self.I_FORM_TEAM):
                break
            if self.appear_then_click(self.I_BACK_BL, interval=1):
                continue

        self.ui_current = page_soul_zones
        self.ui_goto(page_main)

    def is_room_dead(self) -> bool:
        # 如果在探索界面或者是出现在组队界面，那就是可能房间死了
        sleep(0.5)
        if self.appear(self.I_MATCHING) or self.appear(self.I_CHECK_EXPLORATION):
            sleep(0.5)
            if self.appear(self.I_MATCHING) or self.appear(self.I_CHECK_EXPLORATION):
                return True
        return False

    def battle_wait(self, random_click_swipt_enable: bool) -> bool:
        """
        重写战斗等待
        # https://github.com/runhey/OnmyojiAutoScript/issues/95
        :param random_click_swipt_enable:
        :return:
        """
        # 重写
        self.device.stuck_record_add('BATTLE_STATUS_S')
        self.device.click_record_clear()
        self.C_REWARD_1.name = 'C_REWARD'
        self.C_REWARD_2.name = 'C_REWARD'
        self.C_REWARD_3.name = 'C_REWARD'
        # 战斗过程 随机点击和滑动 防封
        logger.info("Start battle process")
        while 1:
            self.screenshot()
            action_click = random.choice([self.C_WIN_1, self.C_WIN_2, self.C_WIN_3])
            if self.appear_then_click(self.I_WIN, action=action_click, interval=0.8):
                # 赢的那个鼓
                continue
            if self.appear(self.I_GREED_GHOST):
                # 贪吃鬼
                logger.info('I_GREED_GHOST Orochi Win battle')
                self.wait_until_appear(self.I_REWARD, wait_time=1.5)
                self.screenshot()
                if not self.appear(self.I_GREED_GHOST):
                    logger.warning('Greedy ghost disappear. Maybe it is a false battle')
                    continue
                while 1:
                    self.screenshot()
                    # 检查自选御魂弹窗
                    if self.current_count <= 1:
                        if self.appear_then_click(self.I_UI_BACK_RED):
                            # 出现关闭御魂弹窗，说明没选择自选御魂，当前自选次数减一
                            self.current_count -= 1
                            continue
                    action_click = random.choice([self.C_REWARD_1, self.C_REWARD_2, self.C_REWARD_3])
                    if not self.appear(self.I_GREED_GHOST):
                        break
                    if self.appear(self.I_SOUL_FULL_ENSURE):
                        self.appear_then_click(self.I_SOUL_FULL_ENSURE)
                        if self.soul_full_push:
                            self.push_notify("御魂溢出")
                            self.soul_full_push = False
                            self.set_next_run(task='SoulsTidy',target=datetime.now())
                        continue
                    if self.click(action_click, interval=1.5):
                        continue
                return True
            if self.appear(self.I_REWARD):
                # 魂
                logger.info('I_REWARD Orochi Win battle')
                appear_greed_ghost = self.appear(self.I_GREED_GHOST)
                while 1:
                    self.screenshot()
                    # 检查自选御魂弹窗
                    if self.current_count <= 1:
                        if self.appear_then_click(self.I_UI_BACK_RED):
                            # 出现关闭御魂弹窗，说明没选择自选御魂，当前自选次数减一
                            self.current_count -= 1
                            continue
                    action_click = random.choice([self.C_REWARD_1, self.C_REWARD_2, self.C_REWARD_3])
                    if self.appear_then_click(self.I_REWARD, action=action_click, interval=1.5):
                        continue
                    if not self.appear(self.I_REWARD):
                        break
                return True

            if self.appear(self.I_FALSE):
                logger.warning('False battle')
                self.ui_click_until_disappear(self.I_FALSE)
                return False

            # 如果开启战斗过程随机滑动
            if random_click_swipt_enable:
                self.random_click_swipt()


if __name__ == '__main__':
    from module.config.config import Config
    from module.device.device import Device

    c = Config('oas1')
    d = Device(c)
    t = ScriptTask(c, d)
    t.battle_wait(False)
    t.run()
