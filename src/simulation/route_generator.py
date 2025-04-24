import pandas as pd
import numpy as np
from searoute import searoute
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

    def generate_route(self, start_port: Dict = None, end_port: Dict = None) -> List[Tuple[float, float]]:
        """Generate a maritime route between two ports using searoute-py."""
        if start_port is None or end_port is None:
            start_port, end_port = self.select_random_ports()

        try:
            # Generate route using searoute-py
            route = searoute.searoute(
                (start_port['longitude'], start_port['latitude']),
                (end_port['longitude'], end_port['latitude'])
            )
            
            # Convert route to list of (lat, lon) tuples
            waypoints = [(point[1], point[0]) for point in route]
            return waypoints
        except Exception as e:
            print(f"Error generating route: {e}")
            # Fallback to simple linear interpolation
            return self._linear_route(
                (start_port['latitude'], start_port['longitude']),
                (end_port['latitude'], end_port['longitude'])
            )

    def _linear_route(self, start: Tuple[float, float], end: Tuple[float, float], 
                     num_points: int = 50) -> List[Tuple[float, float]]:
        """Generate a simple linear route between two points (fallback method)."""
        lats = np.linspace(start[0], end[0], num_points)
        lons = np.linspace(start[1], end[1], num_points)
        return list(zip(lats, lons))

    def calculate_distance(self, route: List[Tuple[float, float]]) -> float:
        """Calculate the total distance of the route in nautical miles."""
        total_distance = 0
        for i in range(len(route) - 1):
            lat1, lon1 = route[i]
            lat2, lon2 = route[i + 1]
            total_distance += self._haversine_distance(lat1, lon1, lat2, lon2)
        return total_distance

    def _haversine_distance(self, lat1: float, lon1: float, 
                          lat2: float, lon2: float) -> float:
        """Calculate the great circle distance between two points in nautical miles."""
        R = 3440.065  # Earth's radius in nautical miles
        
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        return R * c

if __name__ == "__main__":
    # Test the route generator
    generator = RouteGenerator()
    start, end = generator.select_random_ports()
    route = generator.generate_route(start, end)
    distance = generator.calculate_distance(route)
    
    print(f"Generated route from {start['port_name']} to {end['port_name']}")
    print(f"Total distance: {distance:.2f} nautical miles")
    print(f"Number of waypoints: {len(route)}") 