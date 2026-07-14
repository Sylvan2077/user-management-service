import os
import shutil
import subprocess
import json

import requests

from src.common.logs import logger
from src.common.temp_cache import TempCache
from src.common.utils import rand_str, encode_passwd, decode_passwd
from src.config import config
from src.service.module.fb_user_manager import (
    create_filebrowser_user,
    delete_filebrowser_user,
    change_password,
    generate_request_headers as fb_headers,
    sync_filebrowser_user,
)
from src.service.module.sym_talk_manager import (
    create_sym_talk_user,
    delete_sym_talk_user,
    change_user_info,
    parse_user_html,
    generate_request_headers as sym_headers,
    sync_sym_user,
)
from src.service.module.vpn_manager import (
    create_vpn_user,
    delete_vpn_user,
    update_vpn_info,
    sync_vpn_user,
)

settings = config.Settings()
vpn_config_path = settings.vpn_config_file_path

def create_user_on_node(node_ip, node_port, username):
    try:
        url = f"http://{node_ip}:{node_port}"
        data = {"username": username, "mode": "create"}
        response = requests.post(url, json=data, timeout=30)
        response_data = response.json()
        return response_data.get("success", False), response_data.get("message", "")
    except Exception as e:
        logger.error(f"连接节点 {node_ip}:{node_port} 失败: {e}")
        return False, str(e)


def get_server_info():
    # 读取缓存文件中配置信息
    cache = TempCache()
    server_info = cache.get("server_info")
    if server_info:
        fb_flag = server_info.get("allow_users_file_browser")
        sym_flag = server_info.get("allow_users_forums")
        vpn_flag = server_info.get("allow_vpn_server")
    else:
        fb_flag = False
        sym_flag = False
        vpn_flag = False
    return fb_flag, sym_flag, vpn_flag


def create_system_user(user_name):
    """
    创建系统用户（多节点）
    """

    username = "caep_" + user_name
    
    failed_nodes = []
    
    for node in settings.system_user_nodes:
        node_ip = node.get("ip")
        node_port = node.get("port")
        logger.info(f"在节点 {node_ip}:{node_port} 创建用户 {username}")
        
        success, message = create_user_on_node(node_ip, node_port, username)
        
        if success:
            logger.info(f"节点 {node_ip}:{node_port} 用户创建成功")
        else:
            logger.error(f"节点 {node_ip}:{node_port} 用户创建失败: {message}")
            failed_nodes.append({"ip": node_ip, "port": node_port, "reason": message})
    
    if failed_nodes:
        error_msg = f"部分节点创建失败: {json.dumps(failed_nodes)}"
        logger.error(error_msg)
        return error_msg
    
    return None


def user_register(user_name, user_passwd):
    """
    1.创建文件管理系统用户
    2.创建VPN用户
    3.创建用户论坛用户
    4.创建系统用户
    任何一个步骤出现问题都将终止创建，并删除已创建的用户
    :param user_name: 用户名称
    :param user_passwd: 用户密码
    :return:
    """

    # 获取缓存文件中配置信息
    fb_flag, sym_flag, vpn_flag = get_server_info()
    # 创建文件管理系统用户
    if fb_flag:
        logger.info("创建文件管理系统用户:{}".format(user_name))
        message = create_filebrowser_user(user_name, user_passwd, user_name + "_data")
        if message:
            logger.error(message)
            return message
    # 创建VPN用户
    if vpn_flag:
        logger.info("创建VPN用户:{}".format(user_name))
        msg = create_vpn_user(user_name, user_passwd)
        if msg:
            if fb_flag:
                # 删除文件管理系统用户
                delete_filebrowser_user(user_name)
            logger.error(msg)
            return msg
    # 创建用户论坛用户
    sym_talk_user_id = ""
    if sym_flag:
        logger.info("创建用户论坛用户:{}".format(user_name))
        response_info = create_sym_talk_user(user_name, user_passwd)
        if message := response_info.get("message"):
            # 创建失败后删除文件管理系统用户和VPN用户
            if fb_flag:
                delete_filebrowser_user(user_name)
            if vpn_flag:
                delete_vpn_user(user_name)
            logger.error(message)
            return message
        sym_talk_user_id = response_info.get("user_id")
    # 创建系统用户
    msg = create_system_user(user_name)
    if msg:
        # 删除文件管理系统用户
        if fb_flag:
            delete_filebrowser_user(user_name)
        if vpn_flag:
            # 删除VPN用户
            delete_vpn_user(user_name)
        # 删除用户论坛用户
        if sym_flag:
            delete_sym_talk_user(sym_talk_user_id)
        logger.error(msg)
        return msg
    return


