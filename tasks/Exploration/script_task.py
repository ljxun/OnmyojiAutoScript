# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey

from tasks.Exploration.solo import ScriptTask as SoloScriptTask


class ScriptTask(SoloScriptTask):
    """ 探索 """
    pass


if __name__ == "__main__":
    from module.config.config import Config

    config = Config('oas1')
    t = ScriptTask(config)
    t.config.exploration.exploration_config.exploration_level = '第二十八章'
    t.run()

