function findPath(startName, endName) {
    const nodes = window.networkData.nodes;
    const edges = window.networkData.edges;

    // Find node IDs by room number or recovered label
    const matches = (n, value) => {
        const needle = value.toLowerCase();
        return (n.name || '').toLowerCase() === needle ||
            (n.label || '').toLowerCase() === needle;
    };
    const startNode = nodes.find(n => matches(n, startName));
    const endNode = nodes.find(n => matches(n, endName));

    if (!startNode) {
        return { error: `Start location "${startName}" not found` };
    }
    if (!endNode) {
        return { error: `End location "${endName}" not found` };
    }

    // Build adjacency list
    const adj = {};
    nodes.forEach(n => { adj[n.id] = []; });
    edges.forEach(e => {
        adj[e.from].push({ to: e.to, weight: e.weight });
        adj[e.to].push({ to: e.from, weight: e.weight });
    });

    // Dijkstra's algorithm
    const distances = {};
    const previous = {};
    const unvisited = new Set();

    nodes.forEach(n => {
        distances[n.id] = Infinity;
        previous[n.id] = null;
        unvisited.add(n.id);
    });
    distances[startNode.id] = 0;

    while (unvisited.size > 0) {
        // Find node with minimum distance
        let currentId = null;
        let minDist = Infinity;
        unvisited.forEach(id => {
            if (distances[id] < minDist) {
                minDist = distances[id];
                currentId = id;
            }
        });

        if (currentId === null || minDist === Infinity) break;

        unvisited.delete(currentId);

        if (currentId === endNode.id) break;

        // Update neighbors
        adj[currentId].forEach(neighbor => {
            if (unvisited.has(neighbor.to)) {
                const alt = distances[currentId] + neighbor.weight;
                if (alt < distances[neighbor.to]) {
                    distances[neighbor.to] = alt;
                    previous[neighbor.to] = currentId;
                }
            }
        });
    }

    // Reconstruct path
    const pathIds = [];
    let current = endNode.id;
    while (current !== null && current !== startNode.id) {
        pathIds.unshift(current);
        current = previous[current];
    }
    pathIds.unshift(startNode.id);

    // Check if path is valid
    if (distances[endNode.id] === Infinity) {
        return null;
    }

    // Convert IDs to names with 3D coordinates
    const pathNodes = pathIds.map(id => nodes.find(n => n.id === id)).filter(n => n);

    const pathNames = pathNodes.map(n => n.label || n.name);
    const pathDetails = pathNodes.map(n => ({
        id: n.id,
        name: n.name,
        label: n.label || n.name,
        floor: n.floor,
        floor_elevation: n.floor_elevation || 0,
        x: n.x || 0,
        y: n.y || 0,
        z: n.z || 0,
        type: n.type || 'Room'
    }));

    return {
        path: pathNames,
        path_details: pathDetails,
        distance: distances[endNode.id],
        steps: pathIds.length - 1,
        nodes: pathNodes,
        start: startNode.label || startNode.name,
        end: endNode.label || endNode.name,
        floors: [...new Set(pathNodes.map(n => n.floor))]
    };
}

// Store function globally
window.findPath = findPath;

console.log('3D Routing engine ready (Dijkstra)');