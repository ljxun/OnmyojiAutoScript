# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey

import time

import os
from module.atom.click import RuleClick
from module.exception import TaskEnd
from module.logger import logger
from tasks.Component.GeneralBattle.general_battle import GeneralBattle
from tasks.Component.SwitchSoul.switch_soul import SwitchSoul
from tasks.GameUi.page import page_main
from tasks.Restart.assets import RestartAssets


class ScriptTask(SwitchSoul, GeneralBattle):
    """ 委派 """
    last_img = None

    def run(self):
        # 加载所有图片
        over_img = "over.png"
        goto_delegate_folder1 = "./tasks/ActivityCommon/委派"
        goto_delegate_folder2 = "./tasks/ActivityCommon/委派"
        goto_delegate_folder3 = "./tasks/ActivityCommon/委派"

        self.ui_goto_page(page_main)

        self.goto_delegate(self._load_image_template(goto_delegate_folder1), over_img)
        logger.hr("已进入灵视界面", 1)
        self.goto_delegate(self._load_image_template(goto_delegate_folder2), over_img)
        logger.hr("已进入委派界面", 1)
        self.start_delegate()
        self.goto_delegate(self._load_image_template(goto_delegate_folder3), over_img)

        logger.hr("委派任务结束", 1)
        # 回到庭院
        self.ui_goto_page(page_main)
        self.set_next_run()
        raise TaskEnd

    def goto_delegate(self, goto_challenge_templates, over_img):
        # 进入挑战界面
        goto_activity = False
        click_count = 1
        while not goto_activity:
            if click_count >= 3:
                self.ui_goto_page(page_main)
                self.set_next_run()
                raise TaskEnd
            self.screenshot()
            # 获得奖励
            if self.ui_reward_appear_click():
                continue
            # 误点聊天频道会自动关闭
            if self.appear_then_click(RestartAssets.I_HARVEST_CHAT_CLOSE):
                continue
            for goto_template in goto_challenge_templates:
                if os.path.basename(goto_template.file) == over_img:
                    self.screenshot()
                    if self.appear(goto_template):
                        goto_activity = True
                        break
                else:
                    if self.appear_then_click(goto_template, interval=1):
                        if self.last_img == goto_template.file:
                            click_count += 1
                        else:
                            click_count = 0
                            self.last_img = goto_template.file
                        break

    def start_delegate(self):
        click_list = []
        x, y, h, w = 180,540,18,45
        for i in range(7):
            C1 = RuleClick(roi_front=(x,y,h,w), roi_back=(x,y,h,w), name=f"click{i}")
            click_list.append(C1)
            x += 140

        logger.info("开始委派")
        for click in click_list:
            self.click(click)
            time.sleep(1)


if __name__ == '__main__':
    from module.config.config import Config

    c = Config('wy')
    t = ScriptTask(c)

    t.run()
