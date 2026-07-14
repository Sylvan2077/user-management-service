#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import sys
import json
import subprocess
import random
from http.server import HTTPServer, BaseHTTPRequestHandler

def is_uid_exists(uid):
    try:
        result = subprocess.run(['id', '-u', str(uid)], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False

def rand_str(length: int = 8):
    """
    生成随机字符串
    :param length: 随机字符串长度,默认8
    :return: random_list
    """

    base_char = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    base_number = "1234567890"

    random_list = [
        random.choices(base_char.upper() + base_char + base_number)[0]
        for _ in range(length)
    ]
    return "".join(random_list)

def create_user(username, uid):
    home_dir = f'/data/home/{username}'
    # 创建文件管理系统用户文件夹
    user_data = os.path.join(home_dir)
    if os.path.exists(user_data):
        shutil.rmtree(user_data)
    print("创建文件管理系统用户文件夹:{}".format(user_data))
    os.makedirs(user_data)
    subprocess.run("chown -R {0}:{0} {1}".format(username, user_data), shell=True)

    cmd = ['useradd', '-d', home_dir, '-m', '-u', str(uid), username]
    try:
        exist_user = "id {}".format(username)
        return_code = subprocess.call(exist_user, shell=True)
        if return_code != 0:
            # 生成随机系统密码
            rand_passwd = rand_str(8)
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            subprocess.run(
                "echo {} | passwd --stdin {}".format(rand_passwd, username), shell=True
            )
        if result.returncode == 0:
            return True, f'User {username} created successfully'
        else:
            return False, result.stderr.strip()
    except Exception as e:
        return False, str(e)

class CreateUserHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)
            
            username = data.get('username')
            uid = data.get('uid')
            
            if not username or uid is None:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'message': 'Missing username or uid parameter'
                }).encode('utf-8'))
                return
            
            if is_uid_exists(uid):
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'message': f'UID {uid} is already in use'
                }).encode('utf-8'))
                return
            
            success, message = create_user(username, uid)
            
            if success:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': True,
                    'message': message
                }).encode('utf-8'))
            else:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'message': f'Failed to create user: {message}'
                }).encode('utf-8'))
                
        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'message': 'Invalid JSON format'
            }).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'message': str(e)
            }).encode('utf-8'))
    
    def log_message(self, format, *args):
        pass

def main():
    if len(sys.argv) != 2:
        print('Usage: python create_user.py <port>')
        sys.exit(1)
    
    port = int(sys.argv[1])
    server_address = ('', port)
    httpd = HTTPServer(server_address, CreateUserHandler)
    
    print(f'Starting create_user HTTP server on port {port}...')
    print('Note: This script requires root privileges to create users')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\nServer stopped.')
        httpd.server_close()

if __name__ == '__main__':
    main()