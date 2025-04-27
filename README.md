# Maritime AIS Simulation & Data Pipeline

A robust system for simulating maritime vessel movements, generating AIS messages, and processing vessel tracking data. This implementation focuses on efficient data handling, real-time simulation, and reliable message processing.

## Current Features

- **AIS Message Simulation**
  - Real-time vessel position updates
  - Configurable message intervals
  - Batch processing for efficiency
  - WebSocket-based message streaming

- **Data Processing**
  - Efficient message ingestion
  - Duplicate detection
  - Data validation
  - Quality metrics tracking

- **Performance Optimizations**
  - Batch processing (10 messages per batch)
  - Efficient database operations
  - Connection pooling
  - Resource management

## Project Structure

```
.
├── README.md
├── requirements.txt
├── setup.py
├── src/
│   ├── simulation/
│   │   ├── ais_simulator.py    # AIS message generation
│   │   └── playback_service.py # WebSocket message streaming
│   ├── data/
│   │   ├── ingestion.py        # Message ingestion pipeline
│   │   └── models.py          # Database models
│   └── main.py                # Application entry point
└── data/
    └── maritime.db            # SQLite database
```

## Setup and Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd maritime-simulation
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the application:
```bash
python src/main.py
```

The system will:
- Initialize the database
- Start the WebSocket server (port 8765)
- Begin AIS message simulation
- Process and store messages

## Configuration

The system can be configured through environment variables:

```bash
# WebSocket Configuration
WS_PORT=8765
WS_HOST=localhost

# Simulation Settings
SIMULATION_SPEED=5.0  # Speed factor (1.0 = real-time)
MESSAGE_INTERVAL=5    # Seconds between messages
BATCH_SIZE=10        # Messages per batch

# Database Settings
DB_PATH=data/maritime.db
```

## Current Implementation Details

### Message Processing
- Messages are processed in batches of 10
- Each batch is processed in ~0.01 seconds
- Messages are validated before storage
- Duplicates are detected and filtered

### Data Quality
- Tracks message statistics:
  - Total messages received
  - Messages processed
  - Invalid messages
  - Duplicate messages

### Performance Metrics
- WebSocket connection stability
- Message processing latency
- Database operation efficiency
- Resource utilization

## Design Decisions

### Database Choice
Using SQLite for:
- Simple deployment
- Zero configuration
- ACID compliance
- Efficient for moderate loads
- Easy backup and portability

### Message Processing
- Batch processing for efficiency
- In-memory buffering
- Connection pooling
- Error recovery

### Simulation Approach
- Real-time position updates
- Configurable intervals
- Efficient resource usage
- Stable message flow

## Future Enhancements

1. **Route Generation**
   - Implement searoute-py for realistic routes
   - Add waypoint handling
   - Support multiple vessels

2. **AIS Message Quality**
   - Proper AIS encoding
   - Realistic vessel movement
   - Speed factor implementation

3. **Analytics**
   - Vessel track retrieval
   - Distance/speed calculations
   - Time-based queries
   - Statistical analysis

4. **Performance**
   - Database indexing
   - Query optimization
   - Caching layer
   - Distributed processing

## License

MIT License 