from src.common.temp_cache import TempCache
from src.common.utils import encode_passwd
from src.config import config
from src.service.module.fb_user_manager import generate_request_headers as fb_login
from src.service.module.sym_talk_manager import generate_request_headers as sym_login
from src.service.module.user_operations import (
    user_register,
    modify_user_info,
    user_change_passwd,
    delete_user,
    update_user,
)

# 读取配置文件
settings = config.Settings()
# 读取缓存文件
cache = TempCache()


class UserManager:
    """
    处理产品线上试用平台关联服务用户相关操作
    """

    def login(self, params):
        """
        登录关联服务管理员帐号
        """

        server_data = {
            "allow_users_forums": params.allow_users_forums,
            "allow_users_file_browser": params.allow_users_file_browser,
            "allow_vpn_server": params.allow_vpn_server,
            "sym_talk_username": params.sym_talk_username,
            "sym_talk_password": params.sym_talk_password,
            "filebrowser_username": params.filebrowser_username,
            "filebrowser_password": params.filebrowser_password,
        }
        # 获取各服务管理员账户配置
        if params.allow_users_forums:
            sym_talk_password = encode_passwd(params.sym_talk_password)
            server_data["sym_talk_password"] = sym_talk_password
            # 尝试登录密码是否正确
            _, message = sym_login(
                params.sym_talk_username,
                params.sym_talk_password,
            )
            if message:
                return message
        else:
            server_data["sym_talk_username"] = ""
            server_data["sym_talk_password"] = ""
        if params.allow_users_file_browser:
            filebrowser_password = encode_passwd(params.filebrowser_password)
            server_data["filebrowser_password"] = filebrowser_password
            # 尝试登录密码是否正确
            _, message = fb_login(
                params.filebrowser_username,
                params.filebrowser_password,
            )
            if message:
                return message
        else:
            server_data["filebrowser_username"] = ""
            server_data["filebrowser_password"] = ""
        cache.set("server_info", server_data)
        return

    def register(self, form_data):
        """
        注册用户
        """

        user_name = form_data.user_name
        user_passwd = form_data.user_passwd
        msg = user_register(user_name, user_passwd)
        return msg

    def modify_user_info(self, form_data):
        """
        修改用户信息
        """

        pre_username = form_data.pre_username
        username = form_data.username
        new_password = form_data.new_password
        msg = modify_user_info(pre_username, username, new_password)
        return msg

    def user_change_passwd(self, form_data):
        """
        用户修改密码
        """

        username = form_data.username
        new_password = form_data.new_password
        old_password = form_data.old_password
        is_fb_superadmin = form_data.is_fb_superadmin
        msg = user_change_passwd(username, new_password, old_password, is_fb_superadmin)
        return msg

    def delete_user(self, names):
        """
        删除用户
        """

        data = delete_user(names)
        return data

    def update_user(self, form_data):
        """
        同步用户
        """

        data = update_user(form_data)
        return data
