"""
输入校验工具函数
"""
import re


def is_valid_part_number(value: str) -> bool:
    """零件图号格式：字母-数字-数字，如 ED-15302-01"""
    return bool(re.match(r"^[A-Za-z]{1,4}-\d{4,6}-\d{2}$", value.strip()))


def is_valid_version(value: str) -> bool:
    """版本号格式：字母+数字，如 A01 A03"""
    return bool(re.match(r"^[A-Z]\d{2}$", value.strip()))


def is_valid_username(value: str) -> bool:
    """用户名：4~32位字母/数字/下划线"""
    return bool(re.match(r"^[A-Za-z0-9_]{4,32}$", value.strip()))


def sanitize_text(value: str, max_length: int = 256) -> str:
    """去除首尾空白，截断超长文本"""
    return value.strip()[:max_length] if value else ""
