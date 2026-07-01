const networkData = {
    nodes: [
        { id: 'R101', name: 'Room 101', floor: 1, x: 0, y: 0 },
        { id: 'R102', name: 'Room 102', floor: 1, x: 10, y: 0 },
        { id: 'R103', name: 'Room 103', floor: 1, x: 20, y: 0 },
        { id: 'D101', name: 'Main Entrance', floor: 0, x: 5, y: -10 },
        { id: 'Stair1', name: 'Stairway A', floor: 1, x: 10, y: 5 },
        { id: 'R201', name: 'Room 201', floor: 2, x: 0, y: 0 },
        { id: 'R202', name: 'Room 202', floor: 2, x: 10, y: 0 },
        { id: 'R203', name: 'Room 203', floor: 2, x: 20, y: 0 },
        { id: 'Stair2', name: 'Stairway A', floor: 2, x: 10, y: 5 },
        { id: 'R301', name: 'Room 301', floor: 3, x: 0, y: 0 },
        { id: 'R302', name: 'Room 302', floor: 3, x: 10, y: 0 },
        { id: 'Stair3', name: 'Stairway A', floor: 3, x: 10, y: 5 },
    ],
    edges: [
        // Floor 1 connections
        { from: 'R101', to: 'D101', weight: 8 },
        { from: 'R101', to: 'R102', weight: 5 },
        { from: 'R102', to: 'R103', weight: 5 },
        { from: 'R102', to: 'Stair1', weight: 3 },
        { from: 'R103', to: 'Stair1', weight: 4 },
        { from: 'D101', to: 'Stair1', weight: 4 },

        // Stairs (floor transitions)
        { from: 'Stair1', to: 'Stair2', weight: 2 },
        { from: 'Stair2', to: 'Stair3', weight: 2 },

        // Floor 2 connections
        { from: 'Stair2', to: 'R201', weight: 4 },
        { from: 'Stair2', to: 'R202', weight: 3 },
        { from: 'R201', to: 'R202', weight: 5 },
        { from: 'R202', to: 'R203', weight: 5 },

        // Floor 3 connections
        { from: 'Stair3', to: 'R301', weight: 4 },
        { from: 'Stair3', to: 'R302', weight: 3 },
        { from: 'R301', to: 'R302', weight: 5 },
    ]
};

// Store network globally
window.networkData = networkData;

console.log('🗺️ Network loaded with', networkData.nodes.length, 'nodes and', networkData.edges.length, 'edges');