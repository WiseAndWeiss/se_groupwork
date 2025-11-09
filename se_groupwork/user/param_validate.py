import re
from typing import Dict

def validate_credentials(username: str, password: str) -> Dict[str, any]:
    """
    验证用户名和密码的合法性
    
    Args:
        username: 待验证的用户名
        password: 待验证的密码
        
    Returns:
        Dict[str, any]: 包含验证结果的字典
    """
    result = {
        'is_valid': False,
        'username_errors': [],
        'password_errors': [],
        'password_strength': 'weak'  # weak, medium, strong
    }
    
    # 1. 用户名验证 [7,8](@ref)
    if not username:
        result['username_errors'].append("用户名不能为空")
    else:
        validated, error = check_username(username)
        if not validated:
            result['username_errors'].append(error)
    
    # 2. 密码基础验证 [5,6](@ref)
    if not password:
        result['password_errors'].append("密码不能为空")
    else:
        # 长度检查：至少6位 [5](@ref)
        if len(password) < 6:
            result['password_errors'].append("密码长度至少为6个字符")
        
        # 密码强度检测
        strength_result = check_password_strength(password)
        result['password_strength'] = strength_result['strength']
        
        if strength_result['strength'] == 'weak':
            result['password_errors'].append("密码强度不足，"+ strength_result['suggestion'])
        
        # 检查密码是否包含用户名
        if username and username.lower() in password.lower():
            result['password_errors'].append("密码不能包含用户名")
        
        # 检查常见弱密码
        weak_passwords = ['123456', 'password', 'qwerty', '111111', 'abc123']
        if password in weak_passwords:
            result['password_errors'].append("该密码过于常见，请选择更复杂的密码")
    
    # 3. 最终结果判断
    result['is_valid'] = (len(result['username_errors']) == 0 and 
                         len(result['password_errors']) == 0)
    
    return result

def check_username(username: str) -> tuple[bool, str]:
    """
    检测账号是否符合规则
    
    Args:
        password: 待检测的账号
        
    Returns:
        tuple[bool, str]: 账号格式是否合法，以及错误的原因（无错误则返回空字符串）
    """
    # 长度检查：3-20个字符 [7](@ref)
    if len(username) < 3 or len(username) > 20:
        return False, "用户名长度必须在3-20个字符之间"
    
    # 格式检查：只能包含字母、数字、下划线 [8](@ref)
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]{2,19}$', username):
        return False, "用户名必须以字母开头，且只能包含字母、数字和下划线"
    
    return True, ""

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

def check_password_strength(password: str) -> Dict[str, str]:
    """
    检测密码强度
    
    Args:
        password: 待检测的密码
        
    Returns:
        Dict[str, str]: 包含强度等级和改进建议的字典
    """
    strength = 'weak'
    suggestion = ""
    
    # 初始化字符类型标记 [9,11](@ref)
    has_upper = False    # 大写字母
    has_lower = False    # 小写字母  
    has_digit = False    # 数字
    has_special = False  # 特殊字符
    
    # 检查每种字符类型是否存在
    for char in password:
        if char.isupper():
            has_upper = True
        elif char.islower():
            has_lower = True
        elif char.isdigit():
            has_digit = True
        elif not char.isspace():  # 非空格的特殊字符
            has_special = True
    
    # 计算强度得分 [10](@ref)
    score = 0
    
    # 长度得分
    if len(password) >= 8:
        score += 1
    if len(password) >= 12:
        score += 1
    
    # 字符类型得分
    type_count = sum([has_upper, has_lower, has_digit, has_special])
    if type_count >= 3:
        score += type_count - 2
    
    # 确定强度等级
    if score >= 4:
        strength = "strong"
        suggestion = "密码强度很好"
    elif score >= 2:
        strength = "medium"
        suggestion = "建议添加大写字母、数字或特殊字符以增强安全性"
    else:
        suggestion = "建议使用至少8位字符，包含大小写字母、数字和特殊字符"
    
    return {'strength': strength, 'suggestion': suggestion}



