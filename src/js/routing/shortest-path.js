/**
 * 3D Shortest Path - Dijkstra Algorithm using real backend data
 * 
 * Uses window.networkData fetched from the backend API.
 * If network data is not yet loaded, will wait and retry.
 */

// Base API URL
const API_BASE = '/api/v1';

// Node lookup cache - populated when network data loads
let nodeLookup = {};

// Track if network data has been loaded
let networkLoaded = false;

/**
 * Initialize network data from window.networkData
 * Called by network.js when data loads
 */
function initNetworkData() {
    const networkData = window.networkData;
    if (networkData && networkData.nodes && networkData.nodes.length > 0) {
        networkLoaded = true;
        
        // Build node lookup by ID
        nodeLookup = {};
        networkData.nodes.forEach(n => {
            nodeLookup[n.id] = n;
        });
        
        console.log(`Network data initialized: ${networkData.nodes.length} nodes, ${networkData.edges.length} edges`);
    } else {
        // Retry after short delay
        setTimeout(initNetworkData, 500);
    }
}

// Initialize on module load
initNetworkData();

/**
 * Find shortest path between two rooms/nodes using Dijkstra
 * @param {string} startId - Start node ID (matches network data IDs)
 * @param {string} endId - End node ID
 * @param {Object} options - Optional settings
 * @returns {Promise<Object>} Path result
 */
async function findPath(startId, endId, options = {}) {
    // Wait for network data to load if not ready
    if (!networkLoaded) {
        await new Promise(resolve => setTimeout(resolve, 1000));
        await initNetworkData();
    }
    
    // Check if we have the start and end nodes
    if (!nodeLookup[startId]) {
        // Try to fetch from backend API
        try {
            const response = await fetch(`${API_BASE}/routing/path/${startId}/${endId}`);
            if (response.ok) {
                const result = await response.json();
                if (result.success && result.data && result.data.path_details) {
                    return formatPathResult(result.data.path_details, result.data.distance, result.data.steps);
                }
            }
        } catch (e) {
            console.error('API path fetch failed:', e);
        }
        return { error: `Start node "${startId}" not found in network data` };
    }
    
    if (!nodeLookup[endId]) {
        return { error: `End node "${endId}" not found in network data` };
    }
    
    // Build adjacency list from network data edges
    const edges = window.networkData.edges || [];
    const adj = {};
    
    // Initialize all nodes
    window.networkData.nodes.forEach(n => {
        adj[n.id] = [];
    });
    
    // Add edges (both directions since it's undirected)
    edges.forEach(e => {
        adj[e.from].push({ to: e.to, weight: e.weight });
        adj[e.to].push({ to: e.from, weight: e.weight });
    });
    
    // Dijkstra's algorithm
    const distances = {};
    const previous = {};
    const unvisited = new Set();
    
    window.networkData.nodes.forEach(n => {
        distances[n.id] = Infinity;
        previous[n.id] = null;
        unvisited.add(n.id);
    });
    distances[startId] = 0;
    
    while (unvisited.size > 0) {
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
        
        if (currentId === endId) break;
        
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
    let current = endId;
    while (current !== null && current !== startId) {
        pathIds.unshift(current);
        current = previous[current];
    }
    pathIds.unshift(startId);
    
    // Check if path is valid
    if (distances[endId] === Infinity) {
        return { error: 'No path found between the specified nodes' };
    }
    
    // Convert IDs to node details
    const pathNodes = pathIds.map(id => nodeLookup[id] || window.networkData.nodes.find(n => n.id === id)).filter(n => n);
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
        distance: distances[endId],
        steps: pathIds.length - 1,
        nodes: pathNodes,
        start: startId,
        end: endId,
        floors: [...new Set(pathNodes.map(n => n.floor))]
    };
}

/**
 * Get distance between two nodes without full path
 * @param {string} startId 
 * @param {string} endId 
 * @returns {Promise<Object>} Distance result
 */
