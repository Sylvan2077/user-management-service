from pydantic import BaseModel, Field

from src.common.status_code import StatusCode


class BaseResponse(BaseModel):
    msg: str = Field(example="成功", title="返回结果")
    code: int = Field(example=200, title="自定义状态码")
    data: dict = Field(example={"foo": "bar"}, title="返回数据")

    def __init__(self, code: int = 200, msg: str = "", data=None):
        if data is None:
            data = {}
        super().__init__(code=code, msg=msg, data=data)
        self.code = code
        self.msg = msg
        self.data = data

    @staticmethod
    def success(status_code: StatusCode = StatusCode.SUCCESS, data: dict = None):
        if data is None:
            data = {}
        return BaseResponse(status_code.code, status_code.msg, data)

    @staticmethod
    def failed(status_code: StatusCode = StatusCode.FAILURE, data: dict = None):
        if data is None:
            data = {}
        return BaseResponse(status_code.code, status_code.msg, data)
