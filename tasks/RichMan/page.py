from tasks.GameUi.assets import GameUiAssets as G
from tasks.GameUi.page import Page, page_guild
from tasks.RichMan.assets import RichManAssets

# 神社 （出现功勋商店代表进入神社）
page_shrine = Page(RichManAssets.I_GUILD_STORE)
page_shrine.link(button=G.I_BACK_YELLOW, destination=page_guild)
page_guild.link(button=RichManAssets.I_GUILD_SHRINE, destination=page_shrine)

# 功勋商店
page_medal_store = Page(RichManAssets.I_GUILD_STORE_PAGE)
page_medal_store.link(button=RichManAssets.I_GUILD_CLOSE_RED, destination=page_shrine)
page_shrine.link(button=RichManAssets.I_GUILD_STORE, destination=page_medal_store)


# 寮内采办
page_guid_procurement = Page(RichManAssets.I_GUILD_STORE_PROCUREMENT_PAGE)
page_guid_procurement.link(button=RichManAssets.I_GUILD_CLOSE_RED, destination=page_shrine)
page_shrine.link(button=RichManAssets.I_GUILD_STORE_PROCUREMENT, destination=page_guid_procurement)