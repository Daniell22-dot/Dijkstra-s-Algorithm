Cesium.Ion.defaultAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI4MTk1NWYyYi1iZWUwLTQzMjQtOWE5MS1jYzA5MTdmNzQwOTAiLCJpZCI6MjQwODQ3LCJpYXQiOjE3MjY4MDQxMjN9.c-Rb3rMh6Gfp1bqMZLmAtE1cyRWB5ckyk-dM3FbYFbs';

// Initialize viewer
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
});


window.viewer = viewer;

viewer.camera.flyTo({
    destination: Cesium.Cartesian3.fromDegrees(36.9617, -0.39811, 400),
    duration: 2.0,
    orientation: {
        heading: Cesium.Math.toRadians(0),
        pitch: Cesium.Math.toRadians(-35),
        roll: 0
    }
});

console.log(' Cesium Viewer initialized');