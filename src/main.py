import asyncio
import os
import sys
from pathlib import Path

# Add the project root directory to Python path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

# Create data directories if they don't exist
os.makedirs(root_dir / "src" / "data", exist_ok=True)

# Ensure ports.csv exists
ports_csv_path = root_dir / "src" / "data" / "ports.csv"
if not ports_csv_path.exists():
    print("Creating ports.csv file...")
    with open(ports_csv_path, "w") as f:
        f.write("""port_id,port_name,latitude,longitude,country
1,Shanghai,31.2304,121.4737,China
2,Singapore,1.2833,103.8333,Singapore
3,Rotterdam,51.9225,4.4792,Netherlands
4,Busan,35.1795,129.0756,South Korea
5,Los Angeles,33.7395,-118.2618,USA
6,Dubai,25.2697,55.2868,UAE
7,Hamburg,53.5511,9.9937,Germany
8,Antwerp,51.2229,4.4003,Belgium
9,Tokyo,35.6545,139.8344,Japan
10,Hong Kong,22.2855,114.1577,China
11,New York,40.7128,-74.0060,USA
12,Sydney,-33.8688,151.2093,Australia
13,Mumbai,18.9750,72.8258,India
14,Cape Town,-33.9249,18.4241,South Africa
15,Rio de Janeiro,-22.9068,-43.1729,Brazil""")

async def main():
    from src.data.models import init_db
    from src.simulation.playback_service import PlaybackService
    from src.data.ingestion import AISIngestionService
    
    # Initialize database
    print("Initializing database...")
    init_db()
    
    # Start the AIS playback service (websocket server)
    playback_service = PlaybackService(port=8765)
    
    # Start the ingestion service (websocket client)
    ingestion_service = AISIngestionService(websocket_url="ws://localhost:8765")
    
    # Run both services concurrently
    await asyncio.gather(
        playback_service.start_server(),
        ingestion_service.process_messages(),
    )

if __name__ == "__main__":
    print("Starting Maritime Vessel Simulation...")
    asyncio.run(main())