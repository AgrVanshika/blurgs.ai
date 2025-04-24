from sqlalchemy import func, and_
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import numpy as np
from models import SessionLocal, AISMessage
from shapely.geometry import Point, LineString
from shapely.ops import transform
import pyproj
from functools import partial

class VesselAnalytics:
    def __init__(self):
        """Initialize the vessel analytics module."""
        # Create a transformer for accurate distance calculations
        self.geod = pyproj.Geod(ellps='WGS84')

    def get_vessel_track(self, mmsi: str, start_time: datetime = None, end_time: datetime = None) -> List[Dict]:
        """Retrieve the track (trajectory) for a given vessel within a time window."""
        with SessionLocal() as session:
            query = session.query(AISMessage).filter(AISMessage.mmsi == mmsi)
            
            if start_time:
                query = query.filter(AISMessage.timestamp >= start_time)
            if end_time:
                query = query.filter(AISMessage.timestamp <= end_time)
                
            # Order by timestamp to get proper trajectory
            query = query.order_by(AISMessage.timestamp)
            
            messages = query.all()
            
            return [{
                'timestamp': msg.timestamp.isoformat(),
                'latitude': msg.latitude,
                'longitude': msg.longitude,
                'speed': msg.speed,
                'course': msg.course
            } for msg in messages]

    def calculate_distance(self, track: List[Dict]) -> float:
        """Calculate the total distance covered in nautical miles."""
        if len(track) < 2:
            return 0.0
            
        total_distance = 0.0
        
        for i in range(len(track) - 1):
            point1 = (track[i]['longitude'], track[i]['latitude'])
            point2 = (track[i + 1]['longitude'], track[i + 1]['latitude'])
            
            # Calculate distance using Geodesic
            _, _, distance = self.geod.inv(point1[0], point1[1], point2[0], point2[1])
            # Convert meters to nautical miles
            total_distance += distance / 1852.0
            
        return total_distance

    def calculate_statistics(self, mmsi: str, start_time: datetime = None, 
                           end_time: datetime = None) -> Dict:
        """Calculate various statistics for a vessel within a time window."""
        track = self.get_vessel_track(mmsi, start_time, end_time)
        
        if not track:
            return {
                'mmsi': mmsi,
                'start_time': start_time.isoformat() if start_time else None,
                'end_time': end_time.isoformat() if end_time else None,
                'total_distance': 0,
                'average_speed': 0,
                'max_speed': 0,
                'number_of_positions': 0
            }
            
        # Calculate statistics
        total_distance = self.calculate_distance(track)
        speeds = [msg['speed'] for msg in track if msg['speed'] is not None]
        
        stats = {
            'mmsi': mmsi,
            'start_time': track[0]['timestamp'],
            'end_time': track[-1]['timestamp'],
            'total_distance': round(total_distance, 2),
            'average_speed': round(np.mean(speeds), 2) if speeds else 0,
            'max_speed': round(max(speeds), 2) if speeds else 0,
            'number_of_positions': len(track)
        }
        
        # Calculate time-based statistics
        if len(track) > 1:
            start = datetime.fromisoformat(track[0]['timestamp'])
            end = datetime.fromisoformat(track[-1]['timestamp'])
            duration = (end - start).total_seconds() / 3600  # hours
            
            if duration > 0:
                stats['average_speed_over_ground'] = round(total_distance / duration, 2)
            
        return stats

    def get_vessel_density_map(self, start_time: datetime = None, end_time: datetime = None,
                             grid_size: float = 0.1) -> List[Dict]:
        """Generate a vessel density map using a grid."""
        with SessionLocal() as session:
            query = session.query(
                func.round(AISMessage.latitude / grid_size) * grid_size,
                func.round(AISMessage.longitude / grid_size) * grid_size,
                func.count()
            )
            
            if start_time:
                query = query.filter(AISMessage.timestamp >= start_time)
            if end_time:
                query = query.filter(AISMessage.timestamp <= end_time)
                
            query = query.group_by(
                func.round(AISMessage.latitude / grid_size),
                func.round(AISMessage.longitude / grid_size)
            )
            
            results = query.all()
            
            return [{
                'latitude': float(lat),
                'longitude': float(lon),
                'count': count
            } for lat, lon, count in results]

    def find_vessel_encounters(self, distance_threshold: float = 1.0,
                             time_window: timedelta = timedelta(minutes=30)) -> List[Dict]:
        """Find instances where vessels come within a certain distance of each other."""
        encounters = []
        
        with SessionLocal() as session:
            # Get all vessels
            vessels = session.query(AISMessage.mmsi).distinct().all()
            vessels = [v[0] for v in vessels]
            
            # Compare each pair of vessels
            for i in range(len(vessels)):
                for j in range(i + 1, len(vessels)):
                    mmsi1, mmsi2 = vessels[i], vessels[j]
                    
                    # Get positions for both vessels
                    positions1 = self.get_vessel_track(mmsi1)
                    positions2 = self.get_vessel_track(mmsi2)
                    
                    # Check for encounters
                    for pos1 in positions1:
                        time1 = datetime.fromisoformat(pos1['timestamp'])
                        point1 = (pos1['longitude'], pos1['latitude'])
                        
                        # Filter positions of vessel 2 within time window
                        nearby_positions = [
                            pos2 for pos2 in positions2
                            if abs(time1 - datetime.fromisoformat(pos2['timestamp'])) <= time_window
                        ]
                        
                        for pos2 in nearby_positions:
                            point2 = (pos2['longitude'], pos2['latitude'])
                            
                            # Calculate distance between points
                            _, _, distance = self.geod.inv(
                                point1[0], point1[1], point2[0], point2[1]
                            )
                            # Convert to nautical miles
                            distance_nm = distance / 1852.0
                            
                            if distance_nm <= distance_threshold:
                                encounters.append({
                                    'mmsi1': mmsi1,
                                    'mmsi2': mmsi2,
                                    'timestamp': pos1['timestamp'],
                                    'distance': round(distance_nm, 2),
                                    'location': {
                                        'latitude': pos1['latitude'],
                                        'longitude': pos1['longitude']
                                    }
                                })
                                
        return encounters

if __name__ == "__main__":
    # Test the analytics module
    analytics = VesselAnalytics()
    
    # Example: Get track and statistics for a vessel
    mmsi = "123456789"
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=24)
    
    track = analytics.get_vessel_track(mmsi, start_time, end_time)
    print(f"\nTrack for vessel {mmsi}:")
    print(f"Number of positions: {len(track)}")
    
    stats = analytics.calculate_statistics(mmsi, start_time, end_time)
    print("\nVessel Statistics:")
    print(json.dumps(stats, indent=2))
    
    # Example: Generate density map
    density = analytics.get_vessel_density_map(start_time, end_time)
    print(f"\nDensity map grid cells: {len(density)}")
    
    # Example: Find vessel encounters
    encounters = analytics.find_vessel_encounters()
    print(f"\nVessel encounters found: {len(encounters)}") 