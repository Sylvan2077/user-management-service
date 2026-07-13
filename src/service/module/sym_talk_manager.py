#!/usr/bin/env python

import json

import requests
from bs4 import BeautifulSoup

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
    # md5转换
    import hashlib

    md5_password = hashlib.md5(password.encode("utf8")).hexdigest()
    # 用户登录API
    login_url = full_url("/login")
    # 根据csrftoken构造请求头
    headers = {
        "Connection": "keep-alive",
        "Content-Type": "application/json; charset=UTF-8",
    }
    # 登录账号及密码
    login_data = dict(nameOrEmail=username, userPassword=md5_password, captcha=captcha)
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
        message = "无法连接至用户论坛，请确认用户论坛是否启动！"
        return ret, message
    elif "密码错误" in ret.text:
        message = "用户论坛管理员密码错误，请确认是否已被修改！"
        return ret, message
    elif "用户不存在" in ret.text:
        message = "用户论坛管理员帐号错误，请确认是否正确！"
        return ret, message
    elif "登录限制" in ret.text:
        message = "用户论坛管理员帐号被限制登录，请确认！"
        return ret, message
    else:
        message = ""
    # 构造cookie
    set_cookie = "LATKE_SESSION_ID={}; sym-ce={}".format(
        ret.cookies.values()[0], ret.cookies.values()[1]
    )
    # 根据X-Auth构造请求头
    headers = {
        "Cookie": set_cookie,
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0",
    }
    return headers, message


def generate_request_headers(*default_info):
    """
    登录用户论坛，并构造请求头
    """
    # 获取用户论坛访问地址
    sym_talk_server = settings.sym_talk_host
    args = {
        "server_addr": sym_talk_server,
        "captcha": "",
    }
    # 设置访问路径为全局变量
    set_server_addr(args.get("server_addr"))
    # 关联服务配置密码登录
    if default_info:
        username = default_info[0]
        password = default_info[1]
        # 调用登录API,获取X-Auth
        headers, message = try_login(username, password, args.get("captcha"))
    else:
        # 解密管理员密码
        server_info = cache.get("server_info")
        username = server_info.get("sym_talk_username")
        # 使用关联服务配置密码登录
        default_password = decode_passwd(server_info.get("sym_talk_password"))
        headers, message = try_login(username, default_password, args.get("captcha"))
    return headers, message


def parse_user_html(username):
    """
    解析用户页面，获取用户ID及状态
    """
    # 获取请求头
    headers, _ = generate_request_headers()
    # 拼接API路径
    change_passwd_url = full_url("/admin/users?query={}".format(username))
    # 获取返回信息
    resp = requests.get(change_passwd_url, headers=headers)
    # 解析HTML内容，获取用户状态
    result_soup = BeautifulSoup(resp.text, "html.parser")
    # 获取用户ID
    a_tag = result_soup.findAll(
        "a", attrs={"class": "fn-right tooltipped tooltipped-w ft-a-title"}
    )
    user_id = ""
    try:
        user_id = a_tag[0].get("href").split("/")[-1]
    except Exception:
        return user_id
    return user_id


def modify_user_status(username, password):
    """
    创建用户时判断是否存在，存在则修改用户状态
    """
    # 解析用户html页面，获取ID及状态
    user_id = parse_user_html(username)
    # 修改用户状态为正常并修改密码
    message = change_user_info(user_id, password, username, 0)
    return user_id, message


def create_sym_talk_user(username, password):
    """
    创建用户论坛用户
    """
    # 返回数据
    data = {"user_id": "", "message": ""}
    # 获取请求头
    headers, message = generate_request_headers()
    if message:
        data["message"] = message
        return data
    # 拼接API路径
    create_sym_talk_user_url = full_url("/admin/add-user")
    # 创建的用户数据
    user_data = {
        "userName": username,  # 用户名
        "userPassword": password,  # 密码
        "userEmail": "{}@mail.com".format(username),  # 邮箱
        "domainNav": 0,
    }
    # 调用create接口创建用户
    resp = requests.post(create_sym_talk_user_url, data=user_data, headers=headers)
    # 获取返回信息
    message = resp.reason
    path_url = resp.request.path_url.split("/")
    if message == "OK" and len(path_url) == 4:
        data["user_id"] = path_url[-1]
    elif message == "OK" and len(path_url) != 4:
        user_id, msg = modify_user_status(username, password)
        data["user_id"] = user_id
        data["message"] = msg
        return data
    else:
        data["message"] = "用户论坛用户创建错误！"
    return data


def delete_sym_talk_user(user_id):
    """
    删除用户论坛用户
    """

    if not user_id:
        return
    # 获取请求头
    headers, message = generate_request_headers()
    if message:
        return message
    # 拼接API路径
    sym_talk_user_url = full_url("/admin/user/{}".format(user_id))
    user_data = {"userStatus": 3}
    requests.post(sym_talk_user_url, data=user_data, headers=headers)
    return


def change_user_info(user_id, new_password, username, *args):
    """
    修改用户密码
    """

    if not user_id:
        return
    # 获取请求头
    headers, message = generate_request_headers()
    if message:
        return message
    # 拼接API路径
    change_passwd_url = full_url("/admin/user/{}".format(user_id))
    if args:
        user_data = {"userPassword": new_password, "userStatus": args[0]}
    else:
        user_data = {"userPassword": new_password}
    resp = requests.post(change_passwd_url, data=user_data, headers=headers)
    # 修改用户名
    if username:
        change_username_url = full_url("/admin/user/{}/username".format(user_id))
        data = {"userName": username}
        resp = requests.post(change_username_url, data=data, headers=headers)
    # 获取返回信息
    message = resp.reason
    if message != "OK":
        return "修改用户论坛用户出错！"
    return


def sync_sym_user(user_id_dict):
    """
    同步用户
    """

    # 获取请求头
    headers, message = generate_request_headers()
    if message:
        return message
    user_id_list = []
    # 拼接API路径
    change_passwd_url = full_url("/admin/users")
    resp = requests.get(change_passwd_url, headers=headers)
    # 解析HTML内容，获取用户状态
    result_soup = BeautifulSoup(resp.text, "html.parser")
    # 获取div标签
    div_tag = result_soup.findAll("div", attrs={"class": "module list"})
    # 获取div标签中的li标签
    li_tag = div_tag[0].findAll("li")
    for single_li_tag in li_tag:
        # 获取li标签中的a标签
        a_tag = single_li_tag.findAll(
            "a", attrs={"class": "fn-right tooltipped tooltipped-w ft-a-title"}
        )
        # 获取用户ID
        user_id = a_tag[0].get("href").split("/")[-1]
        # 获取span标签
        span_tag = single_li_tag.findAll("div", attrs={"class": "fn-clear"})
        # 获取角色
        user_role = span_tag[1].text.split()[1]
        if user_role != "管理员":
            user_id_list.append(user_id)
    for user_id in user_id_list:
        if not user_id_dict.get(user_id):
            # 拼接API路径
            sym_talk_user_url = full_url("/admin/user/{}".format(user_id))
            user_data = {"userStatus": 3}
            # 删除用户
            requests.post(sym_talk_user_url, data=user_data, headers=headers)
        else:
            password = user_id_dict.get(user_id)
            # 拼接API路径
            change_passwd_url = full_url("/admin/user/{}".format(user_id))
            user_data = {"userPassword": password}
            resp = requests.post(change_passwd_url, data=user_data, headers=headers)
            # 获取返回信息
            message = resp.reason
            if message != "OK":
                return "同步用户论坛用户出错！"
    return
