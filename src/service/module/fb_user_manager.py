#!/usr/bin/env python

import json

import requests

from src.common.temp_cache import TempCache
from src.common.utils import decode_passwd
from src.config import config

# 读取缓存文件
cache = TempCache()
# 读取配置文件
settings = config.Settings()


def set_server_addr(addr):
    global server_addr
    server_addr = addr


def full_url(path, **query):
    global server_addr
    from urllib.parse import urlunparse, urlencode, urljoin, ParseResult

    # 解析URL为ParseResult对象
    return urljoin(
        server_addr,
        urlunparse(
            ParseResult(
                scheme="",
                netloc="",
                path=path,
                params="",
                query=urlencode(query),
                fragment="",
            )
        ),
    )


def login(username, password, captcha):
    global server_addr
    # 用户登录API
    login_url = full_url("/api/login")
    # 根据csrftoken构造请求头
    headers = {
        "Connection": "keep-alive",
        "Content-Type": "application/json; charset=UTF-8",
    }
    # 登录账号及密码
    login_data = dict(username=username, password=password, captcha=captcha)
    # 登录操作,返回sess,sessionid
    try:
        ret = requests.post(login_url, data=json.dumps(login_data), headers=headers)
    except requests.ConnectionError:
        ret = ""
    return ret


def try_login(username, password, captcha):
    """测试登录密码是否正确"""
    # 调用登录API,获取X-Auth
    ret = login(username, password, captcha)
    if ret == "":
        message = "无法连接至文件管理系统，请确认文件管理系统是否启动！"
        return ret, message
    elif ret.status_code == 403:
        message = "文件管理系统管理员帐号密码错误，请确认是否正确！"
        return ret, message
    else:
        message = ""
    # 根据X-Auth构造请求头
    headers = {
        "Connection": "keep-alive",
        "X-Auth": ret.text,
        "Content-Type": "application/json; charset=UTF-8",
    }
    return headers, message


def generate_request_headers(*default_info):
    """
    登录文件管理系统，并构造请求头
    """
    # 获取文件管理系统访问地址
    filebrowser_server = settings.file_browser_host
    fb_args = {
        "server_addr": filebrowser_server,
        "captcha": "",
    }
    # 设置访问路径为全局变量
    set_server_addr(fb_args.get("server_addr"))
    # 关联服务配置密码登录
    if default_info:
        username = default_info[0]
        password = default_info[1]
        # 调用登录API,获取X-Auth
        headers, message = try_login(username, password, fb_args.get("captcha"))
    else:
        # 解密管理员密码
        server_info = cache.get("server_info")
        username = server_info.get("filebrowser_username")
        # 使用关联服务配置密码登录
        default_password = decode_passwd(server_info.get("filebrowser_password"))
        headers, message = try_login(username, default_password, fb_args.get("captcha"))
    return headers, message


def create_filebrowser_user(username, password, Scope):
    """
    创建文件管理系统用户
    """

    # 获取请求头
    headers, message = generate_request_headers()
    if message:
        return message
    # 拼接API路径
    create_filebrowser_user_url = full_url("api/users")
    # 创建的用户数据
    user_data = {
        "data": {
            "ID": 0,  # 用户ID(默认，不可更改)
            "Username": username,  # 用户名
            "Password": password,  # 密码
            "Scope": Scope,  # 目录范围
            "Locale": "zh-cn",  # 语言
            "LockPassword": True,  # 禁止用户修改密码
            "ViewMode": "mosaic",  # 用户文件夹页面样式(默认)
            "SingleClick": False,  # 使用单击来打开文件和目录(默认)
            "Perm": {  # 用户权限
                "Admin": False,  # 管理员
                "Execute": False,  # 执行命令
                "Create": True,  # 创建文件和文件夹
                "Rename": True,  # 重命名或移动文件和文件夹
                "Modify": True,  # 编辑
                "Delete": True,  # 删除文件和文件夹
                "Share": True,  # 分享文件
                "Download": False,  # 下载
            },
            "Commands": [],  # 指定用户可以执行的命令(Shell命令)
        },
        "what": "user",
        "which": [],
    }
    # 调用create接口创建用户
    resp = requests.post(
        create_filebrowser_user_url, data=json.dumps(user_data), headers=headers
    )
    # 获取返回信息
    message = resp.reason
    if message == "Created":
        return
    elif message == "Internal Server Error":
        # 如果存在用户则修改密码
        change_password(username, password, username, is_fb_superadmin=False)
        return ""
    else:
        return "文件管理系统用户创建错误！"


def get_all_user():
    """
    获取所有用户信息
    """

    # 获取请求头
    headers, message = generate_request_headers()
    if message:
        return message
    # 拼接API路径
    filebrowser_user_url = full_url("api/users")
    user_data = {}
    # 获取所有用户信息
    resp = requests.get(
        filebrowser_user_url, data=json.dumps(user_data), headers=headers
    )
    # 查询需要删除的用户名及ID
    user_info_json = json.loads(resp.text)
    return user_info_json


def delete_filebrowser_user(username):
    """
    删除文件管理系统用户
    """

    # 获取请求头
    headers, message = generate_request_headers()
    if message:
        return message
    # 获取所有用户信息
    user_info_json = get_all_user()
    for user_info in user_info_json:
        if user_info.get("username") == username:
            user_id = user_info.get("id")
            # 构造需要删除的用户数据
            user_data = {}
            # 调用delete接口删除用户
            delete_filebrowser_user_url = full_url("api/users/{}".format(user_id))
            requests.delete(
                delete_filebrowser_user_url, data=json.dumps(user_data), headers=headers
            )
            return


def change_password(username, password, pre_username, is_fb_superadmin):
    """
    修改用户密码
    """

    # 获取请求头
    headers, message = generate_request_headers()
    if message:
        return message
    # 获取所有用户信息
    user_info_json = get_all_user()
    if is_fb_superadmin:
        user_info_scope = ""
    else:
        user_info_scope = "/{}_data".format(username)
    for user_info in user_info_json:
        if user_info.get("username") == pre_username:
            user_id = user_info.get("id")
            user_info["password"] = password
            user_info["username"] = username
            user_info["scope"] = user_info_scope

            # 修改的用户数据
            user_data = {
                "data": user_info,
                "what": "user",
                "which": ["all"],
            }

            # 调用put方法修改用户密码
            change_password_url = full_url("api/users/{}".format(user_id))
            resp = requests.put(
                change_password_url, data=json.dumps(user_data), headers=headers
            )
            # 获取返回信息
            message = resp.reason
            if message != "OK":
                return "修改文件管理系统用户出错！"
    return


def sync_filebrowser_user(created_success):
    """
    同步文件管理系统用户
    """

    # 获取请求头
    headers, message = generate_request_headers()
    if message:
        return message
    # 获取所有用户信息
    user_info_json = get_all_user()
    for user_info in user_info_json:
        origin_username = user_info.get("username")
        if not created_success.get(origin_username):
            user_id = user_info.get("id")
            # 构造需要删除的用户数据
            user_data = {}
            # 调用delete接口删除用户
            delete_filebrowser_user_url = full_url("api/users/{}".format(user_id))
            requests.delete(
                delete_filebrowser_user_url, data=json.dumps(user_data), headers=headers
            )
        else:
            password = created_success.get(origin_username).get("password")
            change_password(
                origin_username, password, origin_username, is_fb_superadmin=False
            )
    return
