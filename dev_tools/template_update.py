# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey

from module.config.config_model import ConfigModel
from pathlib import Path

if __name__ == "__main__":
    # ConfigModel对象并更新保存
    config = ConfigModel()
    config_path = Path("./config/template.json")
    config.write_json("template", config.dict())
