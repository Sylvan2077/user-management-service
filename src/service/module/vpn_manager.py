import os

from src.config import config

settings = config.Settings()
vpn_config_path = settings.vpn_config_file_path


def exists_vpn_dir():
    """
    判断是否存在VPN文件夹
    """

    msg = ""
    if not os.path.exists(os.path.dirname(vpn_config_path)):
        msg = "OpenVPN路径不存在，请确认！"
    elif not os.path.exists(vpn_config_path):
        msg = "OpenVPN配置文件不存在，请确认！"
    return msg


def create_vpn_user(username, passwd):
    """
    创建VPN用户
    """

    msg = exists_vpn_dir()
    if msg:
        return msg
    with open(vpn_config_path, "a+") as fp:
        fp.write("{} {}\n".format(username, passwd))
    return


def delete_vpn_user(username):
    """
    删除VPN用户
    """

    msg = exists_vpn_dir()
    if msg:
        return msg
    with open(vpn_config_path, "r") as file:
        lines = file.readlines()
    with open(vpn_config_path, "w") as f:
        for line in lines:
            if username not in line:
                f.write(line)
    return


def update_vpn_info(username, new_password, pre_username):
    """
    修改VPN用户信息
    """

    msg = exists_vpn_dir()
    if msg:
        return msg
    with open(vpn_config_path, "r") as file:
        lines = file.readlines()
    with open(vpn_config_path, "w") as f:
        for line in lines:
            if pre_username in line:
                if new_password:
                    f.write("{} {}\n".format(username, new_password))
                else:
                    name_passwd = line.split(" ")
                    f.write("{} {}\n".format(username, name_passwd[1]))
            else:
                f.write(line)
    return


def sync_vpn_user(created_success):
    """
    同步用户
    """

    msg = exists_vpn_dir()
    if msg:
        return msg
    with open(vpn_config_path, "w") as fp:
        if created_success:
            for username, passwd in created_success.items():
                fp.write("{} {}\n".format(username, passwd.get("password")))
        else:
            fp.write("")
    return
