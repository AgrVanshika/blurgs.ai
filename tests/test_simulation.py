import pytest
from datetime import datetime, timedelta
from src.simulation.route_generator import RouteGenerator
from src.simulation.ais_simulator import AISSimulator

def test_route_generator():
    generator = RouteGenerator()
    
    # Test random port selection
    start_port, end_port = generator.select_random_ports()
    assert start_port is not None
    assert end_port is not None
    assert start_port != end_port
    
    # Test route generation
    route = generator.generate_route(start_port, end_port)
    assert len(route) > 0
    assert all(len(point) == 2 for point in route)
    assert all(-90 <= point[0] <= 90 and -180 <= point[1] <= 180 for point in route)
    
    # Test distance calculation
    distance = generator.calculate_distance(route)
    assert distance > 0

def test_ais_simulator():
    simulator = AISSimulator(mmsi="123456789", speed_knots=15.0)
    
    # Test voyage initialization
    start_port, end_port = simulator.start_new_voyage()
    assert start_port is not None
    assert end_port is not None
    
    # Test message generation
    base_time = datetime.utcnow()
    message = simulator.generate_ais_message(base_time)
    
    assert message['mmsi'] == "123456789"
    assert message['message'] == "AIVDM"
    assert 'payload' in message
    assert 'decoded' in message
    
    decoded = message['decoded']
    assert -90 <= decoded['latitude'] <= 90
    assert -180 <= decoded['longitude'] <= 180
    assert decoded['speed'] == 15.0
    assert 0 <= decoded['course'] <= 360
    
    # Test position updates
    time_series = [base_time + timedelta(minutes=i*5) for i in range(5)]
    positions = []
    
    for t in time_series:
        msg = simulator.generate_ais_message(t)
        positions.append((msg['decoded']['latitude'], msg['decoded']['longitude']))
    
    # Verify that position changes over time
    assert len(set(positions)) > 1

def test_route_validity():
    generator = RouteGenerator()
    start_port, end_port = generator.select_random_ports()
    route = generator.generate_route(start_port, end_port)
    
    # Test route continuity
    for i in range(len(route) - 1):
        point1 = route[i]
        point2 = route[i + 1]
        
        # Calculate distance between consecutive points
        distance = generator._haversine_distance(point1[0], point1[1], point2[0], point2[1])
        
        # Points should not be too far apart (arbitrary threshold of 100 nautical miles)
        assert distance <= 100, f"Points too far apart: {distance} nautical miles"

if __name__ == "__main__":
    pytest.main([__file__]) 