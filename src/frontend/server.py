from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import websockets
import asyncio
import json
from pathlib import Path

class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        return super().end_headers()

    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'
        return super().do_GET()

async def websocket_handler(websocket, path):
    try:
        async with websockets.connect('ws://localhost:8766') as ws:
            async def forward_messages():
                while True:
                    try:
                        message = await ws.recv()
                        await websocket.send(message)
                    except websockets.exceptions.ConnectionClosed:
                        break

            async def forward_commands():
                while True:
                    try:
                        command = await websocket.recv()
                        await ws.send(command)
                    except websockets.exceptions.ConnectionClosed:
                        break

            await asyncio.gather(
                forward_messages(),
                forward_commands()
            )
    except Exception as e:
        print(f"WebSocket error: {e}")

def run(server_class=HTTPServer, handler_class=CORSRequestHandler, port=8000):
    # Change to the frontend directory
    frontend_dir = Path(__file__).parent
    os.chdir(frontend_dir)
    
    # Start HTTP server
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting frontend server on http://localhost:{port}")
    
    # Start WebSocket server
    start_server = websockets.serve(websocket_handler, 'localhost', 8001)
    asyncio.get_event_loop().run_until_complete(start_server)
    print(f"WebSocket proxy started on ws://localhost:8001")
    
    # Run both servers
    asyncio.get_event_loop().run_until_complete(httpd.serve_forever())

if __name__ == '__main__':
    run() 