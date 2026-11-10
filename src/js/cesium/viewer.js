Cesium.Ion.defaultAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI4MTk1NWYyYi1iZWUwLTQzMjQtOWE5MS1jYzA5MTdmNzQwOTAiLCJpZCI6MjQwODQ3LCJpYXQiOjE3MjY4MDQxMjN9.c-Rb3rMh6Gfp1bqMZLmAtE1cyRWB5ckyk-dM3FbYFbs';

const USE_SELF_HOSTED = false;

const viewer = new Cesium.Viewer('cesiumContainer', {
    terrain: Cesium.Terrain.fromWorldTerrain(),

    baseLayer: Cesium.ImageryLayer.fromProviderAsync(
        Cesium.ArcGisMapServerImageryProvider.fromUrl(
            'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer'
        )
    ),

    animation: false,
    timeline: false,
    infoBox: false,
    selectionIndicator: false,
    baseLayerPicker: false,
    geocoder: false,
    homeButton: false,
    sceneModePicker: false,
    navigationHelpButton: false,
    fullscreenButton: false,
    shadows: true,

    useBrowserRecommendedResolution: true,
    maximumRenderLoopOptimization: true,
    requestRenderMode: true,
});

window.viewer = viewer;
window.buildingMatrix = null;
window.activeTileset = null;

const DEFAULT_LAT = -0.39811;
const DEFAULT_LON = 36.9617;
const DEFAULT_ALT = 1750;

viewer.camera.flyTo({
    destination: Cesium.Cartesian3.fromDegrees(DEFAULT_LON, DEFAULT_LAT, DEFAULT_ALT),
    duration: 2.0,
    orientation: {
        heading: Cesium.Math.toRadians(0),
        pitch: Cesium.Math.toRadians(-35),
        roll: 0
    }
});

console.log('Cesium Viewer initialized');

async function loadBuildingWithMatrix(tilesetUrl, latitude, longitude, elevation, northRotation) {
    try {
        if (window.activeTileset) {
            viewer.scene.primitives.remove(window.activeTileset);
            window.activeTileset = null;
        }

        const tileset = await Cesium.Cesium3DTileset.fromUrl(tilesetUrl);

        // Create transformation matrix
        const anchorCartesian = Cesium.Cartesian3.fromDegrees(
            longitude,
            latitude,
            elevation
        );

        let matrix = Cesium.Transforms.eastNorthUpToFixedFrame(anchorCartesian);
        if (northRotation !== 0) {
            const headingAngle = Cesium.Math.toRadians(-northRotation);
            const quaternion = Cesium.Quaternion.fromAxisAngle(
                Cesium.Cartesian3.UNIT_Z,
                headingAngle
            );
            const rotationMatrix = Cesium.Matrix3.fromQuaternion(quaternion);
            const rotationMatrix4 = Cesium.Matrix4.fromRotationTranslation(
                rotationMatrix,
                new Cesium.Cartesian3(0, 0, 0)
            );
            matrix = Cesium.Matrix4.multiply(matrix, rotationMatrix4, matrix);
        }

        tileset.modelMatrix = matrix;
        window.buildingMatrix = matrix;
        window.activeTileset = tileset;
        viewer.scene.primitives.add(tileset);
        viewer.zoomTo(tileset);
        console.log(' Building loaded with matrix transformation');
        return tileset;
    } catch (error) {
        console.error('Error loading building:', error);
        throw error;
    }
}
window.loadBuildingWithMatrix = loadBuildingWithMatrix;

function setupMetadataInspector() {
    const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);

    handler.setInputAction(function (movement) {
        const pickedFeature = viewer.scene.pick(movement.position);

        if (Cesium.defined(pickedFeature) &&
            pickedFeature instanceof Cesium.Cesium3DTileFeature) {

            console.log('=== BIM METADATA PROPERTIES ===');
            const propertyIds = pickedFeature.getPropertyIds();
            propertyIds.forEach((id) => {
                const value = pickedFeature.getProperty(id);
                console.log(`${id}: ${value}`);
            });
        }
    }, Cesium.ScreenSpaceEventType.LEFT_CLICK);
}

setupMetadataInspector();

console.log('Metadata inspector ready (click any building element)');