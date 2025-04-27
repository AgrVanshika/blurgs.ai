import asyncio
import websockets
import json
import sys
from datetime import datetime

async def test_client():
    uri = "ws://localhost:8765"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket server")
            
            # Add a test vessel
            add_vessel_msg = {
                "command": "add_vessel",
                "mmsi": "123456789",
                "speed": 15.0
            }
            await websocket.send(json.dumps(add_vessel_msg))
            print("Added test vessel")
            
            # Set simulation speed
            set_speed_msg = {
                "command": "set_speed",
                "speed": 1.0
            }
            await websocket.send(json.dumps(set_speed_msg))
            print("Set simulation speed to 1.0")
            
            # Listen for messages
            print("Listening for vessel updates...")
            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)
                    
                    if "type" in data:
                        if data["type"] == "vessel_added":
                            print(f"\nVessel added: MMSI {data['mmsi']}")
                            print(f"Route: {data['start_port']['port_name']} -> {data['end_port']['port_name']}")
                        elif data["type"] == "speed_updated":
                            print(f"\nSimulation speed updated to: {data['speed']}")
                        elif "decoded" in data:
                            pos = data["decoded"]
                            print(f"\rVessel {data['mmsi']}: "
                                  f"Lat: {pos['latitude']:.4f}, "
                                  f"Lon: {pos['longitude']:.4f}, "
                                  f"Speed: {pos['speed']:.1f} knots, "
                                  f"Course: {pos['course']:.1f}°", end="")
                            sys.stdout.flush()
                            
                except websockets.exceptions.ConnectionClosed:
                    print("\nConnection closed by server")
                    break
                except Exception as e:
                    print(f"\nError: {e}")
                    break
                    
    except Exception as e:
        print(f"Failed to connect to server: {e}")

if __name__ == "__main__":
    asyncio.run(test_client()) 