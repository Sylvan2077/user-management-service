from fastapi import APIRouter

from src.common.rest_response import BaseResponse
from src.common.status_code import StatusCode
from src.config import config
from src.model.schemas import Parameters, RegisterData, ModifyData, ChangePasswdData
from src.service.user_manager_service import UserManager

# 读取配置文件
settings = config.Settings()

router = APIRouter(
    prefix="/user-manager/v1",
    tags=["user-manager"],
    responses={200: {"description": "success"}},
)

user_service = UserManager()


@router.post("/login", response_model=BaseResponse, summary="测试管理员帐号信息")
def try_login(parameters: Parameters):
    errors_msg = user_service.login(parameters)
    data = {"msg": errors_msg}
    if errors_msg:
        return BaseResponse.failed(StatusCode.FAILURE, data)
    else:
        return BaseResponse.success(StatusCode.SUCCESS)


@router.post("/register", response_model=BaseResponse, summary="注册用户")
def register(form_data: RegisterData):
    errors_msg = user_service.register(form_data)
    if errors_msg:
        data = {"msg": errors_msg}
        return BaseResponse.failed(StatusCode.FAILURE, data)
    else:
        return BaseResponse.success(StatusCode.SUCCESS)


@router.put("/modify", response_model=BaseResponse, summary="修改用户信息")
def modify_user_info(form_data: ModifyData):
    errors_msg = user_service.modify_user_info(form_data)
    if errors_msg:
        data = {"msg": errors_msg}
        return BaseResponse.failed(StatusCode.FAILURE, data)
    else:
        return BaseResponse.success(StatusCode.SUCCESS)


@router.put("/change_passwd", response_model=BaseResponse, summary="用户修改密码")
def user_change_passwd(form_data: ChangePasswdData):
    errors_msg = user_service.user_change_passwd(form_data)
    if errors_msg:
        data = {"msg": errors_msg}
        return BaseResponse.failed(StatusCode.FAILURE, data)
    else:
        return BaseResponse.success(StatusCode.SUCCESS)


@router.delete("/delete", response_model=BaseResponse, summary="删除用户")
def delete_user(names: str):
    data = user_service.delete_user(names)
    if data.get("msg"):
        return BaseResponse.failed(StatusCode.FAILURE, data)
    else:
        return BaseResponse.success(StatusCode.SUCCESS, data)


@router.put("/update", response_model=BaseResponse, summary="同步用户")
def update_user(form_data: dict):
    data = user_service.update_user(form_data)
    if data.get("msg"):
        return BaseResponse.failed(StatusCode.FAILURE, data)
    else:
        return BaseResponse.success(StatusCode.SUCCESS, data)
