import asyncio
import websockets
import json
from typing import Set
from ..simulation.playback_service import PlaybackService

class WebSocketServer:
    def __init__(self, host: str = "localhost", port: int = 8766):
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.playback_service = PlaybackService(port=port)

    async def handle_client(self, websocket: websockets.WebSocketServerProtocol):
        """Handle a new WebSocket client connection."""
        self.clients.add(websocket)
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_message(websocket, data)
                except json.JSONDecodeError:
                    print(f"Invalid JSON received: {message}")
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.remove(websocket)

    async def handle_message(self, websocket: websockets.WebSocketServerProtocol, data: dict):
        """Handle incoming WebSocket messages."""
        if "command" in data:
            command = data["command"]
            if command == "add_vessel":
                mmsi = data.get("mmsi", "123456789")
                speed = data.get("speed", 15.0)
                start_port, end_port = self.playback_service.add_vessel(mmsi, speed)
                response = {
                    "type": "vessel_added",
                    "mmsi": mmsi,
                    "start_port": start_port,
                    "end_port": end_port
                }
                await websocket.send(json.dumps(response))
            elif command == "set_speed":
                speed = data.get("speed", 1.0)
                self.playback_service.speed_factor = speed
                response = {
                    "type": "speed_updated",
                    "speed": speed
                }
                await websocket.send(json.dumps(response))

    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients."""
        if not self.clients:
            return
        message_str = json.dumps(message)
        websockets.broadcast(self.clients, message_str)

    async def start(self):
        """Start the WebSocket server."""
        async with websockets.serve(self.handle_client, self.host, self.port):
            print(f"WebSocket server started on ws://{self.host}:{self.port}")
            # Add a vessel automatically when server starts
            self.playback_service.add_vessel("123456789", 15.0)
            await self.playback_service.start_server()

if __name__ == "__main__":
    service = PlaybackService(port=8766)
    asyncio.run(service.start_server()) 