function formatDistance(dist) {
    if (dist < 10) return dist.toFixed(1) + ' m';
    if (dist < 100) return dist.toFixed(0) + ' m';
    return (dist / 1000).toFixed(1) + ' km';
}

function getElementCount() {
    const entities = window.viewer?.entities?.values || [];
    return entities.filter(e => e.properties && e.properties.name).length;
}

function updateStatus(message, color = 'rgba(255,255,255,0.15)') {
    const status = document.getElementById('routeStatus');
    if (status) {
        status.textContent = message;
        status.style.color = color;
    }
}

window.utils = {
    formatDistance,
    getElementCount,
    updateStatus
};