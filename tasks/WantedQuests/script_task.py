# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
from time import sleep

import re
from cached_property import cached_property
from datetime import timedelta, time, datetime
from module.atom.image import RuleImage
from module.base.timer import Timer
from module.exception import TaskEnd
from module.logger import logger
from tasks.Component.Costume.config import MainType
from tasks.Component.GeneralInvite.general_invite import GeneralInvite
from tasks.GameUi.page import page_main, page_exploration
from tasks.Secret.script_task import ScriptTask as SecretScriptTask
from tasks.WantedQuests.assets import WantedQuestsAssets
from tasks.WantedQuests.config import CooperationType, CooperationSelectMask
from typing import List

""" 悬赏封印 """


class ScriptTask(SecretScriptTask, GeneralInvite, WantedQuestsAssets):
    # 定义检查次数
    play_count = 0

    def run(self):

        con = self.config.wanted_quests
        if con.switch_soul.enable:
            self.run_switch_soul(con.switch_soul.switch_group_team)
        if con.switch_soul.enable_switch_by_name:
            self.run_switch_soul_by_name(con.switch_soul.group_name, con.switch_soul.team_name)

        while 1:
            if not self.pre_work():
                # 无法完成预处理 很有可能你已经完成了悬赏任务
                logger.warning('Cannot pre-work')
                logger.warning('You may have completed the reward task')
                self.next_run()
                raise TaskEnd('WantedQuests')
            # 执行悬赏
            self.play_run()

    def play_run(self):
        self.screenshot()
        number_challenge = self.O_WQ_NUMBER.ocr(self.device.image)
        wq_timer = Timer(3)
        wq_timer.start()
        self.limit_count = 20
        while 1:
            self.screenshot()

            if self.appear(self.I_WQ_BOX):
                logger.info("检测到奖励宝箱，尝试领取")
                self.ui_get_reward(self.I_WQ_BOX)
                wq_timer.reset()
                continue

            if self.current_count >= self.limit_count:
                logger.warning(f'战斗次数超标（{self.current_count}次），强制退出')
                self.push_notify(content=f'战斗次数超标（{self.current_count}次），强制退出')
                break

            target_found = False
            O_WQ_INSTANCES = [
                (self.I_WQ_END_1, self.O_WQ_TEXT_1, self.O_WQ_NUM_1),
                (self.I_WQ_END_2, self.O_WQ_TEXT_2, self.O_WQ_NUM_2)
            ]
            TARGET_CHAR = "印"
            for end_obj, text_obj, num_obj in O_WQ_INSTANCES:
                if self.appear(end_obj):
                    continue
                detected_str = text_obj.detect_text(self.device.image)
                if TARGET_CHAR in detected_str:
                    cu, re, total = num_obj.ocr(self.device.image)
                    if cu > total:
                        logger.warning('Current number of wanted quests is greater than total number')
                        cu %= 10
                    if cu < total and re != 0:
                        self.execute_mission(text_obj, re, number_challenge)
                        wq_timer.reset()
                        target_found = True

            if target_found:
                continue

            if self.appear(self.I_WQ_CHECK_TASK):
                logger.info('悬赏发现残留任务，尝试处理')
                # self.save_image(task_name='悬赏发现残留任务', wait_time=0, image_type='png')
                x, y, w, h = self.I_WQ_CHECK_TASK.roi_front
                self.I_WQ_CHECK_TASK_CLICK.roi_front = (x - 70, y, w + 30, h)
                logger.info(f'调整点击区域至: {self.I_WQ_CHECK_TASK_CLICK.roi_front}')
                self.execute_mission(self.I_WQ_CHECK_TASK_CLICK, 1, number_challenge, flag=True)
                # self.save_image(task_name='悬赏发现残留任务,战斗结束', wait_time=0, image_type='png')
                wq_timer.reset()
                continue

            if wq_timer.reached():
                logger.info('悬赏未检测到残留任务，退出循环')
                # self.save_image(task_name='悬赏未检测到残留任务', wait_time=0, image_type='png')
                break

    def next_run(self):
        now_datetime = datetime.now()
        now_time = now_datetime.time()
        server_update_am = self.config.wanted_quests.scheduler.server_update
        server_update_pm = self.config.wanted_quests.scheduler.server_update_pm

        if time(hour=5) <= now_time < time(hour=server_update_pm.hour, minute=server_update_pm.minute,
                                           second=server_update_pm.second):
            next_run_datetime = datetime.combine(now_datetime.date(),
                                                 time(hour=server_update_pm.hour, minute=server_update_pm.minute,
                                                      second=server_update_pm.second))
        elif time(hour=0) <= now_time < time(hour=5):
            next_run_datetime = datetime.combine(now_datetime.date(),
                                                 time(hour=server_update_am.hour, minute=server_update_am.minute,
                                                      second=server_update_am.second))
        else:
            next_run_datetime = datetime.combine(now_datetime.date() + timedelta(days=1),
                                                 time(hour=server_update_am.hour, minute=server_update_am.minute,
                                                      second=server_update_am.second))
        self.set_next_run(task='WantedQuests', target=next_run_datetime)
        # 使用PPOCR
        # OCR_MODEL.switch_to_ppocr()

    def pre_work(self):
        """
        前置工作，
        :return:
        """
        self.play_count += 1
        self.ui_goto_page(page_main)
        done_timer = Timer(5)
        if self.play_count >= 3:
            return False
        while 1:
            self.screenshot()
            if self.appear(self.I_TARCE_DISENABLE):
                break
            if self.appear_then_click(self.I_WQ_SEAL, interval=1):
                continue
            if self.appear_then_click(self.I_WQ_DONE, interval=1):
                continue
            if self.appear_then_click(self.I_TRACE_ENABLE, interval=1):
                continue
            if self.special_main and self.click(self.C_SPECIAL_MAIN, interval=3):
                logger.info('Click special main left to find wanted quests')
                continue
            if self.appear(self.I_UI_BACK_RED):
                if not done_timer.started():
                    done_timer.start()
            if done_timer.started() and done_timer.reached():
                self.ui_click_until_disappear(self.I_UI_BACK_RED)
                return False
        # 已追踪所有任务
        logger.info('All wanted quests are traced')

        # 存在协作任务则邀请
        self.screenshot()
        if self.appear(self.I_WQ_INVITE_1) or self.appear(self.I_WQ_INVITE_2) or self.appear(self.I_WQ_INVITE_3):
            if self.config.wanted_quests.wanted_quests_config.invite_friend_name:
                self.all_cooperation_invite(self.config.wanted_quests.wanted_quests_config.invite_friend_name)
            else:
                self.invite_five()
        self.ui_click_until_disappear(self.I_UI_BACK_RED)
        self.ui_goto_page(page_exploration)
        return True

    def execute_mission(self, ocr, num_want: int, num_challenge: int, flag=False):
        """

        :param ocr: 要点击的 文字
        :param num_want: 一共要打败的怪物数量
        :param num_challenge: 现在有的挑战卷数量
        :param flag:
        :return:
        """
        logger.hr('Start wanted quests')
        click_timer = Timer(5)
        click_timer.start()
        click_count = 0
        while 1:
            self.screenshot()
            if flag:
                if not self.appear(self.I_WQ_CHECK_TASK):
                    return
            if click_count > 5:
                return
            if click_timer.reached():
                return
            if self.appear(self.I_TRACE_TRUE):
                break
            if self.appear(self.I_GOTO_1):
                break
            if self.click(ocr, interval=1):
                click_count += 1
                continue
        if not self.appear(self.I_GOTO_1):
            # 如果没有出现 '前往'按钮， 那就是这个可能是神秘任务但是没有解锁
            logger.warning('This is a secret mission but not unlock')
            self.ui_click(self.I_TRACE_TRUE, self.I_TRACE_FALSE)
            return
        # 找到一个最优的关卡来挑战
        challenge = True if num_challenge >= 10 else False

        def check_battle(cha: bool, wq_type, wq_info) -> tuple:
            battle = False
            self.screenshot()
            type_wq = wq_type.ocr(self.device.image)
            if cha and type_wq == '挑战':
                battle = 'CHALLENGE'
            if type_wq == '秘闻':
                battle = 'SECRET'
            if not battle:
                return None, None
            info = wq_info.ocr(self.device.image)
            try:
                # 匹配： 第九章(数量:5)
                one_number = int(re.findall(r'(\d+)', info)[-1])
                # one_number = int(re.findall(r'\*\(\数量:\s*(\d+)\)', info)[0])
            except IndexError:
                # 匹配： 第九章
                one_number = 3
            # num_want / one_number = 一共要打几次
            if one_number > num_want:
                logger.info(f'[悬赏类型: {type_wq}] [次数: 1]')
                return battle, 1
            else:
                # 添加 min 函数限制最大战斗次数为 5次，防止无限增加
                battle_count = min((num_want + one_number - 1) // one_number, 5)
                logger.info(f'[悬赏类型: {type_wq}] [次数: {battle_count}]')
                return battle, battle_count

        battle, num, goto = None, None, None
        if not battle:
            battle, num = check_battle(challenge, self.O_WQ_TYPE_1, self.O_WQ_INFO_1)
            goto = self.I_GOTO_1
        if not battle:
            battle, num = check_battle(challenge, self.O_WQ_TYPE_2, self.O_WQ_INFO_2)
            goto = self.I_GOTO_2
        if not battle:
            battle, num = check_battle(challenge, self.O_WQ_TYPE_3, self.O_WQ_INFO_3)
            goto = self.I_GOTO_3
        if not battle:
            battle, num = check_battle(challenge, self.O_WQ_TYPE_4, self.O_WQ_INFO_4)
            goto = self.I_GOTO_4

        if battle == 'CHALLENGE':
            self.challenge(goto, num)
        elif battle == 'SECRET':
            self.secret(goto, num)
        else:
            # 没有找到可以挑战的关卡 那就关闭
            logger.warning('No wanted quests can be challenged')
            return False

    def challenge(self, goto, num):
        self.ui_click(goto, self.I_WQC_FIRE)
        # 不需要解锁
        # self.ui_click(self.I_WQC_LOCK, self.I_WQC_UNLOCK)
        self.ui_click_until_disappear(self.I_WQC_FIRE)
        self.battle_config.lock_team_enable = True
        self.run_general_battle(self.battle_config)
        # self.run_general_battle()
        self.wait_until_appear(self.I_WQC_FIRE, wait_time=4)
        self.ui_click_until_disappear(self.I_UI_BACK_RED)
        # 我忘记了打完后是否需要关闭 挑战界面

    def secret(self, goto, num=1):
        self.ui_click(goto, self.I_WQSE_FIRE)
        for i in range(num):
            self.wait_until_appear(self.I_WQSE_FIRE)
            # self.ui_click_until_disappear(self.I_WQSE_FIRE)
            # 又臭又长的对话针的是服了这个网易
            click_count = 0
            while 1:
                self.screenshot()
                if not self.appear(self.I_UI_BACK_RED, threshold=0.7):
                    break
                if self.appear_then_click(self.I_WQSE_FIRE, interval=1):
                    continue
                if self.appear(self.I_UI_BACK_RED, threshold=0.7) and not self.appear(self.I_WQSE_FIRE):
                    self.click(self.C_SECRET_CHAT, interval=0.8)
                    click_count += 1
                    if click_count >= 6:
                        logger.warning('Secret mission chat too long, force to close')
                        click_count = 0
                        self.device.click_record_clear()
                    continue
            self.battle_config.lock_team_enable = False
            success = self.run_general_battle(self.battle_config)
            # 战斗结束对话
            while 1:
                self.screenshot()
                if self.appear(self.I_WQSE_FIRE):
                    break
                if self.appear(self.I_CHECK_SECRET_ZONES):
                    break
                if self.appear(self.I_SE_ENTER):
                    break
                if self.click(self.C_SECRET_CHAT, interval=1):
                    continue
        self.ui_goto_page(page_exploration)
        logger.info('Secret mission finished')

    def invite_random(self, add_button: RuleImage):
        self.screenshot()
        if not self.appear(add_button):
            return False
        self.ui_click(add_button, self.I_WQ_INVITE_ENSURE, interval=2.5)
        logger.info('enter invite form')
        sleep(1)
        self.click(self.I_WQ_FRIEND_1)
        sleep(0.4)
        self.click(self.I_WQ_FRIEND_2)
        sleep(0.4)
        self.click(self.I_WQ_FRIEND_3)
        sleep(0.4)
        self.click(self.I_WQ_FRIEND_4)
        sleep(0.4)
        self.click(self.I_WQ_FRIEND_5)
        sleep(0.2)
        self.screenshot()
        if not self.appear(self.I_WQ_INVITE_SELECTED):
            logger.warning('No friend selected')
            return False
        self.ui_click_until_disappear(self.I_WQ_INVITE_ENSURE)
        sleep(0.5)

    def invite_five(self):
        """
        邀请好友，默认点五个
        :return:
        """

        logger.hr('Invite friends')
        self.invite_random(self.I_WQ_INVITE_1)
        self.invite_random(self.I_WQ_INVITE_2)
        self.invite_random(self.I_WQ_INVITE_3)

    def all_cooperation_invite(self, name: str):
        """
            所有的协作任务依次邀请
        @param name: 被邀请的朋友名
        @return:

        """
        self.screenshot()
        if not self.appear(self.I_WQ_INVITE_1):
            return False

        ret = self.get_cooperation_info()
        if len(ret) == 0:
            logger.info("no Cooperation found")
            return False
        typeMask = 15
        typeMask = CooperationSelectMask[self.config.wanted_quests.wanted_quests_config.cooperation_type.value]
        for item in ret:
            # 该任务是需要邀请的任务类型
            if not (item['type'] & typeMask):
                # BUG 存在多个协作任务时,邀请完第一个协作任务对方接受后,未邀请的任务位置无法确定(缺少信息)
                # 例如 按顺序存在 abc 3个协作任务,邀请完a,好友接受后,这三个任务在界面上的顺序变化,abc 还是bca
                # 如果顺序不变 则应该没有问题
                logger.info("cooperationType %s But needed Type %s ,Skipped", item['type'], typeMask)
                break
            '''
               尝试5次 如果邀请失败 等待20s 重新尝试
               阴阳师BUG: 好友明明在线 但邀请界面找不到该好友(好友未接受任何协作任务的情况下)
           '''
            index = 0
            while index < 5:
                if self.cooperation_invite(item['inviteBtn'], name):
                    item['inviteResult'] = True
                    index = 5
                logger.info("%s not found,Wait 20s,%d invitations left", name, 5 - index - 1)
                index += 1
                sleep(20) if index < 5 else sleep(0)
                #NOTE 等待过程如果出现协作邀请 将会卡住 为了防止卡住
                self.screenshot()
        return ret

    def cooperation_invite(self, btn: RuleImage, name: str):
        """
            单个协作任务邀请
        @param btn:
        @param name:
        @return:
        """
        self.ui_click(btn, self.I_WQ_INVITE_ENSURE, interval=2.5)

        # 选人
        self.O_WQ_INVITE_COLUMN_1.keyword = name
        self.O_WQ_INVITE_COLUMN_2.keyword = name

        find = False
        for i in range(2):
            self.screenshot()
            in_col_1 = self.ocr_appear_click(self.O_WQ_INVITE_COLUMN_1)
            in_col_2 = self.ocr_appear_click(self.O_WQ_INVITE_COLUMN_2)
            find = in_col_2 or in_col_1
            if find:
                self.screenshot()
                if self.appear(self.I_WQ_INVITE_SELECTED):
                    logger.info("friend found and selected")
                    break
                # TODO OCR识别到文字 但是没有选中 尝试重新选择  (选择好友时,弹出协作邀请导致选择好友失败)
            # 在当前服务器没找到,切换服务器
            self.click(self.I_WQ_INVITE_DIFF_SVR)
            # NOTE 跨服好友刷新缓慢,切换标签页难以检测,姑且用延时.非常卡的模拟器可能出问题
            sleep(2)
        # 没有找到需要邀请的人,点击取消 返回悬赏封印界面
        if not find:
            self.screenshot()
            self.click(self.I_WQ_INVITE_CANCEL)
            return False
        #
        self.ui_click_until_disappear(self.I_WQ_INVITE_ENSURE)
        return True

    def get_cooperation_info(self) -> List:
        """
            获取协作任务详情
        @return: 协作任务类型与邀请按钮
        """
        self.screenshot()
        retList = []
        i = 0
        for index in range(3):
            btn = self.__getattribute__("I_WQ_INVITE_" + str(index + 1))
            if not self.appear(btn):
                break
            if self.appear(self.__getattribute__("I_WQ_COOPERATION_TYPE_JADE_" + str(index + 1))):
                retList.append({'type': CooperationType.Jade, 'inviteBtn': btn})
                continue
            if self.appear(self.__getattribute__("I_WQ_COOPERATION_TYPE_DOG_FOOD_" + str(index + 1))):
                retList.append({'type': CooperationType.Food, 'inviteBtn': btn})
                continue
            if self.appear(self.__getattribute__("I_WQ_COOPERATION_TYPE_CAT_FOOD_" + str(index + 1))):
                retList.append({'type': CooperationType.Food, 'inviteBtn': btn})
                continue
            if self.appear(self.__getattribute__("I_WQ_COOPERATION_TYPE_SUSHI_" + str(index + 1))):
                retList.append({'type': CooperationType.Sushi, 'inviteBtn': btn})
                continue
            # NOTE 因为食物协作里面也有金币奖励 ,所以判断金币协作放在最后面
            if self.appear(self.__getattribute__("I_WQ_COOPERATION_TYPE_GOLD_" + str(index + 1))):
                retList.append({'type': CooperationType.Gold, 'inviteBtn': btn})
                continue

        return retList

    @cached_property
    def special_main(self) -> bool:
        # 特殊的庭院需要点一下，左边然后才能找到图标
        main_type = self.config.global_game.costume_config.costume_main_type
        if main_type == MainType.COSTUME_MAIN_3:
            return True
        return False


if __name__ == '__main__':
    from module.config.config import Config

    c = Config('du')
    t = ScriptTask(c)
    t.screenshot()

    t.run()
    # print(t.appear(t.I_WQ_CHECK_TASK))
