import asyncio
import websockets
import json
from datetime import datetime
import pyais
from sqlalchemy.orm import Session
from models import SessionLocal, AISMessage, Vessel
from typing import Dict, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AISIngestionService:
    def __init__(self, websocket_url: str = "ws://localhost:8765"):
        """Initialize the AIS ingestion service."""
        self.websocket_url = websocket_url
        self.stats = {
            'messages_received': 0,
            'messages_processed': 0,
            'invalid_messages': 0,
            'duplicate_messages': 0
        }
        self.last_positions: Dict[str, Dict] = {}

    def validate_message(self, decoded_data: Dict) -> bool:
        """Validate AIS message data."""
        required_fields = ['latitude', 'longitude', 'mmsi']
        if not all(field in decoded_data for field in required_fields):
            return False
        
        # Validate latitude range
        if not -90 <= decoded_data['latitude'] <= 90:
            return False
            
        # Validate longitude range
        if not -180 <= decoded_data['longitude'] <= 180:
            return False
            
        # Validate MMSI format (9 digits)
        if not str(decoded_data['mmsi']).isdigit() or len(str(decoded_data['mmsi'])) != 9:
            return False
            
        return True

    def is_duplicate(self, mmsi: str, timestamp: datetime, position: tuple) -> bool:
        """Check if message is a duplicate based on position and time."""
        if mmsi not in self.last_positions:
            return False
            
        last = self.last_positions[mmsi]
        time_diff = (timestamp - last['timestamp']).total_seconds()
        
        # Consider it duplicate if same position within 1 minute
        if time_diff < 60 and position == last['position']:
            return True
            
        return False

    def store_message(self, session: Session, message: Dict):
        """Store AIS message in database."""
        try:
            # Parse timestamp
            timestamp = datetime.fromisoformat(message['timestamp'])
            
            # Decode AIS payload
            decoded = message['decoded']
            
            # Validate message
            if not self.validate_message(decoded):
                logger.warning(f"Invalid message data: {decoded}")
                self.stats['invalid_messages'] += 1
                return
                
            # Check for duplicates
            position = (decoded['latitude'], decoded['longitude'])
            if self.is_duplicate(message['mmsi'], timestamp, position):
                logger.info(f"Duplicate message detected for MMSI {message['mmsi']}")
                self.stats['duplicate_messages'] += 1
                return
                
            # Update last position
            self.last_positions[message['mmsi']] = {
                'timestamp': timestamp,
                'position': position
            }
            
            # Create AIS message record
            ais_message = AISMessage(
                mmsi=message['mmsi'],
                timestamp=timestamp,
                latitude=decoded['latitude'],
                longitude=decoded['longitude'],
                speed=decoded.get('speed'),
                course=decoded.get('course'),
                heading=decoded.get('heading'),
                raw_message=message['payload'],
                message_type=1  # Position Report Class A
            )
            
            # Create or update vessel record
            vessel = session.query(Vessel).filter_by(mmsi=message['mmsi']).first()
            if not vessel:
                vessel = Vessel(mmsi=message['mmsi'])
                session.add(vessel)
            
            session.add(ais_message)
            session.commit()
            
            self.stats['messages_processed'] += 1
            
        except Exception as e:
            logger.error(f"Error storing message: {e}")
            session.rollback()
            raise

    async def process_messages(self):
        """Process incoming AIS messages from WebSocket."""
        while True:
            try:
                async with websockets.connect(self.websocket_url) as websocket:
                    logger.info(f"Connected to WebSocket at {self.websocket_url}")
                    
                    async for message in websocket:
                        try:
                            data = json.loads(message)
                            self.stats['messages_received'] += 1
                            
                            # Process message in database session
                            with SessionLocal() as session:
                                self.store_message(session, data)
                                
                            # Log statistics periodically
                            if self.stats['messages_received'] % 100 == 0:
                                logger.info(f"Statistics: {json.dumps(self.stats)}")
                                
                        except json.JSONDecodeError:
                            logger.error(f"Invalid JSON received: {message}")
                        except Exception as e:
                            logger.error(f"Error processing message: {e}")
                            
            except websockets.ConnectionClosed:
                logger.warning("WebSocket connection closed. Retrying in 5 seconds...")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                await asyncio.sleep(5)

if __name__ == "__main__":
    service = AISIngestionService()
    asyncio.run(service.process_messages()) 