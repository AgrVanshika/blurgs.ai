import pytest
from datetime import datetime, timedelta
import json
import asyncio
from src.simulation.route_generator import RouteGenerator
from src.simulation.ais_simulator import AISSimulator
from src.data.ingestion import AISIngestionService
from src.data.models import SessionLocal, AISMessage, Vessel
import numpy as np

# Test data
INVALID_MMSI = "123"  # Too short
INVALID_COORDS = (100, 200)  # Outside valid range
DUPLICATE_POSITION = (0, 0)

@pytest.fixture
def route_generator():
    return RouteGenerator()

@pytest.fixture
def ais_simulator():
    return AISSimulator(mmsi="123456789", speed_knots=15.0)

@pytest.fixture
def ingestion_service():
    return AISIngestionService(batch_size=10)

def test_invalid_port_coordinates(route_generator):
    """Test route generation with invalid port coordinates."""
    invalid_port = {
        'port_name': 'Invalid Port',
        'latitude': 200,  # Invalid latitude
        'longitude': 400,  # Invalid longitude
        'country': 'Test'
    }
    
    # Should fall back to linear route
    route = route_generator.generate_route(invalid_port, invalid_port)
    assert len(route) > 0
    assert all(-90 <= point[0] <= 90 for point in route)
    assert all(-180 <= point[1] <= 180 for point in route)

def test_route_generation_edge_cases(route_generator):
    """Test route generation with edge cases."""
    # Test same port
    port = {
        'port_name': 'Test Port',
        'latitude': 0,
        'longitude': 0,
        'country': 'Test'
    }
    route = route_generator.generate_route(port, port)
    assert len(route) > 0
    
    # Test antipodal points
    port1 = {'port_name': 'Port 1', 'latitude': 0, 'longitude': 0, 'country': 'Test'}
    port2 = {'port_name': 'Port 2', 'latitude': 0, 'longitude': 180, 'country': 'Test'}
    route = route_generator.generate_route(port1, port2)
    assert len(route) > 0

def test_ais_message_validation(ais_simulator):
    """Test AIS message validation with invalid data."""
    # Test invalid MMSI
    with pytest.raises(ValueError):
        AISSimulator(mmsi=INVALID_MMSI)
    
    # Test invalid speed
    with pytest.raises(ValueError):
        AISSimulator(mmsi="123456789", speed_knots=-10)
    
    # Test message generation without starting voyage
    with pytest.raises(ValueError):
        ais_simulator.generate_ais_message()

def test_route_continuity(route_generator):
    """Test route continuity and point spacing."""
    start_port, end_port = route_generator.select_random_ports()
    route = route_generator.generate_route(start_port, end_port)
    
    # Check point spacing
    for i in range(len(route) - 1):
        point1 = route[i]
        point2 = route[i + 1]
        distance = route_generator._haversine_distance(
            point1[0], point1[1], point2[0], point2[1]
        )
        # Points should not be too far apart (200 nautical miles is more realistic for open ocean)
        assert distance <= 200, f"Points too far apart: {distance} nautical miles"
        
        # Verify coordinates are valid
        assert -90 <= point1[0] <= 90, f"Invalid latitude: {point1[0]}"
        assert -180 <= point1[1] <= 180, f"Invalid longitude: {point1[1]}"
        assert -90 <= point2[0] <= 90, f"Invalid latitude: {point2[0]}"
        assert -180 <= point2[1] <= 180, f"Invalid longitude: {point2[1]}"

def test_performance_under_load(ingestion_service):
    """Test system performance under load."""
    # Generate 1000 messages
    messages = []
    for i in range(1000):
        message = {
            'mmsi': f'12345678{i % 10}',  # 10 different vessels
            'timestamp': datetime.utcnow().isoformat(),
            'decoded': {
                'latitude': np.random.uniform(-90, 90),
                'longitude': np.random.uniform(-180, 180),
                'speed': np.random.uniform(0, 30),
                'course': np.random.uniform(0, 360)
            },
            'payload': f'test{i}'
        }
        messages.append(message)
    
    # Process messages in batches
    start_time = datetime.utcnow()
    with SessionLocal() as session:
        for message in messages:
            ingestion_service.store_message(session, message)
        session.commit()
    end_time = datetime.utcnow()
    
    # Check processing time
    processing_time = (end_time - start_time).total_seconds()
    assert processing_time < 10  # Should process 1000 messages in under 10 seconds

def test_error_recovery(ingestion_service):
    """Test system recovery from errors."""
    # Test with invalid message
    invalid_message = {
        'mmsi': '123456789',
        'timestamp': 'invalid_timestamp',
        'decoded': {
            'latitude': 200,  # Invalid latitude
            'longitude': 400,  # Invalid longitude
            'speed': -10,  # Invalid speed
            'course': 400  # Invalid course
        },
        'payload': 'test'
    }
    
    # System should handle invalid message without crashing
    with SessionLocal() as session:
        ingestion_service.store_message(session, invalid_message)
        session.commit()
        
        # Verify no message was stored
        count = session.query(AISMessage).filter_by(mmsi='123456789').count()
        assert count == 0

if __name__ == "__main__":
    pytest.main([__file__]) 