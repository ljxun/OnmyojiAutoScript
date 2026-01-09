# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
import cv2
import numpy as np

from numpy import float32, int32, uint8, fromfile
from pathlib import Path

from module.base.decorator import cached_property
from module.logger import logger
from module.base.utils import is_approx_rectangle
from module.atom.base_atom import BaseAtom


class RuleImage(BaseAtom):

    def __init__(self, roi_front: tuple, roi_back: tuple, method: str, threshold: float, file: str, path='') -> None:
        """
        初始化
        :param roi_front: 前置roi
        :param roi_back: 后置roi 用于匹配的区域
        :param method: 匹配方法 "Template matching"
        :param threshold: 阈值  0.8
        :param file: 相对路径, 带后缀
        """
        super().__init__()
        self._match_init = False  # 这个是给后面的 等待图片稳定
        self._image = None  # 这个是匹配的目标
        self._kp = None  #
        self._des = None
        self.method = method

        self.roi_front: list = list(roi_front)
        self.roi_back = roi_back
        self.threshold = threshold
        self.file = file

    def __set_name__(self, owner, name):
        """自动记录变量名（当 RuleImage 实例作为类属性被定义时触发）"""
        self.variable_name = name  # 新增属性，存储变量名

    @cached_property
    def name(self) -> str:
        # return Path(self.file).stem.upper()
        """优先返回变量名，若未捕获则返回文件名"""
        return getattr(self, 'variable_name', Path(self.file).stem.upper())

    def __str__(self):
        return self.name

    __repr__ = __str__

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(self.name)

    def __bool__(self):
        return True

    def load_image(self) -> None:
        """
        加载图片
        :return:
        """
        if self._image is not None:
            return
        img = cv2.imdecode(fromfile(self.file, dtype=uint8), -1)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self._image = img

        height, width, channels = self._image.shape
        if height != self.roi_front[3] or width != self.roi_front[2]:
            self.roi_front[2] = width
            self.roi_front[3] = height
            # logger.info(f"roi_front size changed to {width}x{height}")

    def load_kp_des(self) -> None:
        if self._kp is not None and self._des is not None:
            return
        self._kp, self._des = self.sift.detectAndCompute(self.image, None)

    @property
    def image(self):
        """
        获取图片
        :return:
        """
        if self._image is None:
            self.load_image()
        return self._image

    @cached_property
    def is_template_match(self) -> bool:
        """
        是否是模板匹配
        :return:
        """
        return self.method == "Template matching"

    @cached_property
    def is_template_match_mask(self) -> bool:
        """
        是否是模板匹配
        :return:
        """
        return self.method == "Template matching mask"

    @cached_property
    def is_sift_flann(self) -> bool:
        return self.method == "Sift Flann"

    @cached_property
    def sift(self):
        return cv2.SIFT_create()

    @cached_property
    def kp(self):
        if self._kp is None:
            self.load_kp_des()
        return self._kp

    @cached_property
    def des(self):
        if self._des is None:
            self.load_kp_des()
        return self._des

    def corp(self, image: np.array, roi: list = None) -> np.array:
        """
        截取图片
        :param image:
        :param roi
        :return:
        """
        if roi is None:
            x, y, w, h = self.roi_back
            # 全方向扩展5像素，但不超过屏幕尺寸720x1280
            x = max(0, x - 5)               # 向左扩展5像素，但不能小于0
            y = max(0, y - 5)               # 向上扩展5像素，但不能小于0
            w = min(1280 - x, w + 10)       # 增加10像素宽度（左右各5像素）
            h = min(720 - y, h + 10)        # 增加10像素高度（上下各5像素）
        else:
            x, y, w, h = roi
        x, y, w, h = int(x), int(y), int(w), int(h)
        return image[y:y + h, x:x + w]

    def match(self, image: np.array, threshold: float = None) -> bool:
        """
        :param threshold:
        :param image:
        :return:
        """
        if threshold is None:
            threshold = self.threshold

        if not self.is_template_match:
            if self.is_template_match_mask:
                return self.match_mask(image, threshold)
            elif self.is_sift_flann:
                return self.sift_match(image)
            else:
                raise Exception(f"unknown method {self.method}")

        source = self.corp(image)
        mat = self.image
        res = cv2.matchTemplate(source, mat, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)  # 最小匹配度，最大匹配度，最小匹配度的坐标，最大匹配度的坐标
        # logger.attr(self.name, max_val)
        if max_val > threshold:
            self.update_roi(max_loc)
            # logger.attr(self.name, self.roi_front)
            return True
        else:
            return False

    def match_mask(self, image: np.array, threshold: float = 0.8, mask_path: str = None) -> bool:
        """
        使用蒙版进行图像匹配，只比较蒙版覆盖区域内的像素

        :param image: 输入图像(numpy array)
        :param threshold: 匹配阈值，默认为实例的阈值
        :param mask_path: 蒙版文件路径，如果为None则不使用蒙版
        :return: 匹配成功返回True，否则返回False
        """
        # 裁剪图像到指定区域
        source = self.corp(image)
        template = self.image
        # 如果提供了蒙版路径，则加载蒙版
        if not mask_path:
            mask_path = self.file.replace(".png", "_mask.png")
        try:
            # 使用imdecode支持中文路径
            mask = cv2.imdecode(fromfile(mask_path, dtype=uint8), cv2.IMREAD_GRAYSCALE)
        except Exception as e:
            logger.warning(f"无法加载蒙版 {mask_path}: {e}")
            mask = None

        # 执行模板匹配
        if mask is not None:
            res = cv2.matchTemplate(source, template, cv2.TM_CCOEFF_NORMED, mask=mask)
        else:
            res = cv2.matchTemplate(source, template, cv2.TM_CCOEFF_NORMED)

        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        # logger.attr(self.name, max_val)
        if not np.isfinite(max_val):
            # logger.warning(f"匹配结果无效 {self.name}: {max_val}")
            # 处理无效值情况
            return False
        # 根据阈值判断匹配结果
        if max_val > threshold:
            # 更新ROI坐标
            self.update_roi(max_loc)
            # logger.attr(self.name, self.roi_front)
            return True
        else:
            return False

    def match_test(self, image: np.array, threshold: float = None) -> bool:
        """
        :param threshold:
        :param image:
        :return:
        """
        if threshold is None:
            threshold = self.threshold

        if not self.is_template_match:
            if self.is_template_match_mask:
                return self.match_mask_test(image, threshold)
            elif self.is_sift_flann:
                return self.sift_match(image)
            else:
                raise Exception(f"unknown method {self.method}")

        source = self.corp(image)
        mat = self.image
        res = cv2.matchTemplate(source, mat, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)  # 最小匹配度，最大匹配度，最小匹配度的坐标，最大匹配度的坐标
        logger.attr(self.name, max_val)
        if max_val > threshold:
            self.update_roi(max_loc)
            logger.attr(self.name, self.roi_front)
            return True, max_val
        else:
            return False, max_val

    def match_mask_test(self, image: np.array, threshold: float = 0.8, mask_path: str = None) -> bool:
        """
        使用蒙版进行图像匹配，只比较蒙版覆盖区域内的像素

        :param image: 输入图像(numpy array)
        :param threshold: 匹配阈值，默认为实例的阈值
        :param mask_path: 蒙版文件路径，如果为None则不使用蒙版
        :return: 匹配成功返回True，否则返回False
        """
        # 裁剪图像到指定区域
        source = self.corp(image)
        template = self.image
        # 如果提供了蒙版路径，则加载蒙版
        if not mask_path:
            mask_path = self.file.replace(".png", "_mask.png")
        try:
            # 使用imdecode支持中文路径
            mask = cv2.imdecode(fromfile(mask_path, dtype=uint8), cv2.IMREAD_GRAYSCALE)
        except Exception as e:
            logger.warning(f"无法加载蒙版 {mask_path}: {e}")
            mask = None

        # 执行模板匹配
        if mask is not None:
            # cv2.imwrite("source_debug.png", cv2.cvtColor(source, cv2.COLOR_RGB2BGR))
            # cv2.imwrite("template_debug.png", cv2.cvtColor(template, cv2.COLOR_RGB2BGR))
            # cv2.imwrite("mask_debug.png", mask)
            res = cv2.matchTemplate(source, template, cv2.TM_CCOEFF_NORMED, mask=mask)
        else:
            res = cv2.matchTemplate(source, template, cv2.TM_CCOEFF_NORMED)

        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        logger.attr(self.name, max_val)
        if not np.isfinite(max_val):
            # logger.warning(f"匹配结果无效 {self.name}: {max_val}")
            # 处理无效值情况
            return False, max_val
        # 根据阈值判断匹配结果
        if max_val > threshold:
            # 更新ROI坐标
            self.update_roi(max_loc)
            logger.attr(self.name, self.roi_front)
            return True, max_val
        else:
            return False, max_val

    def update_roi(self, max_loc):
        # 更新ROI坐标
        self.roi_front[0] = max_loc[0] + max(0, self.roi_back[0] - 5)
        self.roi_front[1] = max_loc[1] + max(0, self.roi_back[1] - 5)

    def match_first(self, image: np.array, threshold: float = None) -> bool:
        """
        自上而下找第一个匹配结果
        :param threshold:
        :param image:
        :return:
        """
        if threshold is None:
            threshold = self.threshold

        if not self.is_template_match:
            return self.sift_match(image)
            # raise Exception(f"unknown method {self.method}")

        source = self.corp(image)
        mat = self.image
        res = cv2.matchTemplate(source, mat, cv2.TM_CCOEFF_NORMED)
        # 获取所有超过阈值的坐标
        loc = np.where(res >= threshold)
        if loc[0].size == 0:  # 无匹配
            return False

        # 直接取 y 最小的点（即最顶部）
        top_loc = loc[0]
        # 更新 ROI（根据需求调整）
        self.roi_front[0] = top_loc[0] + self.roi_back[0]
        self.roi_front[1] = top_loc[1] + self.roi_back[1]

        return True

    def match_gray(self, image: np.array, threshold: float = None) -> bool:
        """
        :param threshold: 匹配阈值，默认为实例的阈值
        :param image: 输入图像
        :return: 匹配成功返回True，否则返回False
        """
        if threshold is None:
            threshold = self.threshold

        if not self.is_template_match:
            return self.sift_match(image)

        # 裁剪图像到指定区域
        source = self.corp(image)
        template = self.image

        # 转换为灰度图像以去除颜色影响
        if source.ndim == 3:
            source = cv2.cvtColor(source, cv2.COLOR_BGR2GRAY)
        if template.ndim == 3:
            template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

        # 执行模板匹配
        res = cv2.matchTemplate(source, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        # logger.attr(self.name, max_val)
        # 根据阈值判断匹配结果
        if max_val > threshold:
            # 更新ROI坐标
            self.update_roi(max_loc)
            return True
        else:
            return False

    def match_all(self, image: np.array, threshold: float = None, roi: list = None) -> list[tuple]:
        """
        区别于match，这个是返回所有的匹配结果
        :param roi:
        :param image:
        :param threshold:
        :return:
        """
        if roi is not None:
            self.roi_back = roi
        if threshold is None:
            threshold = self.threshold
        if not self.is_template_match:
            raise Exception(f"unknown method {self.method}")
        source = self.corp(image)
        mat = self.image
        results = cv2.matchTemplate(source, mat, cv2.TM_CCOEFF_NORMED)
        locations = np.where(results >= threshold)
        matches = []
        for pt in zip(*locations[::-1]):  # (x, y) coordinates
            score = results[pt[1], pt[0]]
            # 得分, x, y, w, h
            x = self.roi_back[0] + pt[0]
            y = self.roi_back[1] + pt[1]
            matches.append((score, x, y, mat.shape[1], mat.shape[0]))
        return matches

    def match_all_any(self, image: np.array, threshold: float = None, roi: list = None, nms_threshold: float = 0.3) -> list[tuple]:
        """
        区别于match，这个是返回所有的匹配结果，去除冗余匹配项（例如：多个框选区域重叠的情况）时使用。
        :param roi:
        :param image:
        :param threshold:
        :return:
        """
        if roi is not None:
            self.roi_back = roi
        if threshold is None:
            threshold = self.threshold
        if not self.is_template_match:
            raise Exception(f"unknown method {self.method}")
        source = self.corp(image)
        mat = self.image
        results = cv2.matchTemplate(source, mat, cv2.TM_CCOEFF_NORMED)
        locations = np.where(results >= threshold)
        matches = []
        for pt in zip(*locations[::-1]):  # (x, y) coordinates
            score = results[pt[1], pt[0]]
            # 得分, x, y, w, h
            x = self.roi_back[0] + pt[0]
            y = self.roi_back[1] + pt[1]
            matches.append((score, x, y, mat.shape[1], mat.shape[0]))
        if len(matches) > 0:
            scores = np.array([m[0] for m in matches])
            boxes = np.array([[m[1], m[2], m[3], m[4]] for m in matches])
            # 使用OpenCV的NMSBoxes
            indices = cv2.dnn.NMSBoxes(boxes.tolist(), scores.tolist(), score_threshold=threshold, nms_threshold=nms_threshold)
            filtered_matches = [matches[i] for i in indices]
            return filtered_matches
        return matches

    def coord_roi_back(self) -> tuple:
        """
         获取roi_back的随机的点击的坐标
        :return:
        """
        return self.coord_list(self.roi_back)

    def front_center(self) -> tuple:
        """
        获取roi_front的中心坐标
        :return:
        """
        x, y, w, h = self.roi_front
        return int(x + w // 2), int(y + h // 2)

    def test_match(self, image: np.array):
        if self.is_template_match:
            return self.match(image)
        if self.is_sift_flann:
            return self.sift_match(image, show=True)

    def sift_match(self, image: np.array, show=False) -> bool:
        """
        特征匹配，同样会修改 roi_front
        :param image: 是游戏的截图，就是转通道后的截图
        :param show: 测试用的
        :return:
        """
        source = self.corp(image)
        kp, des = self.sift.detectAndCompute(source, None)
        # 参数1：index_params
        #    对于SIFT和SURF，可以传入参数index_params=dict(algorithm=FLANN_INDEX_KDTREE, trees=5)。
        #    对于ORB，可以传入参数index_params=dict(algorithm=FLANN_INDEX_LSH, table_number=6, key_size=12）。
        index_params = dict(algorithm=1, trees=5)
        # 参数2：search_params 指定递归遍历的次数，值越高结果越准确，但是消耗的时间也越多。
        search_params = dict(checks=50)
        # 根据设置的参数创建特征匹配器 指定匹配的算法和kd树的层数,指定返回的个数
        flann = cv2.FlannBasedMatcher(index_params, search_params)
        # 利用创建好的特征匹配器利用k近邻算法来用模板的特征描述符去匹配图像的特征描述符，k指的是返回前k个最匹配的特征区域
        # 返回的是最匹配的两个特征点的信息，返回的类型是一个列表，列表元素的类型是Dmatch数据类型，具体是什么我也不知道
        # 第一个参数是小图的des, 第二个参数是大图的des
        matches = flann.knnMatch(self.des, des, k=2)

        good = []
        result = True
        for i, (m, n) in enumerate(matches):
            # 设定阈值, 距离小于对方的距离的0.7倍我们认为是好的匹配点.
            if m.distance < 0.6 * n.distance:
                good.append(m)
        if len(good) >= 10:
            src_pts = float32([self.kp[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
            dst_pts = float32([kp[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

            # 计算透视变换矩阵m， 要求点的数量>=4
            m, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
            # 创建一个包含模板图像四个角坐标的数组
            w, h = self.roi_front[2], self.roi_front[3]
            pts = float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
            if m is None:
                result = False
            else:
                dst = int32(cv2.perspectiveTransform(pts, m))
                self.roi_front[0] = dst[0, 0, 0] + self.roi_back[0]
                self.roi_front[1] = dst[0, 0, 1] + self.roi_back[1]
                if show:
                    cv2.polylines(source, [dst], isClosed=True, color=(0, 0, 255), thickness=2)
                if not is_approx_rectangle(np.array([pos[0] for pos in dst])):
                    result = False
        else:
            result = False

        # https://blog.csdn.net/cungudafa/article/details/105399278
        # https://blog.csdn.net/qq_45832961/article/details/122776322
        if show:
            # 准备一个空的掩膜来绘制好的匹配
            mask_matches = [[0, 0] for i in range(len(matches))]
            # 向掩膜中添加数据
            for i, (m, n) in enumerate(matches):
                if m.distance < 0.6 * n.distance:  # 理论上0.7最好
                    mask_matches[i] = [1, 0]
            img_matches = cv2.drawMatchesKnn(self.image, self.kp, source, kp, matches, None,
                                             matchColor=(0, 255, 0), singlePointColor=(255, 0, 0),
                                             matchesMask=mask_matches, flags=0)
            cv2.imshow(f'Sift Flann: {self.name}', img_matches)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        return result

    def match_mean_color(self, image, color: tuple, bias=10) -> bool:
        """

        :param image:
        :param color:  rgb
        :param bias:
        :return:
        """
        image = self.corp(image)
        average_color = cv2.mean(image)
        # logger.info(f'{self.name} average_color: {average_color}')
        for i in range(3):
            if abs(average_color[i] - color[i]) > bias:
                return False
        return True


if __name__ == "__main__":

    from tasks.KekkaiUtilize.assets import KekkaiUtilizeAssets

    IMAGE_FILE = r"D:\MuMu12\共享文件夹\Screenshots\MuMu12-20250404-231231.png"
    file = Path(IMAGE_FILE)
    img = cv2.imdecode(fromfile(file, dtype=uint8), -1)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    target = KekkaiUtilizeAssets.I_U_FISH_6
    match = target.match_all_any(img, threshold=0.8, nms_threshold=0.3)
    print(match)
