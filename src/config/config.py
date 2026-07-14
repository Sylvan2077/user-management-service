import os
import json


class Settings:
    def __init__(self):
        host_port = os.environ.get("USER_MANAGEMENT_HOST", "http://0.0.0.0:9000")
        self.host = host_port.split(":")[1].strip("/")
        self.port = int(host_port.split(":")[2])
        self.vpn_config_file_path = os.environ.get(
            "VPN_CONFIG_FILE_PATH", "/opt/scns_apps_platform/thirdparty/user-passwd"
        )
        self.file_browser_data_dir = os.environ.get("FILE_BROWSER_DATA_DIR", "/public_files_dir")
        self.file_browser_host = os.environ.get(
            "FILE_BROWSER_HOST", "http://0.0.0.0:8088"
        )
        self.sym_talk_host = os.environ.get(
            "SYM_TALK_HOST", "http://0.0.0.0:8080"
        )
        nodes_env = os.environ.get("SYSTEM_USER_NODES", '[{"ip": "127.0.0.1", "port": 8888}]')
        try:
            self.system_user_nodes = json.loads(nodes_env)
        except json.JSONDecodeError:
            self.system_user_nodes = [{"ip": "127.0.0.1", "port": 8888}]