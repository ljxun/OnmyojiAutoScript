# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
import time

import cv2
from cached_property import cached_property
from datetime import datetime
from module.base.timer import Timer
from pathlib import Path
from tasks.Exploration.version import highlight
from tasks.Script.config_device import ScreenshotMethod
from tasks.base_task import BaseTask


class GetAnimation(BaseTask):

    @cached_property
    def save_folder(self) -> Path:
        save_time = datetime.now().strftime('%Y%m%dT%H%M%S')
        save_folder = Path(f'./log/temp/{save_time}')
        save_folder.mkdir(parents=True, exist_ok=True)
        return save_folder

    def run_screenshot(self):
        self.config.model.script.device.screenshot_method = ScreenshotMethod.WINDOW_BACKGROUND
        run_timer = Timer(3)
        sho_timer = Timer(0.1)
        run_timer.start()
        sho_timer.start()
        save_images = {}
        while 1:
            if run_timer.reached():
                break
            if sho_timer.reached():
                sho_timer.reset()
                image = self.device.screenshot_window_background()
                # image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                image = highlight(image)
                time_now1 = int(time.time() * 1000)
                save_images[time_now1] = image
        for time_now, image in save_images.items():
            cv2.imwrite(str(self.save_folder / f'all{time_now}.png'), image)
