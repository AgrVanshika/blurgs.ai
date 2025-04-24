# Maritime Vessel Route Simulation & Data Engineering

This project implements a maritime vessel route simulation and AIS data processing system. It generates realistic vessel routes between ports, simulates AIS messages, and provides a data pipeline for storage and analysis.

## Features

- Route generation between ports using searoute-py
- AIS message simulation with realistic vessel movement
- WebSocket-based playback system with variable speeds
- Data ingestion pipeline with validation and quality checks
- Efficient data storage and retrieval system
- Analytics queries for vessel tracking and statistics

## Project Structure

```
.
├── README.md
├── requirements.txt
├── src/
│   ├── simulation/
│   │   ├── route_generator.py
│   │   ├── ais_simulator.py
│   │   └── playback_service.py
│   ├── data/
│   │   ├── ports.csv
│   │   ├── ingestion.py
│   │   └── models.py
│   ├── api/
│   │   ├── websocket.py
│   │   └── rest.py
│   └── analytics/
│       └── queries.py
└── tests/
    ├── test_simulation.py
    ├── test_ingestion.py
    └── test_analytics.py
```

## Setup and Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd maritime-simulation
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
python src/data/models.py
```

## Usage

1. Start the WebSocket server:
```bash
python src/api/websocket.py
```

2. Run the simulation:
```bash
python src/simulation/playback_service.py
```

3. Start the data ingestion:
```bash
python src/data/ingestion.py
```

## Design Decisions

### Database Choice
We use PostgreSQL for the following reasons:
- Strong support for geospatial data with PostGIS
- ACID compliance for data integrity
- Efficient indexing capabilities
- Support for time-series data
- Scalability for large datasets

### Data Model
The schema is designed to efficiently store AIS messages while supporting fast queries:
- Partitioning by time for efficient historical queries
- Spatial indexing for location-based queries
- Optimized for common access patterns

### Simulation Approach
- Routes are generated using searoute-py for realistic paths
- Position interpolation between waypoints for smooth movement
- Configurable simulation speed for flexible playback

## Testing

Run the test suite:
```bash
pytest tests/
```

## Future Improvements

1. Support for multiple concurrent vessels
2. Real-time visualization dashboard
3. Advanced analytics and machine learning features
4. Distributed processing for large-scale simulations
5. Caching layer for frequently accessed data

## License

MIT License 