def modify_user_info(pre_username, username, new_password):
    """
    修改用户信息
    :param pre_username: 原用户名
    :param username: 修改后用户名
    :param new_password: 新密码
    :return:
    """

    # 系统用户名
    system_username = "caep_" + username
    # 获取缓存文件中配置信息
    fb_flag, sym_flag, vpn_flag = get_server_info()
    # 修改VPN用户密码
    if new_password and vpn_flag:
        msg = update_vpn_info(username, new_password, pre_username)
        if msg:
            logger.error(msg)
            return msg
    # 如果修改用户名，则修改VPN用户信息
    if pre_username != username and vpn_flag:
        msg = update_vpn_info(username, new_password, pre_username)
        if msg:
            logger.error(msg)
            return msg
    # 修改文件管理系统的用户密码
    if fb_flag:
        if new_password or pre_username != username:
            message = change_password(
                username, new_password, pre_username, is_fb_superadmin=False
            )
            if message:
                if vpn_flag:
                    update_vpn_info(pre_username, new_password, username)
                logger.error(message)
                return message
    # 修改用户论坛用户密码
    user_id = ""
    if sym_flag:
        _, message = sym_headers()
        if message:
            logger.error(message)
            return message
        if pre_username != username:
            sym_username = username
            user_id = parse_user_html(pre_username)
        else:
            sym_username = ""
            user_id = parse_user_html(username)
        message = change_user_info(user_id, new_password, sym_username)
        if message:
            if fb_flag:
                change_password(
                    username, new_password, pre_username, is_fb_superadmin=False
                )
            if vpn_flag:
                update_vpn_info(pre_username, new_password, username)
            logger.error(message)
            return message
    # 如果更改了用户名，则创建系统用户，并删除原用户相关文件
    if pre_username != username:
        try:
            # 1.创建系统用户
            # 判断用户是否存在
            exist_user = "id {}".format(system_username)
            return_code = subprocess.call(exist_user, shell=True)
            if return_code != 0:
                # 生成随机系统密码
                rand_passwd = rand_str(8)
                subprocess.run("useradd {}".format(system_username), shell=True)
                subprocess.run(
                    "echo {} | passwd --stdin {}".format(rand_passwd, system_username),
                    shell=True,
                )
            # 2.删除原系统用户
            subprocess.run("pkill -u {}".format("caep_" + pre_username), shell=True)
            subprocess.run("userdel -r {}".format("caep_" + pre_username), shell=True)
            # 3.创建文件管理系统用户文件夹
            user_data = os.path.join(settings.file_browser_data_dir, username + "_data")
            if not os.path.exists(user_data):
                os.makedirs(user_data)
            subprocess.run(
                "chown -R {0}:{0} {1}".format(system_username, user_data), shell=True
            )
            # 4.创建用户家目录下的数据文件夹，并软链接至文件管理系统用户文件夹
            user_home_data_path = "/home/{}/data".format(system_username)
            # 创建软链接
            subprocess.run(
                "ln -s {} {}".format(user_data, user_home_data_path), shell=True
            )
            # 修改所属组
            subprocess.run(
                "chown -h {0}:{0} {1}".format(system_username, user_home_data_path),
                shell=True,
            )

            # 5.复制原用户文件到新用户目录
            pre_user_data = os.path.join(
                settings.file_browser_data_dir, pre_username + "_data"
            )
            new_user_data = os.path.join(
                settings.file_browser_data_dir, username + "_data"
            )
            if os.path.exists(pre_user_data):
                subprocess.run(
                    "cp -r {}/* {}".format(pre_user_data, new_user_data), shell=True
                )
                # 6.删除文件管理系统的用户文件夹
                shutil.rmtree(pre_user_data)
            # 删除用户turbo-vnc相关文件
            turbo_vnc_tmp_path = "/tmp/turbo-vnc/caep_{}-vnc".format(username)
            if os.path.exists(turbo_vnc_tmp_path):
                shutil.rmtree(turbo_vnc_tmp_path)
        except Exception as e:
            if fb_flag:
                change_password(
                    username, new_password, pre_username, is_fb_superadmin=False
                )
            if vpn_flag:
                update_vpn_info(pre_username, new_password, username)
            if sym_flag:
                change_user_info(user_id, new_password, username)
            logger.error(e)
            return e.args[0]


