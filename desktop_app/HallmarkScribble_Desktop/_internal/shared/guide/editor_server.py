"""
Simple HTTP server to handle HTML editor save requests
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import base64
import threading

class EditorHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Serve image files
        if self.path.startswith('/image/'):
            try:
                # Extract filepath from URL and decode it
                from urllib.parse import unquote
                filepath = self.path[7:]  # Remove '/image/'
                filepath = unquote(filepath)  # Decode URL encoding
                filepath = filepath.replace('/', os.sep)
                
                if os.path.exists(filepath):
                    with open(filepath, 'rb') as f:
                        img_data = f.read()
                    
                    self.send_response(200)
                    self.send_header('Content-Type', 'image/png')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(img_data)
                else:
                    self.send_response(404)
                    self.end_headers()
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                print(f"Error serving image: {e}")
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        
        # Enable CORS
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        try:
            if self.path == '/save_image':
                # Save annotated image
                scribble_dir = data['scribbleDir']
                filename = data['filename']
                data_url = data['dataURL']
                
                # Convert data URL to image
                img_data = data_url.split(',')[1]
                img_bytes = base64.b64decode(img_data)
                
                # Save to file
                filepath = os.path.join(scribble_dir, filename)
                with open(filepath, 'wb') as f:
                    f.write(img_bytes)
                
                response = {'success': True}
                
            elif self.path == '/save_changes':
                # Save transcript and notes
                scribble_dir = data['scribbleDir']
                transcript = data['transcript']
                notes = data['notes']
                
                # Save transcript
                transcript_path = os.path.join(scribble_dir, 'transcript.txt')
                with open(transcript_path, 'w', encoding='utf-8') as f:
                    f.write(transcript)
                
                # Save notes to a JSON file
                notes_path = os.path.join(scribble_dir, 'editor_notes.json')
                with open(notes_path, 'w', encoding='utf-8') as f:
                    json.dump(notes, f, indent=2)
                
                response = {'success': True}
            else:
                response = {'success': False, 'error': 'Unknown endpoint'}
                
        except Exception as e:
            response = {'success': False, 'error': str(e)}
        
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def do_OPTIONS(self):
        # Handle CORS preflight
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress log messages
        pass

server = None
server_thread = None

def start_editor_server(port=8765):
    """Start the editor HTTP server in a background thread"""
    global server, server_thread
    
    if server is not None:
        return  # Already running
    
    try:
        server = HTTPServer(('localhost', port), EditorHandler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        print(f"Editor server started on port {port}")
    except OSError as e:
        if "address already in use" in str(e).lower():
            print(f"Editor server already running on port {port}")
        else:
            raise

def stop_editor_server():
    """Stop the editor HTTP server"""
    global server
    if server is not None:
        server.shutdown()
        server = None
        print("Editor server stopped")
