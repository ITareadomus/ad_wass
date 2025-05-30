
#!/usr/bin/env python3
import json
import subprocess
import sys
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import time

class CustomHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()
    
    def do_POST(self):
        if self.path == '/run-script':
            self.handle_run_script()
        elif self.path == '/save-selection':
            self.handle_save_selection()
        else:
            self.send_response(404)
            self.end_headers()
    
    def handle_run_script(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            script_name = data.get('script')
            if not script_name:
                self.send_json_response({'success': False, 'error': 'Nome script mancante'})
                return
            
            # Costruisci il percorso dello script
            if script_name == 'cleaner_list.py':
                script_path = os.path.join('SELEZIONI_SERA', 'cleaner_list.py')
            elif script_name == 'cleaner_selection.py':
                script_path = os.path.join('SELEZIONI_SERA', 'cleaner_selection.py')
            else:
                self.send_json_response({'success': False, 'error': 'Script non riconosciuto'})
                return
            
            if not os.path.exists(script_path):
                self.send_json_response({'success': False, 'error': f'Script {script_path} non trovato'})
                return
            
            # Esegui lo script
            try:
                result = subprocess.run([sys.executable, script_path], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=60,
                                      cwd=os.getcwd())
                
                if result.returncode == 0:
                    self.send_json_response({'success': True, 'output': result.stdout})
                else:
                    self.send_json_response({'success': False, 'error': result.stderr or 'Errore sconosciuto'})
            
            except subprocess.TimeoutExpired:
                self.send_json_response({'success': False, 'error': 'Script timeout (>60s)'})
            except Exception as e:
                self.send_json_response({'success': False, 'error': str(e)})
                
        except Exception as e:
            self.send_json_response({'success': False, 'error': f'Errore parsing richiesta: {str(e)}'})
    
    def handle_save_selection(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # Salva nel file sel_cleaners.json
            with open('sel_cleaners.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            
            self.send_json_response({'success': True})
            
        except Exception as e:
            self.send_json_response({'success': False, 'error': str(e)})
    
    def send_json_response(self, data):
        response = json.dumps(data)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))

def run_server():
    server_address = ('0.0.0.0', 5000)
    httpd = HTTPServer(server_address, CustomHandler)
    print(f"Server in esecuzione su http://0.0.0.0:5000")
    print("Aprire cleaner_selector.html nel browser")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()
