# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
from module.atom.image import RuleImage
from tasks.Component.RightActivity.assets import RightActivityAssets
from tasks.GameUi.game_ui import GameUi
from tasks.GameUi.page import page_main


class RightActivity(GameUi, RightActivityAssets):
    def enter(self, target: RuleImage):
        self.ui_goto_page(page_main)

        self.ui_click(self.I_TOGGLE_BUTTON, target, interval=2)
        self.ui_click_until_disappear(target, interval=3)

    def right_open(self):
        self.ui_click(self.I_RA_CLOSE, self.I_RA_OPEN, interval=2)

    def right_close(self):
        self.ui_click(self.I_RA_OPEN, self.I_RA_CLOSE, interval=2)


