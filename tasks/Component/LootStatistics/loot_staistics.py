# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey

from tasks.base_task import BaseTask


class LootStatistics(BaseTask):

    def loot_detect(self, image) -> dict:
        """

        :param image:
        :return: 返回举例
        {
        "RealmRaidPass": 1,
        }
        """
        return {}


