# This Python file uses the following encoding: utf-8
# @brief    Ryou Dokan Toppa (阴阳竂道馆突破功能)
# @author   jackyhwei
# @note     draft version without full test
# github    https://github.com/roarhill/oas
import random
import time
from enum import Enum

import numpy as np
from cached_property import cached_property

from module.atom.image_grid import ImageGrid
from module.exception import TaskEnd
from module.logger import logger
from tasks.Component.GeneralBattle.general_battle import GeneralBattle
from tasks.Component.SwitchSoul.switch_soul import SwitchSoul
from tasks.Dokan.assets import DokanAssets
from tasks.Dokan.config import Dokan
from tasks.Dokan.utils import detect_safe_area2
from tasks.GameUi.game_ui import GameUi
from tasks.GameUi.page import page_main, page_shikigami_records, page_guild
from tasks.RichMan.assets import RichManAssets

global_count = 0

class DokanScene(Enum):
    # 未知界面
    RYOU_DOKAN_SCENE_UNKNOWN = 0
    # 进入道馆，集结中
    RYOU_DOKAN_SCENE_GATHERING = 1
    # 进入战场，等待用户点击开始战斗
    RYOU_DOKAN_SCENE_IN_FIELD = 2
    # 通常是失败了，并退出来到集结界面，可重新开始点击右下角挑战进入战斗
    RYOU_DOKAN_SCENE_START_CHALLENGE = 3
    # 失败次数超过上限，CD中
    RYOU_DOKAN_SCENE_CD = 4
    # 战斗进行中
    RYOU_DOKAN_SCENE_FIGHTING = 5
    # 加油进行中
    RYOU_DOKAN_SCENE_CHEERING = 6
    # 道馆失败投票保留
    RYOU_DOKAN_SCENE_FAILED_VOTE_NO = 7
    # 阴阳竂
    RYOU_DOKAN_RYOU = 8
    # 战斗结算，可能是打完小朋友了，也可能是失败了。
    RYOU_DOKAN_SCENE_BATTLE_OVER = 9
    # 等待BOSS战
    RYOU_DOKAN_SCENE_BOSS_WAITING = 10
    # 道馆结束
    RYOU_DOKAN_SCENE_FINISHED = 99

    def __str__(self):
        return self.name.title()

    def print(self):
        print(DokanScene.RYOU_DOKAN_SCENE_GATHERING)  # 输出: DokanScene.Ryou_Daoguan_Scene_Gathering
        print(DokanScene.RYOU_DOKAN_SCENE_CD.value)  # 输出: 2
        print(str(DokanScene.RYOU_DOKAN_SCENE_FIGHTING))  # 输出: Ryou_Daoguan_Scene_Fighting


