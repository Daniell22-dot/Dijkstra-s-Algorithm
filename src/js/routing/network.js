const networkData = {
    nodes: [
        // Ground Floor
        { id: 'R101', name: 'Room 101', floor: 'Ground', floor_elevation: 0, x: 0, y: 0, z: 0, is_room: true, type: 'Lecture Hall' },
        { id: 'R102', name: 'Room 102', floor: 'Ground', floor_elevation: 0, x: 10, y: 0, z: 0, is_room: true, type: 'Computer Lab' },
        { id: 'R103', name: 'Room 103', floor: 'Ground', floor_elevation: 0, x: 20, y: 0, z: 0, is_room: true, type: 'Workshop' },
        { id: 'R104', name: 'Room 104', floor: 'Ground', floor_elevation: 0, x: 0, y: 10, z: 0, is_room: true, type: 'Office' },
        { id: 'D101', name: 'Main Entrance', floor: 'Ground', floor_elevation: 0, x: 5, y: -10, z: 0, is_room: false, type: 'Door' },
        { id: 'Stair1', name: 'Stairway Ground', floor: 'Ground', floor_elevation: 0, x: 10, y: 5, z: 0, is_room: false, type: 'Stairway' },

        // First Floor
        { id: 'R201', name: 'Room 201', floor: 'First', floor_elevation: 4.2, x: 0, y: 0, z: 4.2, is_room: true, type: 'Lecture Hall' },
        { id: 'R202', name: 'Room 202', floor: 'First', floor_elevation: 4.2, x: 10, y: 0, z: 4.2, is_room: true, type: 'Office' },
        { id: 'R203', name: 'Room 203', floor: 'First', floor_elevation: 4.2, x: 20, y: 0, z: 4.2, is_room: true, type: 'Conference Room' },
        { id: 'R204', name: 'Room 204', floor: 'First', floor_elevation: 4.2, x: 0, y: 10, z: 4.2, is_room: true, type: 'Computer Lab' },
        { id: 'Stair2', name: 'Stairway First', floor: 'First', floor_elevation: 4.2, x: 10, y: 5, z: 4.2, is_room: false, type: 'Stairway' },

        // Second Floor
        { id: 'R301', name: 'Room 301', floor: 'Second', floor_elevation: 8.4, x: 0, y: 0, z: 8.4, is_room: true, type: 'Research Lab' },
        { id: 'R302', name: 'Room 302', floor: 'Second', floor_elevation: 8.4, x: 10, y: 0, z: 8.4, is_room: true, type: 'Design Studio' },
        { id: 'R303', name: 'Room 303', floor: 'Second', floor_elevation: 8.4, x: 20, y: 0, z: 8.4, is_room: true, type: 'Office' },
        { id: 'Stair3', name: 'Stairway Second', floor: 'Second', floor_elevation: 8.4, x: 10, y: 5, z: 8.4, is_room: false, type: 'Stairway' },
    ],
    edges: [
        // Ground Floor connections
        { from: 'R101', to: 'D101', weight: 8, floor: 'Ground', type: 'door' },
        { from: 'R101', to: 'R102', weight: 5, floor: 'Ground', type: 'corridor' },
        { from: 'R102', to: 'R103', weight: 5, floor: 'Ground', type: 'corridor' },
        { from: 'R102', to: 'R104', weight: 7, floor: 'Ground', type: 'corridor' },
        { from: 'R102', to: 'Stair1', weight: 3, floor: 'Ground', type: 'corridor' },
        { from: 'R103', to: 'Stair1', weight: 4, floor: 'Ground', type: 'corridor' },
        { from: 'D101', to: 'Stair1', weight: 4, floor: 'Ground', type: 'corridor' },

        // Stairs (floor transitions - Z changes)
        { from: 'Stair1', to: 'Stair2', weight: 2, floor: 'Transition', type: 'stair' },
        { from: 'Stair2', to: 'Stair3', weight: 2, floor: 'Transition', type: 'stair' },

        // First Floor connections
        { from: 'Stair2', to: 'R201', weight: 4, floor: 'First', type: 'corridor' },
        { from: 'Stair2', to: 'R202', weight: 3, floor: 'First', type: 'corridor' },
        { from: 'Stair2', to: 'R204', weight: 5, floor: 'First', type: 'corridor' },
        { from: 'R201', to: 'R202', weight: 5, floor: 'First', type: 'corridor' },
        { from: 'R202', to: 'R203', weight: 5, floor: 'First', type: 'corridor' },
        { from: 'R203', to: 'R204', weight: 7, floor: 'First', type: 'corridor' },

        // Second Floor connections
        { from: 'Stair3', to: 'R301', weight: 4, floor: 'Second', type: 'corridor' },
        { from: 'Stair3', to: 'R302', weight: 3, floor: 'Second', type: 'corridor' },
        { from: 'R301', to: 'R302', weight: 5, floor: 'Second', type: 'corridor' },
        { from: 'R302', to: 'R303', weight: 5, floor: 'Second', type: 'corridor' },
    ],
    floors: ['Ground', 'First', 'Second']
};

// Store network globally
window.networkData = networkData;

console.log('3D Network loaded with', networkData.nodes.length, 'nodes and', networkData.edges.length, 'edges');
console.log('Floors:', networkData.floors.join(', '));