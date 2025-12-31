from tasks.GameUi.assets import GameUiAssets as G
from tasks.GameUi.page import Page, page_main
from tasks.TalismanPass.assets import TalismanPassAssets

# 花合战 daily
page_daily = Page(G.I_CHECK_DAILY)
page_daily.additional = [TalismanPassAssets.I_TP_SKIP, G.O_CLICK_CLOSE_1, G.O_CLICK_CLOSE_2]
page_daily.link(button=G.I_BACK_YELLOW, destination=page_main)
page_main.link(button=G.I_MAIN_GOTO_DAILY, destination=page_daily)

# 花合战成就 daily
page_accomplishment = Page(TalismanPassAssets.I_ACCOMPLISHMENTS_2)
page_accomplishment.link(button=G.I_BACK_YELLOW, destination=page_daily)
page_daily.link(button=TalismanPassAssets.I_ACCOMPLISHMENTS_1, destination=page_accomplishment)
