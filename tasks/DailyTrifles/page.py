from tasks.DailyTrifles.assets import DailyTriflesAssets
from tasks.GameUi.assets import GameUiAssets
from tasks.GameUi.page import Page, page_mall, page_summon, page_main, page_shikigami_records
from tasks.RichMan.assets import RichManAssets

# 商店签到
page_store_sign = Page(DailyTriflesAssets.I_GIFT_RECOMMEND)
page_mall.link(button=DailyTriflesAssets.I_ROOM_GIFT, destination=page_store_sign)
page_store_sign.link(button=GameUiAssets.I_BACK_YELLOW, destination=page_mall)

# 进入Special 购买寿司
page_mall_special = Page(RichManAssets.I_SIDE_CHECK_SPECIAL)
page_mall.link(button=RichManAssets.I_MALL_SUNDRY, destination=page_mall_special)
page_mall.link(button=RichManAssets.I_SIDE_SURE_SPECIAL, destination=page_mall_special)
page_mall_special.link(button=GameUiAssets.I_BACK_YELLOW, destination=page_mall)


# 召唤商店
page_summon_store = Page(DailyTriflesAssets.I_SUMMON_STORE_PAGE)
page_summon.link(button=DailyTriflesAssets.I_SUMMON_STORE, destination=page_summon_store)
page_summon_store.link(button=GameUiAssets.I_BACK_YELLOW, destination=page_summon)

# 式神碎片页面
page_shikigami_debris = Page(DailyTriflesAssets.I_PAGE_SHIKIGAMI_DEBRIS)
page_shikigami_debris.link(button=GameUiAssets.I_BACK_YELLOW, destination=page_main)
page_shikigami_records.link(button=DailyTriflesAssets.I_GOTO_SHIKIGAMI_DEBRIS, destination=page_shikigami_debris)
