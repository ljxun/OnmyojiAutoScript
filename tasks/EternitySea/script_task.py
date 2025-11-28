# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
from time import sleep

import random
from datetime import datetime, timedelta
from module.exception import RequestHumanTakeover
from module.exception import TaskEnd
from module.logger import logger
from tasks.Component.GeneralBattle.general_battle import GeneralBattle
from tasks.Component.GeneralInvite.general_invite import GeneralInvite
from tasks.Component.GeneralRoom.general_room import GeneralRoom
from tasks.Component.SwitchSoul.switch_soul import SwitchSoul
from tasks.EternitySea.assets import EternitySeaAssets
from tasks.EternitySea.config import EternitySea
from tasks.GameUi.page import page_main, page_soul_zones
from tasks.Orochi.config import UserStatus


class ScriptTask(GeneralBattle, GeneralRoom, GeneralInvite, SwitchSoul, EternitySeaAssets):
    """ 永生之海 """
    soul_full_push = True

    @property
    def task_name(self):
        return "EternitySea"

    def _two_teams_switch_sous(self, config):
        if config.enable:
            self.run_switch_soul(config.switch_group_team)

        if config.enable_switch_by_name:
            self.run_switch_soul_by_name(config.group_name, config.team_name)

    def run(self) -> None:

        self.limit_count = self._task_config.eternity_sea_config.limit_count
        self.limit_time = self._limit_time

        self._two_teams_switch_sous(self._task_config.switch_soul_config_1)
        self._two_teams_switch_sous(self._task_config.switch_soul_config_2)
        self.ui_goto_page(page_main)
        match self._task_config.eternity_sea_config.user_status:
            case UserStatus.LEADER: success = self.run_leader()
            case UserStatus.MEMBER: success = self.run_member()
            case UserStatus.ALONE: success = self.run_alone()
            case _: logger.error('Unknown user status')

        # if success:
        #     self.set_next_run(self.task_name, finish=True, success=True)
        # else:
        #     self.set_next_run(self.task_name, finish=False, success=False)
        # 设置下一次运行时间是周5
        self.next_run_week(5)
        # 个人突破
        self.set_next_run(task='RealmRaid', target=datetime.now())

        raise TaskEnd(self.task_name)

    def run_leader(self):
        logger.info('Start run leader')
        self._navigate_to_soul_zones()
        self._enter_eternity_sea()
        layer = self._task_config.eternity_sea_config.layer
        self.check_layer(layer)
        self.check_lock(self._task_config.general_battle_config.lock_team_enable)
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
            if self.check_and_invite(self._task_config.invite_config.default_invite):
                continue

            #限制
            if self.current_count >= self.limit_count:
                logger.info("EternitySea count limit out")
                break
            if datetime.now() - self.start_time >= self.limit_time:
                logger.info("EternitySea time limit out")
                break

            # 如果没有进入房间那就不需要后面的邀请
            if not self.is_in_room():
                if self.is_room_dead():
                    logger.warning('eternity_sea task failed')
                    success = False
                    break
                continue

            # 点击挑战
            if not is_first:
                if self.run_invite(config=self._task_config.invite_config):
                    self.run_general_battle(config=self._task_config.general_battle_config)
                else:
                    # 邀请失败，退出任务
                    logger.warning('Invite failed and exit this eternity_sea task')
                    success = False
                    break

            # 第一次会邀请队友
            if is_first:
                if not self.run_invite(config=self._task_config.invite_config, is_first=True):
                    logger.warning('Invite failed and exit this eternity_sea task')
                    success = False
                    break
                else:
                    is_first = False
                    self.run_general_battle(config=self._task_config.general_battle_config)

        # 当结束或者是失败退出循环的时候只有两个UI的可能，在房间或者是在组队界面
        # 如果在房间就退出
        self.save_image(push_flag=True, wait_time=0, content=f'任务已完成{self.current_count}次,用时: {timedelta(seconds=int((datetime.now() - self.start_time).total_seconds()))}')
        if self.exit_room():
            pass
        # 如果在组队界面就退出
        if self.exit_team():
            pass

        self.ui_goto_page(page_main)

        if not success:
            return False
        return True

    def run_member(self):
        logger.info('Start run member')

        # 进入战斗流程
        self.device.stuck_record_add('BATTLE_STATUS_S')
        while 1:
            self.screenshot()

            #限制
            if self.current_count >= self.limit_count:
                logger.info("EternitySea count limit out")
                break
            if datetime.now() - self.start_time >= self.limit_time:
                logger.info("EternitySea time limit out")
                break

            if self.check_then_accept():
                continue

            if self.is_in_room():
                self.device.stuck_record_clear()
                if self.wait_battle(wait_time=self._task_config.invite_config.wait_time):
                    self.run_general_battle(config=self._task_config.general_battle_config)
                else:
                    break
            # 队长秒开的时候，检测是否进入到战斗中
            elif self.check_take_over_battle(False, config=self._task_config.general_battle_config):
                continue

        self.save_image(push_flag=True, wait_time=0, content=f'任务已完成{self.current_count}次,用时: {timedelta(seconds=int((datetime.now() - self.start_time).total_seconds()))}')
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

        self.ui_goto_page(page_main)
        return True

    def run_alone(self) -> bool:
        logger.info("Start run alone")
        self._navigate_to_soul_zones()
        self._enter_eternity_sea()

        if self._task_config.general_battle_config.lock_team_enable == False:
            logger.critical(f"Only supports lock team mode")
            raise RequestHumanTakeover

        while 1:
            self.screenshot()

            if not self._is_in_eternity_sea():
                continue

            if self.current_count >= self.limit_count:
                logger.info("EternitySea count limit out")
                break
            if datetime.now() - self.start_time >= self.limit_time:
                logger.info("EternitySea time limit out")
                break

            # 点击挑战
            while 1:
                self.screenshot()
                if self.appear_then_click(self.I_ETERNITY_SEA_FIRE, interval=1):
                    pass

                if not self.appear(self.I_ETERNITY_SEA_FIRE):
                    self.run_general_battle(config=self._task_config.general_battle_config)
                    break
        return True

    def is_room_dead(self) -> bool:
        # 如果在探索界面或者是出现在组队界面，那就是可能房间死了
        sleep(0.5)
        if self.appear(self.I_MATCHING) or self.appear(self.I_CHECK_EXPLORATION):
            sleep(0.5)
            if self.appear(self.I_MATCHING) or self.appear(self.I_CHECK_EXPLORATION):
                return True
        return False

    def eternitysea_enter(self) -> bool:
        logger.info('Enter EternitySea')
        while True:
            self.screenshot()
            if self.appear(self.I_FORM_TEAM):
                return True
            if self.appear_then_click(self.I_ETERNITY_SEA, interval=1):
                continue


    def _is_in_eternity_sea(self) -> bool:
        self.screenshot()
        return self.appear(self.I_ETERNITY_SEA_FIRE)

    @property
    def _limit_time(self) -> timedelta:
        limit_time = self._task_config.eternity_sea_config.limit_time
        return timedelta(
            hours=limit_time.hour, minutes=limit_time.minute, seconds=limit_time.second
        )

    def _enter_eternity_sea(self) -> None:
        logger.info("Enter eternity_sea")
        while True:
            self.screenshot()
            if self.appear(self.I_FORM_TEAM, interval=1):
                return True
            if self.appear_then_click(self.I_ETERNITY_SEA, interval=1):
                continue
            #有可能点击到录像
            if self.appear_then_click(self.I_BACK_BOTTOM, interval=1):
                continue

    def _navigate_to_soul_zones(self) -> None:
        self.ui_goto_page(page_soul_zones)

    @property
    def _task_config(self) -> EternitySea:
        return self.config.model.eternity_sea

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
        检查是否锁定阵容, 要求在永生之海界面
        :param lock:
        :return:
        """
        logger.info('Check lock: %s', lock)
        if lock:
            while 1:
                self.screenshot()
                if self.appear(self.I_NEWETERNITYSEA_LOCK):
                    return True
                if self.appear_then_click(self.I_ETERNITYSEA_UNLOCK, interval=1):
                    continue
        else:
            while 1:
                self.screenshot()
                if self.appear(self.I_ETERNITYSEA_UNLOCK):
                    return True
                if self.appear_then_click(self.I_NEWETERNITYSEA_LOCK, interval=1):
                    continue

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
                            self.set_next_run(task='SoulsTidy', target=datetime.now())
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


if __name__ == "__main__":
    from module.config.config import Config
    from module.device.device import Device

    c = Config("oas1")
    d = Device(c)
    t = ScriptTask(c, d)
    t.run()
    # t.screenshot()