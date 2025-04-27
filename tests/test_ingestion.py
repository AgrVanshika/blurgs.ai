import pytest
from datetime import datetime
from src.data.ingestion import AISIngestionService
from src.data.models import SessionLocal, AISMessage, Vessel

@pytest.fixture
def ingestion_service():
    return AISIngestionService(websocket_url="ws://localhost:8765")

@pytest.fixture
def valid_message():
    return {
        "message": "AIVDM",
        "mmsi": "123456789",
        "timestamp": datetime.utcnow().isoformat(),
        "payload": "!AIVDM,1,1,,A,DUMMY-123456789,0*hh",
        "decoded": {
            "mmsi": "123456789",
            "latitude": 31.2304,
            "longitude": 121.4737,
            "speed": 15.0,
            "course": 215.0,
            "heading": 215.0
        }
    }

@pytest.fixture
def invalid_message():
    return {
        "message": "AIVDM",
        "mmsi": "123",  # Invalid MMSI
        "timestamp": "invalid_timestamp",
        "payload": "test",
        "decoded": {
            "latitude": 200,  # Invalid latitude
            "longitude": 400,  # Invalid longitude
            "speed": -10,  # Invalid speed
            "course": 400  # Invalid course
        }
    }

def test_ingestion_service_initialization(ingestion_service):
    """Test ingestion service initialization."""
    assert ingestion_service.websocket_url == "ws://localhost:8765"
    assert ingestion_service.batch_size == 10
    assert len(ingestion_service.message_buffer) == 0
    assert ingestion_service.stats["messages_received"] == 0
    assert ingestion_service.stats["messages_processed"] == 0

def test_message_validation(ingestion_service, valid_message, invalid_message):
    """Test message validation."""
    assert ingestion_service.validate_message(valid_message) is True
    assert ingestion_service.validate_message(invalid_message) is False

def test_duplicate_detection(ingestion_service, valid_message):
    """Test duplicate message detection."""
    # First message should not be a duplicate
    position = (valid_message["decoded"]["latitude"], valid_message["decoded"]["longitude"])
    timestamp = datetime.fromisoformat(valid_message["timestamp"])
    assert ingestion_service.is_duplicate(valid_message["mmsi"], timestamp, position) is False
    
    # Same position within 1 minute should be a duplicate
    assert ingestion_service.is_duplicate(valid_message["mmsi"], timestamp, position) is True

def test_message_storage(ingestion_service, valid_message):
    """Test message storage in database."""
    with SessionLocal() as session:
        # Store the message
        ingestion_service.store_message(session, valid_message)
        session.commit()
        
        # Verify message was stored
        message = session.query(AISMessage).filter_by(mmsi=valid_message["mmsi"]).first()
        assert message is not None
        assert message.mmsi == valid_message["mmsi"]
        assert message.latitude == valid_message["decoded"]["latitude"]
        assert message.longitude == valid_message["decoded"]["longitude"]
        
        # Verify vessel was created
        vessel = session.query(Vessel).filter_by(mmsi=valid_message["mmsi"]).first()
        assert vessel is not None
        assert vessel.mmsi == valid_message["mmsi"]

def test_invalid_message_handling(ingestion_service, invalid_message):
    """Test handling of invalid messages."""
    with SessionLocal() as session:
        # Store invalid message
        ingestion_service.store_message(session, invalid_message)
        session.commit()
        
        # Verify message was not stored
        message = session.query(AISMessage).filter_by(mmsi=invalid_message["mmsi"]).first()
        assert message is None
        
        # Verify stats were updated
        assert ingestion_service.stats["invalid_messages"] > 0

def test_batch_processing(ingestion_service, valid_message):
    """Test batch processing of messages."""
    # Add messages to buffer
    for _ in range(15):  # More than batch size
        ingestion_service.message_buffer.append(valid_message)
    
    # Process batch
    with SessionLocal() as session:
        ingestion_service.process_batch()
        session.commit()
        
        # Verify messages were processed
        assert len(ingestion_service.message_buffer) == 5  # Remaining messages
        assert ingestion_service.stats["messages_processed"] == 10  # Batch size

if __name__ == "__main__":
    pytest.main([__file__]) 