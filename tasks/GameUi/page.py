import traceback
from tasks.DailyTrifles.assets import DailyTriflesAssets
from tasks.GameUi.assets import GameUiAssets as G
from tasks.KekkaiUtilize.assets import KekkaiUtilizeAssets
from tasks.Restart.assets import RestartAssets
from tasks.RyouToppa.assets import RyouToppaAssets


class PageRegistry:
    _registry = set()

    @classmethod
    def register(cls, page):
        """注册指定页面"""
        cls._registry.add(page)

    @classmethod
    def all(cls):
        return list(cls._registry)


class Page:
    def __init__(self, check_button, links=None):
        if links is None:
            links = {}
        self.check_button = check_button
        self.links = links
        self.additional: list = None  # 附加按钮或者是ocr检测按钮
        (filename, line_number, function_name, text) = traceback.extract_stack()[-2]
        self.name = text[:text.find('=')].strip()
        PageRegistry.register(self)

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return self.name

    def link(self, button, destination):
        self.links[destination] = button


# 登录login
page_login = Page(G.I_CHECK_LOGIN_FORM)
# Main Home 主页
page_main = Page(G.I_CHECK_MAIN)
page_login.link(button=RestartAssets.O_LOGIN_ENTER_GAME, destination=page_main)
page_main.additional = [G.I_AD_CLOSE_RED, G.I_BACK_FRIENDS, RestartAssets.I_LOGIN_SCROOLL_CLOSE]
# 召唤summon
page_summon = Page(G.I_CHECK_SUMMON)
page_summon.link(button=G.I_SUMMON_GOTO_MAIN, destination=page_main)
page_main.link(button=G.I_MAIN_GOTO_SUMMON, destination=page_summon)
# 探索exploration
page_exploration = Page(G.I_EXPLORATION_GOTO_AWAKE_ZONE)
page_exploration.link(button=G.I_BACK_YELLOW, destination=page_main)
page_main.link(button=G.I_MAIN_GOTO_EXPLORATION, destination=page_exploration)
# 町中town
page_town = Page(G.I_CHECK_TOWN)
page_town.link(button=G.I_TOWN_GOTO_MAIN, destination=page_main)
page_main.link(button=G.I_MAIN_GOTO_TOWN, destination=page_town)

# ************************************* 探索部分 *****************************************#
# 觉醒 awake zones
page_awake_zones = Page(G.I_CHECK_AWAKE)
page_awake_zones.link(button=G.I_BACK_YELLOW, destination=page_exploration)
page_exploration.link(button=G.I_EXPLORATION_GOTO_AWAKE_ZONE, destination=page_awake_zones)
# 御魂 soul zones
page_soul_zones = Page(G.I_CHECK_SOUL_ZONES)
page_soul_zones.link(button=G.I_BACK_YELLOW, destination=page_exploration)
page_exploration.link(button=G.I_EXPLORATION_GOTO_SOUL_ZONE, destination=page_soul_zones)
# 结界突破 realm raid
page_realm_raid = Page(G.I_CHECK_REALM_RAID)
page_realm_raid.link(button=G.I_REALM_RAID_GOTO_EXPLORATION, destination=page_exploration)
page_exploration.link(button=G.I_EXPLORATION_GOTO_REALM_RAID, destination=page_realm_raid)
# 寮突破 击破奖励
page_kekkai_toppa = Page(RyouToppaAssets.I_RYOU_REWARD)
page_kekkai_toppa.link(button=G.I_REALM_RAID_GOTO_EXPLORATION, destination=page_exploration)
page_realm_raid.link(button=RyouToppaAssets.I_RYOU_TOPPA, destination=page_kekkai_toppa)
page_kekkai_toppa.link(button=G.I_RYOUTOPPA_GOTO_REALMRAID, destination=page_realm_raid)
# 御灵 goryou realm
page_goryou_realm = Page(G.I_CHECK_GORYOU)
page_goryou_realm.link(button=G.I_BACK_YELLOW, destination=page_exploration)
page_exploration.link(button=G.I_EXPLORATION_GOTO_GORYOU_REALM, destination=page_goryou_realm)
# 委派 delegation
page_delegation = Page(G.I_CHECK_DELEGATION)
page_delegation.link(button=G.I_BACK_YELLOW, destination=page_exploration)
page_exploration.link(button=G.I_EXPLORATION_GOTO_DELEGATION, destination=page_delegation)
# 秘闻副本 SECRET zones
page_secret_zones = Page(G.I_CHECK_SECRET_ZONES)
page_secret_zones.link(button=G.I_BACK_YELLOW, destination=page_exploration)
page_exploration.link(button=G.I_EXPLORATION_GOTO_SECRET_ZONES, destination=page_secret_zones)
# 地域鬼王 area boss
page_area_boss = Page(G.I_CHECK_AREA_BOSS)
page_area_boss.link(button=G.I_BACK_YELLOW, destination=page_exploration)
page_exploration.link(button=G.I_EXPLORATION_GOTO_AREA_BOSS, destination=page_area_boss)
# 平安奇谭 heian kitan
page_heian_kitan = Page(G.I_CHECK_HEIAN_KITAN)
page_heian_kitan.link(button=G.I_CHECK_HEIAN_KITAN, destination=page_exploration)
page_exploration.link(button=G.I_EXPLORATION_GOTO_HEIAN_KITAN, destination=page_heian_kitan)
# 六道之门 six gates
page_six_gates = Page(G.I_CHECK_SIX_GATES)
page_six_gates.link(button=G.I_SIX_GATES_GOTO_EXPLORATION, destination=page_exploration)
page_exploration.link(button=G.I_EXPLORATION_GOTO_SIX_GATES, destination=page_six_gates)
# 契灵之境 bondling fairyland
page_bondling_fairyland = Page(G.I_CHECK_BONDLING_FAIRYLAND)
page_bondling_fairyland.link(button=G.I_BACK_YELLOW, destination=page_exploration)
page_exploration.link(button=G.I_EXPLORATION_GOTO_BONDLING_FAIRYLAND, destination=page_bondling_fairyland)