async function getDistance(startId, endId) {
    // Ensure network data is loaded
    if (!networkLoaded) {
        await new Promise(resolve => setTimeout(resolve, 1000));
        await initNetworkData();
    }
    
    // Build adjacency list
    const adj = {};
    window.networkData.nodes.forEach(n => { adj[n.id] = []; });
    (window.networkData.edges || []).forEach(e => {
        adj[e.from].push({ to: e.to, weight: e.weight });
        adj[e.to].push({ to: e.from, weight: e.from });
    });
    
    // Dijkstra
    const distances = {};
    const previous = {};
    const unvisited = new Set();
    window.networkData.nodes.forEach(n => {
        distances[n.id] = Infinity;
        previous[n.id] = null;
        unvisited.add(n.id);
    });
    distances[startId] = 0;
    
    while (unvisited.size > 0) {
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
        
        if (currentId === endId) break;
        
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
    
    if (distances[endId] === Infinity) {
        return { error: 'No path found' };
    }
    return { distance: distances[endId], steps: pathIds.length - 1 };
}

/**
 * Format path result from API or client-side
 * @param {Array} pathDetails - Path details array
 * @param {number} distance - Total distance
 * @param {number} steps - Number of steps
 * @returns {Object} Formatted result
 */
function formatPathResult(pathDetails, distance, steps) {
    if (!pathDetails || pathDetails.length === 0) {
        return { error: 'No path found' };
    }
    
    const pathNames = pathDetails.map(n => n.name || n.label || n.id);
    const pathDetailsFormatted = pathDetails.map(n => ({
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
    
    const allFloors = [...new Set(pathDetails.map(n => n.floor))];
    
    return {
        path: pathNames,
        path_details: pathDetailsFormatted,
        distance: distance || 0,
        steps: steps || (pathDetails.length - 1),
        nodes: pathDetails.map(n => ({
            id: n.id,
            name: n.name,
            label: n.label || n.name,
            floor: n.floor
        })),
        start: pathDetails[0] ? pathDetails[0].id : startId,
        end: pathDetails[pathDetails.length - 1] ? pathDetails[pathDetails.length - 1].id : endId,
        floors: allFloors
    };
}

/**
 * Validate if two rooms are connected
 * @param {string} startId 
 * @param {string} endId 
 * @returns {Promise<Object>} Validation result
 */
async function validateRooms(startId, endId) {
    // Ensure network data is loaded
    if (!networkLoaded) {
        await new Promise(resolve => setTimeout(resolve, 1000));
        await initNetworkData();
    }
    
    // Check if nodes exist
    if (!nodeLookup[startId] || !nodeLookup[endId]) {
        // Try API validation
        try {
            const response = await fetch(`${API_BASE}/routing/validate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ start: startId, end: endId })
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    return { connected: true, data: result.data };
                }
            }
        } catch (e) {
            console.error('API validate failed:', e);
        }
        
        // Client-side check: see if there's a path
        try {
            const pathResult = await findPath(startId, endId);
            if (!pathResult.error) {
                return { connected: true, path: pathResult.path, distance: pathResult.distance };
            }
        } catch (e) {
            // Continue to return disconnected
        }
        
        return { connected: false, error: 'Nodes not found and API validation failed' };
    }
    
    // Client-side validation using Dijkstra
    // Build adjacency list
    const adj = {};
    window.networkData.nodes.forEach(n => { adj[n.id] = [] });
    (window.networkData.edges || []).forEach(e => {
        adj[e.from].push({ to: e.to, weight: e.weight });
        adj[e.to].push({ to: e.from, weight: e.from });
    });
    
    // Dijkstra
    const distances = {};
    const previous = {};
    const unvisited = new Set();
    window.networkData.nodes.forEach(n => {
        distances[n.id] = Infinity;
        previous[n.id] = null;
        unvisited.add(n.id);
    });
    distances[startId] = 0;
    
    while (unvisited.size > 0) {
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
        
        if (currentId === endId) break;
        
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
    
    if (distances[endId] === Infinity) {
        return { connected: false, error: 'No path found' };
    }
    
    return { connected: true, path: findPath(startId, endId).path, distance: findPath(startId, endId).distance };
}

// Export globally for UI integration
window.findPath = findPath;
window.getDistance = getDistance;
window.validateRooms = validateRooms;
window.initNetworkData = initNetworkData;
window.API_BASE = API_BASE;
window.nodeLookup = nodeLookup;
window.networkLoaded = networkLoaded;

console.log('Routing pathfinding module loaded - uses real backend data');