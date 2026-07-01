document.addEventListener('DOMContentLoaded', () => {
    console.log(' DeKUT 3D Campus Digital Twin');
    console.log(' Click any room to view details');
    console.log(' Use mouse to navigate: Zoom, Pan, Rotate');
    console.log(' Press ESC to close panels');

    initApp();
});

function initApp() {
    
    setupUI();

    showWelcome();
}

function setupUI() {
    // Info panel close button
    const closeBtn = document.getElementById('closeInfo');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            document.getElementById('infoPanel').classList.remove('visible');
        });
    }

    // Routing panel close button
    const closeRouting = document.getElementById('closeRouting');
    if (closeRouting) {
        closeRouting.addEventListener('click', () => {
            document.getElementById('routingPanel').classList.remove('visible');
        });
    }

    // Routing toggle button
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
}

function handleRouteRequest() {
    const start = document.getElementById('startInput').value.trim();
    const end = document.getElementById('endInput').value.trim();

    if (!start || !end) {
        document.getElementById('routeResult').innerHTML = `
            <span class="route-info"> Please enter both start and end locations</span>
        `;
        return;
    }

    // Call routing function from shortest-path.js
    if (window.findPath) {
        const result = window.findPath(start, end);
        const resultDiv = document.getElementById('routeResult');

        if (result) {
            resultDiv.innerHTML = `
                <div class="route-found"> Route found!</div>
                <div class="route-distance"> ${result.distance} · ${result.steps} steps</div>
                <div style="color:rgba(255,255,255,0.2); font-size:10px; margin-top:4px;">
                    ${result.path.join(' → ')}
                </div>
            `;
            document.getElementById('routeStatus').textContent = 'Route found!';
            document.getElementById('routeStatus').style.color = '#34d399';
        } else {
            resultDiv.innerHTML = `
                <span class="route-info"> No route found between "${start}" and "${end}"</span>
            `;
            document.getElementById('routeStatus').textContent = 'No route';
            document.getElementById('routeStatus').style.color = '#ef4444';
        }
    } else {
        document.getElementById('routeResult').innerHTML = `
            <span class="route-info"> Routing engine loading...</span>
        `;
    }
}

function showWelcome() {
    setTimeout(() => {
        const panel = document.getElementById('infoPanel');
        document.getElementById('elName').textContent = ' Welcome';
        document.getElementById('elType').textContent = 'DeKUT Campus Digital Twin';
        document.getElementById('elFloor').textContent = 'Click any element';
        document.getElementById('elArea').textContent = 'to view BIM data';
        document.getElementById('elCapacity').textContent = ' Indoor Routing';
        document.getElementById('elEquipment').textContent = ' Shortest Path';
        document.getElementById('elRisk').className = 'risk-badge low';
        document.getElementById('elRisk').textContent = ' Click → Info | Route → Find Path';
        panel.classList.add('visible');

        setTimeout(() => {
            panel.classList.remove('visible');
        }, 4000);
    }, 1000);
}