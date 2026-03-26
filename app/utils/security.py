"""
密码哈希与校验（bcrypt）
"""
import re
import bcrypt
from app.utils.config_manager import ConfigManager


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def check_password_strength(password: str) -> tuple[bool, str]:
    """
    校验密码强度，返回 (通过, 错误信息)。
    """
    cfg = ConfigManager()
    min_len = cfg.getint("security", "min_password_length", 8)
    require_upper = cfg.getbool("security", "pwd_require_upper", True)
    require_digit = cfg.getbool("security", "pwd_require_digit", True)
    require_special = cfg.getbool("security", "pwd_require_special", False)

    if len(password) < min_len:
        return False, f"密码长度不能少于 {min_len} 位"
    if require_upper and not re.search(r"[A-Z]", password):
        return False, "密码必须包含至少一个大写字母"
    if require_digit and not re.search(r"\d", password):
        return False, "密码必须包含至少一个数字"
    if require_special and not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "密码必须包含至少一个特殊字符"
    return True, ""
