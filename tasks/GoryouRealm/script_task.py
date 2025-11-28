# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
from datetime import datetime, timedelta
from module.exception import TaskEnd
from module.logger import logger
from random import randint
from tasks.Component.GeneralBattle.general_battle import GeneralBattle
from tasks.Component.SwitchSoul.switch_soul import SwitchSoul
from tasks.GameUi.page import page_goryou_realm
from tasks.GoryouRealm.assets import GoryouRealmAssets
from tasks.GoryouRealm.config import GoryouClass


class ScriptTask(GeneralBattle, SwitchSoul, GoryouRealmAssets):
    """ 御灵 """

    def run(self):
        con = self.config.goryou_realm
        limit_time = con.goryou_config.limit_time
        self.limit_count = con.goryou_config.limit_count
        self.limit_time: timedelta = timedelta(hours=limit_time.hour, minutes=limit_time.minute,
                                               seconds=limit_time.second)
        if con.switch_soul_config.enable:
            self.run_switch_soul(con.switch_soul_config.switch_group_team)

        self.ui_goto_page(page_goryou_realm)

        match_click = {
            GoryouClass.Dark_Divine_Dragon: self.C_GR_C_1,
            GoryouClass.Dark_Hakuzousu: self.C_GR_C_2,
            GoryouClass.Dark_Black_Panther: self.C_GR_C_3,
            GoryouClass.Dark_Peacock: self.C_GR_C_4,
        }
        while 1:
            self.screenshot()
            if self.appear(self.I_GR_FIRE):
                logger.info('Enter GoryouRealm')
                break
            if self.click(match_click[self.check_date(con.goryou_config.goryou_class)], interval=1):
                continue
        self.check_lock(con.general_battle_config.lock_team_enable, self.I_GR_LOCK, self.I_GR_UNLOCK)

        # 开始循环
        while 1:
            self.screenshot()
            if not self.appear(self.I_GR_FIRE):
                continue

            # 判断是否有更高优先级任务，去执行新任务
            self._check_first_priority_task()

            if self.current_count >= self.limit_count:
                logger.info('GoryouRealm count limit out')
                break
            if datetime.now() - self.start_time >= self.limit_time:
                logger.info('GoryouRealm time limit out')
                break
            ticket = self.O_GR_TICKET.ocr(self.device.image)
            if ticket == 0:
                break

            # 点击挑战
            while 1:
                self.screenshot()
                if self.appear_then_click(self.I_GR_FIRE, interval=1):
                    pass
                if not self.appear(self.I_GR_FIRE):
                    self.run_general_battle(config=con.general_battle_config)
                    break

        self.ui_click(self.I_UI_BACK_BLUE, self.I_CHECK_EXPLORATION)
        logger.info('Back to exploration')
        self.set_next_run(task='GoryouRealm', success=True, finish=True)
        # 是否开启绘卷捐赠任务
        if con.goryou_config.open_memory_scrolls:
            self.set_next_run(task='MemoryScrolls', target=datetime.now())
        raise TaskEnd

    def check_date(self, goryou_class: GoryouClass = GoryouClass.RANDOM) -> GoryouClass:
        day_of_week = self.start_time.weekday()
        if day_of_week == 0:
            # 周一不开放，退出
            logger.warning('Today is Monday and GoryouRealm is not open')
            self.set_next_run(task='GoryouRealm', success=False, finish=True)
            raise TaskEnd('GoryouRealm')

        match_day = {
            GoryouClass.RANDOM: [1, 2, 3, 4, 5, 6],
            GoryouClass.Dark_Divine_Dragon: [1, 5, 6],
            GoryouClass.Dark_Hakuzousu: [2, 5, 6],
            GoryouClass.Dark_Black_Panther: [3, 5, 6],
            GoryouClass.Dark_Peacock: [4, 5, 6],
        }
        match_class = {
            1: GoryouClass.Dark_Divine_Dragon,
            2: GoryouClass.Dark_Hakuzousu,
            3: GoryouClass.Dark_Black_Panther,
            4: GoryouClass.Dark_Peacock,
        }
        if goryou_class == GoryouClass.RANDOM:
            random_num = randint(1, 4)
            goryou_class = match_class[random_num]
        if day_of_week not in match_day[goryou_class]:
            logger.warning(f'Today is {day_of_week} that do not support {goryou_class.name}')
            logger.info(f'OAS will run {match_class[day_of_week].name} instead')
            goryou_class = match_class[day_of_week]

        return goryou_class


if __name__ == '__main__':
    from module.config.config import Config
    from module.device.device import Device
    c = Config('du')
    d = Device(c)
    t = ScriptTask(c, d)
    t.screenshot()

    t.run()
