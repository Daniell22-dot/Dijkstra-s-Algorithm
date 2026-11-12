/**
 * 3D Routing Network - Fetches real data from backend API
 * 
 * Instead of hardcoded sample data, this module fetches the actual
 * network graph from the Flask backend API and stores it in window.networkData.
 */

// Base API URL - configure based on your deployment
const API_BASE = '/api/v1';

// Initialize network data storage
let networkData = {
    nodes: [],
    edges: [],
    floors: []
};

// Fetch real network data from backend API
async function fetchNetworkData() {
    try {
        const response = await fetch(`${API_BASE}/routing/network`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        if (result.success && result.data) {
            networkData = {
                nodes: result.data.nodes || [],
                edges: result.data.edges || [],
                floors: ['Ground', 'First', 'Second']  // Will be enriched from data
            };
            
            // Extract unique floors from nodes
            const nodeFloors = [...new Set(result.data.nodes.map(n => n.floor))];
            if (nodeFloors.length > 0) {
                networkData.floors = nodeFloors.sort();
            }
            
            // If edges have floor info, use that too
            if (result.data.edges && result.data.edges.length > 0) {
                const edgeFloors = [...new Set(result.data.edges.map(e => e.floor))];
                if (edgeFloors.length > 0) {
                    // Merge floors from both nodes and edges
                    const allFloors = [...new Set([...nodeFloors, ...edgeFloors])];
                    networkData.floors = allFloors.sort();
                }
            }
            
            console.log(`Network data loaded: ${networkData.nodes.length} nodes, ${networkData.edges.length} edges, floors: ${networkData.floors.join(', ')}`);
        } else {
            console.warn('Failed to load network data:', result.error);
        }
    } catch (error) {
        console.error('Error fetching network data:', error);
        // Fallback: mark as loading error, don't use hardcoded fallback
        networkData = { nodes: [], edges: [], floors: [] };
    }
}

// Initialize when module loads
fetchNetworkData();

 // Export for global access
 window.networkData = networkData;
 window.fetchNetworkData = fetchNetworkData;

 console.log('Routing network module loaded - fetching real data from API');