def user_change_passwd(username, new_password, old_password, is_fb_superadmin):
    """
    用户修改密码
    :param username: 用户名
    :param new_password: 新密码
    :param old_password: 旧密码
    :param is_fb_superadmin: 是否为管理员用户
    :return:
    """

    fb_flag, sym_flag, vpn_flag = get_server_info()
    # 修改文件管理系统的用户密码
    if fb_flag:
        message = change_password(username, new_password, username, is_fb_superadmin)
        if message:
            return message
    if not is_fb_superadmin:
        # 修改VPN用户密码
        if vpn_flag:
            msg = update_vpn_info(username, new_password, username)
            if msg:
                if fb_flag:
                    change_password(username, old_password, username, is_fb_superadmin)
                return msg
    # 修改用户论坛用户密码
    if sym_flag:
        # 获取用户论坛的用户ID
        user_id = parse_user_html(username)
        msg = change_user_info(user_id, new_password, "")
        if msg:
            if fb_flag:
                change_password(username, old_password, username, is_fb_superadmin)
            if vpn_flag:
                update_vpn_info(username, old_password, username)
            return msg
    if is_fb_superadmin:
        # 将缓存文件中管理员的密码更新
        cache = TempCache()
        server_info = cache.get("server_info")
        if fb_flag:
            server_info["filebrowser_password"] = encode_passwd(new_password)
        if sym_flag:
            server_info["sym_talk_password"] = encode_passwd(new_password)
        cache.set("server_info", server_info)
    return


def delete_user(names):
    """
    删除用户
    :param names: 需要删除的用户列表
    :return:
    """

    fb_flag, sym_flag, vpn_flag = get_server_info()
    data = {"msg": "", "data": []}
    # 登陆文件管理系统
    if fb_flag:
        _, message = fb_headers()
        if message:
            logger.error(message)
            data["msg"] = message
            return data
    # 登陆用户论坛
    if sym_flag:
        _, message = sym_headers()
        if message:
            logger.error(message)
            data["msg"] = message
            return data
    user_names = names.split(",")
    delete_failed = []
    for user_name in user_names:
        reason = []
        logger.info("删除用户：{}".format(user_name))
        if vpn_flag:
            # 删除VPN用户
            msg = delete_vpn_user(user_name)
            if msg:
                reason.append("删除VPN用户失败")
        # 调用HTTP服务删除系统用户
        username = "caep_" + user_name
        delete_failed_nodes = []
        for node in settings.system_user_nodes:
            node_ip = node.get("ip")
            node_port = node.get("port")
            try:
                url = f"http://{node_ip}:{node_port}"
                data = {"username": username, "mode": "del"}
                response = requests.post(url, json=data, timeout=30)
                response_data = response.json()
                if not response_data.get("success"):
                    delete_failed_nodes.append({"ip": node_ip, "port": node_port, "reason": response_data.get("message", "删除失败")})
            except Exception as e:
                delete_failed_nodes.append({"ip": node_ip, "port": node_port, "reason": str(e)})
        
        if delete_failed_nodes:
            reason.append(f"删除系统用户失败: {json.dumps(delete_failed_nodes)}")
        # 删除文件管理系统的用户文件夹
        # user_data = os.path.join(settings.file_browser_data_dir, user_name + "_data")
        # if os.path.exists(user_data):
        #     shutil.rmtree(user_data)
        # 删除用户turbo-vnc相关文件
        turbo_vnc_tmp_path = "/tmp/turbo-vnc/caep_{}-vnc".format(user_name)
        if os.path.exists(turbo_vnc_tmp_path):
            shutil.rmtree(turbo_vnc_tmp_path)
        # 删除文件管理系统用户
        if fb_flag:
            msg = delete_filebrowser_user(user_name)
            if msg:
                reason.append("删除文件管理系统用户失败")
        # 删除用户论坛用户
        if sym_flag:
            user_id = parse_user_html(user_name)
            msg = delete_sym_talk_user(user_id)
            if msg:
                reason.append("删除用户论坛用户失败")
        if reason:
            reason.append("请手动清理！")
            delete_failed.append({"username": user_name, "reason": ",".join(reason)})
    data["data"] = delete_failed
    return data


