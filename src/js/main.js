document.addEventListener('DOMContentLoaded', () => {
    console.log('DeKUT 3D Campus Digital Twin');
    console.log('Click any room to view details');
    console.log('Use mouse to navigate: Zoom, Pan, Rotate');
    console.log('Press ESC to close panels');
    console.log('Upload your own ArchiCAD IFC files');

    initApp();
});

function initApp() {
    setupUI();
    showWelcome();
    loadBuildings();
}

function setupUI() {
    const closeBtn = document.getElementById('closeInfo');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            document.getElementById('infoPanel').classList.remove('visible');
        });
    }
    const closeRouting = document.getElementById('closeRouting');
    if (closeRouting) {
        closeRouting.addEventListener('click', () => {
            document.getElementById('routingPanel').classList.remove('visible');
        });
    }

    const btnRouting = document.getElementById('btnRouting');
    if (btnRouting) {
        btnRouting.addEventListener('click', () => {
            const panel = document.getElementById('routingPanel');
            panel.classList.toggle('visible');
            btnRouting.classList.toggle('highlight');
        });
    }

    // Reset view button
    const btnReset = document.getElementById('btnReset');
    if (btnReset) {
        btnReset.addEventListener('click', () => {
            if (window.viewer) {
                window.viewer.camera.flyTo({
                    destination: Cesium.Cartesian3.fromDegrees(36.9617, -0.39811, 400),
                    duration: 1.5,
                    orientation: {
                        heading: Cesium.Math.toRadians(0),
                        pitch: Cesium.Math.toRadians(-35),
                        roll: 0
                    }
                });
            }
        });
    }

    // ESC key to close panels
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.getElementById('infoPanel').classList.remove('visible');
            document.getElementById('routingPanel').classList.remove('visible');
        }
    });

    // Find Route button
    const findRoute = document.getElementById('findRoute');
    if (findRoute) {
        findRoute.addEventListener('click', handleRouteRequest);
    }

    // Enter key on inputs
    ['startInput', 'endInput'].forEach(id => {
        const input = document.getElementById(id);
        if (input) {
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    handleRouteRequest();
                }
            });
        }
    });

    // Upload button
    const uploadBtn = document.getElementById('uploadBtn');
    if (uploadBtn) {
        uploadBtn.addEventListener('click', handleUpload);
    }

    // File input change
    const fileInput = document.getElementById('fileInput');
    if (fileInput) {
        fileInput.addEventListener('change', (e) => {
            const fileName = e.target.files[0]?.name || 'No file selected';
            document.getElementById('fileStatus').textContent = fileName;
        });
    }

    // Floor filter buttons
    document.querySelectorAll('.floor-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const floor = btn.dataset.floor;
            if (window.filterBuildingView) {
                window.filterBuildingView(floor);
            }

            document.querySelectorAll('.floor-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        });
    });
}

async function handleRouteRequest() {
    const start = document.getElementById('startInput').value.trim();
    const end = document.getElementById('endInput').value.trim();

    if (!start || !end) {
        document.getElementById('routeResult').innerHTML = `
            <span class="route-info">Please enter both start and end locations</span>
        `;
        return;
    }

    // Get current building
    const buildingSelect = document.getElementById('buildingSelect');
    const buildingId = buildingSelect.value;

    if (!buildingId) {
        document.getElementById('routeResult').innerHTML = `
            <span class="route-info">Please select a building first</span>
        `;
        return;
    }

    try {
        const response = await fetch('/api/route', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                building_id: buildingId,
                start: start,
                end: end
            })
        });

        const result = await response.json();
        const resultDiv = document.getElementById('routeResult');

        if (result.status === 'success') {
            const data = result.data;

            // Draw route on 3D model
            if (window.drawRoute) {
                window.drawRoute(data.path_details);
            }

            // Update route status
            document.getElementById('routeStatus').textContent = 'Route found!';
            document.getElementById('routeStatus').style.color = '#34d399';

            // Show result
            resultDiv.innerHTML = `
                <div class="route-found"> Route found!</div>
                <div class="route-distance"> ${data.distance.toFixed(1)} units · ${data.steps} steps</div>
                <div style="color:rgba(255,255,255,0.3); font-size:10px; margin-top:4px;">
                    ${data.path.join(' → ')}
                </div>
                <div style="color:rgba(255,255,255,0.2); font-size:9px; margin-top:2px;">
                    Floors: ${data.floors.join(', ')}
                </div>
            `;
        } else {
            resultDiv.innerHTML = `
                <span class="route-info">${result.message || 'No route found'}</span>
            `;
            document.getElementById('routeStatus').textContent = 'No route';
            document.getElementById('routeStatus').style.color = '#ef4444';
        }
    } catch (error) {
        document.getElementById('routeResult').innerHTML = `
            <span class="route-info">Error: ${error.message}</span>
        `;
    }
}

