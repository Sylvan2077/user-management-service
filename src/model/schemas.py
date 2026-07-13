from pydantic import BaseModel, Field


class Parameters(BaseModel):
    """
    关联服务管理员帐号信息
    """

    allow_users_forums: bool = Field(default=False, description="是否开启用户论坛服务")
    allow_users_file_browser: bool = Field(default=False, description="是否开启文件管理服务")
    allow_vpn_server: bool = Field(default=False, description="是否开启VPN服务")
    filebrowser_username: str = Field(default=None, description="文件管理服务管理员帐号")
    filebrowser_password: str = Field(default=None, description="文件管理服务管理员密码")
    sym_talk_username: str = Field(default=None, description="用户论坛服务管理员帐号")
    sym_talk_password: str = Field(default=None, description="用户论坛服务管理员密码")


class RegisterData(BaseModel):
    user_name: str
    user_passwd: str


class ModifyData(BaseModel):
    pre_username: str
    username: str
    new_password: str


class ChangePasswdData(BaseModel):
    username: str
    new_password: str
    old_password: str
    is_fb_superadmin: bool