def update_user(form_data):
    """
    同步用户
    :param form_data: 需要同步的用户对象
    :return:
    """

    _, _, vpn_flag = get_server_info()
    # 判断vpn_flag，True：内部版本，创建文件管理系统和用户论坛用户；False：外部版本，创建文件管理用户
    # 创建成功的用户信息
    created_success = {}
    # 创建成功的用户ID
    user_id_dict = {}
    # 创建失败的用户信息
    created_failed = []
    # 返回信息
    data = {"msg": "", "data": []}
    if vpn_flag:
        # 如果试用平台没有用户，则直接清理
        if form_data:
            # 确认关联服务是否开启
            _, message = fb_headers()
            if message:
                logger.error(message)
                data["msg"] = message
                return data
            # 登陆用户论坛
            _, message = sym_headers()
            if message:
                logger.error(message)
                data["msg"] = message
                return data
            # 内部版本，创建文件管理系统和用户论坛用户
            for username, encode_passwd in form_data.items():
                # 将密码进行解密
                password = decode_passwd(encode_passwd)
                # 创建文件管理系统用户
                message = create_filebrowser_user(
                    username, password, username + "_data"
                )
                if message:
                    created_failed.append(
                        {"username": username, "reason": "创建文件管理系统用户失败"}
                    )
                    logger.error(message)
                    continue
                # 创建用户论坛用户
                response_info = create_sym_talk_user(username, password)
                if message := response_info.get("message"):
                    created_failed.append(
                        {"username": username, "reason": "创建用户论坛用户失败"}
                    )
                    logger.error(message)
                    continue
                else:
                    user_id = response_info.get("user_id")
                # 判断系统用户是否存在，不存在则创建
                msg = create_system_user(username)
                if msg:
                    created_failed.append({"username": username, "reason": f"创建系统用户失败: {msg}"})
                    continue
                # 创建成功后更新
                created_success.update(
                    {username: {"password": password, "user_id": user_id}}
                )
                user_id_dict.update({user_id: password})
        # 同步文件管理系统用户
        filebrowser_message = sync_filebrowser_user(created_success)
        if filebrowser_message:
            data["msg"] = filebrowser_message
            return data
        # 同步用户论坛用户
        sym_message = sync_sym_user(user_id_dict)
        if sym_message:
            data["msg"] = sym_message
            return data
        # 同步VPN用户
        vpn_message = sync_vpn_user(created_success)
        if vpn_message:
            data["msg"] = vpn_message
            return data
    else:
        if form_data:
            # 外部版本，创建文件管理用户
            for username, encode_passwd in form_data.items():
                password = decode_passwd(encode_passwd)
                # 创建文件管理系统用户
                message = create_filebrowser_user(
                    username, password, username + "_data"
                )
                if message:
                    created_failed.append(
                        {"username": username, "reason": "创建文件管理系统用户失败"}
                    )
                    logger.error(message)
                    continue
                created_success.update({username: {"password": password}})
        # 同步文件管理系统用户
        message = sync_filebrowser_user(created_success)
        if message:
            data["msg"] = message
            return data
    data["data"] = created_failed
    return data