class ScriptTask(GeneralBattle, GameUi, SwitchSoul, DokanAssets, RichManAssets):
    medal_grid: ImageGrid = None
    attack_priority_selected: bool = False
    team_switched: bool = False
    green_mark_done: bool = False

    @cached_property
    def _attack_priorities(self) -> list:
        return [self.I_RYOU_DOKAN_ATTACK_PRIORITY_0,
                self.I_RYOU_DOKAN_ATTACK_PRIORITY_1,
                self.I_RYOU_DOKAN_ATTACK_PRIORITY_2,
                self.I_RYOU_DOKAN_ATTACK_PRIORITY_3,
                self.I_RYOU_DOKAN_ATTACK_PRIORITY_4]

    def run(self):
        """ 道馆主函数

        :return:
        """
        cfg: Dokan = self.config.dokan
        current_scene: DokanScene = DokanScene.RYOU_DOKAN_SCENE_UNKNOWN
        in_dokan: bool = False

        # 攻击优先顺序
        attack_priority: int = cfg.dokan_config.dokan_attack_priority

        # 自动换御魂
        if cfg.switch_soul_config.enable:
            self.ui_get_current_page()
            self.ui_goto(page_shikigami_records)
            self.run_switch_soul(cfg.switch_soul_config.switch_group_team)
        if cfg.switch_soul_config.enable_switch_by_name:
            self.ui_get_current_page()
            self.ui_goto(page_shikigami_records)
            self.run_switch_soul_by_name(cfg.switch_soul_config.group_name, cfg.switch_soul_config.team_name)

        # scene_err_count = 0

        # 在阴阳竂界面点击并进入道馆
        # 检测当前界面的场景（时间关系，暂时没有做庭院、町中等主界面的场景检测, 应考虑在GameUI.game_ui.ui_get_current_page()里实现）
        # in_dokan, current_scene = self.get_current_scene(True)


        # 寮管理开启道馆
        # if cfg.dokan_config.dokan_enable:
        #     self.goto_dokan_open()
        # else:
        #     # self.goto_dokan_new()
        self.goto_dokan()

        # 开始道馆流程
        while 1:
            self.screenshot()

            self.device.stuck_record_add('BATTLE_STATUS_S')
            self.device.click_record_clear()
            time.sleep(1)

            # 检测当前界面的场景（时间关系，暂时没有做庭院、町中等主界面的场景检测, 应考虑在GameUI.game_ui.ui_get_current_page()里实现）
            in_dokan, current_scene = self.get_current_scene(True)

            logger.info(f"in_dokan={in_dokan}, current_scene={current_scene}")

            # 如果当前不在道馆，或者被人工操作退出道馆了，重新尝试进入道馆
            if not in_dokan:
                # scene_err_count += 1
                # logger.info(f"err count={scene_err_count}")
                # if scene_err_count >= 3:
                # self.goto_dokan_new()
                self.goto_dokan()
                #     # 先点击一下，然后等5秒再重新截图
                #     self.anti_detect(True, True, False)
                #     time.sleep(5)
                #     continue
                # else:
                #     scene_err_count = 0

            # 场景状态：道馆集结中
            if current_scene == DokanScene.RYOU_DOKAN_SCENE_GATHERING:
                logger.debug(f"Ryou DOKAN gathering...")
                # 如果还未选择优先攻击，选一下
                if not self.attack_priority_selected:
                    self.dokan_choose_attack_priority(attack_priority=attack_priority)
                    self.attack_priority_selected = True
                    continue
            # 场景状态：等待馆主战开始
            elif current_scene == DokanScene.RYOU_DOKAN_SCENE_BOSS_WAITING:
                logger.debug(f"Ryou DOKAN boss battle waiting...")
            # 场景状态：检查右下角有没有挑战？通常是失败了，并退出来到集结界面，可重新开始点击右下角挑战进入战斗
            elif current_scene == DokanScene.RYOU_DOKAN_SCENE_START_CHALLENGE:
                logger.info("挑战次数已经重置！可以进行挑战了")
                self.ui_click_until_disappear(self.I_RYOU_DOKAN_START_CHALLENGE)
                # # 场景状态：进入战斗，待准备
                # elif current_scene == DokanScene.RYOU_DOKAN_SCENE_IN_FIELD:
                logger.info("场景状态：进入战斗，待准备")
                # 战斗
                self.dokan_battle(cfg)
                # 战斗结束后，随便点三下，确保跳过各种结算画面
                # self.click(click=self.C_DOKAN_READY_FOR_BATTLE, interval=1.5)
                # self.click(click=self.C_DOKAN_RANDOM_CLICK_AREA2, interval=2.2)
                # self.click(click=self.C_DOKAN_RANDOM_CLICK_AREA3, interval=1.8)
                # 每次战斗结束都重置绿标
                self.green_mark_done = False
            # 场景状态：如果CD中，开始加油
            elif current_scene == DokanScene.RYOU_DOKAN_SCENE_CD:
                logger.info(f"Fail CD: start cheering={cfg.dokan_config.dokan_auto_cheering_while_cd}..")
                if cfg.dokan_config.dokan_auto_cheering_while_cd:
                    pass
            # 场景状态：战斗中，左上角的加油图标
            elif current_scene == DokanScene.RYOU_DOKAN_SCENE_FIGHTING:
                logger.info("Battle undergoing")
            # # 场景状态：加油中
            # elif current_scene == DokanScene.RYOU_DOKAN_SCENE_CHEERING:
            #     self.appear_then_click(self.I_RYOU_DOKAN_CHEERING)
            # 场景状态：道馆已经结束
            # elif current_scene == DokanScene.RYOU_DOKAN_SCENE_FINISHED:
            #     logger.info("Dokan challenge finished, exit Dokan")
            #     break
            elif current_scene == DokanScene.RYOU_DOKAN_SCENE_FAILED_VOTE_NO:
                logger.info("Dokan challenge failed: vote for keep the awards")
            else:
                logger.info(f"unknown scene, skipped")

            # 防封，随机移动，随机点击（安全点击），随机时延
            # if not self.anti_detect(True, True, True):
            #     time.sleep(1)

    def dokan_battle(self, cfg: Dokan):
        """ 道馆战斗
        道馆集结结束后会自动进入战斗，打完一个也会自动进入下一个，因此直接点击右下角的开始

        :return: 战斗成功(True) or 战斗失败(False) or 区域不可用（False）
        """
        # config: GeneralBattleConfig = cfg.general_battle_config

        # 正式进攻会设定 2s - 10s 的随机延迟，避免攻击间隔及其相近被检测为脚本。
        # if cfg.dokan_config.random_delay:
        #     self.anti_detect(False, False, True)

        # 上面可能睡了一觉，重新截图
        self.screenshot()

        # 更换队伍
        # if not self.team_switched:
        #     logger.info(
        #         f"switch team preset: enable={config.preset_enable}, preset_group={config.preset_group}, preset_team={config.preset_team}")
        #     self.switch_preset_team(config.preset_enable, config.preset_group, config.preset_team)
        #     self.team_switched = True
        #     # 切完队伍后有时候会卡顿，先睡一觉，防止快速跳到绿标流程，导致未能成功绿标
        #     time.sleep(3)

        # # 等待准备按钮的出现
        # self.wait_until_appear(self.I_PREPARE_HIGHLIGHT)
        #
        # # 点击准备
        # if self.appear_then_click(self.I_PREPARE_HIGHLIGHT, interval=1.5):
        #     logger.info("Prepare")
        #
        #     # 绿标式神, should we check there's a green marked role?
        #     if not self.green_mark_done and self.is_in_battle(False):
        #         logger.info(
        #             f"green mark: enable={config.green_enable}, green_mark={config.green_mark}")
        #         self.green_mark(config.green_enable, config.green_mark)
        #         self.green_mark_done = True

        # 等待战斗结果
        # logger.info(f"等待战斗结果:config.random_click_swipt_enable={config.random_click_swipt_enable}")
        # logger.info("come on baby, let's go.")

        while 1:
            # logger.info("take a nap")

            # self.device.stuck_record_add('BATTLE_STATUS_S')
            # self.device.click_record_clear()
            # time.sleep(1)

            self.screenshot()

            # 打完一个小朋友，自动进入下一个小朋友
            if self.appear_then_click(self.I_RYOU_DOKAN_IN_FIELD):
                logger.info(f"开始点击准备....")
                self.ui_click_until_disappear(self.I_RYOU_DOKAN_IN_FIELD)
                logger.info(f"已经完成准备点击！开始战斗")
                global global_count
                global_count += 1
                self.device.stuck_record_add('BATTLE_STATUS_S')
                self.device.click_record_clear()
                # 绿标
                if not self.green_mark_done:
                    self.green_mark(config.green_enable, config.green_mark)
                    self.green_mark_done = True

                logger.info(f"battle starts {global_count}")

            # # 如果出现赢 就点击
            # if self.appear_then_click(GeneralBattle.I_WIN, threshold=0.8):
            #     self.ui_click_until_disappear(GeneralBattle.I_WIN)
            #     logger.info("Dokan guards eliminated, boss is on the way")
            #     logger.info("领奖励,那个红色打鼓")
            #     win = True
            #     break
            #
            # # 如果出现打败馆主的赢，就点击
            # if self.appear_then_click(self.I_RYOU_DOKAN_WIN, threshold=0.8):
            #     self.ui_click_until_disappear(self.I_RYOU_DOKAN_WIN)
            #     logger.info("We've defeated the boss, and win the final game.")
            #     logger.info("馆主的赢，就点击.")
            #     win = True
            #     break

            # # 如果出现失败 就点击，返回False。 TODO 不知道挑战馆主失败是不是同一个画面？
            # if self.appear_then_click(GeneralBattle.I_FALSE, threshold=0.8):
            #     self.ui_click_until_disappear(GeneralBattle.I_FALSE)
            #     logger.info("Battle failed")
            #     logger.info("如果出现失败 就点击，返回False")
            #     win = False
            #     break

            # 如果领奖励
            if self.appear_then_click(self.I_RYOU_DOKAN_BATTLE_OVER, threshold=0.6):
                self.ui_click_until_disappear(self.I_RYOU_DOKAN_BATTLE_OVER)
                logger.info("Battle over")
                logger.info("领奖励,那个魂")
                win = True
                break

            # # 如果领奖励出现金币
            # if self.appear_then_click(GeneralBattle.I_REWARD_GOLD, threshold=0.8):
            #     self.ui_click_until_disappear(GeneralBattle.I_REWARD_GOLD)
            #     logger.info("领奖励,那个金币")
            #     win = True
            #     break

            # 如果开启战斗过程随机滑动
            if config.random_click_swipt_enable:
                logger.info("随机滑动....")
                logger.info("random swipt ...")
                self.random_click_swipt()

    def dokan_choose_attack_priority(self, attack_priority: int) -> bool:
        """ 选择优先攻击
        : return
        """
        logger.hr('Try to choose attack priority')
        max_try = 5

        if not self.appear_then_click(self.I_RYOU_DOKAN_ATTACK_PRIORITY, interval=2):
            logger.error(f"can not find dokan priority option button, choose attack priority process skipped")
            return False

        logger.info(f"start select attack priority: {attack_priority}, remain try: {max_try}")
        try:
            target_attack = self._attack_priorities[attack_priority]
        except:
            target_attack = self._attack_priorities[0]

        while 1:
            self.screenshot()
            if max_try <= 0:
                logger.warn("give up priority selection!")
                break

            if self.appear_then_click(target_attack, interval=1.8):
                self.attack_priority_selected = True
                logger.info(f"selected attack priority: {attack_priority}")
                break

            max_try -= 1

        return True

    def anti_detect(self, random_move: bool = True, random_click: bool = True, random_delay: bool = True):
        '''额外的防封测试

        准备找个号做做爬楼活动的每天300次试试
        '''
        res = False
        # 三个行为中，任何一个生效了都返回True, 否则返回False
        if random_move:
            self.random_click_swipt()
            res = True
        if random_click:
            # 0到2秒之间的随机浮点数
            sleep = random.uniform(0, 2)
            # 只保留2位小数
            sleep = round(sleep, 2)
            if not self.config.dokan.dokan_config.anti_detect_click_fixed_random_area:
                # 多搞几个安全点击区域
                num = random.randint(0, 5)
                if num == 0:
                    self.click(click=self.C_DOKAN_RANDOM_CLICK_AREA, interval=sleep)
                elif num == 1:
                    self.click(click=self.C_DOKAN_RANDOM_CLICK_AREA2, interval=sleep)
                elif num == 2:
                    self.click(click=self.C_DOKAN_RANDOM_CLICK_AREA3, interval=sleep)
                elif num == 3:
                    self.click(click=self.C_DOKAN_RANDOM_CLICK_AREA, interval=sleep)
                else:
                    self.click(click=self.C_DOKAN_RANDOM_CLICK_AREA2, interval=sleep)
            else:
                # 假设安全区域是绿色的
                safe_color_lower = np.array([45, 25, 25])  # HSV颜色空间的绿色下界
                safe_color_upper = np.array([90, 255, 255])  # HSV颜色空间的绿色上界
                pos = detect_safe_area2(self.device.image, safe_color_lower, safe_color_upper, 3, True)
                logger.info(f"random click area: {pos}, delay: {sleep}")
                self.click(pos)

            res = True
        if random_delay:
            # 0到2秒之间的随机浮点数
            sleep = random.uniform(0, 5)
            # 只保留2位小数
            sleep = round(sleep, 2)
            time.sleep(sleep)
            res = True
        return res

    def goto_main(self):
        ''' 保持好习惯，一个任务结束了就返回庭院，方便下一任务的开始或者是出错重启
          退出道馆。注意：有的时候有退出确认框，有的时候没有。未找到规律。
               先试试用确认框的，若是实在不行，就改成等道馆时间结束后，系统自动退出
               但是如果出错了，需要重启任务时必须走GameUi.ui_goto(page_main)，
               那样有或者无确认框不确定性还是会导致ui_goto()出错
        '''
        # self.ui_current = page_dokan
        # self.ui_goto(page_main)

        max_try = 3
        while 1:
            self.screenshot()
            if self.appear_then_click(GeneralBattle.I_EXIT, interval=1.5):
                logger.info(f"Click {GeneralBattle.I_EXIT.name}")
                continue
            # 点了后EXIT后，可能无确认框
            if self.appear_then_click(self.I_RYOU_DOKAN_EXIT_ENSURE, interval=1.5):
                logger.info(f"Click {self.I_RYOU_DOKAN_EXIT_ENSURE}")
                break
            else:
                max_try -= 1
                time.sleep(1.2)

            if max_try <= 0:
                break

        # 退出道馆地图
        while 1:
            self.screenshot()
            # 确认后会跳到竂地图，再点击左上角的蓝色的返回，但是不知道这个返回有没有确认
            if self.appear_then_click(GameUi.I_BACK_BL, interval=2.5):
                logger.info(f"Click {GameUi.I_BACK_BL.name}")
                break
        self.ui_get_current_page()
        self.ui_goto(page_main)

    def goto_dokan(self):
        self.ui_get_current_page()
        self.ui_goto(page_guild)

        if self.is_in_dokan():
            return True

            # 进入选择寮界面
        while 1:
            self.screenshot()

            if self.appear_then_click(self.I_DAOGUAN, interval=1):
                continue
            if self.appear_then_click(self.I_GUILD_SHRINE, interval=1):
                continue
            if self.appear(self.I_FANGSHOU, interval=1):
                break
            if self.appear(self.I_RYOU_DOKAN_CHECK, threshold=0.6):
                return

        DOKAN_STATUS_str = self.O_DOKAN_STATUS.detect_text(self.device.image)
        logger.info(DOKAN_STATUS_str)
        if '挑战成功' in DOKAN_STATUS_str or '0次' in DOKAN_STATUS_str:

            # 保持好习惯，一个任务结束了就返回到庭院，方便下一任务的开始
            self.goto_main()
            # 设置下次运行时间
            self.set_next_run(task='Dokan', finish=True, server=True, success=True)
            raise TaskEnd
        elif '集结中' in DOKAN_STATUS_str:
            self.goto_dokan_click()
            return True
        else:
            if self.config.dokan.dokan_config.dokan_enable:
                self.open_dokan()
            return False

    def goto_dokan_click(self):
        while 1:
            self.screenshot()

            if self.is_in_dokan():
                break

            pos = self.O_DOKAN_MAP.ocr_full(self.device.image)
            if pos == (0, 0, 0, 0):
                logger.info(f"failed to find {self.O_DOKAN_MAP.keyword}")
            else:
                # 取中间
                x = pos[0] + pos[2] / 2
                # 往上偏移20
                y = pos[1] - 20
                logger.info("ocr detect result pos={pos}, try click pos, x={x}, y={y}")
                self.device.click(x=x, y=y)

    # def goto_dokan_new(self):
    #     ''' 进入道馆
    #     道馆相关场景
    #     :return
    #     '''
    #     self.ui_get_current_page()
    #     try_count = 0
    #     while try_count < 5:
    #         # 点击进入道馆
    #         logger.info("Entering Ryou")
    #         self.ui_goto(page_guild)
    #         # 查找道馆
    #         activity = "道馆"
    #         pos = self.list_find(self.L_RYOU_ACTIVITY_LIST, activity)
    #         if pos:
    #             logger.info(f"Enter Dokan map: pos = {pos}")
    #             self.device.click(x=pos[0], y=pos[1])
    #
    #             # 进了后的画面，我没有截图，盲猜应该是在画面正中间的
    #             time.sleep(2)
    #             image = self.screenshot()
    #
    #             pos = self.O_DOKAN_MAP.ocr_full(image)
    #             if pos == (0, 0, 0, 0):
    #                 logger.info(f"failed to find {self.O_DOKAN_MAP.keyword}")
    #             else:
    #                 # 取中间
    #                 x = pos[0] + pos[2] / 2
    #                 # 往上偏移20
    #                 y = pos[1] - 20
    #
    #                 logger.info("ocr detect result pos={pos}, try click pos, x={x}, y={y}")
    #
    #                 self.device.click(x=x, y=y)
    #
    #                 break
    #         try_count += 1
    #         time.sleep(1)
    #
    #     print(f"try_count: {try_count}")

    def is_in_dokan(self):
        """
          判断是否在道馆里面
          :return:
          """
        self.screenshot()
        if self.appear(self.I_RYOU_DOKAN_CHECK, threshold=0.6):
            return True
        return False

    # def dokan_status(self):
    #
    #     """
    #   判断道馆开启状态
    #   :return:
    #   """
    #
    #     if self.is_in_dokan():
    #         return True
    #
    #     # 进入选择寮界面
    #     while 1:
    #         self.screenshot()
    #
    #         if self.appear_then_click(self.I_DAOGUAN, interval=1):
    #             continue
    #         if self.appear_then_click(self.I_GUILD_SHRINE, interval=1):
    #             continue
    #         if self.appear(self.I_FANGSHOU, interval=1):
    #             break
    #         if self.appear(self.I_RYOU_DOKAN_CHECK, threshold=0.6):
    #             return
    #
    #     DOKAN_STATUS_str = self.O_DOKAN_STATUS.detect_text(self.device.image)
    #     logger.info(DOKAN_STATUS_str)
    #     if '挑战成功' in DOKAN_STATUS_str or '0次' in DOKAN_STATUS_str:
    #
    #         # 保持好习惯，一个任务结束了就返回到庭院，方便下一任务的开始
    #         self.goto_main()
    #         # 设置下次运行时间
    #         self.set_next_run(task='Dokan', finish=True, server=True, success=True)
    #         raise TaskEnd
    #     elif '集结中' in DOKAN_STATUS_str:
    #         self.goto_dokan()
    #         return True
    #     else:
    #         self.open_dokan()
    #         return False

    def open_dokan(self):

        # 判断是否需要建立道馆
        count = 0
        while 1:
            self.screenshot()
            if self.appear_then_click(self.I_CREATE_DAOGUAN_SURE, interval=1):
                self.screenshot()
                if not self.appear(self.I_CREATE_DAOGUAN_SURE, interval=1):
                    break
                continue
            if not self.appear(self.I_CREATE_DAOGUAN, interval=1):
                break
            if self.appear_then_click(self.I_CREATE_DAOGUAN, interval=1):
                count += 1
                if count < 3:
                    continue
                break
            # if self.appear(self.I_CREATE_DAOGUAN, interval=0.8):
            #     break
        count = 0
        num = 0
        while 1:
            self.screenshot()

            DOKAN_1 = self.O_DOKAN_READY_SEL1.ocr_digit(self.device.image)
            DOKAN_2 = self.O_DOKAN_READY_SEL2.ocr_digit(self.device.image)
            DOKAN_3 = self.O_DOKAN_READY_SEL3.ocr_digit(self.device.image)
            DOKAN_4 = self.O_DOKAN_READY_SEL4.ocr_digit(self.device.image)

            if DOKAN_1 == 0 or DOKAN_2 == 0 or DOKAN_3 == 0 or DOKAN_4 == 0:
                count += 1
                if count < 5:
                    continue
            else:
                break

        DOKAN_list = [DOKAN_1, DOKAN_2, DOKAN_3, DOKAN_4]
        DOKAN_list_sort = sorted(DOKAN_list)
        DOKAN_click_list = [self.O_DOKAN_READY_SEL1, self.O_DOKAN_READY_SEL2, self.O_DOKAN_READY_SEL3,
                            self.O_DOKAN_READY_SEL4]

        while 1:
            DOKAN_index = DOKAN_list.index(DOKAN_list_sort[num])

            if self.click(DOKAN_click_list[DOKAN_index], interval=1):
                if num < 4:
                    num += 1
                else:
                    num = 0

            self.screenshot()
            if self.appear(self.I_NEWTZ, interval=1):
                break

        while 1:
            self.screenshot()
            if self.appear_then_click(self.I_NEWTZ, interval=1):
                continue
            if self.appear_then_click(self.I_OK, interval=1):
                count += 1
                if count < 3:
                    continue
                break
            if self.appear(self.I_RYOU_DOKAN_CHECK, threshold=0.6):
                break

    def get_current_scene(self, reuse_screenshot: bool = True):
        ''' 检测当前场景
        '''
        if not reuse_screenshot:
            self.screenshot()
        logger.info(f"get_current_scene={reuse_screenshot}")
        # 场景检测：阴阳竂
        if self.appear(self.I_SCENE_RYOU, threshold=0.8):
            return False, DokanScene.RYOU_DOKAN_RYOU

        # 状态：判断是否集结中
        # if self.ocr_appear(self.O_DOKAN_GATHERING):
        if self.appear(self.I_RYOU_DOKAN_GATHERING, threshold=0.95):
            return True, DokanScene.RYOU_DOKAN_SCENE_GATHERING
        # 状态：是否在等待馆主战
        # if self.ocr_appear(self.O_DOKAN_BOSS_WAITING):
        if self.appear(self.I_DOKAN_BOSS_WAITING):
            return True, DokanScene.RYOU_DOKAN_SCENE_BOSS_WAITING

        # 状态：检查右下角有没有挑战？通常是失败了，并退出来到集结界面，可重新开始点击右下角挑战进入战斗
        elif self.appear(self.I_RYOU_DOKAN_START_CHALLENGE, 0.95):
            return True, DokanScene.RYOU_DOKAN_SCENE_START_CHALLENGE

        # # 状态：进入战斗，待开始
        # elif self.appear(self.I_RYOU_DOKAN_IN_FIELD, threshold=0.85):
        #     return True, DokanScene.RYOU_DOKAN_SCENE_IN_FIELD
        # 状态：战斗结算，可能是打完小朋友了，也可能是失败了。
        if self.appear(self.I_RYOU_DOKAN_BATTLE_OVER, threshold=0.85):
            return True, DokanScene.RYOU_DOKAN_SCENE_BATTLE_OVER

        # 状态：达到失败次数，CD中
        if self.appear(self.I_RYOU_DOKAN_CD, threshold=0.8):
            return True, DokanScene.RYOU_DOKAN_SCENE_CD

        # # 状态：加油中，左下角有鼓
        # if self.appear_then_click(self.I_RYOU_DOKAN_CHEERING, threshold=0.8) or self.appear(
        #         self.I_RYOU_DOKAN_CHEERING_GRAY, threshold=0.8):
        #     return True, DokanScene.RYOU_DOKAN_SCENE_CHEERING
        # # 状态：战斗中，左上角的加油图标
        # if self.appear(self.I_RYOU_DOKAN_FIGHTING, threshold=0.8):
        #     return True, DokanScene.RYOU_DOKAN_SCENE_FIGHTING
        # if self.appear(self.I_RYOU_DOKAN_FAILED_VOTE_NO):
        #     return True, DokanScene.RYOU_DOKAN_SCENE_FAILED_VOTE_NO

        # 状态：道馆已经结束，图片位置会偏移，换OCR
        if self.ocr_appear(self.O_DOKAN_SUCCEEDED):
            # if self.appear(self.I_RYOU_DOKAN_FINISHED, threshold=0.8):
            return True, DokanScene.RYOU_DOKAN_SCENE_FINISHED

        return False, DokanScene.RYOU_DOKAN_SCENE_UNKNOWN


# def test_goto_main():
#     from module.config.config import Config
#     from module.device.device import Device
#     from tasks.GameUi.page import page_dokan
#
#     config = Config('oas1')
#     device = Device(config)
#     t = ScriptTask(config, device)
#     # t.run()
#     t.ui_current = page_dokan
#     t.ui_goto(page_main)


if __name__ == "__main__":
    from module.config.config import Config
    from module.device.device import Device

    config = Config('mi')
    device = Device(config)
    t = ScriptTask(config, device)
    t.run()

    # test_ocr_locate_dokan_target()
    # test_anti_detect_random_click()
    # test_goto_main()
