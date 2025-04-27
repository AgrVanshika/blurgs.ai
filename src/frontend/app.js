// Initialize map
const map = L.map('map').setView([0, 0], 2);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

// Store vessel markers and tracks
const vessels = new Map();
const stats = {
    messagesReceived: 0,
    vesselsTracked: 0,
    lastUpdate: null
};

// WebSocket connection
let ws; // Don't initialize yet

function connectWebSocket() {
    ws = new WebSocket('ws://localhost:8001');

    ws.onopen = () => {
        console.log('Connected to WebSocket server');
        updateStats();
        // Add initial vessel
        addVessel();
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Received message:', data);
        stats.messagesReceived++;
        
        if (data.message === "AIVDM") {
            updateVessel(data);
        } else if (data.type === 'vessel_added') {
            console.log(`Vessel added: ${data.mmsi}`);
            stats.vesselsTracked++;
        }
        
        updateStats();
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
        console.log('WebSocket connection closed');
        // Try to reconnect after 5 seconds
        setTimeout(() => {
            console.log('Attempting to reconnect...');
            connectWebSocket();
        }, 5000);
    };
}

// Initialize WebSocket connection
connectWebSocket();

// Update vessel position on map
function updateVessel(data) {
    const mmsi = data.mmsi;
    const position = [data.decoded.latitude, data.decoded.longitude];
    
    if (!vessels.has(mmsi)) {
        // Create new vessel marker and track
        const marker = L.marker(position, {
            icon: L.divIcon({
                className: 'vessel-marker',
                html: '🚢',
                iconSize: [30, 30]
            })
        }).addTo(map);
        
        // Add popup with vessel info
        marker.bindPopup(`<b>MMSI:</b> ${mmsi}<br><b>Speed:</b> ${data.decoded.speed} knots`);
        
        const track = L.polyline([], {color: 'blue'}).addTo(map);
        
        vessels.set(mmsi, {
            marker: marker,
            track: track,
            positions: []
        });
        
        // Update vessel count
        stats.vesselsTracked = vessels.size;
    }
    
    const vessel = vessels.get(mmsi);
    vessel.marker.setLatLng(position);
    vessel.positions.push(position);
    vessel.track.setLatLngs(vessel.positions);
    
    // Update popup content
    vessel.marker.setPopupContent(`
        <b>MMSI:</b> ${mmsi}<br>
        <b>Speed:</b> ${data.decoded.speed} knots<br>
        <b>Course:</b> ${data.decoded.course}°<br>
        <b>Position:</b> ${position[0].toFixed(4)}, ${position[1].toFixed(4)}
    `);
    
    // Center map on vessel if this is the first one
    if (vessels.size === 1) {
        map.setView(position, 10);
    }
}

// Update statistics display
function updateStats() {
    const statsDiv = document.getElementById('stats');
    stats.lastUpdate = new Date().toLocaleTimeString();
    statsDiv.innerHTML = `
        <p>Messages Received: ${stats.messagesReceived}</p>
        <p>Vessels Tracked: ${stats.vesselsTracked}</p>
        <p>Last Update: ${stats.lastUpdate}</p>
    `;
}

// Control functions
function setSpeed(speed) {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            command: 'set_speed',
            speed: speed
        }));
    } else {
        console.error("WebSocket not connected");
    }
}

function addVessel() {
    if (ws && ws.readyState === WebSocket.OPEN) {
        const mmsi = Math.floor(Math.random() * 900000000 + 100000000).toString();
        const speed = Math.floor(Math.random() * 20 + 10);
        ws.send(JSON.stringify({
            command: 'add_vessel',
            mmsi: mmsi,
            speed: speed
        }));
    } else {
        console.error("WebSocket not connected");
    }
}