# ************************************* 町中部分 *****************************************#
# 斗技 duel
page_duel = Page(G.I_CHECK_DUEL)
page_duel.link(button=G.I_BACK_YELLOW, destination=page_town)
page_town.link(button=G.I_TOWN_GOTO_DUEL, destination=page_duel)
# 逢魔之时 demon_encounter
page_demon_encounter = Page(G.I_CHECK_DEMON_ENCOUNTER)
page_demon_encounter.link(button=G.I_BACK_YELLOW, destination=page_town)
page_town.link(button=G.I_TOWN_GOTO_DEMON_ENCOUNTER, destination=page_demon_encounter)
# 麒麟 kirin
page_kirin = Page(G.I_CHECK_KIRIN)
page_kirin.link(button=G.I_BACK_YELLOW, destination=page_town)
page_town.link(button=G.I_TOWN_GOTO_HUNT, destination=page_kirin)
# 阴界之门 netherworld
page_netherworld = Page(G.I_CHECK_NETHERWORLD)
page_netherworld.link(button=G.I_BACK_YELLOW, destination=page_town)
page_town.link(button=G.I_TOWN_GOTO_HUNT, destination=page_netherworld)
# 协同斗技 draft_duel
page_draft_duel = Page(G.I_CHECK_DRAFT_DUEL)
page_draft_duel.link(button=G.I_BACK_YELLOW, destination=page_town)
page_town.link(button=G.I_TOWN_GOTO_DRAFT_DUEL, destination=page_draft_duel)
# 百鬼弈 hyakkisen
page_hyakkisen = Page(G.I_CHECK_HYAKKISEN)
page_hyakkisen.link(button=G.I_BACK_YELLOW, destination=page_town)
page_town.link(button=G.I_TOWN_GOTO_HYAKKISEN, destination=page_hyakkisen)
# 百鬼夜行
page_hyakkiyakou = Page(G.I_CHECK_KYAKKIYAKOU)
page_hyakkiyakou.link(button=G.I_HYAKKIYAKOU_CLOSE, destination=page_town)
page_town.link(button=G.I_TOWN_GOTO_HYAKKIYAKOU, destination=page_hyakkiyakou)

# ************************************* 庭院部分 *****************************************#
# 式神录 shikigami_records
page_shikigami_records = Page(G.I_CHECK_RECORDS)
page_shikigami_records.additional = [G.I_AD_DISAPPEAR, G.I_RECORDS_CLOSE]
page_shikigami_records.link(button=G.I_BACK_YELLOW, destination=page_main)
page_main.link(button=G.I_MAIN_GOTO_SHIKIGAMI_RECORDS, destination=page_shikigami_records)
# 阴阳术 onmyodo
page_onmyodo = Page(G.I_CHECK_ONMYODO)
page_onmyodo.link(button=G.I_BACK_YELLOW, destination=page_main)
page_main.link(button=G.I_MAIN_GOTO_ONMYODO, destination=page_onmyodo)
# 好友 friends
page_friends = Page(G.I_CHECK_FRIENDS)
page_friends.link(button=G.I_BACK_YELLOW, destination=page_main)
page_main.link(button=G.I_MAIN_GOTO_FRIENDS, destination=page_friends)
# 商店 mall
page_mall = Page(check_button=[G.I_CHECK_MALL, DailyTriflesAssets.I_ROOM_GIFT])
page_mall.additional = [G.I_AD_CLOSE_RED, G.I_BACK_YELLOW, G.I_DLC_CLOSE]
page_mall.link(button=G.I_BACK_YELLOW, destination=page_main)
page_main.link(button=G.I_MAIN_GOTO_MALL, destination=page_mall)
# 阴阳寮 guild
page_guild = Page(G.I_CHECK_GUILD)
page_guild.additional = [KekkaiUtilizeAssets.I_PLANT_TREE_CLOSE]
page_guild.link(button=G.I_BACK_YELLOW, destination=page_main)
page_main.link(button=G.I_MAIN_GOTO_GUILD, destination=page_guild)
# 结界
page_realm = Page(G.I_CHECK_REALM_SHIN)
page_realm.additional = [KekkaiUtilizeAssets.I_PLANT_TREE_CLOSE]
page_realm.link(button=G.I_BACK_YELLOW, destination=page_guild)
page_guild.link(button=G.I_CHECK_GUILD, destination=page_realm)
# 组队 team
page_team = Page(G.I_CHECK_TEAM)
page_team.link(button=G.I_BACK_YELLOW, destination=page_main)
page_main.link(button=G.I_MAIN_GOTO_TEAM, destination=page_team)
# 收集 collection
page_collection = Page(G.I_CHECK_COLLECTION)
page_collection.link(button=G.I_BACK_YELLOW, destination=page_main)
page_main.link(button=G.I_MAIN_GOTO_COLLECTION, destination=page_collection)
# 珍旅居
page_travel = Page(G.I_CHECK_TRAVEL)
page_travel.link(button=G.I_BACK_YELLOW, destination=page_main)
page_main.link(button=G.I_MAIN_GOTO_TRAVEL, destination=page_travel)

# 活动总览
page_all_active = Page(G.I_PAGE_ALL_ACTIVE)
page_all_active.link(button=G.I_BACK_YELLOW, destination=page_main)
page_main.link(button=G.I_PAGE_MAIN_GOTO_PAGE_ALL_ACTIVE, destination=page_all_active)
