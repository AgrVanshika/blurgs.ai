import asyncio
import websockets
import json
from datetime import datetime, timedelta
import time
from typing import Dict, List
from .ais_simulator import AISSimulator

class PlaybackService:
    def __init__(self, port: int = 8765):
        """Initialize the playback service."""
        self.port = port
        self.simulators: Dict[str, AISSimulator] = {}
        self.speed_factor = 5.0  # Default to 5x speed
        self.interval = 5  # 5 seconds between messages
        self.connected_clients = set()
        self.start_time = None
        self.message_count = 0
        self.batch_size = 10  # Process messages in batches
        self.message_queue = asyncio.Queue()

    def add_vessel(self, mmsi: str, speed_knots: float = 15.0):
        """Add a vessel to the simulation."""
        try:
            simulator = AISSimulator(mmsi=mmsi, speed_knots=speed_knots)
            start_port, end_port = simulator.start_new_voyage()
            self.simulators[mmsi] = simulator
            
            print(f"\nAdded vessel {mmsi}:")
            print(f"  Speed: {speed_knots} knots")
            print(f"  Route: {start_port['port_name']} → {end_port['port_name']}")
            print(f"  Distance: {simulator.total_distance:.2f} nautical miles")
            print(f"  Estimated duration: {simulator.total_distance / speed_knots:.2f} hours")
            
            return start_port, end_port
        except Exception as e:
            print(f"Error adding vessel {mmsi}: {e}")
            raise

    async def broadcast_message(self, message: Dict):
        """Broadcast a message to all connected clients."""
        if not self.connected_clients:
            return
        
        try:
            message_str = json.dumps(message)
            websockets.broadcast(self.connected_clients, message_str)
            self.message_count += 1
            
            # Print statistics every 100 messages
            if self.message_count % 100 == 0:
                elapsed = (datetime.utcnow() - self.start_time).total_seconds()
                print(f"\nSimulation Statistics:")
                print(f"  Messages sent: {self.message_count}")
                print(f"  Active vessels: {len(self.simulators)}")
                print(f"  Runtime: {elapsed/60:.1f} minutes")
                print(f"  Speed factor: {self.speed_factor}x")
                print(f"  Messages per second: {self.message_count/elapsed:.1f}")
        except Exception as e:
            print(f"Error broadcasting message: {e}")

    async def generate_messages(self):
        """Generate and broadcast AIS messages for all vessels."""
        self.start_time = datetime.utcnow()
        print("\nStarting message generation...")
        
        while True:
            current_time = datetime.utcnow()
            messages = []
            
            # Generate messages for each vessel
            for mmsi, simulator in self.simulators.items():
                try:
                    message = simulator.generate_ais_message(current_time)
                    messages.append(message)
                except Exception as e:
                    print(f"Error generating message for vessel {mmsi}: {e}")
            
            # Process messages in batches
            for i in range(0, len(messages), self.batch_size):
                batch = messages[i:i + self.batch_size]
                await asyncio.gather(*[self.broadcast_message(msg) for msg in batch])
            
            # Calculate sleep time based on speed factor
            if self.speed_factor <= 0:  # Send all messages immediately
                continue
            else:
                sleep_time = self.interval / self.speed_factor
                await asyncio.sleep(sleep_time)

    async def handle_client(self, websocket):
        """Handle WebSocket client connection."""
        self.connected_clients.add(websocket)
        print(f"\nNew client connected. Total clients: {len(self.connected_clients)}")
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    if 'command' in data:
                        await self.handle_command(data)
                except json.JSONDecodeError:
                    print(f"Invalid JSON received: {message}")
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.connected_clients.remove(websocket)
            print(f"Client disconnected. Remaining clients: {len(self.connected_clients)}")

    async def handle_command(self, data: Dict):
        """Handle client commands."""
        command = data.get('command')
        if command == 'set_speed':
            self.speed_factor = float(data.get('speed_factor', 5.0))
            print(f"\nSimulation speed changed to {self.speed_factor}x")
        elif command == 'add_vessel':
            mmsi = data.get('mmsi')
            speed = float(data.get('speed', 15.0))
            if mmsi:
                start, end = self.add_vessel(mmsi, speed)
                await self.broadcast_message({
                    'type': 'vessel_added',
                    'mmsi': mmsi,
                    'start_port': start['port_name'],
                    'end_port': end['port_name']
                })

    async def start_server(self):
        """Start the WebSocket server."""
        async with websockets.serve(self.handle_client, "localhost", self.port):
            print(f"\nWebSocket server started on ws://localhost:{self.port}")
            
            # Add initial vessel
            self.add_vessel("123456789", 15.0)
            self.add_vessel("123456790", 17.0)
            
            # Start message generation
            await self.generate_messages()

if __name__ == "__main__":
    service = PlaybackService()
    asyncio.run(service.start_server())