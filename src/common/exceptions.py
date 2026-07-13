from src.common.status_code import StatusCode


class ApiException(Exception):
    status_code: StatusCode

    def __init__(self, status_code: StatusCode = StatusCode.FAILURE):
        self.status_code = status_code


class TaskException(Exception):
    msg: str

    def __init__(self, msg: str):
        self.msg = msg
