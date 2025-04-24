import asyncio
import websockets
import json
from datetime import datetime, timedelta
import time
from typing import Dict, List
from ais_simulator import AISSimulator

class PlaybackService:
    def __init__(self, port: int = 8765):
        """Initialize the playback service."""
        self.port = port
        self.simulators: Dict[str, AISSimulator] = {}
        self.speed_factor = 1.0
        self.interval = 300  # 5 minutes in seconds
        self.connected_clients = set()

    def add_vessel(self, mmsi: str, speed_knots: float = 15.0):
        """Add a vessel to the simulation."""
        simulator = AISSimulator(mmsi=mmsi, speed_knots=speed_knots)
        self.simulators[mmsi] = simulator
        return simulator.start_new_voyage()

    async def broadcast_message(self, message: Dict):
        """Broadcast a message to all connected clients."""
        if not self.connected_clients:
            return
        
        websockets.broadcast(self.connected_clients, json.dumps(message))

    async def generate_messages(self):
        """Generate and broadcast AIS messages for all vessels."""
        start_time = datetime.utcnow()
        
        while True:
            current_time = datetime.utcnow()
            elapsed = (current_time - start_time).total_seconds()
            
            # Generate messages for each vessel
            for mmsi, simulator in self.simulators.items():
                try:
                    message = simulator.generate_ais_message(current_time)
                    await self.broadcast_message(message)
                except Exception as e:
                    print(f"Error generating message for vessel {mmsi}: {e}")
            
            # Calculate sleep time based on speed factor
            if self.speed_factor <= 0:  # Send all messages immediately
                continue
            else:
                sleep_time = self.interval / self.speed_factor
                await asyncio.sleep(sleep_time)

    async def handle_client(self, websocket):
        """Handle WebSocket client connection."""
        self.connected_clients.add(websocket)
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    if 'command' in data:
                        await self.handle_command(data)
                except json.JSONDecodeError:
                    print(f"Invalid JSON received: {message}")
        finally:
            self.connected_clients.remove(websocket)

    async def handle_command(self, data: Dict):
        """Handle client commands."""
        command = data.get('command')
        if command == 'set_speed':
            self.speed_factor = float(data.get('speed_factor', 1.0))
        elif command == 'add_vessel':
            mmsi = data.get('mmsi')
            speed = float(data.get('speed', 15.0))
            if mmsi:
                start, end = self.add_vessel(mmsi, speed)
                await self.broadcast_message({
                    'type': 'voyage_start',
                    'mmsi': mmsi,
                    'start_port': start['port_name'],
                    'end_port': end['port_name']
                })

    async def start_server(self):
        """Start the WebSocket server."""
        async with websockets.serve(self.handle_client, "localhost", self.port):
            print(f"WebSocket server started on ws://localhost:{self.port}")
            
            # Add a test vessel
            self.add_vessel("123456789", 15.0)
            
            # Start message generation
            await self.generate_messages()

if __name__ == "__main__":
    service = PlaybackService()
    asyncio.run(service.start_server()) 