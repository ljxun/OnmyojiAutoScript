# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
import os
import random
from cached_property import cached_property
from datetime import datetime, timedelta, time
from module.atom.image import RuleImage
from module.atom.ocr import RuleOcr
from module.base.timer import Timer
from module.exception import TaskEnd
from module.logger import logger
from tasks.ActivityCommon.config import NumberType, ModeType
from tasks.Component.GeneralBattle.general_battle import GeneralBattle
from tasks.Component.SwitchSoul.switch_soul import SwitchSoul
from tasks.GameUi.page import page_main
from tasks.Restart.assets import RestartAssets


class ScriptTask(SwitchSoul, GeneralBattle):
    """ 战斗 """
    SoulsFUll = False

    def run_config(self, config, goto_challenge_folder, battle_folder):

        # 加载进入挑战界面图片列表
        goto_activity_templates = self._load_image_template(goto_challenge_folder)

        # 加载战斗图片列表
        battle_templates = self._load_image_template(battle_folder)
        challenge = RuleImage(
            roi_front=(1100, 540, 170, 170),
            roi_back=(1100, 540, 170, 170),
            threshold=0.8,
            method="Template matching",
            file=f"{goto_challenge_folder}/挑战.png"
        )
        battle_templates.append(challenge)

        self.run_activity(config, goto_activity_templates, battle_templates, challenge)

    def run_activity(self, config, goto_challenge_templates, battle_templates, challenge) -> None:
        # 切换御魂
        if config.switch_soul_config.enable:
            self.run_switch_soul(config.switch_soul_config.switch_group_team)
        if config.switch_soul_config.enable_switch_by_name:
            self.run_switch_soul_by_name(config.switch_soul_config.group_name, config.switch_soul_config.team_name)

        self.ui_goto_page(page_main)

        # 进入挑战页面
        self.goto_challenge(goto_challenge_templates)

        # 开始战斗
        battle_result = self.start_battle(config, battle_templates, challenge)

        # 回到庭院
        self.ui_goto_page(page_main)

        if config.activity_common_config.active_souls_clean:
            self.set_next_run(task='SoulsTidy', success=False, finish=False, target=datetime.now())

        if battle_result:
            next_run = datetime.combine(datetime.now().date() + timedelta(days=1), time(5, 5))
            self.set_next_run(task=self.config.task.command, target=next_run)
        else:
            self.set_next_run(task=self.config.task.command, finish=True, success=True)
        raise TaskEnd


    def check_battle(self, config):

        # 使用实例属性缓存，基于config生成唯一标识
        cache_key = id(config.check_battle_config)

        if not hasattr(self, '_battle_cache'):
            self._battle_cache = {}

        if cache_key not in self._battle_cache:
            con = config.check_battle_config
            roi = tuple(map(int, con.ocr_number_roi.split(',')))
            mode = con.ocr_number_mode
            limit_ocr_number = con.limit_ocr_number
            number_type = con.number_type
            O_NUMBER = RuleOcr(roi=roi, area=roi, mode=mode, method="Default", keyword="", name="number")

            self._battle_cache[cache_key] = {
                'roi': roi,
                'mode': mode,
                'limit_ocr_number': limit_ocr_number,
                'number_type': number_type,
                'O_NUMBER': O_NUMBER
            }

        # 使用缓存的数据
        cached = self._battle_cache[cache_key]
        roi = cached['roi']
        mode = cached['mode']
        limit_ocr_number = cached['limit_ocr_number']
        number_type = cached['number_type']
        O_NUMBER = cached['O_NUMBER']

        if mode == ModeType.DigitCounter:
            cu, res, total = self.ocr_result(O_NUMBER)
            if 0 < total == cu + res:
                should_notify = False
                if number_type == NumberType.Ticket:
                    if cu <= limit_ocr_number:
                        should_notify = True
                elif number_type == NumberType.Battle:
                    if cu >= limit_ocr_number:
                        should_notify = True

                if should_notify:
                    self.push_notify(content=f"限制[{limit_ocr_number}]已达到: {cu}/{total}")
                    self.set_next_run()
                    # self.set_next_run(task=self.config.task.command, target=datetime.now() + timedelta(minutes=10))
                    raise TaskEnd

    def goto_challenge(self, goto_challenge_templates):
        # 进入挑战界面
        while 1:
            self.screenshot()
            # 获得奖励
            if self.ui_reward_appear_click():
                continue
            # 误点聊天频道会自动关闭
            if self.appear_then_click(RestartAssets.I_HARVEST_CHAT_CLOSE):
                continue
            for goto_template in goto_challenge_templates:
                if os.path.basename(goto_template.file) == '挑战.png':
                    self.screenshot()
                    if self.appear(goto_template):
                        logger.hr("已在挑战界面", 2)
                        return
                else:
                    if self.appear_then_click(goto_template, interval=1):
                        break

    def start_battle(self, config, battle_templates, challenge):

        limit_time = config.activity_common_config.limit_time
        enable = config.activity_common_config.enable
        each_limit_second = 0
        if enable:
            # 限制次数
            self.limit_count = config.activity_common_config.limit_count
            # 限制时间
            self.limit_time: timedelta = timedelta(hours=limit_time.hour, minutes=limit_time.minute, seconds=limit_time.second)
            # 每场战斗限制秒数
            each_limit_second = config.activity_common_config.each_limit_second

        # 开始战斗
        logger.hr("开始战斗")
        click_count = 0
        click_count_max = 6
        last_clicked_file = None  # 记录上一次点击的文件名
        over_task = False
        challenge_clicked = False
        run_timer = Timer(each_limit_second)
        while 1:
            self.screenshot()

            if run_timer.reached() and each_limit_second > 0:
                logger.info('本场战斗时间已到, 退出')
                self.exit_battle()
                run_timer.reset()
                continue

            if challenge_clicked and not self.appear(challenge):
                self.current_count += 1
                logger.hr("General battle Start", 2)
                logger.info(f"Current count: {self.current_count} / {self.limit_count}")
                task_run_time = datetime.now() - self.start_time
                task_run_time_seconds = timedelta(seconds=int(task_run_time.total_seconds()))
                logger.info(f"Current times: {task_run_time_seconds} / {self.limit_time}")
                challenge_clicked = False

            # 获得奖励
            if self.ui_reward_appear_click():
                run_timer.reset()
                continue
            # 误点聊天频道会自动关闭
            if self.appear_then_click(RestartAssets.I_HARVEST_CHAT_CLOSE):
                self.device.stuck_record_add('BATTLE_STATUS_S')
                continue

            # 开始战斗循环识图
            for image_template in battle_templates:
                current_file = os.path.basename(image_template.file)

                if current_file == '挑战.png':
                    self.screenshot()
                    if self.appear(challenge):
                        # 判断是否有更高优先级任务，去执行新任务
                        if config.activity_common_config.enable_check_first_priority_task:
                            self._check_first_priority_task()
                        if config.check_battle_config.enable:
                            if self.check_battle(config):
                                return True
                        if over_task:
                            return True
                        if enable:
                            if datetime.now() - self.start_time > self.limit_time:
                                self.push_notify(f"{self.limit_time} 时间限制已到，结束任务")
                                return
                            if self.current_count >= self.limit_count:
                                self.push_notify(f"{self.limit_count} 次数限制已到，结束任务")
                                return

                if self.appear_then_click(image_template, interval=1):
                    if current_file == '御魂溢出确认.png':
                        if not self.SoulsFUll:
                            self.push_notify("御魂溢出")
                            self.SoulsFUll = True
                            self.set_next_run(task='SoulsTidy', success=False, finish=False, target=datetime.now())

                    if current_file == '挑战.png':
                        challenge_clicked = True

                    if current_file == '赢（鼓）.png' or '御魂勾玉' in current_file:
                        run_timer.reset()
                        action_click = random.choice([self.C_REWARD_1, self.C_REWARD_2, self.C_REWARD_3])
                        self.click(action_click, interval=1)

                    # 判断是否连续点击同一图片
                    if current_file == last_clicked_file:
                        click_count += 1
                        if click_count >= click_count_max:
                            self.push_notify("点击同一图片最大次数，结束任务")
                            over_task = True
                    else:
                        click_count = 0  # 点击不同图片时重置计数

                    last_clicked_file = current_file  # 更新记录
                    if current_file == '挑战.png' or current_file == '准备.png':
                        run_timer.start()
                        self.device.stuck_record_add('BATTLE_STATUS_S')


if __name__ == '__main__':
    from module.config.config import Config

    c = Config('du')
    t = ScriptTask(c)
    t.screenshot()
    t.check_battle(c.activity_common_2)

    # t.run()