async function handleUpload() {
    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];

    if (!file) {
        alert('Please select an IFC file first');
        return;
    }

    const buildingId = document.getElementById('uploadBuildingId').value.trim();
    const latitude = document.getElementById('uploadLat').value.trim();
    const longitude = document.getElementById('uploadLon').value.trim();
    const elevation = document.getElementById('uploadElevation').value.trim() || '0';
    const northRotation = document.getElementById('uploadRotation').value.trim() || '0';

    if (!buildingId || !latitude || !longitude) {
        alert('Building ID, Latitude, and Longitude are required');
        return;
    }

    const statusDiv = document.getElementById('uploadStatus');
    statusDiv.innerHTML = 'Uploading and processing... (This may take a few minutes)';
    statusDiv.style.color = '#f59e0b';

    const formData = new FormData();
    formData.append('file', file);
    formData.append('building_id', buildingId);
    formData.append('latitude', latitude);
    formData.append('longitude', longitude);
    formData.append('elevation', elevation);
    formData.append('north_rotation', northRotation);

    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.status === 'success') {
            statusDiv.innerHTML = `${result.message}`;
            statusDiv.style.color = '#34d399';

            // Load the new building
            if (window.loadBuildingWithMatrix) {
                await window.loadBuildingWithMatrix(
                    result.tileset_url,
                    parseFloat(latitude),
                    parseFloat(longitude),
                    parseFloat(elevation),
                    parseFloat(northRotation)
                );
            }

            // Refresh building list
            loadBuildings();

            // Close upload panel
            document.getElementById('uploadPanel').classList.remove('visible');

        } else {
            statusDiv.innerHTML = `${result.message}`;
            statusDiv.style.color = '#ef4444';
        }
    } catch (error) {
        statusDiv.innerHTML = ` Error: ${error.message}`;
        statusDiv.style.color = '#ef4444';
    }
}

// LOAD BUILDINGS FROM REGISTRY
async function loadBuildings() {
    try {
        const response = await fetch('/api/buildings');
        const result = await response.json();

        if (result.status === 'success') {
            const select = document.getElementById('buildingSelect');
            select.innerHTML = '<option value="">-- Select Building --</option>';

            const buildings = Object.keys(result.data);
            buildings.forEach(id => {
                const option = document.createElement('option');
                option.value = id;
                option.textContent = id;
                select.appendChild(option);
            });

            // Load first building automatically
            if (buildings.length > 0) {
                const firstId = buildings[0];
                const data = result.data[firstId];
                select.value = firstId;

                if (window.loadBuildingWithMatrix) {
                    await window.loadBuildingWithMatrix(
                        data.tileset_url,
                        data.lat,
                        data.lon,
                        data.alt || 0,
                        data.north_rotation || 0
                    );

                    // Load routing network for this building
                    await loadRoutingNetwork(firstId);
                }
            }
        }
    } catch (error) {
        console.error('Error loading buildings:', error);
    }
}


async function loadRoutingNetwork(buildingId) {
    try {
        const response = await fetch(`/static/${buildingId}/routing_graph.json`);
        const data = await response.json();

        // Update network data globally
        if (window.networkData) {
            window.networkData.nodes = data.nodes || [];
            window.networkData.edges = data.edges || [];
            window.networkData.floors = data.floors || [];
        }

        // Populate room dropdowns
        const startInput = document.getElementById('startInput');
        const endInput = document.getElementById('endInput');

        const roomNames = data.nodes
            .filter(n => n.is_room)
            .map(n => n.name)
            .sort();

        // Set up datalist for autocomplete
        const datalist = document.getElementById('roomList');
        datalist.innerHTML = '';
        roomNames.forEach(name => {
            const option = document.createElement('option');
            option.value = name;
            datalist.appendChild(option);
        });

        console.log('Routing network loaded:', roomNames.length, 'rooms');
    } catch (error) {
        console.error('Error loading routing network:', error);
    }
}


// WELCOME MESSAGE
function showWelcome() {
    setTimeout(() => {
        const panel = document.getElementById('infoPanel');
        document.getElementById('elName').textContent = 'Welcome';
        document.getElementById('elType').textContent = 'DeKUT Campus Digital Twin';
        document.getElementById('elFloor').textContent = 'Click any element';
        document.getElementById('elArea').textContent = 'to view BIM data';
        document.getElementById('elCapacity').textContent = 'Indoor Routing';
        document.getElementById('elRisk').className = 'risk-badge low';
        document.getElementById('elRisk').textContent = 'Upload |Route | Click';
        panel.classList.add('visible');

        setTimeout(() => {
            panel.classList.remove('visible');
        }, 5000);
    }, 1000);
}