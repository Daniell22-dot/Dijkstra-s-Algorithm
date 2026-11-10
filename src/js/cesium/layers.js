const floorHeights = {
    'Ground': 0.0,
    'First': 4.2,
    'Second': 8.4,
    'Third': 12.6
};

let currentActiveFloor = 'all';

let currentRouteEntity = null;
let rawRouteData = [];

function filterBuildingView(targetFloor) {
    currentActiveFloor = targetFloor;

    const tileset = window.activeTileset;
    if (!tileset) {
        console.warn('No tileset loaded');
        return;
    }

    if (targetFloor === 'all') {
        tileset.style = new Cesium.Cesium3DTileStyle({
            color: 'color("white", 1.0)'
        });
    } else {
        tileset.style = new Cesium.Cesium3DTileStyle({
            color: {
                conditions: [
                    [`${getFloorProperty()} == '${targetFloor}'`, 'color("white", 1.0)'],
                    ['true', 'color("white", 0.05)']
                ]
            }
        });
    }

    updateRouteLineVisibility();
    triggerBirdsEyeView(targetFloor);
}

function getFloorProperty() {
    return 'floor';
}

function triggerBirdsEyeView(targetFloor) {
    if (!window.buildingMatrix) {
        console.warn('No building matrix available');
        return;
    }

    const buildingCenter = Cesium.Matrix4.getTranslation(
        window.buildingMatrix,
        new Cesium.Cartesian3()
    );

    const cartographicCenter = Cesium.Cartographic.fromCartesian(buildingCenter);

    let floorOffset = 0;
    if (targetFloor !== 'all' && floorHeights[targetFloor] !== undefined) {
        floorOffset = floorHeights[targetFloor];
    }

    const targetHeight = cartographicCenter.height + floorOffset + 1750.0;

    const cameraDestination = Cesium.Cartesian3.fromRadians(
        cartographicCenter.longitude,
        cartographicCenter.latitude,
        targetHeight
    );

    viewer.camera.flyTo({
        destination: cameraDestination,
        orientation: {
            heading: Cesium.Math.toRadians(0),
            pitch: Cesium.Math.toRadians(-90.0),
            roll: 0.0
        },
        duration: 2.0
    });
}


function updateRouteLineVisibility() {
    if (!currentRouteEntity || rawRouteData.length === 0) {
        return;
    }

    const updatedPoints = [];

    rawRouteData.forEach(node => {
        if (currentActiveFloor !== 'all' && node.floor !== currentActiveFloor) {
            return;
        }
        const localPoint = new Cesium.Cartesian3(node.x, node.y, node.z);
        const globalPoint = Cesium.Matrix4.multiplyByPoint(
            window.buildingMatrix,
            localPoint,
            new Cesium.Cartesian3()
        );
        updatedPoints.push(globalPoint);
    });

    if (currentRouteEntity && currentRouteEntity.polyline) {
        currentRouteEntity.polyline.positions = updatedPoints;
    }
}

function drawRoute(pathDetails, color = Cesium.Color.CHARTREUSE) {
    if (currentRouteEntity) {
        viewer.entities.remove(currentRouteEntity);
        currentRouteEntity = null;
    }

    if (!pathDetails || pathDetails.length < 2) {
        return;
    }

    rawRouteData = pathDetails;
}

const globalPositions = [];
pathDetails.forEach(node => {
    const localPoint = new Cesium.Cartesian3(node.x, node.y, node.z);
    const globalPoint = Cesium.Matrix4.multiplyByPoint(
        window.buildingMatrix,
        localPoint,
        new Cesium.Cartesian3()
    );
    globalPositions.push(globalPoint);
});

currentRouteEntity = viewer.entities.add({
    name: 'Indoor Route',
    polyline: {
        positions: globalPositions,
        width: 6,
        material: new Cesium.PolylineGlowMaterialProperty({
            glowPower: 0.3,
            color: color
        }),
        clampToGround: false,
        depthFailMaterial: new Cesium.PolylineDashMaterialProperty({
            color: color.withAlpha(0.5)
        })
    }
});

if (globalPositions.length >= 2) {
    viewer.entities.add({
        position: globalPositions[0],
        point: {
            pixelSize: 14,
            color: Cesium.Color.GREEN,
            outlineColor: Cesium.Color.WHITE,
            outlineWidth: 2
        },
        label: {
            text: 'Start',
            font: '12px Inter, sans-serif',
            fillColor: Cesium.Color.WHITE,
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 2,
            pixelOffset: new Cesium.Cartesian2(0, -20),
            showBackground: true,
            backgroundColor: new Cesium.Color(0, 0, 0, 0.6),
            backgroundPadding: new Cesium.Cartesian2(6, 4)
        }
    });

    viewer.entities.add({
        position: globalPositions[globalPositions.length - 1],
        point: {
            pixelSize: 14,
            color: Cesium.Color.RED,
            outlineColor: Cesium.Color.WHITE,
            outlineWidth: 2
        },
        label: {
            text: 'End',
            font: '12px Inter, sans-serif',
            fillColor: Cesium.Color.WHITE,
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 2,
            pixelOffset: new Cesium.Cartesian2(0, -20),
            showBackground: true,
            backgroundColor: new Cesium.Color(0, 0, 0, 0.6),
            backgroundPadding: new Cesium.Cartesian2(6, 4)
        }
    });
}

console.log(' Route drawn with', globalPositions.length, 'points');

window.filterBuildingView = filterBuildingView;
window.triggerBirdsEyeView = triggerBirdsEyeView;
window.drawRoute = drawRoute;
window.updateRouteLineVisibility = updateRouteLineVisibility;
window.floorHeights = floorHeights;
window.currentActiveFloor = currentActiveFloor;