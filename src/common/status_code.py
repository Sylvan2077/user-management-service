from enum import Enum


class StatusCode(Enum):
    SUCCESS = (21101, "请求成功")
    FAILURE = (51101, "请求异常")

    @property
    def code(self):
        return self.value[0]

    @property
    def msg(self):
        return self.value[1]
