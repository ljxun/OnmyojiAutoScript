# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
import time

import numpy as np
from cached_property import cached_property
from datetime import timedelta, datetime
from enum import Enum
from module.atom.click import RuleClick
from module.exception import TaskEnd
from module.logger import logger
from tasks.Component.GeneralBattle.general_battle import GeneralBattle
from tasks.Component.GeneralInvite.general_invite import GeneralInvite
from tasks.Component.GeneralRoom.general_room import GeneralRoom
from tasks.Component.ReplaceShikigami.replace_shikigami import ReplaceShikigami
from tasks.Component.SwitchSoul.switch_soul import SwitchSoul
from tasks.Exploration.assets import ExplorationAssets
from tasks.Exploration.config import ChooseRarity, UpType
from tasks.Exploration.config import ExplorationLevel
from tasks.GameUi.page import page_exploration, page_main
from tasks.Utils.config_enum import ShikigamiClass


class Scene(Enum):
    UNKNOWN = 0  #
    WORLD = 1  # 探索大世界
    ENTRANCE = 2  # 入口弹窗
    MAIN = 3  # 探索里面
    BATTLE_PREPARE = 4  # 战斗准备
    BATTLE_FIGHTING = 5  # 战斗中
    TEAM = 6  # 组队


class BaseExploration(GeneralBattle, GeneralRoom, GeneralInvite, ReplaceShikigami, SwitchSoul, ExplorationAssets):
    last_scene_log = None  # 新增：用于缓存上一次的日志内容

    @cached_property
    def _config(self):
        self.config.exploration.general_battle_config.lock_team_enable = True
        limit_time = self.config.exploration.exploration_config.limit_time
        self.limit_time: timedelta = timedelta(
            hours=limit_time.hour,
            minutes=limit_time.minute,
            seconds=limit_time.second
        )
        return self.config.model.exploration

    def get_current_scene(self, reuse_screenshot: bool = True) -> Scene:
        if not reuse_screenshot:
            self.screenshot()

        # 初始化 scene 变量
        scene = Scene.UNKNOWN
        if self.appear(self.I_CHECK_EXPLORATION) and not (self.appear(self.I_E_SETTINGS_BUTTON) or self.appear(self.I_E_AUTO_ROTATE_ON) or self.appear(self.I_E_AUTO_ROTATE_OFF)):
            scene = Scene.WORLD
            log_message = "在探索大世界中"
        elif self.appear(self.I_BACK_RED) and self.appear(self.I_E_EXPLORATION_CLICK):
            scene = Scene.ENTRANCE
            log_message = "在探索入口弹窗中"
        elif self.appear(self.I_E_SETTINGS_BUTTON) or self.appear(self.I_E_AUTO_ROTATE_ON) or self.appear(self.I_E_AUTO_ROTATE_OFF) or self.appear(self.I_LOCK_ON) or self.appear(self.I_LOCK_OFF):
            scene = Scene.MAIN
            log_message = "在探索里面"
        elif self.is_in_prepare():
            scene = Scene.BATTLE_PREPARE
            log_message = "在战斗准备"
        elif self.is_in_battle():
            scene = Scene.BATTLE_FIGHTING
            log_message = "在战斗中"
        elif self.is_in_room() or self.appear(self.I_CREATE_ENSURE):
            scene = Scene.TEAM
            log_message = "在组队界面中"
        elif self.appear(self.I_CHECK_MAIN):
            scene = Scene.UNKNOWN
            log_message = "在庭院中"
            # 探索页面
            self.ui_goto_page(page_exploration)
        else:
            log_message = "未知"

        # 新增：判断日志是否重复，避免重复打印
        if log_message != self.last_scene_log:
            logger.info(f"当前场景: {log_message}")
            self.last_scene_log = log_message

        return scene

    def pre_process(self):
        explorationConfig = self._config
        if explorationConfig.switch_soul_config.enable:
            self.run_switch_soul(explorationConfig.switch_soul_config.switch_group_team)

        if explorationConfig.switch_soul_config.enable_switch_by_name:
            self.run_switch_soul_by_name(explorationConfig.switch_soul_config.group_name,
                                         explorationConfig.switch_soul_config.team_name)

        # 开启加成
        con = self.config.exploration.exploration_config
        if con.buff_gold_50_click or con.buff_gold_100_click or con.buff_exp_50_click or con.buff_exp_100_click:
            self.ui_goto_page(page_main)
            self.open_buff()
            if con.buff_gold_50_click:
                self.gold_50()
            if con.buff_gold_100_click:
                self.gold_100()
            if con.buff_exp_50_click:
                self.exp_50()
            if con.buff_exp_100_click:
                self.exp_100()
            self.close_buff()

    def post_process(self):
        con = self._config.exploration_config
        if con.buff_gold_50_click or con.buff_gold_100_click or con.buff_exp_50_click or con.buff_exp_100_click:
            self.ui_goto_page(page_main)
            self.open_buff()
            self.gold_50(is_open=False)
            self.gold_100(is_open=False)
            self.exp_50(is_open=False)
            self.exp_100(is_open=False)
            self.close_buff()
        self.set_next_run(task='Exploration', success=True, finish=False)
        raise TaskEnd

    # 打开指定的章节：
    def open_expect_level(self, goal_level):
        swipeCount = 0
        while 1:
            # 判断有无目标章节
            self.screenshot()
            # 获取当前章节名
            results = self.O_E_EXPLORATION_LEVEL_NUMBER.detect_and_ocr(self.device.image)
            text1 = [result.ocr_text for result in results]
            logger.info(f"当前章节: {text1}")
            if not text1:
                self.ui_click_until_disappear(self.I_BACK_RED)
                continue
            logger.info(f"目标章节: {goal_level}")

            # 判断目标章节与当前章节的相对位置
            should_swipe_up = self._should_swipe_up(text1, goal_level)

            # 判断当前章节有无目标章节
            result = set(text1).intersection({goal_level})
            # 有则跳出检测
            if self.appear(self.I_E_EXPLORATION_CLICK) or result and len(result) > 0:
                break
            if self.appear_then_click(self.I_UI_CONFIRM, interval=1):
                continue
            if self.appear_then_click(self.I_UI_CONFIRM_SAMLL, interval=1):
                continue
            self.device.click_record_clear()

            # 根据判断结果决定滑动方向
            if should_swipe_up:
                self.swipe(self.S_SWIPE_LEVEL_UP)
            else:
                self.swipe(self.S_SWIPE_LEVEL_DOWN)

            swipeCount += 1
            if swipeCount >= 25:
                return False

        # 选中对应章节
        while 1:
            self.screenshot()
            if self.appear_then_click(self.I_UI_CONFIRM, interval=1):
                continue
            if self.appear_then_click(self.I_UI_CONFIRM_SAMLL, interval=1):
                continue
            self.O_E_EXPLORATION_LEVEL_NUMBER.keyword = goal_level
            if self.O_E_EXPLORATION_LEVEL_NUMBER.ocr(self.device.image):
                logger.info(f"已找到目标章节: {goal_level} {self.O_E_EXPLORATION_LEVEL_NUMBER.area}")
                x = self.O_E_EXPLORATION_LEVEL_NUMBER.area[0]
                y = self.O_E_EXPLORATION_LEVEL_NUMBER.area[1]
                w = self.O_E_EXPLORATION_LEVEL_NUMBER.area[2]
                h = self.O_E_EXPLORATION_LEVEL_NUMBER.area[3]
                CLICK_TMP = RuleClick(roi_front=(x,y+30,w,h), roi_back=(x,y+30,w,h), name="CLICK_TMP")
                self.click(CLICK_TMP)
                self.wait_until_appear(self.I_E_EXPLORATION_CLICK, wait_time=3)
            if self.appear(self.I_E_EXPLORATION_CLICK):
                break
            if self.is_in_room():
                break

        return True

    # 候补：
    def enter_settings_and_do_operations(self):
        # 打开设置
        while 1:
            self.screenshot()
            if self.appear(self.I_E_OPEN_SETTINGS):
                logger.info("Open settings")
                break
            if self.is_in_battle():
                logger.warning('Opening settings failed due to now in battle')
                return
            if self.click(self.C_CLICK_SETTINGS, interval=2):
                continue

        # 候补出战数量识别
        self.screenshot()
        if not self.appear(self.I_E_OPEN_SETTINGS):
            logger.warning('Opening settings failed due to now in battle')
            return
        cu, res, total = self.O_E_ALTERNATE_NUMBER.ocr(self.device.image)
        if cu >= 20:
            logger.info(f"当前狗粮数量：{cu}, 大于20，无需补充")
            logger.info("Alternate number is full")
            self.ui_click_until_disappear(self.I_E_SURE_BUTTON)
            return
        else:
            logger.info(f"当前狗粮数量：{cu}, 小于20，补充狗粮")
            self.add_shiki()

    # 添加式神
    def add_shiki(self, screenshot=True):
        if screenshot:
            self.screenshot()
            if not self.appear(self.I_E_OPEN_SETTINGS):
                logger.warning('Opening settings failed due to now in battle')
                return
        choose_rarity = self._config.exploration_config.choose_rarity
        rarity = ShikigamiClass.N if choose_rarity == ChooseRarity.N else ShikigamiClass.MATERIAL
        self.switch_shikigami_class(rarity)

        self.click(self.C_CLICK_STANDBY_TEAM)
        # 移动至未候补的狗粮
        while 1:
            # 慢一点
            time.sleep(0.5)
            self.screenshot()
            if not self.appear(self.I_E_OPEN_SETTINGS):
                logger.warning('Opening settings failed due to now in battle')
                return
            if self.appear(self.I_E_RATATE_EXSIT):
                self.swipe(self.S_SWIPE_SHIKI_TO_LEFT)
            else:
                break
        while 1:
            # 候补出战数量识别
            self.screenshot()
            if not self.appear(self.I_E_OPEN_SETTINGS):
                logger.warning('Opening settings failed due to now in battle')
                return
            cu, res, total = self.O_E_ALTERNATE_NUMBER.ocr(self.device.image)
            if cu >= 40:
                logger.info(f"当前狗粮数量：{cu}, 大于40，补充完毕")
                break
            self.swipe(self.S_SWIPE_SHIKI_TO_LEFT_ONE)
            # 慢一点
            time.sleep(0.5)
            self.screenshot()
            self.click(self.L_ROTATE_1)
            self.device.click_record_clear()

        self.appear_then_click(self.I_E_SURE_BUTTON)

    # 找up按钮
    def search_up_fight(self, up_type: UpType = None):
        if up_type is None:
            up_type = self._config.exploration_config.up_type
        if up_type != UpType.ALL:
            match up_type:
                case UpType.EXP:
                    find_flag = self.I_UP_EXP
                case UpType.COIN:
                    find_flag = self.I_UP_COIN
                case UpType.DARUMAA:
                    find_flag = self.I_UP_DARUMA
                case _:
                    find_flag = self.I_UP_EXP
            appear = self.appear(find_flag)
            if not appear:
                return None
            logger.info(f'Found up type: {up_type} at  {find_flag.roi_front}')
            x, y, _, _ = find_flag.roi_front
            x_center, y_center = find_flag.front_center()
            roi_back_y = max(0, y - 300)
            roi_back_h = y - 20 - roi_back_y
            roi_back_x = max(0, x - 160)
            roi_back_w = min(1280, x + 200) - roi_back_x
            # self.I_NORMAL_BATTLE_BUTTON.roi_back = [roi_back_x, roi_back_y, roi_back_w, roi_back_h]
            logger.info(f'It will search normal battle button at {roi_back_x, roi_back_y, roi_back_w, roi_back_h}')
            matches = self.I_NORMAL_BATTLE_BUTTON.match_all(
                image=self.device.image,
                threshold=0.9,
                roi=[roi_back_x, roi_back_y, roi_back_w, roi_back_h]
            )
            if not matches:
                return None
            distances = []
            for match in matches:
                x_match, y_match = match[1], match[2]
                distance = np.linalg.norm(
                    np.array([x_center, y_center]) - np.array([x_match, y_match])
                )
                distances.append((distance, match))
            distances.sort(key=lambda x: x[0], reverse=False)
            match = distances[0][1]
            roi_front = list(match[1:])  # x,y,w,h
            self.I_NORMAL_BATTLE_BUTTON.roi_front = roi_front
            logger.info(f"Found normal battle button at {roi_front}")
            return self.I_NORMAL_BATTLE_BUTTON
        if self.appear(self.I_NORMAL_BATTLE_BUTTON):
            return self.I_NORMAL_BATTLE_BUTTON
        return None

    def check_boss_number(self, con_scrolls):
        if con_scrolls.check_boss_num:
            cu, res, total = self.O_CHECK_BOSS_NUM.ocr(self.device.image)
            message = f"当前鬼王掉落数量: {cu} / {total} 剩余: {res}"
            logger.info(message)
            if cu + res == total and cu == 50 and total == 50:
                self.push_notify(message)
                self.set_next_run()
                raise TaskEnd

    def activate_realm_raid(self, con_scrolls, con) -> None:
        # 判断是否开启突破票检测
        if not con_scrolls.scrolls_enable:
            return
        self.screenshot()
        if self.appear(self.I_E_EXPLORATION_CLICK) or self.appear(self.I_EXP_CREATE_TEAM):
            cu, res, total = self.O_REALM_RAID_NUMBER1.ocr(self.device.image)
        else:
            cu, res, total = self.O_REALM_RAID_NUMBER.ocr(self.device.image)

        # 判断突破票数量

        # 添加校验：只有当总值等于30时才认为是突破券数量
        if total != 30:
            logger.warning(f"识别到的总值{total}不是30，可能不是突破券，跳过此次识别")
            return  
    
        if cu < con_scrolls.scrolls_threshold:
            return
        logger.info(f"突破票数量:{cu}, 结束探索任务")
        # 关闭加成
        if self.appear(self.I_RED_CLOSE):
            self.ui_click_until_disappear(self.I_RED_CLOSE)
        if self.appear(self.I_UI_CANCEL):
            self.ui_click_until_disappear(self.I_UI_CANCEL)
        if self.appear(self.I_UI_CANCEL_SAMLL):
            self.ui_click_until_disappear(self.I_UI_CANCEL_SAMLL)
        self.ui_goto_page(page_main)
        if con.buff_gold_50_click or con.buff_gold_100_click or con.buff_exp_50_click or con.buff_exp_100_click:
            self.open_buff()
            self.gold_50(is_open=False)
            self.gold_100(is_open=False)
            self.exp_50(is_open=False)
            self.exp_100(is_open=False)
            self.close_buff()

        # 设置下次执行行时间
        logger.info("RealmRaid and Exploration  set_next_run !")
        cd = con_scrolls.scrolls_cd
        timedelta_cd = timedelta(hours=cd.hour, minutes=cd.minute, seconds=cd.second)
        datetime_now = datetime.now()
        self.set_next_run(task='Exploration', target=datetime_now + timedelta_cd)
        # 个突
        self.set_next_run(task='RealmRaid', target=datetime_now)
        # 御魂整理
        self.set_next_run(task='SoulsTidy', target=datetime_now)
        # 绘卷捐赠
        self.set_next_run(task='MemoryScrolls', target=datetime_now)
        raise TaskEnd

    #
    def check_exit(self, check_flag: bool = True) -> bool:

        # 判断是否开启绘卷模式
        if not self._config.scrolls.scrolls_enable:
            # True 表示要退出这个任务
            if self.current_count >= self.limit_count:
                logger.info('探索次数已到, 结束探索任务')
                return True
            if datetime.now() - self.start_time >= self.limit_time:
                logger.info('探索时间限制已到, 结束探索任务')
                return True
        else:
            if check_flag:
                self.activate_realm_raid(self._config.scrolls, self._config.exploration_config)
        return False

    def quit_explore(self):
        logger.info('退出本次探索')
        while 1:
            self.screenshot()
            if self.appear(self.I_BACK_RED) and self.appear(self.I_E_EXPLORATION_CLICK):
                break
            if self.appear(self.I_CHECK_EXPLORATION) and not (self.appear(self.I_E_SETTINGS_BUTTON) or self.appear(self.I_E_AUTO_ROTATE_ON) or self.appear(self.I_E_AUTO_ROTATE_OFF)):
                break
            if self.appear(self.I_BUFF_1):
                break
            if self.appear_then_click(self.I_E_EXIT_CONFIRM, interval=0.8):
                continue
            if self.appear_then_click(self.I_BACK_YELLOW, interval=1.5):
                continue

    def fire(self, button) -> bool:
        self.ui_click_until_disappear(button, interval=3)
        if (self.appear(self.I_E_SETTINGS_BUTTON) or
                self.appear(self.I_E_AUTO_ROTATE_ON) or
                self.appear(self.I_E_AUTO_ROTATE_OFF)):
            # 如果还在探索说明，这个是显示滑动导致挑战按钮不在范围内
            logger.warning('Fire button disappear, but still in exploration')
            return False
        self.run_general_battle(self._config.general_battle_config)
        return True

    def get_box(self):
        if self.appear(self.I_TREASURE_BOX_CLICK):
            # 宝箱
            logger.info('Treasure box appear, get it.')
            self.ui_click_until_disappear(self.I_TREASURE_BOX_CLICK)
        if self.appear(self.I_MAP_BOX_CLICK):
            logger.info('Map box appear, get it.')
            # 地图宝箱
            while 1:
                self.screenshot()
                if not self.appear(self.I_MAP_BOX_CLICK):
                    break
                if self.appear_then_click(self.I_MAP_BOX_CLICK):
                    # self.save_image(image_type=True, push_flag=True, wait_time=0)
                    # x, y = self.I_MAP_BOX_CLICK.coord_center()
                    # self.device.click(x=x, y=y, control_name=self.I_MAP_BOX_CLICK.name)
                    time.sleep(0.5)

    def _should_swipe_up(self, current_levels, target_level):
        """
        判断是否需要向上滑动
        小章节在上面，大章节在下面
        """
        # 获取所有章节列表
        exploration_levels = list(ExplorationLevel)

        # 找到目标章节在枚举中的索引
        target_index = -1
        for i, level in enumerate(exploration_levels):
            if level.value == target_level:
                target_index = i
                break

        if target_index == -1:
            return True  # 无法找到目标章节，默认向上滑动

        # 检查当前显示的章节
        for current_level in current_levels:
            # 找到当前章节在枚举中的索引
            for i, level in enumerate(exploration_levels):
                if level.value == current_level:
                    # 如果当前显示的章节索引大于目标章节索引
                    # 说明目标章节在上方，需要向上滑动
                    if i > target_index:
                        return True
                    break

        # 默认向下滑动（目标章节在下方）
        return False


if __name__ == "__main__":
    from module.config.config import Config

    config = Config('oas1')
    t = BaseExploration(config)
    t.screenshot()

    # IMAGE_FILE = r"C:\Users\萌萌哒\Desktop\QQ20240818-163854.png"
    # image = load_image(IMAGE_FILE)
    # t.device.image = image
    while 1:
    # print(t.search_up_fight(UpType.EXP))
        t.screenshot()
        print(t.I_UP_DARUMA.test_match(t.device.image))
        time.sleep(0.2)
    # Image.fromarray(t.device.image.astype(np.uint8)).show()

