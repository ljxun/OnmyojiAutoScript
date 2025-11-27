# base_atom.py
import numpy as np


class BaseAtom:
    def __init__(self):
        self.roi_front = [0, 0, 0, 0]  # 默认值

    # def coord(self) -> tuple:
    #     """
    #     获取坐标, 从roi_front使用正态分布获取坐标
    #     :return:
    #     """
    #     x, y, w, h = self.roi_front
    #     # 使用正态分布生成坐标，均值为中心点
    #     # 这样可以确保大约99.7%的点落在区域内
    #     center_x = x + w // 2
    #     center_y = y + h // 2
    #     # 标准差 σ（控制分布范围，通常取 ROI 宽度/高度的 1/4 ~ 1/2）
    #     sigma_x = w / 4  # 可调整，比如 w/3, w/2
    #     sigma_y = h / 4  # 可调整，比如 h/3, h/2
    #
    #     # 生成正态分布的随机坐标（但限制在 ROI 范围内）
    #     while True:
    #         # 生成正态分布的 x 和 y（均值=中心点，标准差=σ）
    #         rand_x = int(np.random.normal(center_x, sigma_x))
    #         rand_y = int(np.random.normal(center_y, sigma_y))
    #
    #         # 确保坐标在 ROI 范围内 [x, x+w] × [y, y+h]
    #         if x <= rand_x <= x + w and y <= rand_y <= y + h:
    #             return rand_x, rand_y

    def coord_center(self) -> tuple:
        x, y, w, h = self.roi_front
        return int(x + w // 2), int(y + h // 2)

    def coord(self) -> tuple:
        """
        获取总区域中心1/2区域内的正态分布坐标
        :return: 坐标元组 (x, y)
        """
        x, y, w, h = self.roi_front
        # 计算1/2区域的尺寸
        tenth_w = w // 2
        tenth_h = h // 2
        # 计算1/2区域的左上角坐标（位于整个ROI中心）
        tenth_x = x + (w - tenth_w) // 2
        tenth_y = y + (h - tenth_h) // 2
        # 计算1/2区域的中心点
        center_x = tenth_x + tenth_w // 2
        center_y = tenth_y + tenth_h // 2
        # 设置标准差为1/2区域的1/4
        sigma_x = tenth_w / 4
        sigma_y = tenth_h / 4

        # 生成正态分布的随机坐标（限制在1/2区域内）
        while True:
            rand_x = int(np.random.normal(center_x, sigma_x))
            rand_y = int(np.random.normal(center_y, sigma_y))

            # 确保坐标在1/2区域内
            if tenth_x <= rand_x <= tenth_x + tenth_w and tenth_y <= rand_y <= tenth_y + tenth_h:
                return rand_x, rand_y

