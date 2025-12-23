import re
from typing import Dict


def check_phone_number(phone_number: str) -> tuple[bool, str]:
    """
    检测手机号是否符合规则
    
    Args:
        phone_number: 待检测的手机号
        
    Returns:
        tuple[bool, str]: 手机号格式是否合法，以及错误的原因（无错误则返回空字符串）
    """
    # 格式检查： 比较复杂，具体请见https://www.cnblogs.com/treeofb/p/17468979.html
    if not re.match(r'^(13[0-9]|14[01456879]|15[0-35-9]|16[2567]|17[0-8]|18[0-9]|19[0-35-9])\d{8}$', phone_number):
        return False, "请输入正确的手机号"
    
    return True, ""


def validate_credentials_new(username: str, password: str) -> Dict[str, any]:
    """
    新版账号/密码校验：
    - 账号：2-20 位，仅数字、字母或 !@#$%^&*_；
    - 密码：8-16 位，仅数字、字母或 !@#$%^&*，且至少包含两类字符。
    """
    result = {
        'is_valid': False,
        'username_errors': [],
        'password_errors': [],
    }

    # 校验账号
    valid_username, username_error = check_username_new(username)
    if not valid_username:
        result['username_errors'].append(username_error)

    # 校验密码
    valid_password, password_error = check_password_new(password)
    if not valid_password:
        result['password_errors'].append(password_error)

    result['is_valid'] = (not result['username_errors']) and (not result['password_errors'])
    return result

def check_username_new(username: str) -> tuple[bool, str]:
    """
    新版账号校验：2-20 位，仅数字、字母或 !@#$%^&*
    """
    if not username:
        return False, "用户名不能为空"
    if not re.fullmatch(r'[A-Za-z0-9!@#$%^&_*]{2,20}', username):
        return False, "用户名需为2-20位，允许字母、数字或!@#$%^&*"
    return True, ""

def check_password_new(password: str) -> tuple[bool, str]:
    """
    新版密码校验：8-16 位，仅数字、字母或 !@#$%^&*，且至少包含两类字符。
    """
    if not password:
        return False, "密码不能为空"
    if not re.fullmatch(r'[A-Za-z0-9!@#$%^&*]{8,16}', password):
        return False, "密码需为8-16位，允许字母、数字或!@#$%^&*"
    has_letter = bool(re.search(r'[A-Za-z]', password))
    has_digit = bool(re.search(r'\d', password))
    has_special = bool(re.search(r'[!@#$%^&*]', password))
    category_count = sum([has_letter, has_digit, has_special])
    if category_count < 2:
        return False, "密码需至少包含字母、数字、特殊字符中的两种"
    return True, ""