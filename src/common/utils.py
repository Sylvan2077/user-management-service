import random


KEY = "80ae3923a36d721c254ca57754455a98"


def encode_passwd(new_password):
    """
    加密管理员密码
    """

    encrypt_passwd = ""
    for i, j in zip(new_password, KEY):
        old_temp = str(ord(i) + ord(j)) + "_"
        encrypt_passwd += old_temp
    return encrypt_passwd


def decode_passwd(data):
    """
    解密管理员密码
    """

    decrypt_passwd = ""
    if data:
        for i, j in zip(data.split("_")[:-1], KEY):
            old_tmp = chr(int(i) - ord(j))
            decrypt_passwd += old_tmp
    return decrypt_passwd


def rand_str(length: int = 8):
    """
    生成随机字符串
    :param length: 随机字符串长度,默认8
    :return: random_list
    """

    base_char = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    base_number = "1234567890"

    random_list = [
        random.choices(base_char.upper() + base_char + base_number)[0]
        for _ in range(length)
    ]
    return "".join(random_list)
