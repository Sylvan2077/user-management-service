#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import random
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler

def get_max_uid():
    try:
        result = subprocess.run(
            ['awk', '-F:', '{print $3}', '/etc/passwd'],
            capture_output=True, text=True
        )
        uids = [int(line.strip()) for line in result.stdout.split('\n') if line.strip().isdigit()]
        if uids:
            return max(uids)
        return 1000
    except Exception as e:
        return 1000

def find_available_uid():
    min_uid = 1100
    max_uid = get_max_uid()
    
    if max_uid < min_uid:
        return None
    
    uids = list(range(min_uid, max_uid + 1))
    random.shuffle(uids)
    
    for uid in uids:
        result = subprocess.run(['id', '-u', str(uid)], capture_output=True)
        if result.returncode != 0:
            return uid
    return None

def execute_script(script_path, *args):
    try:
        result = subprocess.run(
            ['bash', script_path] + list(args),
            capture_output=True, text=True
        )
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"success": False, "message": result.stderr.strip() or "脚本执行失败"}
    except Exception as e:
        return {"success": False, "message": str(e)}

class CreateUserHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(body)
            
            username = data.get('username')
            mode = data.get('mode')
            
            if not username or not mode:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'message': 'Missing username or mode parameter'
                }).encode('utf-8'))
                return
            
            script_dir = os.path.dirname(os.path.abspath(__file__))
            
            if mode == 'create':
                uid = find_available_uid()
                if uid is None:
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'success': False,
                        'message': 'No available UID found'
                    }).encode('utf-8'))
                    return
                
                script_path = os.path.join(script_dir, 'user_create.sh')
                result = execute_script(script_path, username, str(uid))
                
            elif mode == 'del':
                script_path = os.path.join(script_dir, 'user_del.sh')
                result = execute_script(script_path, username)
                
            else:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': False,
                    'message': f'Invalid mode: {mode}. Use "create" or "del".'
                }).encode('utf-8'))
                return
            
            if result.get('success'):
                self.send_response(200)
            else:
                self.send_response(500)
            
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode('utf-8'))
                
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
    print('Note: This script requires root privileges to create/delete users')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\nServer stopped.')
        httpd.server_close()

if __name__ == '__main__':
    main()