"""
配置验证和自动修正模块
当配置参数不符合要求时，自动修改为默认值并打印日志
"""
import copy
from module.logger import logger
from pydantic import fields
from typing import Any


class ConfigValidator:
    """
    配置验证和自动修正类
    """

    def __init__(self, config_model=None):
        self.config_model = config_model


def _fix_by_model_field_type(config_name, config_data: dict, model_class) -> dict:
    """
    通过模型字段类型信息来修复配置数据
    :param config_data: 配置数据
    :param model_class: 模型类
    :return: 修复后的配置数据
    """
    if not hasattr(model_class, '__fields__'):
        return config_data

    fixed_data = copy.deepcopy(config_data)

    for field_name, field_info in model_class.__fields__.items():
        if field_name in fixed_data:
            field_value = fixed_data[field_name]
            expected_type = field_info.type_

            # 如果是嵌套模型，递归处理
            if isinstance(field_value, dict) and hasattr(expected_type, '__fields__'):
                fixed_data[field_name] = _fix_by_model_field_type(config_name, field_value, expected_type)
            else:
                # 尝试修复字段值
                fixed_value = _try_fix_field_value(config_name, field_value, field_info, expected_type, field_name)
                if fixed_value != field_value:
                    fixed_data[field_name] = fixed_value

    return fixed_data


def _try_fix_field_value(config_name, value: Any, field_info: fields.FieldInfo, expected_type: type, field_name: str) -> Any:
    """
    尝试修复字段值，基于模型字段类型信息
    :param value: 当前值
    :param field_info: 字段信息
    :param expected_type: 期望类型
    :param field_name: 字段名称
    :return: 修复后的值
    """
    # 检查是否是枚举类型
    if hasattr(expected_type, '__members__'):  # 枚举类型
        try:
            # 尝试找到最接近的有效值
            valid_values = list(expected_type.__members__.keys()) + [str(v.value) for v in
                                                                     expected_type.__members__.values()]

            if str(value) not in valid_values:
                # 查找相似值
                for valid_val in valid_values:
                    if str(valid_val).lower() in str(value).lower() or str(value).lower() in str(valid_val).lower():
                        logger.warning(f"[{config_name}] 字段 {field_name} 的值 '{value}' 修正为 '{valid_val}'")
                        return valid_val

                # 如果找不到相似值，使用默认值或第一个有效值
                if field_info.default is not None and field_info.default != ...:
                    return field_info.default
                elif valid_values:
                    logger.warning(f"[{config_name}] 字段 {field_name} 的值 '{value}' 修正为默认值 '{valid_values[0]}'")
                    return valid_values[0]
        except Exception:
            pass  # 如果枚举检查失败，继续其他修复方式

    # 检查基本类型转换
    if expected_type == int and isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            pass
    elif expected_type == float and isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            pass
    elif expected_type == bool and isinstance(value, str):
        if value.lower() in ['true', '1', 'yes', 'on']:
            return True
        elif value.lower() in ['false', '0', 'no', 'off']:
            return False

    return value
