import json
import os
from json import JSONDecodeError

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


class TempCache:
    def __init__(self, cache_name: str = "cache.json"):
        # 缓存文件保存在自己的工作目录中
        self.cache_file_path = os.path.join(BASE_DIR, cache_name)
        self.cache = self.load_cache_from_file()

    def set(self, key, value):
        # 保存缓存信息
        self.cache[key] = value
        self.save_cache_to_file()

    def get(self, key):
        # 获取缓存信息
        self.cache = self.load_cache_from_file()
        return self.cache.get(key)

    def delete(self, key):
        # 删除缓存信息
        self.cache = self.load_cache_from_file()
        if key in self.cache:
            del self.cache[key]
            self.save_cache_to_file()

    def save_cache_to_file(self):
        # 保存缓存信息
        with open(self.cache_file_path, "w") as file:
            json.dump(self.cache, file)

    def load_cache_from_file(self):
        # 读取缓存信息
        try:
            with open(self.cache_file_path, "r") as file:
                return json.load(file)
        except (FileNotFoundError, JSONDecodeError):
            return {}
