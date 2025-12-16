# This Python file uses the following encoding: utf-8
# @brief    Ryou Dokan Toppa (阴阳竂道馆突破功能)
# @author   jackyhwei
# @note     draft version without full test
# github    https://github.com/roarhill/oas
import time
from time import sleep

import cv2
import re
import tasks.Dokan.inner_page as ipages
from tasks.Dokan.inner_page import page_dokan
from datetime import datetime, timedelta
from enum import Enum
from module.atom.click import RuleClick
from module.atom.image import RuleImage
from module.atom.ocr import RuleOcr
from module.base.timer import Timer
from module.exception import TaskEnd
from module.logger import logger
from tasks.Component.GeneralBattle.config_general_battle import GreenMarkType, GeneralBattleConfig
from tasks.Component.GeneralBattle.general_battle import GeneralBattle
from tasks.Component.GeneralInvite.assets import GeneralInviteAssets
from tasks.Component.SwitchSoul.switch_soul import SwitchSoul
from tasks.Dokan.assets import DokanAssets
from tasks.Dokan.config import Dokan
from tasks.GameUi.page import PageRegistry
from tasks.GameUi.page import page_guild
from tasks.RichMan.assets import RichManAssets


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
    # 再战道馆投票
    RYOU_DOKAN_SCENE_FAILED_VOTE_NO = 7
    # 阴阳竂
    RYOU_DOKAN_RYOU = 8
    # 战斗结算，可能是打完小朋友了，也可能是失败了。
    RYOU_DOKAN_SCENE_BATTLE_OVER = 9
    # 等待BOSS战
    RYOU_DOKAN_SCENE_BOSS_WAITING = 10

    # 正在查找道馆,处于地图界面
    RYOU_DOKAN_SCENE_FINDING_DOKAN = 97

    def __str__(self):
        return self.name.title()


