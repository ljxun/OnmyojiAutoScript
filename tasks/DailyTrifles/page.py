from tasks.DailyTrifles.assets import DailyTriflesAssets
from tasks.GameUi.page import Page, page_mall
from tasks.RichMan.assets import RichManAssets

# 商店签到
page_store_sign = Page(DailyTriflesAssets.I_GIFT_RECOMMEND)
page_mall.link(button=DailyTriflesAssets.I_ROOM_GIFT, destination=page_store_sign)

# 进入Special 购买寿司
page_mall_special = Page(RichManAssets.I_SIDE_CHECK_SPECIAL)
page_mall.link(button=RichManAssets.I_SIDE_SURE_SPECIAL, destination=page_mall_special)
page_mall.link(button=RichManAssets.I_MALL_SUNDRY, destination=page_mall_special)
