# FastAPI User Management Service
FastAPI User Management Service是使用FastAPI为产品线上试用平台构建的用户管理服务，包括文件管理系统、用户论坛以及VPN用户的注册、修改、删除等操作。
## 安装
使用以下命令安装项目及其依赖：
```bash
pip install -r requirements.txt


## 快速开始

运行以下命令启动 FastAPI 服务器

uvicorn main:app --reload

API 将在 http://localhost:9000 上运行

## API 文档

Swagger 文档: http://localhost:9000/docs
ReDoc 文档: http://localhost:9000/redoc

## 示例
TODO
```
## 配置项
本服务需要的基本配置如下：
1. vpn_config_file_path：VPN配置文件路径
2. file_browser_data_dir：文件管理系统的用户目录