# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey

class ConfigManual:
    """
    module.device
    """

    SCHEDULER_PRIORITY = """
        Restart > BackUp > CourtyardAffairs
        > KekkaiUtilize > KekkaiActivation > MemoryScrolls
        > WantedQuests > DemonEncounter > SoulsTidy 
        > AreaBoss > GoldYoukai > ExperienceYoukai > Nian > NianTrue > Tako > RealmRaid > DailyTrifles > Exploration
        > Dokan > AbyssShadows > DemonRetreat > GuildBanquet > Hunt
        > Pets > EternitySea > Orochi > FallenSun > BondlingFairyland > EvoZone 
        > RyouToppa
        > ActivityCommon > ActivityCommon2 > ActivityShikigami 
        > GoryouRealm > HeroTest
        > TrueOrochi > RichMan > Secret > WeeklyTrifles > SixRealms > Sougenbi 
        > CollectiveMissions
        > Delegation > Hyakkiyakou
        > MysteryShop > Duel > MetaDemon > FrogBoss > FloatParade > Quiz > KittyShop > AutoCake
        > TalismanPass > MainStory > LBS
        > SwitchAccountLoop
        > SwitchAccountOnce
        """

    DEVICE_OVER_HTTP = False
    FORWARD_PORT_RANGE = (20000, 21000)
    REVERSE_SERVER_PORT = 7903

    # ASCREENCAP_FILEPATH_LOCAL = './bin/ascreencap'
    # ASCREENCAP_FILEPATH_REMOTE = '/data/local/tmp/ascreencap'

    # 'DroidCast', 'DroidCast_raw'
    DROIDCAST_VERSION = 'DroidCast'
    DROIDCAST_FILEPATH_LOCAL = './bin/droidcast/DroidCast_raw-release-1.0.apk'
    DROIDCAST_FILEPATH_REMOTE = '/data/local/tmp/DroidCast_raw.apk'

    MINITOUCH_FILEPATH_REMOTE = '/data/local/tmp/minitouch'

    HERMIT_FILEPATH_LOCAL = './bin/hermit/hermit.apk'
