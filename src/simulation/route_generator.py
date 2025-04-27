import pandas as pd
import numpy as np
from geopy.distance import geodesic
from typing import List, Tuple, Dict
import random
from pathlib import Path

class RouteGenerator:
    def __init__(self, ports_file: str = None):
        """Initialize the route generator with a ports database."""
        if ports_file is None:
            ports_file = Path(__file__).parent.parent / "data" / "ports.csv"
        self.ports_df = pd.read_csv(ports_file)
        
    def select_random_ports(self) -> Tuple[Dict, Dict]:
        """Select two random ports from the database."""
        selected_ports = self.ports_df.sample(n=2)
        start_port = selected_ports.iloc[0].to_dict()
        end_port = selected_ports.iloc[1].to_dict()
        return start_port, end_port

    def validate_port(self, port: Dict) -> bool:
        """Validate port coordinates."""
        if not isinstance(port, dict):
            return False
            
        required_fields = ['latitude', 'longitude']
        if not all(field in port for field in required_fields):
            return False
            
        try:
            lat = float(port['latitude'])
            lon = float(port['longitude'])
            return -90 <= lat <= 90 and -180 <= lon <= 180
        except (ValueError, TypeError):
            return False

    def generate_route(self, start_port: Dict = None, end_port: Dict = None) -> List[Tuple[float, float]]:
        """Generate a maritime route between two ports using geopy."""
        if start_port is None or end_port is None:
            start_port, end_port = self.select_random_ports()

        # Validate ports
        if not self.validate_port(start_port) or not self.validate_port(end_port):
            # Fallback to linear route with valid coordinates
            start_lat = max(-90, min(90, float(start_port.get('latitude', 0))))
            start_lon = max(-180, min(180, float(start_port.get('longitude', 0))))
            end_lat = max(-90, min(90, float(end_port.get('latitude', 0))))
            end_lon = max(-180, min(180, float(end_port.get('longitude', 0))))
            return self._linear_route((start_lat, start_lon), (end_lat, end_lon))

        # Use geopy to calculate the route
        start_point = (start_port['latitude'], start_port['longitude'])
        end_point = (end_port['latitude'], end_port['longitude'])
        
        # Calculate intermediate points
        distance = geodesic(start_point, end_point).nautical
        num_points = max(10, int(distance / 10))  # One point every 10 nautical miles, minimum 10 points
        
        return self._linear_route(start_point, end_point, num_points)

    def _linear_route(self, start: Tuple[float, float], end: Tuple[float, float], 
                     num_points: int = 50) -> List[Tuple[float, float]]:
        """Generate a simple linear route between two points."""
        # Ensure coordinates are within valid ranges
        start_lat = max(-90, min(90, start[0]))
        start_lon = max(-180, min(180, start[1]))
        end_lat = max(-90, min(90, end[0]))
        end_lon = max(-180, min(180, end[1]))
        
        lats = np.linspace(start_lat, end_lat, num_points)
        lons = np.linspace(start_lon, end_lon, num_points)
        return list(zip(lats, lons))

    def calculate_distance(self, route: List[Tuple[float, float]]) -> float:
        """Calculate the total distance of the route in nautical miles."""
        total_distance = 0
        for i in range(len(route) - 1):
            point1 = route[i]
            point2 = route[i + 1]
            total_distance += geodesic(point1, point2).nautical
        return total_distance

if __name__ == "__main__":
    # Test the route generator
    generator = RouteGenerator()
    start, end = generator.select_random_ports()
    route = generator.generate_route(start, end)
    distance = generator.calculate_distance(route)
    
    print(f"Generated route from {start['port_name']} to {end['port_name']}")
    print(f"Total distance: {distance:.2f} nautical miles")
    print(f"Number of waypoints: {len(route)}") 