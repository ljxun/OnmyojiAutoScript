import numpy as np
import ppocronnx.predict_system
from module.logger import logger


class TextSystem(ppocronnx.predict_system.TextSystem):
    def __init__(
            self,
            use_angle_cls=False,
            box_thresh=0.6,
            unclip_ratio=1.6,
            rec_model_path=None,
            det_model_path=None,
            ort_providers=None
    ):
        if not isinstance(use_angle_cls, bool):
            raise ValueError("use_angle_cls参数必须为布尔值")
        if not isinstance(box_thresh, float) or not 0 <= box_thresh <= 1:
            raise ValueError("box_thresh参数必须为0到1之间的浮点数")
        if not isinstance(unclip_ratio, (int, float)) or unclip_ratio <= 0:
            raise ValueError("unclip_ratio参数必须为正数")
            
        logger.info(f"初始化PPOCR模型, 使用角度分类: {use_angle_cls}")
        super().__init__(
            use_angle_cls=use_angle_cls,
            box_thresh=box_thresh,
            unclip_ratio=unclip_ratio,
            rec_model_path=rec_model_path,
            det_model_path=det_model_path,
            ort_providers=ort_providers
        )


def sorted_boxes(dt_boxes):
    """
    对文本框进行排序，从上到下，从左到右
    参数:
        dt_boxes(array): 检测到的文本框，形状为[4, 2]
    返回:
        排序后的文本框(array)，形状为[4, 2]
    """
    if dt_boxes is None or dt_boxes.shape[0] == 0:
        logger.warning("输入文本框为空")
        return np.zeros((0, 4, 2), dtype=dt_boxes.dtype if dt_boxes is not None else np.float32)

        
    num_boxes = dt_boxes.shape[0]
    sorted_boxes = sorted(dt_boxes, key=lambda x: (x[0][1], x[0][0]))
    _boxes = list(sorted_boxes)

    for i in range(num_boxes - 1):
        for j in range(i, -1, -1):
            if abs(_boxes[j + 1][0][1] - _boxes[j][0][1]) < 10 and \
                    (_boxes[j + 1][0][0] < _boxes[j][0][0]):
                tmp = _boxes[j]
                _boxes[j] = _boxes[j + 1]
                _boxes[j + 1] = tmp
            else:
                break
    return _boxes

# 使用PaddleOCR 2.6中的sorted_boxes()替换ppocr-onnx中的实现
ppocronnx.predict_system.sorted_boxes = sorted_boxes