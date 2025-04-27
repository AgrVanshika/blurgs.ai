from sqlalchemy import func, desc, and_, text
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import numpy as np
from src.data.models import SessionLocal, AISMessage, Vessel

def get_vessel_track(mmsi: str, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> List[Dict]:
    """
    Retrieve the full track (trajectory) for a given vessel.
    
    Args:
        mmsi: The Maritime Mobile Service Identity number
        start_time: Optional start time filter
        end_time: Optional end time filter
        
    Returns:
        List of position points with timestamps
    """
    with SessionLocal() as session:
        query = session.query(
            AISMessage.timestamp,
            AISMessage.latitude,
            AISMessage.longitude,
            AISMessage.speed,
            AISMessage.course
        ).filter(AISMessage.mmsi == mmsi)
        
        if start_time:
            query = query.filter(AISMessage.timestamp >= start_time)
        if end_time:
            query = query.filter(AISMessage.timestamp <= end_time)
            
        # Order by timestamp
        query = query.order_by(AISMessage.timestamp)
        
        results = query.all()
        
        track = [
            {
                "timestamp": r.timestamp.isoformat(),
                "latitude": r.latitude,
                "longitude": r.longitude,
                "speed": r.speed,
                "course": r.course
            }
            for r in results
        ]
        
        return track

def calculate_vessel_statistics(mmsi: str, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> Dict:
    """
    Calculate statistics for a vessel within a specified time window.
    
    Args:
        mmsi: The Maritime Mobile Service Identity number
        start_time: Optional start time filter (defaults to all data)
        end_time: Optional end time filter (defaults to current time)
        
    Returns:
        Dictionary with statistics (distance, avg_speed, etc.)
    """
    with SessionLocal() as session:
        # Query vessel data
        query = session.query(
            AISMessage.timestamp,
            AISMessage.latitude,
            AISMessage.longitude,
            AISMessage.speed
        ).filter(AISMessage.mmsi == mmsi)
        
        if start_time:
            query = query.filter(AISMessage.timestamp >= start_time)
        if end_time:
            query = query.filter(AISMessage.timestamp <= end_time)
            
        # Order by timestamp
        query = query.order_by(AISMessage.timestamp)
        
        results = query.all()
        
        if not results:
            return {
                "mmsi": mmsi,
                "points_count": 0,
                "start_time": None,
                "end_time": None,
                "total_distance_nm": 0,
                "avg_speed_knots": 0,
                "max_speed_knots": 0,
                "duration_hours": 0
            }
        
        # Calculate distance between points using Haversine formula
        total_distance = 0
        speeds = []
        
        for i in range(1, len(results)):
            lat1, lon1 = results[i-1].latitude, results[i-1].longitude
            lat2, lon2 = results[i].latitude, results[i].longitude
            
            # Calculate distance in nautical miles
            distance = haversine_distance(lat1, lon1, lat2, lon2)
            total_distance += distance
            
            # Collect speeds
            if results[i].speed is not None:
                speeds.append(results[i].speed)
        
        # Calculate statistics
        start_time = results[0].timestamp
        end_time = results[-1].timestamp
        duration_hours = (end_time - start_time).total_seconds() / 3600
        
        avg_speed = np.mean(speeds) if speeds else 0
        max_speed = max(speeds) if speeds else 0
        
        return {
            "mmsi": mmsi,
            "points_count": len(results),
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "total_distance_nm": round(total_distance, 2),
            "avg_speed_knots": round(avg_speed, 2),
            "max_speed_knots": round(max_speed, 2),
            "duration_hours": round(duration_hours, 2)
        }

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points 
    in nautical miles using the haversine formula.
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    r = 3440.065  # Radius of earth in nautical miles
    
    return c * r

def get_active_vessels(hours: int = 24) -> List[Dict]:
    """
    Get a list of active vessels in the past specified hours.
    """
    with SessionLocal() as session:
        # Calculate the start time
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Get vessels with recent activity
        active_vessels = session.query(
            AISMessage.mmsi,
            func.count().label('msg_count'),
            func.min(AISMessage.timestamp).label('first_seen'),
            func.max(AISMessage.timestamp).label('last_seen')
        ).filter(
            AISMessage.timestamp >= start_