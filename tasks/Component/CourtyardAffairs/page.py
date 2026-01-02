from tasks.CourtyardAffairs.assets import CourtyardAffairsAssets
from tasks.GameUi.page import page_main
from tasks.GameUi.page import Page
from tasks.GameUi.assets import GameUiAssets

# 通过刷新寻找庭院事务按钮
# page_courtyard_affairs_button = Page(CourtyardAffairsAssets.I_COURTYARD_AFFAIRS_BUTTON)
# page_courtyard_affairs_button.link(button=GameUiAssets.I_BACK_YELLOW, destination=page_main)
# page_main.link(button=GameUiAssets.I_REFRESH, destination=page_courtyard_affairs_button)

# 庭院事务主页
page_courtyard_affairs = Page(CourtyardAffairsAssets.I_COURTYARD_AFFAIRS_PAGE)
page_courtyard_affairs.link(button=GameUiAssets.I_BACK_YELLOW, destination=page_main)
page_main.link(button=CourtyardAffairsAssets.I_COURTYARD_AFFAIRS_BUTTON, destination=page_courtyard_affairs)
