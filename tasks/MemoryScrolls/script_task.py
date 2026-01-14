# This Python file uses the following encoding: utf-8
# @author ghg11
# github https://github.com/ghg11
from module.base.timer import Timer
from module.exception import TaskEnd
from module.logger import logger
from tasks.GameUi.game_ui import GameUi
from tasks.GameUi.page import page_summon
from tasks.MemoryScrolls.assets import MemoryScrollsAssets
from tasks.MemoryScrolls.config import ScrollNumber


class ScriptTask(GameUi, MemoryScrollsAssets):
    """ 绘卷 捐赠 """
    def run(self):
        # 进入绘卷主界面
        self.ui_goto_page(page_summon)
        self.ui_click(self.I_MS_ENTER, self.I_MS_MAIN)

        con = self.config.memory_scrolls
        # 如果每天只刷小绘卷50，则先检测小绘卷数量
        if con.memory_scrolls_finish.check_ms_s_50_enable:
            self.check_ms_s_50(con.memory_scrolls_finish)

        # 进入指定分卷 进行捐献
        self.goto_scroll(con.memory_scrolls_config)

        # 设置下一次运行时间
        self.set_next_run(task='MemoryScrolls', success=True)
        raise TaskEnd
    
    def check_ms_s_50(self, con):
        """先检测小绘卷数量"""
        while 1:
            self.screenshot()
            if self.appear(self.I_MS_FRAGMENT_S_VERIFICATION):
                cu, res, total = self.O_MS_COUNT_S.ocr(self.device.image)
                message = f'小绘卷进度: {cu}/{total} '
                if self.appear(self.I_MS_FRAGMENT_S_50) or (cu == total == 50):
                    time = con.next_run_time
                    # 安排下次探索和御灵任务
                    if con.auto_finish_exploration:
                        message += f'探索 设置明天{time}点执行'
                        self.custom_next_run(task='Exploration', custom_time=time, time_delta=1)
                    if con.auto_finish_goryourealm:
                        message += f'御灵 设置明天{time}点执行'
                        self.custom_next_run(task='GoryouRealm', custom_time=time, time_delta=1)
                self.push_notify(content=message)
                break
            if self.appear_then_click(self.I_MS_FRAGMENT_S, interval=1.5):
                continue
        self.ui_click_until_smt_disappear(self.I_MS_MAIN, stop=self.I_MS_FRAGMENT_S_VERIFICATION, interval=1.5)

    def goto_scroll(self, con):
        """
        进入指定分卷
        :param con
        """
        while 1:
            self.screenshot()
            # 暂时用手动截取叉号，后续替换为通用图片
            if self.appear(self.I_MS_CLOSE):
                logger.info('进入绘卷捐献页面')
                break
            match con.scroll_number:
                case ScrollNumber.ONE:
                    self.click(self.C_MS_SCROLL_1, interval=1)
                case ScrollNumber.TWO:
                    self.click(self.C_MS_SCROLL_2, interval=1)
                case ScrollNumber.THREE:
                    self.click(self.C_MS_SCROLL_3, interval=1)
                case ScrollNumber.FOUR:
                    self.click(self.C_MS_SCROLL_4, interval=1)
                case ScrollNumber.FIVE:
                    self.click(self.C_MS_SCROLL_5, interval=1)
                case ScrollNumber.SIX:
                    self.click(self.C_MS_SCROLL_6, interval=1)
                case _:
                    logger.error(f'未知的绘卷编号：{con.scroll_number}')

        # 进度100%，结束
        if self.appear(self.I_MS_COMPLETE):
            self.close_task(con)
        else:
            # 查看排名
            self.ui_click(self.I_MS_OPEN_LEAGUETABLES, self.I_MS_MY_RANKING)
            while 1:
                self.screenshot()
                my_ranking = self.O_MS_MY_RANKING.ocr(self.device.image)
                if my_ranking != 0:
                    break
            if (my_ranking >= con.ranking or my_ranking <= 0) or con.ranking == 0:
                logger.info(f"{con.scroll_number}本次排名{my_ranking},高于{con.ranking},开始捐赠")
                if con.auto_contribute_memoryscrolls:
                    # 进行捐赠
                    self.ui_click(self.I_MS_OPEN_MEMORY, self.I_MS_CONTRIBUTE)
                    # 自动捐献碎片
                    logger.info(f'正在为{con.scroll_number}捐献碎片')
                    # 捐献前分数
                    ms_accrued_scores = self.O_MS_ACCRUED_SCORES.ocr(self.device.image)
                    # 开始捐赠
                    if con.score == 0:
                        self.contribute_memoryscrolls_all(ms_accrued_scores)
                    else:
                        self.contribute_memoryscrolls(ms_accrued_scores, con.score)
                    # 捐献前分数
                    ms_accrued_scores_after = self.O_MS_ACCRUED_SCORES.ocr(self.device.image)
                    ms_progress = self.O_MS_PROGRESS.ocr(self.device.image)
                    message = f'{con.scroll_number} 排名{my_ranking}，本次捐献{ms_accrued_scores_after - ms_accrued_scores}，累计捐献{ms_accrued_scores_after}积分，进度{ms_progress}%'
                    self.push_notify(content=message)
                else:
                    self.push_notify(content=f"未开启捐赠")
            else:
                self.push_notify(content=f"{con.scroll_number}本次排名{my_ranking},低于{con.ranking},无需捐赠")

    def close_task(self, con):
        message = f'{con.scroll_number}进度100%'
        if con.close_memoryscrolls:
            message += ',关闭绘卷任务'
            self.config.memory_scrolls.scheduler.enable = False
        if con.close_exploration:
            message += ',关闭探索任务'
            self.config.exploration.scheduler.enable = False
        if con.close_goryourealm:
            message += ',关闭御灵任务'
            self.config.goryou_realm.scheduler.enable = False

        self.config.save()
        self.push_notify(content=message)

    def contribute_memoryscrolls_all(self, ms_accrued_scores):
        """
        全部捐献碎片
        :return: None
        """
        wait_timer = Timer(120)
        wait_timer.start()
        while 1:
            self.screenshot()
            if wait_timer.reached():
                logger.info('等待超时')
                return
            if self.appear(self.I_MS_ZERO_S) and self.appear(self.I_MS_ZERO_M) and self.appear(self.I_MS_ZERO_L):
                logger.info('全部绘卷已捐献')
                ms_accrued_scores_now = self.O_MS_ACCRUED_SCORES.ocr(self.device.image)
                logger.info(f'本次已捐献{ms_accrued_scores_now - ms_accrued_scores}积分')
                return
            self.swipe(self.S_MS_SWIPE_S, interval=1)
            self.swipe(self.S_MS_SWIPE_M, interval=1)
            self.swipe(self.S_MS_SWIPE_L, interval=1)
            if self.appear_then_click(self.I_MS_CONTRIBUTE, interval=2):
                logger.info('已捐献记忆绘卷')
                # 等待捐献动画结束
                while 1:
                    self.screenshot()
                    if self.wait_until_appear(self.I_MS_CONTRIBUTED, wait_time=3):
                        self.click(self.C_MS_CONTRIBUTED, interval=1)
                    else:
                        break

    def contribute_memoryscrolls(self, ms_accrued_scores, donation_scores):
        """
        部分捐献碎片
        :return: None
        """
        wait_timer = Timer(120)
        wait_timer.start()
        while 1:
            self.screenshot()
            if wait_timer.reached():
                logger.info('等待超时')
                return
            if self.appear(self.I_MS_ZERO_S) and self.appear(self.I_MS_ZERO_M) and self.appear(self.I_MS_ZERO_L):
                logger.info('全部绘卷已捐献')
                ms_accrued_scores_now = self.O_MS_ACCRUED_SCORES.ocr(self.device.image)
                logger.info(f'本次已捐献{ms_accrued_scores_now - ms_accrued_scores}积分')
                return

            self.appear_then_click(self.I_MS_ADD_S)
            if self.appear(self.I_MS_ZERO_S):
                self.appear_then_click(self.I_MS_ADD_M)
            if self.appear(self.I_MS_ZERO_M):
                self.appear_then_click(self.I_MS_ADD_L)

            if self.appear_then_click(self.I_MS_CONTRIBUTE, interval=2):
                logger.info('已捐献记忆绘卷')
            # 等待捐献动画结束
            while 1:
                self.screenshot()
                if self.wait_until_appear(self.I_MS_CONTRIBUTED, wait_time=3):
                    self.click(self.C_MS_CONTRIBUTED, interval=1)
                else:
                    break

            ms_accrued_scores_now = self.O_MS_ACCRUED_SCORES.ocr(self.device.image)
            if ms_accrued_scores_now >= ms_accrued_scores + donation_scores:
                logger.info(f'本次已捐献{ms_accrued_scores_now - ms_accrued_scores}积分,超过{donation_scores}')
                return
    

if __name__ == '__main__':
    from module.config.config import Config
    c = Config('du')
    t = ScriptTask(c)
    # t.screenshot()

    t.run()





