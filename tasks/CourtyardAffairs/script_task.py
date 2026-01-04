# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
from module.exception import TaskEnd
from tasks.Component.CourtyardAffairs.courtyard_affairs import CourtyardAffairs


class ScriptTask(CourtyardAffairs):
    """ 庭院事务 """

    def run(self) -> None:
        self.courtyard_affairs()
        self.set_next_run()
        raise TaskEnd


if __name__ == "__main__":
    from module.config.config import Config

    c = Config("4399")
    t = ScriptTask(c)
    t.run()
