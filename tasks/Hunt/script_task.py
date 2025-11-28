# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
from datetime import timedelta, datetime, time
from module.base.timer import Timer
from module.exception import TaskEnd
from module.logger import logger
from tasks.Component.GeneralBattle.config_general_battle import GeneralBattleConfig
from tasks.Component.GeneralBattle.general_battle import GeneralBattle
from tasks.Component.GeneralInvite.general_invite import GeneralInvite
from tasks.Component.SwitchSoul.switch_soul import SwitchSoul
from tasks.GameUi.page import page_kirin, page_netherworld
from tasks.Hunt.assets import HuntAssets


class ScriptTask(GeneralBattle, GeneralInvite, SwitchSoul, HuntAssets):
    """ 狩猎战 """
    kirin_day = True  # 不是麒麟就是阴界之门

    def run(self):
        if not self.check_datetime():
            # 设置下次运行时间 为今天的晚上七点钟
            raise TaskEnd('Hunt')

        if self.kirin_day:
            con = self.config.hunt.kirin_config
        else:
            con = self.config.hunt.nether_world_config

        if con.enable:
            self.run_switch_soul(con.switch_group_team)

        if self.kirin_day:
            success = self.kirin()
        else:
            success = self.netherworld()

        # 处理通用战斗配置
        config = GeneralBattleConfig()
        if success:
            if con.enable:
                preset_group, preset_team = self.split_group_team(con.switch_group_team)
                config.preset_enable = con.preset_enable
                config.preset_group = preset_group
                config.preset_team = preset_team
                config.lock_team_enable = False
            self.run_general_battle(config)

        self.set_next_run(task='Hunt', success=True, finish=True)
        raise TaskEnd('Hunt')

    def kirin(self):
        logger.hr('麒麟', 2)
        self.ui_goto_page(page_kirin)
        while 1:
            self.screenshot()

            self.check_and_invite()

            if self.appear(self.I_KIRIN_END):
                # 麒麟已挑战
                logger.warning('麒麟已挑战')
                return False
            if self.appear_then_click(self.I_KIRIN_CHALLAGE, interval=1):
                continue
            if self.appear(self.I_PREPARE_HIGHLIGHT):
                logger.info('Arrive the Kirin')
                return True

    def netherworld(self):
        logger.hr('阴界之门', 2)
        self.ui_goto_page(page_netherworld)
        while 1:
            self.screenshot()
            if self.is_in_room(False):
                self.screenshot()
                if not self.appear(self.I_FIRE):
                    continue
                self.click_fire()
                logger.info('Start battle')
                return True

            if self.appear_then_click(self.I_NW, interval=0.9):
                continue
            if self.appear_then_click(self.I_UI_CONFIRM, interval=0.9):
                continue
            if self.appear_then_click(self.I_NW_CHALLAGE, interval=1.5):
                continue
            if self.appear(self.I_NW_DONE):
                # 今日已挑战
                logger.warning('今日已挑战')
                self.ui_click_until_disappear(self.I_UI_BACK_RED)
                return False

    def battle_wait(self, random_click_swipt_enable: bool) -> bool:
        """
        重写，
        阴界之门： 胜利后回到狩猎战的主界面
        麒麟： 胜利后回到麒麟的主界面
        :param random_click_swipt_enable:
        :return:
        """
        # 战斗过程 随机点击和滑动 防封
        logger.info("Start battle process")
        self.device.stuck_record_clear()
        self.device.stuck_record_add('BATTLE_STATUS_S')
        swipe_count = 1
        stuck_timer = Timer(240)
        stuck_timer.start()
        exit_battle_second = self.config.hunt.kirin_config.exit_battle_second
        exit_battle_timer = Timer(exit_battle_second)
        if self.kirin_day and exit_battle_second > 0:
            exit_battle_timer.start()
        while 1:
            self.screenshot()
            if self.kirin_day and exit_battle_second > 0 and exit_battle_timer.reached():
                logger.info(f'时间到达 {exit_battle_second}s, 退出战斗')
                if self.appear_then_click(self.I_EXIT_ENSURE, interval=1):
                    exit_battle_timer.reset()
                    continue
                if self.appear_then_click(self.I_UI_EXIT, interval=1):
                    continue
            if self.appear(self.I_WIN):
                logger.info('Battle win')
                self.ui_click_until_disappear(self.I_WIN)
                return True
            # 如果出现失败 就点击，返回False
            if self.appear(self.I_FALSE, threshold=0.8):
                logger.info("Battle result is false")
                self.ui_click_until_disappear(self.I_FALSE)
                return False
            if self.appear(self.I_PREPARE_HIGHLIGHT):
                if self.appear_then_click(self.I_EXIT_ENSURE, interval=1):
                    continue
                if self.appear_then_click(self.I_UI_EXIT, interval=1):
                    continue
            # 如果三分钟还没打完，再延长五分钟
            if stuck_timer and stuck_timer.reached():
                stuck_timer.reset()
                # 3 * 240s = 12min 退出
                if swipe_count >= 3:
                    logger.info('battle timeout')
                    break
                swipe_count += 1
                self.device.stuck_record_clear()
                self.device.stuck_record_add('BATTLE_STATUS_S')

    def check_datetime(self) -> bool:
        """
        检查日期和时间, 会设置是麒麟还是阴界之门
        :return: 符合有效时间范围返回True, 否则返回False
        """
        now = datetime.now()
        day_of_week = now.weekday()

        # 根据星期几判断是麒麟日还是阴界之门日
        if 0 <= day_of_week <= 3:
            self.kirin_day = True
            valid_start, valid_end = time(6, 0), time(23, 0)
            task_name = "麒麟"
        else:  # 4 <= day_of_week <= 6
            self.kirin_day = False
            valid_start, valid_end = time(19, 0), time(23, 0)  # 修改结束时间为23点
            task_name = "阴界之门"

        # 检查当前时间是否在有效范围内
        if valid_start <= now.time() <= valid_end:
            return True
        else:
            logger.warning(f'{task_name}时间不符合{valid_start}-{valid_end}，当前时间: {now.time()}')

            # 统一设定下次运行时间为当天或次日的19:00
            target_time = time(19, 0)
            if now.time() < target_time:
                next_run = datetime.combine(now.date(), target_time)
            else:
                next_run = datetime.combine(now.date() + timedelta(days=1), target_time)

            self.set_next_run(task='Hunt', target=next_run)
            raise TaskEnd


if __name__ == '__main__':
    from module.config.config import Config

    c = Config('4399')
    t = ScriptTask(c)

    t.battle_wait(False)
