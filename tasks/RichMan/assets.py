from module.atom.image import RuleImage
from module.atom.click import RuleClick
from module.atom.long_click import RuleLongClick
from module.atom.swipe import RuleSwipe
from module.atom.ocr import RuleOcr
from module.atom.list import RuleList

# This file was automatically generated by ./dev_tools/assets_extract.py.
# Don't modify it manually.
class RichManAssets: 


	# Image Rule Assets
	# 神社 
	I_GUILD_SHRINE = RuleImage(roi_front=(869,623,64,62), roi_back=(869,623,64,62), threshold=0.8, method="Template matching", file="./tasks/RichMan/guild/guild_guild_shrine.png")
	# 功勋商店 
	I_GUILD_STORE = RuleImage(roi_front=(651,420,212,161), roi_back=(651,420,212,161), threshold=0.8, method="Template matching", file="./tasks/RichMan/guild/guild_guild_store.png")
	# description 
	I_GUILD_CLOSE_RED = RuleImage(roi_front=(1029,120,53,57), roi_back=(1029,120,53,57), threshold=0.8, method="Template matching", file="./tasks/RichMan/guild/guild_guild_close_red.png")
	# 蓝票 
	I_GUILD_BLUE = RuleImage(roi_front=(794,186,74,73), roi_back=(315,164,584,370), threshold=0.8, method="Template matching", file="./tasks/RichMan/guild/guild_guild_blue.png")
	# 黑蛋碎片 
	I_GUILD_SCRAP = RuleImage(roi_front=(570,439,71,68), roi_back=(331,160,559,372), threshold=0.8, method="Template matching", file="./tasks/RichMan/guild/guild_guild_scrap.png")
	# 皮肤券 
	I_GUILD_SKIN = RuleImage(roi_front=(795,438,71,72), roi_back=(320,162,573,371), threshold=0.6, method="Template matching", file="./tasks/RichMan/guild/guild_guild_skin.png")
	# 购买检查 
	I_GUILD_CHECK_SCRAP = RuleImage(roi_front=(561,429,90,88), roi_back=(561,429,90,88), threshold=0.8, method="Template matching", file="./tasks/RichMan/guild/guild_guild_check_scrap.png")


	# Ocr Rule Assets
	# 总的功勋 
	O_GUILD_TOTAL = RuleOcr(roi=(978,16,58,27), area=(978,16,58,27), mode="Digit", method="Default", keyword="", name="guild_total")
	# Ocr-description 
	O_GUILD_NUMBER_BLUE = RuleOcr(roi=(888,269,25,33), area=(888,269,25,33), mode="Digit", method="Default", keyword="", name="guild_number_blue")
	# Ocr-description 
	O_GUILD_NUMBER_BLACK = RuleOcr(roi=(663,523,21,27), area=(663,523,21,27), mode="Digit", method="Default", keyword="", name="guild_number_black")
	# Ocr-description 
	O_GUILD_NUMBER_SKIN = RuleOcr(roi=(889,519,21,35), area=(889,519,21,35), mode="Digit", method="Default", keyword="", name="guild_number_skin")
	# 本周剩余数量x 
	O_GUILD_REMAIN = RuleOcr(roi=(304,268,154,33), area=(304,268,154,33), mode="Single", method="Default", keyword="", name="guild_remain")


	# Swipe Rule Assets
	# description 
	S_GUILD_STORE = RuleSwipe(roi_front=(807,460,46,35), roi_back=(720,214,90,34), mode="default", name="guild_store")


	# Image Rule Assets
	# 兑换随机御魂 
	I_BL_BUY_SOULS = RuleImage(roi_front=(197,476,90,38), roi_back=(197,476,90,38), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/bondlings/bondlings_bl_buy_souls.png")
	# 兑换契灵石头 
	I_BL_BUY_STONE = RuleImage(roi_front=(493,472,89,42), roi_back=(493,472,89,42), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/bondlings/bondlings_bl_buy_stone.png")
	# 兑换高级盘 
	I_BL_BUY_HIGH = RuleImage(roi_front=(779,473,89,42), roi_back=(779,473,89,42), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/bondlings/bondlings_bl_buy_high.png")
	# 兑换中级盘 
	I_BL_BUY_MEDIUM = RuleImage(roi_front=(1079,476,93,40), roi_back=(1079,476,93,40), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/bondlings/bondlings_bl_buy_medium.png")


	# Ocr Rule Assets
	# 御魂剩余 
	O_BL_RES_SOULS = RuleOcr(roi=(90,281,31,34), area=(90,281,31,34), mode="Digit", method="Default", keyword="", name="bl_res_souls")
	# 石头剩余 
	O_BL_RES_STONE = RuleOcr(roi=(357,284,29,34), area=(357,284,29,34), mode="Digit", method="Default", keyword="", name="bl_res_stone")
	# 高级盘剩余 
	O_BL_RES_HIGH = RuleOcr(roi=(642,284,29,31), area=(642,284,29,31), mode="Digit", method="Default", keyword="", name="bl_res_high")
	# 中级盘剩余 
	O_BL_RES_MEDIUM = RuleOcr(roi=(918,285,28,27), area=(918,285,28,27), mode="Digit", method="Default", keyword="", name="bl_res_medium")
	# 检查契灵的钱是否够 
	O_BL_CHECK_MONEY = RuleOcr(roi=(1123,12,127,33), area=(1123,12,127,33), mode="DigitCounter", method="Default", keyword="", name="bl_check_money")


	# Image Rule Assets
	# 蓝票 
	I_CH_BLUE = RuleImage(roi_front=(623,142,145,111), roi_back=(623,142,145,111), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/charisma/charisma_ch_blue.png")
	# description 
	I_CH_BLACK = RuleImage(roi_front=(848,393,141,110), roi_back=(848,393,141,110), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/charisma/charisma_ch_black.png")
	# 蓝票购买确认 
	I_CH_CHECK_BLUE = RuleImage(roi_front=(587,243,100,100), roi_back=(587,243,100,100), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/charisma/charisma_ch_check_blue.png")


	# Image Rule Assets
	# 进入寄售屋 
	I_CON_ENTER_CHECK = RuleImage(roi_front=(660,423,393,162), roi_back=(660,423,393,162), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/consignment/consignment_con_enter_check.png")
	# 兑换 
	I_CON_ENTER = RuleImage(roi_front=(1176,304,68,74), roi_back=(1176,304,68,74), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/consignment/consignment_con_enter.png")
	# 寄售券 
	I_CON_TICKET = RuleImage(roi_front=(700,194,100,100), roi_back=(700,194,100,100), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/consignment/consignment_con_ticket.png")


	# Ocr Rule Assets
	# 寄售券可以购买的数量 
	O_CON_NUMBER = RuleOcr(roi=(813,140,34,38), area=(813,140,34,38), mode="Digit", method="Default", keyword="", name="con_number")


	# Image Rule Assets
	# 红蛋 
	I_FS_RED = RuleImage(roi_front=(400,138,141,135), roi_back=(400,138,141,135), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/friendship_points/friendship_points_fs_red.png")
	# 破碎的咒符 
	I_FS_BROKEN = RuleImage(roi_front=(173,142,149,129), roi_back=(173,142,149,129), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/friendship_points/friendship_points_fs_broken.png")
	# description 
	I_FS_WHITE_CLICK = RuleImage(roi_front=(627,140,138,132), roi_back=(627,140,138,132), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/friendship_points/friendship_points_fs_white_click.png")
	# 白蛋确认 
	I_FS_WHITE_CHECK = RuleImage(roi_front=(589,227,100,100), roi_back=(589,227,100,100), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/friendship_points/friendship_points_fs_white_check.png")


	# Image Rule Assets
	# 蓝票 
	I_HONOR_BLUE = RuleImage(roi_front=(868,152,100,100), roi_back=(154,113,864,476), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/honor/honor_honor_blue.png")
	# 黑蛋碎片 
	I_HONOR_BLACK = RuleImage(roi_front=(645,406,100,100), roi_back=(145,96,883,491), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/honor/honor_honor_black.png")
	# 三星白蛋 
	I_HONOR_WHITE = RuleImage(roi_front=(424,399,100,100), roi_back=(155,127,841,388), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/honor/honor_honor_white.png")


	# Ocr Rule Assets
	# Ocr-description 
	O_HONOR_BLUE = RuleOcr(roi=(973,113,22,26), area=(973,113,22,26), mode="Digit", method="Default", keyword="", name="honor_blue")
	# Ocr-description 
	O_HONOR_BLACK = RuleOcr(roi=(749,358,24,34), area=(749,358,24,34), mode="Digit", method="Default", keyword="", name="honor_black")
	# 三星白蛋 
	O_HONOR_WHITE = RuleOcr(roi=(527,359,25,28), area=(527,359,25,28), mode="Digit", method="Default", keyword="", name="honor_white")


	# Image Rule Assets
	# 黑蛋 
	I_ME_BLACK = RuleImage(roi_front=(631,152,130,120), roi_back=(165,121,859,431), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/medal/medal_me_black.png")
	# 蓝票 
	I_ME_BLUE = RuleImage(roi_front=(176,148,138,126), roi_back=(139,115,887,464), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/medal/medal_me_blue.png")
	# 体力 
	I_ME_AP = RuleImage(roi_front=(842,395,145,123), roi_back=(156,111,862,454), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/medal/medal_me_ap.png")
	# 随机御魂 
	I_ME_SOULS = RuleImage(roi_front=(173,391,148,133), roi_back=(121,116,898,476), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/medal/medal_me_souls.png")
	# 白蛋 
	I_ME_WHITE = RuleImage(roi_front=(399,391,142,131), roi_back=(115,114,908,452), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/medal/medal_me_white.png")
	# 御灵挑战券 
	I_ME_CHALLENGE_PASS = RuleImage(roi_front=(618,390,146,129), roi_back=(114,102,914,478), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/medal/medal_me_challenge_pass.png")
	# 红蛋 
	I_ME_RED = RuleImage(roi_front=(847,146,137,129), roi_back=(141,129,864,454), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/medal/medal_me_red.png")
	# 破碎的咒符 
	I_ME_BROKEN = RuleImage(roi_front=(398,144,143,116), roi_back=(146,116,866,475), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/medal/medal_me_broken.png")
	# 购买检查 
	I_ME_CHECK_BLACK = RuleImage(roi_front=(585,230,100,100), roi_back=(585,230,100,100), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/medal/medal_me_check_black.png")
	# 购买检查 
	I_ME_CHECK_BLUE = RuleImage(roi_front=(587,238,100,100), roi_back=(587,238,100,100), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/medal/medal_me_check_blue.png")
	# 购买检查 
	I_ME_CHECK_AP = RuleImage(roi_front=(588,242,100,100), roi_back=(588,242,100,100), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/medal/medal_me_check_ap.png")
	# 购买检查 
	I_ME_CHECK_SOULS = RuleImage(roi_front=(590,257,100,100), roi_back=(590,257,100,100), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/medal/medal_me_check_souls.png")


	# Image Rule Assets
	# 寄售屋 
	I_MALL_CONSIGNMENT = RuleImage(roi_front=(200,626,63,72), roi_back=(175,610,120,103), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/navbar/navbar_mall_consignment.png")
	# 寄售屋 
	I_MALL_CONSIGNMENT_CHECK = RuleImage(roi_front=(12,166,100,390), roi_back=(12,166,100,390), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/navbar/navbar_mall_consignment_check.png")
	# 密卷屋 
	I_MALL_SCCALES = RuleImage(roi_front=(447,634,91,64), roi_back=(427,621,147,92), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/navbar/navbar_mall_sccales.png")
	# 密卷屋 
	I_MALL_SCCALES_CHECK = RuleImage(roi_front=(409,253,100,100), roi_back=(409,253,100,100), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/navbar/navbar_mall_sccales_check.png")
	# description 
	I_MALL_SCALES_SURE = RuleImage(roi_front=(1195,100,62,85), roi_back=(1195,100,62,85), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/navbar/navbar_mall_scales_sure.png")
	# 契灵商店 
	I_MALL_BONDLINGS_SURE = RuleImage(roi_front=(1194,421,69,74), roi_back=(1194,421,69,74), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/navbar/navbar_mall_bondlings_sure.png")
	# 契灵商店 
	I_MALL_BONDLINGS_CHECK = RuleImage(roi_front=(355,186,34,104), roi_back=(355,186,34,104), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/navbar/navbar_mall_bondlings_check.png")
	# 杂货铺 
	I_MALL_SUNDRY = RuleImage(roi_front=(856,639,74,61), roi_back=(834,621,116,90), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/navbar/navbar_mall_sundry.png")
	# 杂货铺 
	I_MALL_SUNDRY_CHECK = RuleImage(roi_front=(1093,10,31,44), roi_back=(1093,10,31,44), threshold=0.7, method="Template matching", file="./tasks/RichMan/mall/navbar/navbar_mall_sundry_check.png")


	# Image Rule Assets
	# 特殊 
	I_SIDE_SURE_SPECIAL = RuleImage(roi_front=(1172,91,70,74), roi_back=(1172,91,70,74), threshold=0.7, method="Template matching", file="./tasks/RichMan/mall/navbar/navbar_side_sure_special.png")
	# 特殊 
	I_SIDE_CHECK_SPECIAL = RuleImage(roi_front=(102,7,42,42), roi_back=(102,7,42,42), threshold=0.7, method="Template matching", file="./tasks/RichMan/mall/navbar/navbar_side_check_special.png")
	# 荣誉 
	I_SIDE_SUER_HONOR = RuleImage(roi_front=(1180,191,59,60), roi_back=(1150,159,103,132), threshold=0.7, method="Template matching", file="./tasks/RichMan/mall/navbar/navbar_side_suer_honor.png")
	# 荣誉 
	I_SIDE_CHECK_HONOR = RuleImage(roi_front=(694,12,41,42), roi_back=(694,12,41,42), threshold=0.7, method="Template matching", file="./tasks/RichMan/mall/navbar/navbar_side_check_honor.png")
	# 友情点 
	I_SIDE_SURE_FRIENDS = RuleImage(roi_front=(1190,287,43,52), roi_back=(1163,258,93,109), threshold=0.7, method="Template matching", file="./tasks/RichMan/mall/navbar/navbar_side_sure_friends.png")
	# 友情点 
	I_SIDE_CHECK_FRIENDS = RuleImage(roi_front=(890,8,39,43), roi_back=(890,8,39,43), threshold=0.7, method="Template matching", file="./tasks/RichMan/mall/navbar/navbar_side_check_friends.png")
	# 勋章 
	I_SIDE_SURE_MEDAL = RuleImage(roi_front=(1190,375,39,62), roi_back=(1156,352,99,113), threshold=0.7, method="Template matching", file="./tasks/RichMan/mall/navbar/navbar_side_sure_medal.png")
	# 勋章 
	I_SIDE_CHECK_MEDAL = RuleImage(roi_front=(665,6,40,44), roi_back=(453,1,476,58), threshold=0.7, method="Template matching", file="./tasks/RichMan/mall/navbar/navbar_side_check_medal.png")
	# 魅力值 
	I_SIDE_SURE_CHARISMA = RuleImage(roi_front=(1181,467,59,58), roi_back=(1158,445,101,106), threshold=0.7, method="Template matching", file="./tasks/RichMan/mall/navbar/navbar_side_sure_charisma.png")
	# 魅力值 
	I_SIDE_CHECK_CHARISMA = RuleImage(roi_front=(886,4,48,46), roi_back=(886,4,48,46), threshold=0.7, method="Template matching", file="./tasks/RichMan/mall/navbar/navbar_side_check_charisma.png")


	# Ocr Rule Assets
	# 左数第一个 
	O_MALL_RESOURCE_1 = RuleOcr(roi=(144,7,100,43), area=(144,7,100,43), mode="Digit", method="Default", keyword="", name="mall_resource_1")
	# 左数第二个 
	O_MALL_RESOURCE_2 = RuleOcr(roi=(326,8,124,39), area=(326,8,124,39), mode="Digit", method="Default", keyword="", name="mall_resource_2")
	# 左数第二个 
	O_MALL_RESOURCE_3 = RuleOcr(roi=(533,9,107,38), area=(533,9,107,38), mode="Digit", method="Default", keyword="", name="mall_resource_3")
	# 左数第二个 
	O_MALL_RESOURCE_4 = RuleOcr(roi=(739,8,100,39), area=(739,8,100,39), mode="Digit", method="Default", keyword="", name="mall_resource_4")
	# 左数第二个 
	O_MALL_RESOURCE_5 = RuleOcr(roi=(935,11,100,37), area=(935,11,100,37), mode="Digit", method="Default", keyword="", name="mall_resource_5")
	# 左数第二个 
	O_MALL_RESOURCE_6 = RuleOcr(roi=(1129,6,100,41), area=(1129,6,100,41), mode="Digit", method="Default", keyword="", name="mall_resource_6")


	# Click Rule Assets
	# 一号位 
	C_SCA_DEMON_1 = RuleClick(roi_front=(255,158,100,100), roi_back=(255,158,100,100), name="sca_demon_1")
	# 二号位 
	C_SCA_DEMON_2 = RuleClick(roi_front=(181,318,100,100), roi_back=(181,318,100,100), name="sca_demon_2")
	# 三号位 
	C_SCA_DEMON_3 = RuleClick(roi_front=(257,476,100,100), roi_back=(257,476,100,100), name="sca_demon_3")
	# 四号位 
	C_SCA_DEMON_4 = RuleClick(roi_front=(553,478,100,100), roi_back=(553,478,100,100), name="sca_demon_4")
	# 五号位 
	C_SCA_DEMON_5 = RuleClick(roi_front=(639,316,100,100), roi_back=(639,316,100,100), name="sca_demon_5")
	# 六号位 
	C_SCA_DEMON_6 = RuleClick(roi_front=(560,155,100,100), roi_back=(560,155,100,100), name="sca_demon_6")
	# 点击魂外部 
	C_SCA_SOULS_GET = RuleClick(roi_front=(116,70,952,100), roi_back=(116,70,952,100), name="sca_souls_get")
	# 点击外部的区域返回到御魂礼盒主界面 
	C_SCA_SOULS_BACK = RuleClick(roi_front=(118,14,503,51), roi_back=(118,14,503,51), name="sca_souls_back")


	# Image Rule Assets
	# 蛇皮 
	I_SCA_OROCHI_SCALES = RuleImage(roi_front=(110,261,100,100), roi_back=(110,261,100,100), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/scales/scales_sca_orochi_scales.png")
	# 首领御魂 
	I_SCA_DEMON_SOULS = RuleImage(roi_front=(707,260,100,100), roi_back=(707,260,100,100), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/scales/scales_sca_demon_souls.png")
	# 永生之海 
	I_SCA_PICTURE_BOOK = RuleImage(roi_front=(995,258,100,100), roi_back=(995,258,100,100), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/scales/scales_sca_picture_book.png")
	# 土蜘蛛 
	I_SCA_DEMON_BOSS_1 = RuleImage(roi_front=(246,224,112,126), roi_back=(168,142,346,290), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/scales/scales_sca_demon_boss_1.png")
	# 胧车 
	I_SCA_DEMON_BOSS_2 = RuleImage(roi_front=(457,203,123,153), roi_back=(413,136,273,250), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/scales/scales_sca_demon_boss_2.png")
	# 荒骷髅 
	I_SCA_DEMON_BOSS_3 = RuleImage(roi_front=(686,239,131,121), roi_back=(631,132,344,273), threshold=0.6, method="Template matching", file="./tasks/RichMan/mall/scales/scales_sca_demon_boss_3.png")
	# 地震鲶 
	I_SCA_DEMON_BOSS_4 = RuleImage(roi_front=(912,188,141,169), roi_back=(804,121,315,292), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/scales/scales_sca_demon_boss_4.png")
	# 蜃气楼 
	I_SCA_DEMON_BOSS_5 = RuleImage(roi_front=(345,469,136,160), roi_back=(241,414,504,242), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/scales/scales_sca_demon_boss_5.png")
	# 歌姬 
	I_SCA_DEMON_BOSS_6 = RuleImage(roi_front=(561,480,141,141), roi_back=(437,402,555,236), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/scales/scales_sca_demon_boss_6.png")
	# 永生之海第一个选择 
	I_SCA_SELECT_1 = RuleImage(roi_front=(189,519,113,51), roi_back=(189,519,113,51), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/scales/scales_sca_select_1.png")
	# description 
	I_SCA_SELECT_2 = RuleImage(roi_front=(583,519,116,54), roi_back=(583,519,116,54), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/scales/scales_sca_select_2.png")
	# description 
	I_SCA_SELECT_3 = RuleImage(roi_front=(972,517,123,50), roi_back=(972,517,123,50), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/scales/scales_sca_select_3.png")
	# 获得的六星 
	I_SCA_SIX_STAR = RuleImage(roi_front=(119,261,100,22), roi_back=(108,246,261,57), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/scales/scales_sca_six_star.png")
	# 点击屏幕继续 
	I_SCA_REWARD = RuleImage(roi_front=(584,503,100,100), roi_back=(584,503,100,100), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/scales/scales_sca_reward.png")
	# 点击兑换 
	I_SCA_DEMON_BUY = RuleImage(roi_front=(861,572,180,62), roi_back=(861,572,180,62), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/scales/scales_sca_demon_buy.png")
	# 夜荒魂 
	I_SCA_DEMON_BOSS_7 = RuleImage(roi_front=(819,489,100,100), roi_back=(640,423,412,222), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/scales/scales_sca_demon_boss_7.png")


	# Ocr Rule Assets
	# 蛇皮剩余可买的 
	O_SCA_NUMBER_OROCHI = RuleOcr(roi=(46,318,27,25), area=(46,318,27,25), mode="Digit", method="Default", keyword="", name="sca_number_orochi")
	# 首领御魂剩余可买的 
	O_SCA_NUMBER_DEMON = RuleOcr(roi=(627,319,30,25), area=(627,319,30,25), mode="Digit", method="Default", keyword="", name="sca_number_demon")
	# 永生之海 
	O_SCA_NUMBER_SEA = RuleOcr(roi=(926,321,30,23), area=(926,321,30,23), mode="Digit", method="Default", keyword="", name="sca_number_sea")
	# 多少号位 
	O_SCA_DEMON_POSTION = RuleOcr(roi=(960,244,88,41), area=(960,244,88,41), mode="Single", method="Default", keyword="", name="sca_demon_postion")
	# 朴素的御魂 
	O_SCA_RES_OROCHI = RuleOcr(roi=(531,9,127,37), area=(531,9,127,37), mode="DigitCounter", method="Default", keyword="", name="sca_res_orochi")
	# 首领御魂数量 
	O_SCA_RES_DEMON = RuleOcr(roi=(949,10,86,35), area=(949,10,86,35), mode="Digit", method="Default", keyword="", name="sca_res_demon")
	# 永生之海 
	O_SCA_RES_SEA = RuleOcr(roi=(1152,11,80,38), area=(1152,11,80,38), mode="Digit", method="Default", keyword="", name="sca_res_sea")


	# Image Rule Assets
	# 购买御灵 
	I_SP_BUY_TOTEM = RuleImage(roi_front=(398,299,148,113), roi_back=(160,121,880,487), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/special/special_sp_buy_totem.png")
	# 购买中级盘 
	I_SP_BUY_MEDIUM = RuleImage(roi_front=(392,150,150,108), roi_back=(144,113,908,501), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/special/special_sp_buy_medium.png")
	# 购买低级盘 
	I_SP_BUY_LOW = RuleImage(roi_front=(176,148,144,108), roi_back=(128,142,902,449), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/special/special_sp_buy_low.png")
	# 判断是否滑动到底 
	I_SP_SWIPE_CHECK = RuleImage(roi_front=(900,164,42,61), roi_back=(173,144,840,379), threshold=0.8, method="Template matching", file="./tasks/RichMan/mall/special/special_sp_swipe_check.png")


	# Ocr Rule Assets
	# 本周剩余数量xx 
	O_SP_RES_NUMBER = RuleOcr(roi=(376,183,192,40), area=(376,183,192,40), mode="Single", method="Default", keyword="", name="sp_res_number")


	# Swipe Rule Assets
	# 向下滑动 
	S_SP_DOWN = RuleSwipe(roi_front=(249,419,486,22), roi_back=(339,300,301,22), mode="default", name="sp_down")


	# Click Rule Assets
	# description 
	C_C_SHRINE = RuleClick(roi_front=(1098,261,56,100), roi_back=(1098,261,56,100), name="c_shrine")


	# Image Rule Assets
	# 下期预览 
	I_S_NEXT_PERIOD = RuleImage(roi_front=(1083,574,90,86), roi_back=(1083,574,90,86), threshold=0.8, method="Template matching", file="./tasks/RichMan/shrine/shrine_s_next_period.png")
	# description 
	I_S_WHITE_FIVE = RuleImage(roi_front=(769,143,77,85), roi_back=(769,143,77,85), threshold=0.85, method="Template matching", file="./tasks/RichMan/shrine/shrine_s_white_five.png")
	# description 
	I_S_WHITE_FOUR = RuleImage(roi_front=(951,144,73,82), roi_back=(951,144,73,82), threshold=0.85, method="Template matching", file="./tasks/RichMan/shrine/shrine_s_white_four.png")
	# 黑蛋 
	I_S_BLACK = RuleImage(roi_front=(588,143,78,83), roi_back=(588,143,78,83), threshold=0.9, method="Template matching", file="./tasks/RichMan/shrine/shrine_s_black.png")
	# description 
	I_S_BUY_BLACK = RuleImage(roi_front=(777,508,173,60), roi_back=(777,508,173,60), threshold=0.8, method="Template matching", file="./tasks/RichMan/shrine/shrine_s_buy_black.png")
	# description 
	I_S_BUY_WHITE_FIVE = RuleImage(roi_front=(778,512,177,56), roi_back=(778,512,177,56), threshold=0.8, method="Template matching", file="./tasks/RichMan/shrine/shrine_s_buy_white_five.png")
	# description 
	I_S_BUY_WHITE_FOUR = RuleImage(roi_front=(779,507,173,64), roi_back=(779,507,173,64), threshold=0.8, method="Template matching", file="./tasks/RichMan/shrine/shrine_s_buy_white_four.png")
	# description 
	I_S_CONFIRM_WHITE_FIVE = RuleImage(roi_front=(554,522,174,61), roi_back=(520,416,220,193), threshold=0.8, method="Template matching", file="./tasks/RichMan/shrine/shrine_s_confirm_white_five.png")
	# description 
	I_S_CONFIRM_WHITE_FOUR = RuleImage(roi_front=(548,486,176,62), roi_back=(509,404,252,231), threshold=0.8, method="Template matching", file="./tasks/RichMan/shrine/shrine_s_confirm_white_four.png")
	# description 
	I_S_CONFIRM_BLACK = RuleImage(roi_front=(547,496,180,62), roi_back=(532,426,214,184), threshold=0.8, method="Template matching", file="./tasks/RichMan/shrine/shrine_s_confirm_black.png")
	# description 
	I_S_BUY_UP = RuleImage(roi_front=(762,412,56,54), roi_back=(762,412,56,54), threshold=0.8, method="Template matching", file="./tasks/RichMan/shrine/shrine_s_buy_up.png")
	# description 
	I_S_CHECK_BLACK = RuleImage(roi_front=(811,225,108,178), roi_back=(811,225,108,178), threshold=0.8, method="Template matching", file="./tasks/RichMan/shrine/shrine_s_check_black.png")
	# description 
	I_S_CHECK_WHITE_FIVE = RuleImage(roi_front=(810,222,109,182), roi_back=(810,222,109,182), threshold=0.8, method="Template matching", file="./tasks/RichMan/shrine/shrine_s_check_white_five.png")
	# description 
	I_S_CHECK_WHITE_FOUR = RuleImage(roi_front=(808,222,113,181), roi_back=(808,222,113,181), threshold=0.8, method="Template matching", file="./tasks/RichMan/shrine/shrine_s_check_white_four.png")
	# description 
	I_CENTER1 = RuleImage(roi_front=(1101,621,48,51), roi_back=(1072,596,100,100), threshold=0.8, method="Template matching", file="./tasks/RichMan/shrine/shrine_center1.png")
	# description 
	I_CENTER2 = RuleImage(roi_front=(76,590,79,75), roi_back=(65,575,100,100), threshold=0.8, method="Template matching", file="./tasks/RichMan/shrine/shrine_center2.png")


	# Ocr Rule Assets
	# Ocr-description 
	O_S_TOTAL = RuleOcr(roi=(1134,11,112,36), area=(1134,11,112,36), mode="Digit", method="Default", keyword="", name="s_total")
	# 已兑换 
	O_S_BLACK = RuleOcr(roi=(582,179,84,48), area=(582,179,84,48), mode="Single", method="Default", keyword="", name="s_black")
	# Ocr-description 
	O_S_WHITE_FIVE = RuleOcr(roi=(774,174,69,44), area=(774,174,69,44), mode="Single", method="Default", keyword="", name="s_white_five")
	# Ocr-description 
	O_S_WHITE_FOUR = RuleOcr(roi=(952,168,74,60), area=(952,168,74,60), mode="Single", method="Default", keyword="", name="s_white_four")
	# 买两个四星蛋 
	O_S_FOUR_NUMBER = RuleOcr(roi=(581,414,46,45), area=(581,414,46,45), mode="Digit", method="Default", keyword="2", name="s_four_number")


	# Image Rule Assets
	# 千物宝库 
	I_TT_ENTER = RuleImage(roi_front=(1140,585,73,76), roi_back=(1140,585,73,76), threshold=0.8, method="Template matching", file="./tasks/RichMan/tt/tt_tt_enter.png")
	# 确认进入 
	I_TT_CHECK = RuleImage(roi_front=(141,61,228,67), roi_back=(141,61,228,67), threshold=0.8, method="Template matching", file="./tasks/RichMan/tt/tt_tt_check.png")
	# description 
	I_TT_BLACK = RuleImage(roi_front=(710,176,91,90), roi_back=(453,171,589,109), threshold=0.8, method="Template matching", file="./tasks/RichMan/tt/tt_tt_black.png")
	# description 
	I_TT_TICKET_BULE = RuleImage(roi_front=(484,176,85,91), roi_back=(475,170,562,110), threshold=0.8, method="Template matching", file="./tasks/RichMan/tt/tt_tt_ticket_bule.png")
	# description 
	I_TT_AP = RuleImage(roi_front=(938,177,88,87), roi_back=(467,167,581,123), threshold=0.8, method="Template matching", file="./tasks/RichMan/tt/tt_tt_ap.png")
	# 提高 
	I_TT_BUY_UP = RuleImage(roi_front=(755,427,59,57), roi_back=(740,386,80,146), threshold=0.8, method="Template matching", file="./tasks/RichMan/tt/tt_tt_buy_up.png")
	# description 
	I_TT_BUY_CONFIRM = RuleImage(roi_front=(584,512,53,53), roi_back=(553,487,169,115), threshold=0.8, method="Template matching", file="./tasks/RichMan/tt/tt_tt_buy_confirm.png")


	# Ocr Rule Assets
	# Ocr-description 
	O_TT_TOTOL = RuleOcr(roi=(1121,10,116,35), area=(1121,10,116,35), mode="Digit", method="Default", keyword="", name="tt_totol")
	# Ocr-description 
	O_TT_BLUE_TICKET = RuleOcr(roi=(509,307,531,92), area=(509,307,531,92), mode="Full", method="Default", keyword="2000", name="tt_blue_ticket")
	# Ocr-description 
	O_TT_BLACK = RuleOcr(roi=(498,313,528,89), area=(498,313,528,89), mode="Full", method="Default", keyword="350", name="tt_black")
	# Ocr-description 
	O_TT_AP = RuleOcr(roi=(502,311,535,91), area=(502,311,535,91), mode="Full", method="Default", keyword="300", name="tt_ap")
	# Ocr-description 
	O_TT_BUY = RuleOcr(roi=(602,509,104,61), area=(602,509,104,61), mode="Full", method="Default", keyword="", name="tt_buy")
	# Ocr-description 
	O_TT_NUMBER = RuleOcr(roi=(576,415,58,49), area=(576,415,58,49), mode="Digit", method="Default", keyword="", name="tt_number")


