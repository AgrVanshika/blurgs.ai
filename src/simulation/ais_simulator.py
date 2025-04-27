import pyais
from datetime import datetime, timedelta
import numpy as np
from typing import List, Tuple, Dict
import json
from src.simulation.route_generator import RouteGenerator

class AISSimulator:
    def __init__(self, mmsi: str, speed_knots: float = 15.0):
        """Initialize an AIS simulator for a vessel."""
        # Validate MMSI
        if not str(mmsi).isdigit() or len(str(mmsi)) != 9:
            raise ValueError(f"Invalid MMSI: {mmsi}. MMSI must be 9 digits.")
        
        # Validate speed
        if speed_knots <= 0:
            raise ValueError(f"Invalid speed: {speed_knots}. Speed must be positive.")
            
        self.mmsi = mmsi
        self.speed_knots = speed_knots
        self.route_generator = RouteGenerator()
        self.current_route = None
        self.current_position_idx = 0
        self.start_time = None
        self.total_distance = 0
        self.message_count = 0
        
    def start_new_voyage(self):
        """Start a new voyage between random ports."""
        start_port, end_port = self.route_generator.select_random_ports()
        self.current_route = self.route_generator.generate_route(start_port, end_port)
        self.total_distance = self.route_generator.calculate_distance(self.current_route)
        self.current_position_idx = 0
        self.start_time = datetime.utcnow()
        self.message_count = 0
        return start_port, end_port

    def calculate_position(self, elapsed_minutes: float) -> Tuple[float, float]:
        """Calculate vessel position after elapsed time."""
        if not self.current_route:
            raise ValueError("No active voyage. Call start_new_voyage() first.")

        # Calculate progress along route based on speed and time
        distance_covered = (self.speed_knots * elapsed_minutes / 60)  # Distance in nautical miles
        progress = min(1.0, distance_covered / self.total_distance)
        
        # Find the appropriate segment
        idx = int(progress * (len(self.current_route) - 1))
        if idx >= len(self.current_route) - 1:
            return self.current_route[-1]
        
        # Interpolate between waypoints
        start = self.current_route[idx]
        end = self.current_route[idx + 1]
        segment_progress = (progress * (len(self.current_route) - 1)) - idx
        
        lat = start[0] + segment_progress * (end[0] - start[0])
        lon = start[1] + segment_progress * (end[1] - start[1])
        
        return (lat, lon)

    def calculate_course(self, pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
        """Calculate true course between two positions."""
        lat1, lon1 = map(np.radians, pos1)
        lat2, lon2 = map(np.radians, pos2)
        
        dlon = lon2 - lon1
        y = np.sin(dlon) * np.cos(lat2)
        x = np.cos(lat1) * np.sin(lat2) - np.sin(lat1) * np.cos(lat2) * np.cos(dlon)
        course = np.degrees(np.arctan2(y, x))
        return (course + 360) % 360

    def generate_ais_message(self, timestamp: datetime = None) -> Dict:
        """Generate an AIS position report message."""
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        if not self.start_time:
            raise ValueError("No active voyage. Call start_new_voyage() first.")
        
        elapsed_minutes = (timestamp - self.start_time).total_seconds() / 60
        current_pos = self.calculate_position(elapsed_minutes)
        
        # Calculate course by looking ahead
        next_pos = self.calculate_position(elapsed_minutes + 1)
        course = self.calculate_course(current_pos, next_pos)
        
        try:
        # 🛠 Instead of real AIS encoding, build a simple dummy payload
            payload = f"!AIVDM,1,1,,A,DUMMY-{self.mmsi}-{timestamp.isoformat()},0*hh"
            
            self.message_count += 1
            
            message = {
                "message": "AIVDM",
                "mmsi": self.mmsi,
                "timestamp": timestamp.isoformat(),
                "payload": payload,
                "decoded": {
                    "mmsi": self.mmsi,
                    "latitude": current_pos[0],
                    "longitude": current_pos[1],
                    "speed": self.speed_knots,
                    "course": course,
                    "heading": course,
                    "message_count": self.message_count,
                    "elapsed_minutes": elapsed_minutes,
                    "distance_covered": self.speed_knots * elapsed_minutes / 60
                }
            }
            
            # Validate basic fields
            if not (-90 <= message['decoded']['latitude'] <= 90 and 
                    -180 <= message['decoded']['longitude'] <= 180):
                raise ValueError("Invalid position coordinates")
            
            return message
        
        except Exception as e:
            print(f"Error generating AIS message: {e}")
            return {
                "message": "AIVDM",
                "mmsi": self.mmsi,
                "timestamp": timestamp.isoformat(),
                "payload": "!AIVDM,1,1,,A,Error generating payload",
                "decoded": {
                    "mmsi": self.mmsi,
                    "latitude": current_pos[0],
                    "longitude": current_pos[1],
                    "speed": self.speed_knots,
                    "course": course,
                    "heading": course,
                    "message_count": self.message_count,
                    "elapsed_minutes": elapsed_minutes,
                    "distance_covered": self.speed_knots * elapsed_minutes / 60
                }
            }

if __name__ == "__main__":
    # Test the AIS simulator
    simulator = AISSimulator(mmsi="123456789", speed_knots=15.0)
    start, end = simulator.start_new_voyage()
    
    print(f"Starting voyage from {start['port_name']} to {end['port_name']}")
    print(f"Total distance: {simulator.total_distance:.2f} nautical miles")
    print(f"Estimated duration: {simulator.total_distance / simulator.speed_knots:.2f} hours")
    
    # Generate some test messages
    for minutes in range(0, 60, 5):
        test_time = simulator.start_time + timedelta(minutes=minutes)
        message = simulator.generate_ais_message(test_time)
        print(f"\nMessage #{message['decoded']['message_count']} at {message['timestamp']}:")
        print(f"Position: {message['decoded']['latitude']:.4f}°N, {message['decoded']['longitude']:.4f}°E")
        print(f"Speed: {message['decoded']['speed']} knots")
        print(f"Course: {message['decoded']['course']:.1f}°")
        print(f"Distance covered: {message['decoded']['distance_covered']:.2f} nautical miles")