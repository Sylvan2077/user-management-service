#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import random
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler

def get_max_uid():
    print("[DEBUG] 开始获取系统最大UID...")
    try:
        result = subprocess.run(
            ['awk', '-F:', '{print $3}', '/etc/passwd'],
            capture_output=True, text=True
        )
        uids = [int(line.strip()) for line in result.stdout.split('\n') if line.strip().isdigit()]
        if uids:
            max_uid = max(uids)
            print(f"[DEBUG] 成功获取系统最大UID: {max_uid}")
            return max_uid
        print("[DEBUG] 未找到UID，使用默认值1000")
        return 1000
    except Exception as e:
        print(f"[ERROR] 获取最大UID失败: {e}")
        return 1000

def find_available_uid():
    min_uid = 1100
    max_uid = get_max_uid()
    print(f"[DEBUG] UID搜索范围: min={min_uid}, max={max_uid}")
    
    if max_uid < min_uid:
        print(f"[DEBUG] 最大UID({max_uid})小于最小UID({min_uid})，从{min_uid}开始顺序查找")
    else:
        uids = list(range(min_uid, max_uid + 1))
        print(f"[DEBUG] 生成UID列表，共{len(uids)}个候选UID")
        random.shuffle(uids)
        print(f"[DEBUG] 随机打乱UID顺序，开始遍历查找可用UID...")
        
        for uid in uids:
            result = subprocess.run(['id', '-u', str(uid)], capture_output=True)
            if result.returncode != 0:
                print(f"[DEBUG] 找到可用UID: {uid}")
                return uid
        print(f"[DEBUG] 在{min_uid}-{max_uid}范围内未找到可用UID")
    
    print(f"[DEBUG] 从{min_uid}开始向上顺序查找可用UID...")
    uid = min_uid
    while uid < 65535:
        result = subprocess.run(['id', '-u', str(uid)], capture_output=True)
        if result.returncode != 0:
            print(f"[DEBUG] 找到可用UID: {uid}")
            return uid
        uid += 1
    
    print("[ERROR] 未找到可用UID（已达最大限制65535）")
    return None

def execute_script(script_path, *args):
    print(f"[DEBUG] 准备执行脚本: {script_path}")
    print(f"[DEBUG] 脚本参数: {args}")
    try:
        result = subprocess.run(
            ['bash', script_path] + list(args),
            capture_output=True, text=True
        )
        print(f"[DEBUG] 脚本执行完成，返回码: {result.returncode}")
        print(f"[DEBUG] 脚本输出: {result.stdout.strip()}")
        if result.stderr:
            print(f"[DEBUG] 脚本错误输出: {result.stderr.strip()}")
        
        try:
            response = json.loads(result.stdout)
            print(f"[DEBUG] 解析脚本JSON响应成功")
            return response
        except json.JSONDecodeError:
            print(f"[WARN] 脚本输出不是有效JSON格式")
            return {"success": False, "message": result.stderr.strip() or "脚本执行失败"}
    except Exception as e:
        print(f"[ERROR] 执行脚本失败: {e}")
        return {"success": False, "message": str(e)}

class CreateUserHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        print("\n" + "="*50)
        print("[REQUEST] 收到新的HTTP POST请求")
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            print(f"[DEBUG] 请求内容长度: {content_length}")
            
            body = self.rfile.read(content_length).decode('utf-8')
            print(f"[DEBUG] 请求体内容: {body}")
            
            data = json.loads(body)
            print(f"[DEBUG] 解析JSON成功")
            
            username = data.get('username')
            mode = data.get('mode')
            print(f"[DEBUG] 提取参数: username={username}, mode={mode}")
            
            if not username or not mode:
                print("[ERROR] 参数缺失: username或mode为空")
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'message': 'Missing username or mode parameter'
                }).encode('utf-8'))
                return
            
            script_dir = os.path.dirname(os.path.abspath(__file__))
            print(f"[DEBUG] 脚本目录: {script_dir}")
            
            if mode == 'create':
                print("[DEBUG] 模式: 创建用户")
                uid = find_available_uid()
                print(f"[DEBUG] 获取到可用UID: {uid}")
                
                if uid is None:
                    print("[ERROR] 未找到可用UID")
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'success': False,
                        'message': 'No available UID found'
                    }).encode('utf-8'))
                    return
                
                script_path = os.path.join(script_dir, 'user_create.sh')
                print(f"[DEBUG] 用户创建脚本路径: {script_path}")
                result = execute_script(script_path, username, str(uid))
                
            elif mode == 'del':
                print("[DEBUG] 模式: 删除用户")
                script_path = os.path.join(script_dir, 'user_del.sh')
                print(f"[DEBUG] 用户删除脚本路径: {script_path}")
                result = execute_script(script_path, username)
                
            else:
                print(f"[ERROR] 无效模式: {mode}")
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'message': f'Invalid mode: {mode}. Use "create" or "del".'
                }).encode('utf-8'))
                return
            
            if result.get('success'):
                print(f"[SUCCESS] 操作成功: {result.get('message')}")
                self.send_response(200)
            else:
                print(f"[FAILURE] 操作失败: {result.get('message')}")
                self.send_response(500)
            
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response_json = json.dumps(result)
            print(f"[DEBUG] 发送响应: {response_json}")
            self.wfile.write(response_json.encode('utf-8'))
                
        except json.JSONDecodeError as e:
            print(f"[ERROR] JSON解析失败: {e}")
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'message': 'Invalid JSON format'
            }).encode('utf-8'))
        except Exception as e:
            print(f"[ERROR] 请求处理异常: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'success': False,
                'message': str(e)
            }).encode('utf-8'))
        print("[REQUEST] 请求处理完成")
        print("="*50 + "\n")
    
    def log_message(self, format, *args):
        pass

def main():
    if len(sys.argv) != 2:
        print("Usage: python user_manage.py <port>")
        sys.exit(1)
    
    port = int(sys.argv[1])
    server_address = ('', port)
    httpd = HTTPServer(server_address, CreateUserHandler)
    
    print(f"\n[INFO] 启动用户管理HTTP服务")
    print(f"[INFO] 监听地址: 0.0.0.0:{port}")
    print(f"[INFO] 服务进程ID: {os.getpid()}")
    print(f"[INFO] 需要root权限才能创建/删除用户")
    print(f"[INFO] 按 Ctrl+C 停止服务\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[INFO] 收到停止信号，正在关闭服务...")
        httpd.server_close()
        print("[INFO] 服务已停止")

if __name__ == '__main__':
    main()