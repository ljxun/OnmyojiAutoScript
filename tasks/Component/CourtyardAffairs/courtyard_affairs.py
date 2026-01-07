# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
from module.logger import logger
from tasks.Component.CourtyardAffairs.assets import CourtyardAffairsAssets
from tasks.Component.CourtyardAffairs.page import page_courtyard_affairs
from tasks.GameUi.game_ui import GameUi
from tasks.Restart.assets import RestartAssets


class CourtyardAffairs(GameUi, CourtyardAffairsAssets):
    """ 庭院事务 """
    def courtyard_affairs(self) -> None:
        self.ui_goto_page(page_courtyard_affairs)

        click_count = 0
        while 1:
            self.screenshot()

            if click_count >= 3:
                logger.warning('庭院暂无可完成的事务!')
                # self.save_image(task_name="庭院暂无可完成的事务",image_type=True, wait_time=0)
                break
            # 点击取消
            if self.appear_then_click(RestartAssets.I_LOGIN_CANCEL_BATTLE):
                logger.info('式神满级，是否提取物经验？-点击取消')
                # self.save_image(task_name="庭院事务领取？-点击取消", push_flag=True, wait_time=0, image_type=True)
                click_count = 0
                continue
            if self.appear(self.I_SUCCESS_CLAIMED):
                # self.save_image(task_name="庭院事务完成",image_type=True)
                break
            if self.appear_then_click(self.I_COMPLETE_WITH_ONE_CLICK, interval=1):
                click_count += 1
                continue


if __name__ == "__main__":
    from module.config.config import Config

    c = Config("MI")
    t = CourtyardAffairs(c)
    t.courtyard_affairs()
