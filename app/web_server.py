#!/usr/bin/env python3
import json
import subprocess
import sys
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import time
from datetime import datetime, timedelta

class CustomHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        if self.path == '/':
            self.path = '/static/convocazioni.html'
        elif self.path == '/convocazioni' or self.path == '/convocazioni.html':
            self.path = '/static/convocazioni.html'
        elif self.path == '/assegnazioni' or self.path == '/assegnazioni.html':
            self.path = '/static/assegnazioni.html'
        elif self.path == '/styles.css':
            self.path = '/static/styles.css'
        elif self.path.startswith('/get-cleaners-by-date'):
            self.handle_get_cleaners_by_date()
            return
        elif self.path.startswith('/static/'):
            # Serve files from static directory
            pass
        elif self.path.endswith('.json'):
            # Serve JSON files from data directory
            if not self.path.startswith('/data/'):
                self.path = '/data' + self.path

        return super().do_GET()

    def do_POST(self):
        if self.path == '/run-script':
            self.handle_run_script()
        elif self.path == '/save-selection':
            self.handle_save_selection()
        elif self.path == '/get-assignments':
            self.handle_get_assignments()
        else:
            self.send_response(404)
            self.end_headers()

    def handle_run_script(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            script_name = data.get('script')
            percentage = data.get('percentage')  # Nuovo parametro per la percentuale
            selected_date = data.get('date', '')  # Data selezionata

            if not script_name:
                self.send_json_response({'success': False, 'error': 'Nome script mancante'})
                return

            # Costruisci il percorso dello script nella cartella scripts
            if script_name == 'cleaner_list.py':
                script_path = 'scripts/cleaner_list.py'
            elif script_name == 'cleaner_selection.py':
                script_path = 'scripts/cleaner_selection.py'
            elif script_name == 'algoritmo.py':
                script_path = 'scripts/algoritmo.py'
            elif script_name == 'gmaps.py':
                script_path = 'scripts/gmaps.py'
            elif script_name == 'gpt_assignments.py':
                script_path = 'scripts/gpt_assignments.py'
            elif script_name == 'route_optimizer.py':
                script_path = 'scripts/route_optimizer.py'
            elif script_name == 'task_selection.py':
                script_path = 'scripts/task_selection.py'
            else:
                self.send_json_response({'success': False, 'error': 'Script non riconosciuto'})
                return

            if not os.path.exists(script_path):
                self.send_json_response({'success': False, 'error': f'Script {script_path} non trovato'})
                return

            # Esegui lo script
            try:
                # Prepara il comando con la percentuale e data se fornite
                cmd = [sys.executable, script_path]
                if script_name == 'cleaner_selection.py':
                    cmd.append(str(percentage))
                    if selected_date:
                        cmd.append(selected_date)

                result = subprocess.run(cmd,
                                      capture_output=True,
                                      text=True,
                                      timeout=120,  # Aumentato a 120 secondi
                                      cwd=os.getcwd())

                if result.returncode == 0:
                    self.send_json_response({'success': True, 'output': result.stdout})
                else:
                    self.send_json_response({'success': False, 'error': result.stderr or 'Errore sconosciuto'})

            except subprocess.TimeoutExpired:
                self.send_json_response({'success': False, 'error': f'Script timeout (>120s): {scriptName}'})
            except Exception as e:
                self.send_json_response({'success': False, 'error': f'Errore esecuzione script {scriptName}: {str(e)}'})

        except Exception as e:
            self.send_json_response({'success': False, 'error': f'Errore parsing richiesta: {str(e)}'})

    def handle_save_selection(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            selected_date = data.get('date', '')

            # Se non viene fornita una data, usa quella di domani
            if not selected_date:
                tomorrow = datetime.now() + timedelta(days=1)
                selected_date = tomorrow.strftime("%Y-%m-%d")

            # Carica i dati esistenti o crea una struttura vuota
            try:
                with open('data/sel_cleaners.json', 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                existing_data = {"dates": {}}

            # Assicurati che la struttura contenga la chiave "dates"
            if "dates" not in existing_data:
                existing_data = {"dates": {}}

            # Aggiorna i dati per la data specifica
            existing_data["dates"][selected_date] = data

            with open('data/sel_cleaners.json', 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=4, ensure_ascii=False)

            self.send_json_response({'success': True})

        except Exception as e:
            self.send_json_response({'success': False, 'error': str(e)})

    def handle_get_assignments(self):
        try:
            # Carica le assegnazioni dal file JSON se esiste
            assignments_file = 'data/assignments.json'
            if os.path.exists(assignments_file):
                with open(assignments_file, 'r', encoding='utf-8') as f:
                    assignments_data = json.load(f)
                    # Forza refresh del file
                    print(f"Caricato assignments.json con timestamp: {assignments_data.get('timestamp', 'N/A')}")
                self.send_json_response({'success': True, 'assignments': assignments_data})
            else:
                self.send_json_response({'success': False, 'error': 'File data/assignments.json non trovato'})
        except Exception as e:
            self.send_json_response({'success': False, 'error': str(e)})

    def handle_get_cleaners_by_date(self):
        try:
            # Estrai la data dal query parameter
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            selected_date = query_params.get('date', [None])[0]

            if not selected_date:
                self.send_json_response({'success': False, 'error': 'Data mancante'})
                return

            # Carica i dati dal file sel_cleaners.json
            sel_cleaners_file = 'data/sel_cleaners.json'
            if os.path.exists(sel_cleaners_file):
                with open(sel_cleaners_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Controlla se esiste la struttura "dates"
                if "dates" in data and selected_date in data["dates"]:
                    date_data = data["dates"][selected_date]
                    cleaners = date_data.get("cleaners", [])
                    self.send_json_response({
                        'success': True, 
                        'cleaners': cleaners,
                        'date_data': date_data
                    })
                else:
                    # Nessun cleaner trovato per questa data
                    self.send_json_response({
                        'success': True, 
                        'cleaners': [],
                        'date_data': None
                    })
            else:
                # File non trovato
                self.send_json_response({
                    'success': True, 
                    'cleaners': [],
                    'date_data': None
                })

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