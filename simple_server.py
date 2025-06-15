#!/usr/bin/env python3
"""
Simple HTTP server to serve sample documents for testing
"""
import http.server
import socketserver
import os
import threading
import time

PORT = 8000

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def start_server():
    """Start the HTTP server in a separate thread"""
    with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
        print(f"Serving sample documents at http://localhost:{PORT}")
        print(f"Sample document URL: http://localhost:{PORT}/sample_document.txt")
        httpd.serve_forever()

def run_server_background():
    """Run server in background thread"""
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    return server_thread

if __name__ == "__main__":
    start_server() 