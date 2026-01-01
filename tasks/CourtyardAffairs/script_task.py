# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
from module.exception import TaskEnd
from module.logger import logger
from tasks.CourtyardAffairs.assets import CourtyardAffairsAssets
from tasks.CourtyardAffairs.page import page_courtyard_affairs
from tasks.GameUi.game_ui import GameUi
from tasks.GameUi.page import page_main


class ScriptTask(GameUi, CourtyardAffairsAssets):
    """ 庭院事务 """

    def run(self) -> None:
        self.ui_goto_page(page_main)
        self.ui_click(self.I_REFRESH, self.I_COURTYARD_AFFAIRS_BUTTON)
        self.ui_goto_page(page_courtyard_affairs)

        click_count = 0
        while 1:
            if click_count >= 3:
                logger.warning('庭院暂无可完成的事务!')
                self.save_image(task_name="庭院暂无可完成的事务", wait_time=0)
                break
            self.screenshot()
            if self.appear(self.I_SUCCESS_CLAIMED):
                self.save_image(task_name="庭院事务完成")
                break
            if self.appear_then_click(self.I_COMPLETE_WITH_ONE_CLICK, interval=1):
                click_count += 1
                continue

        self.set_next_run()
        raise TaskEnd


if __name__ == "__main__":
    from module.config.config import Config

    c = Config("4399")
    t = ScriptTask(c)
    t.run()