class ScriptTask(GeneralBattle, SwitchSoul, DokanAssets, RichManAssets):
    """ 道馆 """
    team_switched: bool = False
    # 战斗次数
    battle_count: int = 0
    # 寮友进入道馆次数
    goto_dokan_num: int = 0
    # 今日是否第一次道馆 是否放弃
    dokan_quit: bool = False
    # 上一个场景
    last_scene = None
    # 查找的所有道馆
    find_dokan_list = []
    # 开启的是否为福利寮
    open_welfare = False
    # 福利寮名单
    welfare_names = None
    # 福利寮创建时间
    create_doukan_time = None
    # 记录开启道馆时间,两次道馆要间隔15分钟
    first_open_dokan_time = None
    # 道馆可战斗次数
    dokan_battle_number = 0

    def welfare_name_str(self):
        """
        从配置文件加载福利寮名单，只加载一次
        """
        welfare_file = 'config/福利寮名单.txt'
        try:
            with open(welfare_file, 'r', encoding='utf-8') as file:
                # 读取所有行并放到一个列表中
                lines = file.readlines()
                # 去除每行末尾的换行符并过滤空行
                content = [line.strip() for line in lines if line.strip()]
                return content
        except FileNotFoundError:
            self.push_notify(content=f"福利寮名单文件未找到: {config_path}")
            logger.warning(f"福利寮名单文件未找到: {config_path}")
            return ''
        except Exception as e:
            self.push_notify(content=f"读取福利寮名单时出错: {e}")
            logger.error(f"读取福利寮名单时出错: {e}")
            return ''

    def check_current_weekday(self, success=False):
        today = datetime.today()
        current_weekday = today.weekday()  # 周一为0，周日为6
        next_run_weekday = 1
        if current_weekday in [4, 5, 6] or (current_weekday == 3 and success):
            self.next_run_week(next_run_weekday)
            self.finish_task()

    def run(self):
        # 检查今天周几
        self.check_current_weekday()

        cfg: Dokan = self.config.dokan

        # 发送请求检查福利寮开启情况
        if cfg.welfare_config.enable_get_requests:
            response = self.get_requests(cfg.welfare_config.get_requests_url)
            json_response = response.json()
            datetime_now = datetime.now()
            # 解析时间戳并设置创建道馆时间
            timestamp = json_response.get('timestamp')
            if not timestamp:
                self.set_next_run(target=datetime_now + timedelta(minutes=3))
                self.finish_task()
            # 解析时间戳获取时分秒
            timestamp_time = datetime.fromtimestamp(timestamp)
            logger.info(f"福利道馆创建时间: {timestamp_time}")
            # 检查响应有效性
            if not json_response or not json_response.get('est', False):
                logger.warning(f"福利道馆未开启: {json_response}")
                if datetime_now.time() > timestamp_time.time():
                    self.set_next_run(target=datetime_now + timedelta(minutes=3))
                    self.finish_task()
                self.set_next_run(target=datetime.combine(datetime_now.date(), timestamp_time.time()))
                self.finish_task()

            # 获取明天的日期，但使用timestamp的时分秒
            tomorrow_date = (datetime_now + timedelta(days=1)).date()
            self.create_doukan_time = datetime.combine(tomorrow_date, timestamp_time.time())
            logger.info(f"明天道馆执行时间: {self.create_doukan_time}")

        # 加载福利寮名单
        self.welfare_names = self.welfare_name_str()

        # 开始道馆流程
        self.goto_dokan()
        self.dokan_process(cfg)

    def dokan_process(self, cfg: Dokan):
        # 开始道馆流程
        logger.info("开始道馆流程")
        scene_timer = Timer(50)
        scene_timer.start()
        timer_count = 1
        
        while 1:

            if scene_timer and scene_timer.reached():
                scene_timer.reset()
                if timer_count >= 100:
                    self.save_image(image_type=True, push_flag=True, content=f"道馆流程超时")
                    break
                timer_count += 1
                self.device.stuck_record_clear()
                self.device.stuck_record_add('BATTLE_STATUS_S')

            # 检测当前界面的场景
            in_dokan, current_scene = self.get_current_scene()

            # 如果当前不在道馆，或者被人工操作退出道馆了，重新尝试进入道馆
            if not in_dokan:
                try:
                    # 计算道馆战斗时间
                    if self.first_open_dokan_time is not None and self.dokan_battle_number == 2:
                        MIN_DOKAN_TIME = timedelta(minutes=15)
                        dakan_time = datetime.now() - self.first_open_dokan_time
                        logger.warning(f"道馆持续时间: {dakan_time}")
                        if dakan_time < MIN_DOKAN_TIME:
                            next_run_time = self.first_open_dokan_time + MIN_DOKAN_TIME
                            logger.warning(f"道馆战斗时间不足15分钟，设置下次运行时间: {next_run_time}")
                            self.set_next_run(target=next_run_time)
                            self.finish_task()
                        else:
                            logger.warning(f"道馆持续时间超过15分钟,直接进行下一次道馆")
                except TaskEnd:
                    # 重新抛出TaskEnd异常，这是正常的流程控制
                    self.finish_task()
                except Exception as e:
                    logger.error(f"道馆流程异常: {e}", exc_info=True)
                    self.save_image(image_type=True, push_flag=True, content=f"道馆流程异常: {e}")

                # 重置换阵容和是否为福利寮
                self.team_switched = False
                self.open_welfare = False

                # 重新尝试进入道馆
                self.goto_dokan()
                continue

            # 场景状态：道馆集结中
            if current_scene == DokanScene.RYOU_DOKAN_SCENE_GATHERING:
                self.goto_dokan_num = 0
            # 场景状态：等待馆主战开始
            elif current_scene == DokanScene.RYOU_DOKAN_SCENE_BOSS_WAITING:
                # 管理放弃第一次道馆
                if self.dokan_quit and self.config.dokan.dokan_config.dokan_enable:
                    logger.info("今日第一次道馆，放弃本次道馆")
                    time.sleep(5)
                    while 1:
                        self.screenshot()
                        if self.appear(self.I_CONTINUE_DOKAN, interval=1):
                            break
                        if self.appear(self.I_QUIT_DOKAN_OVER, interval=1):
                            time.sleep(5)
                            break
                        if self.appear_then_click(self.I_QUIT_DOKAN_SURE, interval=1):
                            continue
                        if self.appear_then_click(self.I_QUIT_DOKAN, interval=1):
                            continue

                # 非寮管理，检测到放弃突破，点击同意
                if self.appear_then_click(self.I_CROWD_QUIT_DOKAN, interval=1):
                    logger.info("同意, 放弃本次道馆")
                    continue

            # 场景状态：右下角挑战
            elif current_scene == DokanScene.RYOU_DOKAN_SCENE_START_CHALLENGE:
                self.appear_then_click(self.I_RYOU_DOKAN_START_CHALLENGE, interval=1)
                time.sleep(1)
            # # 场景状态：进入战斗，待准备
            elif current_scene == DokanScene.RYOU_DOKAN_SCENE_IN_FIELD:
                # 战斗
                self.dokan_battle(cfg)
            # 投票
            elif current_scene == DokanScene.RYOU_DOKAN_SCENE_FAILED_VOTE_NO:
                if self.appear_then_click(self.I_QUIT_DOKAN_SURE, interval=1):
                    pass
                if self.appear_then_click(self.I_CONTINUE_DOKAN, interval=1):
                    logger.info("点击, 再战道馆")
                    time.sleep(2)
                    continue

    def get_current_scene(self):
        """ 检测当前场景 """
        self.screenshot()
        self.device.click_record_clear()

        # 再战道馆
        if self.appear(self.I_CONTINUE_DOKAN):
            current_scene = DokanScene.RYOU_DOKAN_SCENE_FAILED_VOTE_NO
            if current_scene != self.last_scene:
                logger.info(f"再战道馆，投票场景")
                self.last_scene = current_scene
            return True, DokanScene.RYOU_DOKAN_SCENE_FAILED_VOTE_NO
        # 场景检测：阴阳竂
        if self.appear(self.I_SCENE_RYOU, threshold=0.8):
            logger.info(f"在阴阳寮中")
            return False, DokanScene.RYOU_DOKAN_RYOU
        # 场景检测：在庭院中
        if self.appear(self.I_BUFF_1, threshold=0.8):
            logger.info(f"在庭院中")
            return False, DokanScene.RYOU_DOKAN_SCENE_UNKNOWN
        # 场景检测：选寮界面
        if self.appear(self.I_FANGSHOU, threshold=0.8):
            logger.info(f"在选寮界面中")
            return False, DokanScene.RYOU_DOKAN_SCENE_FINDING_DOKAN
        # 状态：判断是否集结中
        if self.appear(self.I_RYOU_DOKAN_GATHERING, threshold=0.95):
            current_scene = DokanScene.RYOU_DOKAN_SCENE_GATHERING
            if current_scene != self.last_scene:
                logger.info(f"道馆集结中")
                self.last_scene = current_scene
            return True, DokanScene.RYOU_DOKAN_SCENE_GATHERING
        # 状态：是否在等待馆主战
        if self.appear(self.I_DOKAN_BOSS_WAITING):
            current_scene = DokanScene.RYOU_DOKAN_SCENE_BOSS_WAITING
            if current_scene != self.last_scene:
                logger.info(f"等待馆主战中")
                self.last_scene = current_scene
            return True, DokanScene.RYOU_DOKAN_SCENE_BOSS_WAITING

        # 状态：检查右下角有没有挑战？通常是失败了，并退出来到集结界面，可重新开始点击右下角挑战进入战斗
        if self.appear(self.I_RYOU_DOKAN_START_CHALLENGE, 0.95):
            if self.appear_rgb(self.I_RYOU_DOKAN_START_CHALLENGE):
                logger.info(f"挑战次数已重置")
                time.sleep(1)
                return True, DokanScene.RYOU_DOKAN_SCENE_START_CHALLENGE
            else:
                current_scene = DokanScene.RYOU_DOKAN_SCENE_GATHERING
                if current_scene != self.last_scene:
                    logger.info(f"道馆集结中,挑战未就绪")
                    self.last_scene = current_scene
                return True, DokanScene.RYOU_DOKAN_SCENE_GATHERING

        # 状态：进入战斗，待开始
        if self.appear(self.I_RYOU_DOKAN_IN_FIELD, threshold=0.85):
            logger.info(f"开始点击准备中")
            return True, DokanScene.RYOU_DOKAN_SCENE_IN_FIELD
        # 状态：战斗结算，可能是打完小朋友了，也可能是失败了。
        if self.appear(self.I_RYOU_DOKAN_BATTLE_OVER, threshold=0.85):
            logger.info(f"打完看到魂奖励中")
            self.save_image()
            self.appear_then_click(self.I_RYOU_DOKAN_BATTLE_OVER)
            return True, DokanScene.RYOU_DOKAN_SCENE_BATTLE_OVER
        # 如果出现失败 就点击
        if self.appear(GeneralBattle.I_FALSE, threshold=0.8):
            self.appear_then_click(GeneralBattle.I_FALSE)
            logger.info("战斗失败，返回")
            return True, DokanScene.RYOU_DOKAN_SCENE_BATTLE_OVER
        # 如果出现成功 就点击
        if self.appear(GeneralBattle.I_WIN, threshold=0.8):
            self.appear_then_click(GeneralBattle.I_WIN)
            logger.info("战斗成功，鼓，返回")
            return True, DokanScene.RYOU_DOKAN_SCENE_BATTLE_OVER
        # 状态：达到失败次数，CD中
        if self.appear(self.I_RYOU_DOKAN_CD, threshold=0.8):
            current_scene = DokanScene.RYOU_DOKAN_SCENE_CD
            if current_scene != self.last_scene:
                logger.info(f"等待挑战次数，观战中")
                self.last_scene = current_scene
            return True, DokanScene.RYOU_DOKAN_SCENE_CD

        # 如果出现馆主战斗失败 就点击，返回False。
        if self.appear(self.I_RYOU_DOKAN_FAIL, threshold=0.8):
            self.appear_then_click(self.I_RYOU_DOKAN_FAIL)
            logger.info("馆主战斗失败，返回")
            return True, DokanScene.RYOU_DOKAN_SCENE_UNKNOWN
        # 如果出现打败馆主的赢，就点击
        if self.appear(self.I_RYOU_DOKAN_WIN, threshold=0.8):
            self.appear_then_click(self.I_RYOU_DOKAN_WIN)
            logger.info("馆主的赢，就点击.")
            return True, DokanScene.RYOU_DOKAN_SCENE_UNKNOWN

        return True, DokanScene.RYOU_DOKAN_SCENE_UNKNOWN

    def dokan_battle(self, cfg: Dokan):
        """ 道馆战斗
        道馆集结结束后会自动进入战斗，打完一个也会自动进入下一个，因此直接点击右下角的开始
        :return: 战斗成功(True) or 战斗失败(False) or 区域不可用（False）
        """
        # 更换队伍
        if self.open_welfare == False:
            config: GeneralBattleConfig = cfg.general_battle_config
        else:
            config: GeneralBattleConfig = cfg.general_battle_config2
        if not self.team_switched:
            logger.info(f"switch team preset: enable={config.preset_enable}, preset_group={config.preset_group}, preset_team={config.preset_team}")
            self.switch_preset_team(config.preset_enable, config.preset_group, config.preset_team)
            self.team_switched = True
            # 切完队伍后有时候会卡顿，先睡一觉，防止快速跳到绿标流程，导致未能成功绿标

        while 1:
            self.screenshot()

            # 打完一个小朋友，自动进入下一个小朋友
            if self.appear(self.I_RYOU_DOKAN_IN_FIELD):
                self.battle_count += 1
                logger.info(f"第 {self.battle_count} 次战斗")
                self.ui_click_until_disappear(self.I_RYOU_DOKAN_IN_FIELD)
                # 绿标
                self.dokan_green_mark(config.green_enable, config.green_mark)
                self.device.click_record_clear()
                self.device.stuck_record_add('BATTLE_STATUS_S')

            # 战斗时间已到，无奖励，在等待馆主战场景
            if self.appear(self.I_DOKAN_BOSS_WAITING, threshold=0.8):
                logger.info(f"战斗时间已到，无奖励，等待馆主战中")
                break

            # 如果出现赢 就点击
            if self.appear(GeneralBattle.I_WIN, threshold=0.8):
                logger.info("战斗赢,红色鼓")
                self.ui_click_until_disappear(GeneralBattle.I_WIN)
                break

            # 如果出现打败馆主的赢，就点击
            if self.appear(self.I_RYOU_DOKAN_WIN, threshold=0.8):
                logger.info("馆主的赢，就点击.")
                self.ui_click_until_disappear(self.I_RYOU_DOKAN_WIN)
                break

            # 如果出现失败 就点击，返回False。
            if self.appear(GeneralBattle.I_FALSE, threshold=0.8):
                logger.info("战斗失败，返回")
                self.ui_click_until_disappear(GeneralBattle.I_FALSE)
                break

            # 如果出现馆主战斗失败 就点击，返回False。
            if self.appear(self.I_RYOU_DOKAN_FAIL, threshold=0.8):
                logger.info("馆主战斗失败，返回")
                self.ui_click_until_disappear(self.I_RYOU_DOKAN_FAIL)
                break

            # 如果领奖励
            if self.appear(self.I_RYOU_DOKAN_BATTLE_OVER, threshold=0.6):
                logger.info("领奖励,那个魂")
                self.save_image()
                self.ui_click_until_disappear(self.I_RYOU_DOKAN_BATTLE_OVER)
                break

            # 如果领奖励出现金币
            if self.appear(GeneralBattle.I_REWARD_GOLD, threshold=0.8):
                logger.info("领奖励,那个金币")
                self.ui_click_until_disappear(GeneralBattle.I_REWARD_GOLD)
                break

            # 如果开启战斗过程随机滑动
            if config.random_click_swipt_enable:
                logger.info("随机滑动....")
                logger.info("random swipt ...")
                self.random_click_swipt()

    def dokan_green_mark(self, enable: bool = False, mark_mode: GreenMarkType = GreenMarkType.GREEN_MAIN):
        """
        绿标， 如果不使能就直接返回
        :param enable:
        :param mark_mode:
        :return:
        """
        if enable:
            if self.dokan_wait_until_appear(self.I_GREEN_MARK, self.I_GREEN_MARK_1, wait_time=1):
                # logger.info("识别到绿标，返回")
                return
            else:
                logger.info("第一步识别绿标失败")
                # self.save_image(task_name="Dokan_greenmark_false_first", content="第一步识别绿标失败", push_flag=True, wait_time=0, image_type=True)
            # logger.info("Green is enable")
            x, y = None, None
            # logger.info(f"Green {mark_mode}")
            match mark_mode:
                case GreenMarkType.GREEN_LEFT1:
                    x, y = self.C_GREEN_LEFT_1.coord()
                case GreenMarkType.GREEN_LEFT2:
                    x, y = self.C_GREEN_LEFT_2.coord()
                case GreenMarkType.GREEN_LEFT3:
                    x, y = self.C_GREEN_LEFT_3.coord()
                case GreenMarkType.GREEN_LEFT4:
                    x, y = self.C_GREEN_LEFT_4.coord()
                case GreenMarkType.GREEN_LEFT5:
                    x, y = self.C_DOKAN_GREEN_LEFT_5.coord()
                case GreenMarkType.GREEN_MAIN:
                    x, y = self.C_GREEN_MAIN.coord()

            mark_timer = Timer(5)
            mark_timer.start()
            while 1:
                # 等待那个准备的消失
                self.ui_click_until_disappear(self.I_RYOU_DOKAN_IN_FIELD)
                # 点击坐标
                self.device.click(x, y)
                if self.dokan_wait_until_appear(self.I_GREEN_MARK, self.I_GREEN_MARK_1, wait_time=1):
                    logger.info("识别到绿标,返回")
                    # self.save_image(task_name="Dokan_greenmark_ok", content="点击绿标成功", push_flag=True, wait_time=0, image_type=True)
                    break
                else:
                    logger.info("识别到绿标失败")
                    # self.save_image(task_name="Dokan_greenmark_false", content="识别绿标超时", push_flag=True, wait_time=0, image_type=True)
                if mark_timer.reached():
                    # logger.warning("识别绿标超时,返回")
                    break
                # 判断有无坐标的偏移
                # self.appear_then_click(self.I_LOCAL)

    def dokan_wait_until_appear(self, target, target2, wait_time) -> bool:
        wait_timer = Timer(wait_time)
        wait_timer.start()
        while 1:
            self.screenshot()
            if wait_timer and wait_timer.reached():
                logger.warning(f"Wait until appear {target.name} timeout")
                return False
            if self.appear(target) or self.appear(target2):
                return True

    def goto_dokan(self):

        if self.is_in_dokan():
            return True

        # 进入选择寮界面
        self.ui_goto_page(page_guild)

        while 1:
            self.screenshot()

            if self.appear_then_click(self.I_DAOGUAN, interval=1):
                continue
            if self.appear_then_click(self.I_GUILD_SHRINE, interval=1):
                continue
            if self.appear_then_click(self.I_GUILD_NAME_TITLE, interval=1):
                continue
            if self.appear(self.I_FANGSHOU, interval=1):
                break
            if self.appear(self.I_RYOU_DOKAN_CHECK, threshold=0.6):
                return

        while 1:
            self.screenshot()
            dokan_status_str = self.O_DOKAN_STATUS.detect_text(self.device.image)
            if dokan_status_str != '' and dokan_status_str is not None:
                break

        if '挑战成功' in dokan_status_str or '0次' in dokan_status_str:
            self.dokan_battle_number = 0
            self.check_current_weekday(True)
            if self.create_doukan_time:
                self.set_next_run(target=self.create_doukan_time)
            else:
                self.set_next_run(task='Dokan', finish=True, server=True, success=True)
            self.finish_task()
        elif '集结中' in dokan_status_str:
            # 寮成员进入道馆
            self.dokan_quit = True
            self.goto_dokan_click()
            self.dokan_battle_number = 0
        else:
            if '2次' in dokan_status_str:
                self.dokan_quit = True
                self.dokan_battle_number = 2
            else:
                self.dokan_quit = False
                self.dokan_battle_number = 1
            # 管理开道馆
            if self.config.dokan.dokan_config.dokan_enable:
                self.open_dokan()
            else:
                self.goto_dokan_num += 1
                wait_time = 30
                logger.info(f"寮成员第{self.goto_dokan_num}次进入,等待{wait_time}秒, 管理开启道馆")
                time.sleep(wait_time)
                if self.goto_dokan_num >= 15:
                    logger.info(f"寮成员{self.goto_dokan_num}次未进入道馆, 结束任务!")
                    self.check_current_weekday(True)
                    if self.create_doukan_time:
                        self.set_next_run(target=self.create_doukan_time)
                    else:
                        self.set_next_run(task='Dokan', finish=True, server=True, success=True)
                    self.finish_task()

    def goto_dokan_click(self):
        while 1:
            self.screenshot()

            if self.is_in_dokan():
                break
            if self.appear(GeneralInviteAssets.I_I_ACCEPT):
                continue

            pos = self.O_DOKAN_MAP.ocr_full(self.device.image)
            if pos == (0, 0, 0, 0):
                logger.info(f"failed to find {self.O_DOKAN_MAP.keyword}")
            else:
                # 取中间
                x = pos[0] + pos[2] / 2
                # 往上偏移20
                y = pos[1] - 20
                # logger.info(f"ocr detect result pos={pos}, try click pos, x={x}, y={y}")
                self.device.click(x=x, y=y)

    def is_in_dokan(self):
        """
          判断是否在道馆里面
          :return:
          """
        self.screenshot()
        if self.appear(self.I_RYOU_DOKAN_CHECK, threshold=0.6):
            return True
        return False

    def find_dokan(self, con, welfare_flag):
        """
        寻找符合条件的道馆进行挑战。

        参数:
        score (float): 赏金与人数比值的阈值，默认为4.6。

        返回:
        bool: 是否找到了符合条件的道馆并进行挑战。
        """
        if welfare_flag:
            logger.info('开始寻找福利寮')
            self.find_dokan_list.append(f"─────────（开始寻找福利寮）─────────")
        else:
            logger.info('开始寻找普通寮')
            self.find_dokan_list.append(f"─────────（开始寻找普通寮）─────────")

        is_indokan, cur_scene = self.get_current_scene()
        if cur_scene != DokanScene.RYOU_DOKAN_SCENE_FINDING_DOKAN:
            return True

        # 刷新按钮点击次数
        num_fresh = 0
        # 备份一些重要的ROI区域，以便在循环中恢复
        backup = {'i_point_bounty': self.I_RIGHTPAD_POINT_BOUNTY.roi_back,
                  # 'o_dokan_rightpad_bounty':self.O_DOKAN_RIGHTPAD_BOUNTY.roi,
                  'i_point_people_num': self.I_CENTER_POINT_PEOPLE_NUMBER.roi_back}

        def restore_roi():
            self.I_RIGHTPAD_POINT_BOUNTY.roi_back = backup['i_point_bounty']
            self.I_CENTER_POINT_PEOPLE_NUMBER.roi_back = backup['i_point_people_num']

        def find_challengeable(ignore_score=False):
            """
                查找当前列表状态(一般为4个)中符合条件的道馆,并点击使其显示挑战按钮
            @param ignore_score: 是否忽略道馆系数限制, - True:   那么选择当前列表状态系数最低的那个,点击显示挑战按钮
                                                   - False:  如果存在系数符合条件的,点击并显示挑战按钮
                                                            如果全部不符合条件,不进行任何操作,返回时,不显示挑战按钮
            @type ignore_score: float
            @return:
            @rtype:
            """
            restore_roi()
            self.screenshot()
            # 获取所有匹配结果并直接转换为所需格式
            raw_matches = self.I_RIGHTPAD_POINT_BOUNTY.match_all_any(image=self.device.image, roi=[1095,33,82,569])
            # 直接从匹配结果中提取坐标信息并按y坐标排序
            bounty_list = sorted(
                [[x, y, w, h] for (sc, x, y, w, h) in raw_matches],
                key=lambda item: item[1]  # 按y坐标排序
            )
            logger.info(f'find elements list:{bounty_list}')
            if len(bounty_list) < 4:
                self.save_image(task_name='搜索到的道馆少于4个', image_type=True, wait_time=0, push_flag=True, content='搜索到的道馆少于4个')
            # 默认最小分数
            min_score = 10
            idx_selected = -1
            for idx, item in enumerate(bounty_list):
                self.device.click_record_clear()
                # logger.hr(f"开始识别道馆： No.{idx} = {item}", 2)

                self.O_DOKAN_RIGHTPAD_NAME.roi = self.position_offset(item, (-37, 29, 127, 0))
                dokan_name = self.O_DOKAN_RIGHTPAD_NAME.ocr(self.device.image)
                if dokan_name == "":
                    continue
                if dokan_name in self.welfare_names or "鑫鑫子" in dokan_name:
                    self.dokan_quit = True
                    self.open_welfare = True
                else:
                    # 如果是要开启福利寮，但是此寮不是福利寮，则跳过
                    if welfare_flag:
                        self.find_dokan_list.append(f"道馆: {dokan_name}, 不是福利寮")
                        continue

                # 点击使挑战按钮消失的区域(C_DOKAN_CANCEL_SELECT_DOKAN), 点击可能点击到其他寮,
                # 因此需要在此处多点几次,直到挑战按钮消失,
                # 又因为出现挑战按钮动画时长较长,因此需要耗时
                self.screenshot()
                while self.appear(self.I_CENTER_CHALLENGE):
                    self.click(self.C_DOKAN_CANCEL_SELECT_DOKAN, interval=1.5)
                    self.wait_animate_stable(self.C_DOKAN_CANCEL_SELECT_DOKAN_CHECK_ANIMATE, interval=0.5, timeout=1.5)

                # 扩大搜索区域,防止找不到
                self.I_RIGHTPAD_POINT_BOUNTY.roi_back = self.position_offset(item, (-10, -10, 20, 20))
                # Note: 道馆不可挑战时(被别的寮打了),8秒后跳过
                if not self.ui_click_until_appear_or_timeout(self.I_RIGHTPAD_POINT_BOUNTY, self.I_CENTER_CHALLENGE, interval=1.5, timeout=5):
                    logger.info(f"can't find challenge button,idx={idx} item={item}")
                    # 道馆不可挑战,挑战按钮不会弹出 ,直接进行下一个
                    continue

                # 获取防守人数
                self.screenshot()
                if not self.appear(self.I_CENTER_POINT_PEOPLE_NUMBER):
                    logger.warning(f"can't find point people number image, item={item}")
                    continue
                self.O_DOKAN_CENTER_PEOPLE_NUMBER.roi = self.position_offset(self.I_CENTER_POINT_PEOPLE_NUMBER.roi_front,(0, 0, 0, 30))
                p_num = self.O_DOKAN_CENTER_PEOPLE_NUMBER.detect_text(self.device.image)
                tmp = re.search(r"(\d+)", p_num)
                if not tmp:
                    logger.warning(f"can't find people number in ocr result,item={item}, p_num={p_num}")
                    continue
                p_num = int(tmp.group())

                # 最少人数随着刷新次数减少
                if num_fresh >= self.config.dokan.welfare_config.fresh_num_less_people:
                    min_people = con.min_people_num - num_fresh
                    min_people = max(min_people, 110)
                else:
                    min_people = con.min_people_num

                if p_num < min_people:
                    message = f"道馆: {dokan_name}, 人数:{p_num}, 不符合要求人数:{min_people}"
                    self.find_dokan_list.append(message)
                    logger.warning(message)
                    self.open_welfare = False
                    continue

                # 如果是要开启福利寮，且此寮人数校验已经通过，直接确认此寮
                if self.open_welfare:
                    message = f"✅ 开启福利道馆: {dokan_name}, 人数:{p_num}, 刷新次数:{num_fresh}"
                    self.find_dokan_list.append(message)
                    self.push_notify(content=message)
                    return True

                # 获取赏金金额
                self.O_DOKAN_RIGHTPAD_BOUNTY.roi = self.position_offset(item, (0, 0, 100, 0))
                bounty = self.O_DOKAN_RIGHTPAD_BOUNTY.ocr(self.device.image)
                tmp = re.search(r'(\d+)', bounty)
                if not tmp:
                    logger.warning(f"can't find bounty,item = {item},ocr bounty={bounty}")
                    continue
                bounty = int(tmp.group())
                
                item_score = float(f"{bounty / p_num:.2f}")
                dokan_info = (f"道馆: {dokan_name}, 资金: {bounty}, 人数: {p_num}, 系数: {item_score}")
                self.find_dokan_list.append(dokan_info)
                logger.info(f"========== {dokan_info} ==========")

                if item_score < min_score:
                    min_score = item_score
                    idx_selected = idx
                # 大于系数 或者 系数过小(文字识别错误导致)
                if item_score > con.find_dokan_score or item_score < 1.5:
                    logger.warning(f"系数{item_score}大于{con.find_dokan_score},不符合要求")
                    continue
                if bounty < con.min_bounty:
                    logger.warning(f"寮资金{bounty}少于{con.min_bounty},不符合要求")
                    continue
                # 道馆是否退出，来决定是否需要判断馆主等级
                if not self.dokan_quit:
                    # 馆主不是修习等级的
                    if not self.appear(self.I_CENTER_GUANZHU_XIUXI):
                        logger.warning(f"馆主不是修习等级的,不符合要求")
                        continue
                self.push_notify(content=f"开启道馆: {dokan_name},资金: {bounty},人数: {p_num},系数: {item_score}")
                return True
            # 在所有列表中都没有符合的,且忽略系数限制,那么就选择最低分数的那个,点击显示挑战按钮
            if ignore_score:
                x, y, w, h = bounty_list[idx_selected]
                while 1:
                    self.device.click(x, y)
                    sleep(0.5)
                    self.screenshot()
                    if self.appear(self.I_CENTER_CHALLENGE):
                        self.push_notify(content=f"选择当前列表中系数最低的{min_score}")
                        return True
            return False

        logger.hr("开始寻找合适的道馆", 2)
        while num_fresh < con.fresh_num:
            for i in range(3):
                sleep(3)
                if find_challengeable():
                    while 1:
                        self.screenshot()
                        if self.appear(self.I_RYOU_DOKAN_CHECK, interval=1):
                            break
                        if self.appear_then_click(self.I_CHALLENGE_ENSURE, interval=1):
                            continue
                        if self.appear_then_click(self.I_CENTER_CHALLENGE, interval=1):
                            continue
                    # 恢复初始位置信息,防止下次使用出错
                    restore_roi()
                    self.dokan_switch_soul()
                    return True
                # 滑动道馆列表 最后一次不需要滑动直接刷新
                if i < 2:
                    self.swipe(self.S_DOKAN_LIST_UP, duration=1, wait_up_time=1)

            # 恢复初始位置信息,防止下次使用出错
            restore_roi()
            num_fresh += 1
            logger.hr(f"第{num_fresh}次刷新列表", 2)
            self.find_dokan_list.append(f"─────────第{num_fresh}次刷新列表─────────")
            self.ui_click(self.C_DOKAN_REFRESH, self.I_REFRESH_ENSURE, interval=1)
            self.ui_click_until_disappear(self.I_REFRESH_ENSURE, interval=1)
            sleep(1)

        if welfare_flag:
            self.push_notify(content="未找到福利寮")
            return False

        # 刷新次数用完,仍未找到符合条件的道馆,选择当前列表(约4个)中系数最低的
        logger.warning("刷新次数已经上限,未找到符合条件的道馆,选择当前列表中系数最低的")
        if find_challengeable(ignore_score=True):
            while 1:
                self.screenshot()
                if self.appear(self.I_RYOU_DOKAN_CHECK, interval=1):
                    break
                if self.appear_then_click(self.I_CHALLENGE_ENSURE, interval=1):
                    continue
                if self.appear_then_click(self.I_CENTER_CHALLENGE, interval=1):
                    continue
            self.dokan_switch_soul()
            return True
        return False

    def open_dokan(self):
        # 判断是否需要建立道馆
        while 1:
            self.screenshot()
            if self.appear_then_click(self.I_RED_CLOSE, interval=1):
                continue
            if self.appear_then_click(self.I_CREATE_DAOGUAN_SURE, interval=1):
                time.sleep(3)
                continue
            if self.appear_rgb(self.I_CREATE_DAOGUAN_OK):
                break
            if self.appear_then_click(self.I_CREATE_DAOGUAN, interval=1):
                continue

        dokan_config = self.config.dokan.welfare_config
        if dokan_config.welfare_enable and self.find_dokan(dokan_config, welfare_flag=True):
            logger.info("已找到福利道馆")
        else:
            dokan_config = self.config.dokan.dokan_config
            self.find_dokan(dokan_config, welfare_flag=False)
            logger.info("已找到普通道馆")

        # 记录第一次开启道馆时间
        self.first_open_dokan_time = datetime.now()

        # 道馆数量
        filtered_list = [item for item in self.find_dokan_list if "刷新列表" not in item]
        logger.info(f"总共查看道馆数量: {len(filtered_list)}")

        # 打印道馆列表
        i = 1
        for item in self.find_dokan_list:
            if "刷新列表" in item or "开始寻找" in item:
                i = 1
                logger.info(f"{item}")
                continue
            logger.info(f"Item {i}: {item}")
            i += 1
        self.find_dokan_list = []

    def appear_rgb(self, target, image=None, difference: int = 10):
        """
        判断目标的平均颜色是否与图像中的颜色匹配。

        参数:
        - target: 目标对象，包含目标的文件路径和区域信息。
        - image: 输入图像，如果未提供，则使用设备捕获的图像。
        - difference: 颜色差异阈值，默认为10。

        返回:
        - 如果目标颜色与图像颜色匹配，则返回True，否则返回False。
        """
        # 如果未提供图像，则使用设备捕获的图像
        # logger.info(f"target [{target}], image [{image}]")
        if image is None:
            image = self.device.image

        # 加载图像并计算其平均颜色
        img = cv2.imread(target.file)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        average_color = cv2.mean(img_rgb)
        # logger.info(f"[{target.name}]average_color: {average_color}")

        # 提取目标区域的坐标和尺寸，并确保它们为整数
        x, y, w, h = target.roi_front
        x, y, w, h = int(x), int(y), int(w), int(h)
        # 从输入图像中提取目标区域
        img = image[y:y + h, x:x + w]
        # 计算目标区域的平均颜色
        color = cv2.mean(img)
        # logger.info(f"[{target.name}] color: {color}")

        # 比较目标图像和目标区域的颜色差异
        for i in range(3):
            if abs(average_color[i] - color[i]) > difference:
                # logger.warning(f"颜色匹配失败: [{target.name}]")
                return False

        logger.info(f"颜色匹配成功: [{target.name}]")
        return True

    def ui_click_until_appear_or_timeout(self, click, stop=None, interval: float = 1, timeout: float = 10):
        """
        在UI中点击某个元素，直到目标元素出现或达到超时时间。
        此函数主要用于自动化测试中，模拟用户点击操作，直到出现指定的界面元素或达到预设的超时时间。

        :param click: 要点击的元素规则，可以是图片规则、点击规则或OCR规则。
        :param stop: 可选参数，出现此元素时停止点击。如果为None，则一直点击直到超时。
        :param interval: 每次点击之间的间隔时间（秒）。默认为1秒。
        :param timeout: 总的超时时间（秒）。默认为10秒。
        :return: 如果在超时时间内找到目标元素，则返回True，否则返回False。
        """
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            sleep(0.3)
            self.screenshot()
            if self.appear(stop):
                return True
            if isinstance(click, RuleImage) and self.appear_then_click(click, interval=interval):
                continue
            if isinstance(click, RuleClick) and self.click(click, interval=interval):
                continue
            elif isinstance(click, RuleOcr) and self.ocr_appear_click(click, interval=interval):
                continue
        return False

    def find_all_element(self, item, offset: tuple) -> list[tuple[int, int, int, int]]:
        """
        NOTE: 仅适配查找道馆列表
       在当前对象中查找所有匹配的项目，并返回它们的信息列表。

       此函数的目的是通过循环搜索和匹配给定的项目，并将匹配的项目信息存储到一个列表中。
       如果项目出现，则将其添加到列表中，并根据预定义的规则调整项目的位置。

       参数:
       - item: 需要查找的项目。
       - offset: 如果当前区域查找不到,扩大查找区域的大小

       返回值:
       返回一个包含所有匹配项目信息的列表。
       """
        res_list = []
        while 1:
            if (item.roi_back[0] + item.roi_back[2] > (1280 + offset[2])) or (
                    item.roi_back[1] + item.roi_back[3] > (720 + offset[3])):
                break
            if self.appear(item):
                res_list.append(item.roi_front.copy())
                # 刷新搜索区域,使用上个搜索结果的Y坐标作为起始点的Y坐标,搜索结果的高度作为起始搜索高度
                item.roi_back = self.position_offset(item.roi_back, (
                    0, item.roi_front[1] + item.roi_front[3] - item.roi_back[1], 0,
                    item.roi_front[3] - item.roi_back[3]),
                                                     )
            item.roi_back = self.position_offset(item.roi_back, offset)
        return res_list

    def position_offset(self, src, offset: tuple):
        return (src[0] + offset[0], src[1] + offset[1]
                , src[2] + offset[2], src[3] + offset[3])

    def dokan_switch_soul(self):
        # 更改式神录跳转
        ipages.page_shikigami_records.links.clear()
        if ipages.page_shikigami_records in ipages.page_main.links:
            del ipages.page_main.links[ipages.page_shikigami_records]
        ipages.page_shikigami_records.link(button=self.I_BACK_Y, destination=ipages.page_dokan)
        ipages.page_dokan.link(button=self.I_PAGE_DOKAN_GOTO_SHIKIGAMI_RECORDS, destination=ipages.page_shikigami_records)

        cfg = self.config.dokan

        if self.open_welfare:
            # 自动换御魂 福利寮
            if cfg.switch_soul_config2.enable:
                self.run_switch_soul(cfg.switch_soul_config2.switch_group_team)
            if cfg.switch_soul_config2.enable_switch_by_name:
                self.run_switch_soul_by_name(cfg.switch_soul_config2.group_name, cfg.switch_soul_config2.team_name)
        else:
            # 自动换御魂
            if cfg.switch_soul_config.enable:
                self.run_switch_soul(cfg.switch_soul_config.switch_group_team)
            if cfg.switch_soul_config.enable_switch_by_name:
                self.run_switch_soul_by_name(cfg.switch_soul_config.group_name, cfg.switch_soul_config.team_name)

        self.ui_goto_page(page_dokan)

    def finish_task(self):
        # 恢复式神录跳转
        ipages.page_dokan.links.clear()
        if ipages.page_dokan in ipages.page_shikigami_records.links:
            del ipages.page_shikigami_records.links[ipages.page_dokan]
        ipages.page_main.link(button=self.I_MAIN_GOTO_SHIKIGAMI_RECORDS, destination=ipages.page_shikigami_records)
        ipages.page_shikigami_records.link(button=self.I_BACK_Y, destination=ipages.page_main)

        # 移除临时页面
        PageRegistry.unregister(ipages.page_dokan)

        raise TaskEnd


if __name__ == "__main__":
    from module.config.config import Config

    config = Config('mi')
    t = ScriptTask(config)
    # t.save_image()
    # t.run()
    t.dokan_switch_soul()
    t.finish_task()
    # t.dokan_process(config.dokan)
    # t.find_dokan(config.dokan.welfare_config, True)
    # t.find_dokan()

    # welfare_names = t.welfare_name_str()
    # print(welfare_names)
    # if "锦鲤一一" in welfare_names:
    #     print("有")
    # else:
    #     print("没有")
    # test_ocr_locate_dokan_target()
    # test_anti_detect_random_click()
    # test_goto_main()