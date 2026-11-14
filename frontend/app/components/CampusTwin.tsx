"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type * as CesiumTypes from "cesium";

type Floor = "all" | "Ground" | "First" | "Second";

type NetworkNode = {
  id: string;
  name: string;
  label?: string | null;
  floor: string;
  x: number;
  y: number;
  z: number;
  type?: string;
  is_room?: boolean;
};

type NetworkEdge = {
  from: string;
  to: string;
  weight: number;
  floor?: string;
  type?: string;
};

type NetworkData = {
  nodes: NetworkNode[];
  edges: NetworkEdge[];
  floors?: string[];
};

type BuildingConfig = {
  lat: number;
  lon: number;
  alt: number;
  north_rotation: number;
  tileset_url: string;
};

type RouteResult = {
  path: string[];
  path_details: NetworkNode[];
  distance: number;
  steps: number;
  floors: string[];
};

type StoreyTile = {
  extras?: {
    properties?: {
      spatialStructure?: {
        name?: string;
      };
    };
  };
  content?: {
    _model?: {
      show: boolean;
    };
  };
  children?: StoreyTile[];
};

type ViewerApi = {
  setFloor: (floor: Floor) => void;
  drawRoute: (nodes: NetworkNode[]) => void;
  clearRoute: () => void;
  resetView: () => void;
  topView: () => void;
};

const FALLBACK_BUILDING: BuildingConfig = {
  lat: -0.39916111111111113,
  lon: 36.96279722222223,
  alt: 1772,
  north_rotation: 270,
  tileset_url: "/models/3dtiles/dedo/tileset.json",
};

const FLOOR_TILES: Record<Exclude<Floor, "all">, string> = {
  Ground: "Ground Floor",
  First: "1. Story",
  Second: "2. Story",
};

const FLOOR_Z: Record<Exclude<Floor, "all">, number> = {
  Ground: 0.1,
  First: 3.1,
  Second: 6.1,
};

const FLOOR_OPTIONS: Floor[] = ["all", "Ground", "First", "Second"];

declare global {
  interface Window {
    CESIUM_BASE_URL?: string;
    viewer?: CesiumTypes.Viewer;
    activeTileset?: CesiumTypes.Cesium3DTileset;
  }
}

function nodeLabel(node: NetworkNode) {
  return node.label?.trim() || `Room ${node.name}`;
}

function findPath(
  network: NetworkData,
  startId: string,
  endId: string
): RouteResult | { error: string } {
  const nodeMap = new Map(network.nodes.map((node) => [node.id, node]));
  const start = nodeMap.get(startId);
  const end = nodeMap.get(endId);

  if (!start) return { error: "Start room was not found in the routing graph." };
  if (!end) return { error: "Destination room was not found in the routing graph." };
  if (startId === endId) return { error: "Choose two different rooms." };

  const adjacency = new Map<string, Array<{ to: string; weight: number }>>();
  network.nodes.forEach((node) => adjacency.set(node.id, []));

  network.edges.forEach((edge) => {
    const weight = Number(edge.weight);
    if (!Number.isFinite(weight) || weight <= 0) return;
    adjacency.get(edge.from)?.push({ to: edge.to, weight });
    adjacency.get(edge.to)?.push({ to: edge.from, weight });
  });

  const distances = new Map<string, number>();
  const previous = new Map<string, string | null>();
  const unvisited = new Set<string>();

  network.nodes.forEach((node) => {
    distances.set(node.id, Number.POSITIVE_INFINITY);
    previous.set(node.id, null);
    unvisited.add(node.id);
  });
  distances.set(startId, 0);

  while (unvisited.size > 0) {
    let currentId: string | null = null;
    let currentDistance = Number.POSITIVE_INFINITY;

    unvisited.forEach((id) => {
      const distance = distances.get(id) ?? Number.POSITIVE_INFINITY;
      if (distance < currentDistance) {
        currentDistance = distance;
        currentId = id;
      }
    });

    if (currentId === null || currentDistance === Number.POSITIVE_INFINITY) break;
    unvisited.delete(currentId);
    if (currentId === endId) break;

    for (const neighbour of adjacency.get(currentId) ?? []) {
      if (!unvisited.has(neighbour.to)) continue;
      const alternative = currentDistance + neighbour.weight;
      if (alternative < (distances.get(neighbour.to) ?? Number.POSITIVE_INFINITY)) {
        distances.set(neighbour.to, alternative);
        previous.set(neighbour.to, currentId);
      }
    }
  }

  const totalDistance = distances.get(endId) ?? Number.POSITIVE_INFINITY;
  if (!Number.isFinite(totalDistance)) {
    return { error: "No walkable route exists between those rooms." };
  }

  const pathIds: string[] = [];
  let cursor: string | null = endId;
  while (cursor !== null && cursor !== startId) {
    pathIds.unshift(cursor);
    cursor = previous.get(cursor) ?? null;
  }
  pathIds.unshift(startId);

  const pathDetails = pathIds
    .map((id) => nodeMap.get(id))
    .filter((node): node is NetworkNode => Boolean(node));

  return {
    path: pathDetails.map(nodeLabel),
    path_details: pathDetails,
    distance: totalDistance,
    steps: Math.max(0, pathIds.length - 1),
    floors: [...new Set(pathDetails.map((node) => node.floor))],
  };
}

export default function CampusTwin() {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const viewerApiRef = useRef<ViewerApi | null>(null);
  const pickMarkerRef = useRef<CesiumTypes.Entity | null>(null);

  const [status, setStatus] = useState("Booting Cesium");
  const [network, setNetwork] = useState<NetworkData | null>(null);
  const [building, setBuilding] = useState<BuildingConfig | null>(null);
  const [floor, setFloor] = useState<Floor>("all");
  const [startId, setStartId] = useState("");
  const [endId, setEndId] = useState("");
  const [route, setRoute] = useState<RouteResult | null>(null);
  const [routeError, setRouteError] = useState("");
  const [picked, setPicked] = useState("");
  const [isRouting, setIsRouting] = useState(false);
  const [cameraPitch, setCameraPitch] = useState<number | null>(null);
  const [tileCount, setTileCount] = useState<number | null>(null);

  const roomNodes = useMemo(() => {
    if (!network) return [];
    return network.nodes
      .filter((node) => node.is_room && node.type !== "Corridor")
      .sort((a, b) => {
        const floorOrder = ["Ground", "First", "Second"];
        const floorDelta = floorOrder.indexOf(a.floor) - floorOrder.indexOf(b.floor);
        if (floorDelta !== 0) return floorDelta;
        return nodeLabel(a).localeCompare(nodeLabel(b));
      });
  }, [network]);

  const defaultStartId = useMemo(() => {
    if (!roomNodes.length) return "";
    const preferred = roomNodes.find((node) =>
      nodeLabel(node).toLowerCase().includes("analytical chem")
    );
    return (preferred ?? roomNodes[0]).id;
  }, [roomNodes]);

  const defaultEndId = useMemo(() => {
    if (!roomNodes.length) return "";
    const preferred = roomNodes.find((node) =>
      nodeLabel(node).toLowerCase().includes("dean school")
    );
    return (preferred ?? roomNodes[roomNodes.length - 1]).id;
  }, [roomNodes]);

  const effectiveStartId = startId || defaultStartId;
  const effectiveEndId = endId || defaultEndId;

  useEffect(() => {
    let disposed = false;
    let viewer: CesiumTypes.Viewer | null = null;
    let clickHandler: CesiumTypes.ScreenSpaceEventHandler | null = null;
    let tileset: CesiumTypes.Cesium3DTileset | null = null;
    let targetMatrix: CesiumTypes.Matrix4 | null = null;
    let handleCameraChanged: (() => void) | null = null;
    let activeFloor: Floor = "all";
    const routeEntities: CesiumTypes.Entity[] = [];
    const storeyTiles = new Map<string, StoreyTile>();

    const requestRender = () => viewer?.scene.requestRender();

    const applyFloorToTile = (tile: StoreyTile) => {
      const name = tile.extras?.properties?.spatialStructure?.name;
      if (!name) return;
      const expectedName = activeFloor === "all" ? null : FLOOR_TILES[activeFloor];
      const shouldShow = expectedName === null || name === expectedName;
      if (tile.content?._model) {
        tile.content._model.show = shouldShow;
      }
    };

    const applyFloorToAll = () => {
      storeyTiles.forEach((tile) => applyFloorToTile(tile));
      requestRender();
    };

    const collectStoreyTiles = (tile: StoreyTile) => {
      const name = tile.extras?.properties?.spatialStructure?.name;
      if (name && Object.values(FLOOR_TILES).includes(name)) {
        storeyTiles.set(name, tile);
      }
      tile.children?.forEach(collectStoreyTiles);
    };

    const clearRouteEntities = () => {
      if (!viewer) return;
      routeEntities.forEach((entity) => viewer?.entities.remove(entity));
      routeEntities.length = 0;
      requestRender();
    };

    const init = async () => {
      if (!containerRef.current) return;

      setStatus("Loading campus data");
      const [registryResponse, networkResponse] = await Promise.all([
        fetch("/data/campus_registry.json", { cache: "no-store" }),
        fetch("/data/routing/network_graph.json", { cache: "no-store" }),
      ]);

      const registry = registryResponse.ok ? await registryResponse.json() : {};
      const networkData: NetworkData = await networkResponse.json();
      if (disposed) return;

      const registeredBuilding = registry?.DEDO ?? {};
      const buildingConfig: BuildingConfig = {
        ...FALLBACK_BUILDING,
        ...registeredBuilding,
        tileset_url: "/models/3dtiles/dedo/tileset.json",
      };

      setBuilding(buildingConfig);
      setNetwork(networkData);
      setStatus("Starting WebGL");

      window.CESIUM_BASE_URL = "/cesium";
      const Cesium = await import("cesium");
      if (disposed || !containerRef.current) return;

      viewer = new Cesium.Viewer(containerRef.current, {
        baseLayer: false,
        terrain: undefined,
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
        requestRenderMode: false,
        useBrowserRecommendedResolution: true,
      });

      window.viewer = viewer;
      viewer.scene.backgroundColor = Cesium.Color.BLACK;
      viewer.scene.globe.show = false;
      if (viewer.scene.skyBox) viewer.scene.skyBox.show = false;
      if (viewer.scene.skyAtmosphere) viewer.scene.skyAtmosphere.show = false;
      viewer.scene.fog.enabled = false;
      viewer.scene.globe.depthTestAgainstTerrain = false;
      viewer.scene.screenSpaceCameraController.minimumZoomDistance = 4;
      viewer.scene.screenSpaceCameraController.maximumZoomDistance = 5000;

      handleCameraChanged = () => {
        if (viewer) setCameraPitch(Cesium.Math.toDegrees(viewer.camera.pitch));
      };
      viewer.camera.changed.addEventListener(handleCameraChanged);

      const anchor = Cesium.Cartesian3.fromDegrees(
        buildingConfig.lon,
        buildingConfig.lat,
        buildingConfig.alt
      );

      let matrix = Cesium.Transforms.eastNorthUpToFixedFrame(anchor);
      if (buildingConfig.north_rotation !== 0) {
        const headingAngle = Cesium.Math.toRadians(-buildingConfig.north_rotation);
        const quaternion = Cesium.Quaternion.fromAxisAngle(
          Cesium.Cartesian3.UNIT_Z,
          headingAngle
        );
        const rotation = Cesium.Matrix3.fromQuaternion(quaternion);
        const rotation4 = Cesium.Matrix4.fromRotationTranslation(
          rotation,
          Cesium.Cartesian3.ZERO
        );
        matrix = Cesium.Matrix4.multiply(matrix, rotation4, new Cesium.Matrix4());
      }
      targetMatrix = matrix;

      const groundHalfLat = 90 / 111320;
      const groundHalfLon = 90 / (111320 * Math.cos((buildingConfig.lat * Math.PI) / 180));
      viewer.entities.add({
        name: "Campus ground",
        rectangle: {
          coordinates: Cesium.Rectangle.fromDegrees(
            buildingConfig.lon - groundHalfLon,
            buildingConfig.lat - groundHalfLat,
            buildingConfig.lon + groundHalfLon,
            buildingConfig.lat + groundHalfLat
          ),
          height: buildingConfig.alt - 0.6,
          material: Cesium.Color.fromCssColorString("#05090d").withAlpha(0.96),
          outline: true,
          outlineColor: Cesium.Color.fromCssColorString("#05e563").withAlpha(0.28),
        },
      });

      setStatus("Loading 3D Tiles");
      tileset = await Cesium.Cesium3DTileset.fromUrl(buildingConfig.tileset_url, {
        maximumScreenSpaceError: 8,
        skipLevelOfDetail: true,
      });
      if (disposed) {
        tileset.destroy();
        return;
      }

      const rootTransform = tileset.root?.transform ?? Cesium.Matrix4.IDENTITY;
      const inverseRoot = Cesium.Matrix4.inverse(rootTransform, new Cesium.Matrix4());
      if (!inverseRoot) {
        throw new Error("The tileset root transform is not invertible.");
      }
      tileset.modelMatrix = Cesium.Matrix4.multiply(
        matrix,
        inverseRoot,
        new Cesium.Matrix4()
      );
      viewer.scene.primitives.add(tileset);
      window.activeTileset = tileset;

      collectStoreyTiles(tileset.root as unknown as StoreyTile);
      tileset.tileVisible.addEventListener((tile) => {
        applyFloorToTile(tile as unknown as StoreyTile);
      });
      const tileStats = tileset as unknown as {
        statistics?: { numberOfTilesTotal?: number };
      };
      setTileCount(tileStats.statistics?.numberOfTilesTotal ?? null);
      tileset.allTilesLoaded.addEventListener(() => {
        applyFloorToAll();
        if (tileset) {
          setTileCount(
            (tileset as unknown as {
              statistics?: { numberOfTilesTotal?: number };
            }).statistics?.numberOfTilesTotal ?? null
          );
        }
      });

      const flyToFloor = (selectedFloor: Floor) => {
        if (!viewer || !targetMatrix) return;
        const z = selectedFloor === "all" ? 3 : FLOOR_Z[selectedFloor];
        const center = Cesium.Matrix4.multiplyByPoint(
          targetMatrix,
          new Cesium.Cartesian3(0, 0, z),
          new Cesium.Cartesian3()
        );
        const radius = selectedFloor === "all" ? 55 : 32;
        viewer.camera.flyToBoundingSphere(new Cesium.BoundingSphere(center, radius), {
          offset: new Cesium.HeadingPitchRange(
            Cesium.Math.toRadians(25),
            Cesium.Math.toRadians(-32),
            selectedFloor === "all" ? 135 : 82
          ),
          duration: 1.2,
        });
      };

      const drawRoute = (nodes: NetworkNode[]) => {
        if (!viewer || !targetMatrix) return;
        clearRouteEntities();
        if (nodes.length < 2) return;

        const positions = nodes.map((node) =>
          Cesium.Matrix4.multiplyByPoint(
            targetMatrix as CesiumTypes.Matrix4,
            new Cesium.Cartesian3(node.x, node.y, node.z),
            new Cesium.Cartesian3()
          )
        );

        const routeColor = Cesium.Color.fromCssColorString("#05e563");
        routeEntities.push(
          viewer.entities.add({
            name: "Indoor route",
            polyline: {
              positions,
              width: 7,
              material: new Cesium.PolylineGlowMaterialProperty({
                glowPower: 0.28,
                color: routeColor,
              }),
              depthFailMaterial: new Cesium.PolylineDashMaterialProperty({
                color: routeColor.withAlpha(0.45),
              }),
              clampToGround: false,
            },
          })
        );

        const endpoint = (
          position: CesiumTypes.Cartesian3,
          text: string,
          color: CesiumTypes.Color
        ) => {
          if (!viewer) return;
          routeEntities.push(
            viewer.entities.add({
              position,
              point: {
                pixelSize: 14,
                color,
                outlineColor: Cesium.Color.WHITE,
                outlineWidth: 2,
              },
              label: {
                text,
                font: "12px Inter, sans-serif",
                fillColor: Cesium.Color.WHITE,
                outlineColor: Cesium.Color.BLACK,
                outlineWidth: 2,
                pixelOffset: new Cesium.Cartesian2(0, -22),
                showBackground: true,
                backgroundColor: Cesium.Color.fromCssColorString("#000000").withAlpha(0.72),
                backgroundPadding: new Cesium.Cartesian2(8, 5),
              },
            })
          );
        };

        endpoint(positions[0], "Start", Cesium.Color.fromCssColorString("#05e563"));
        endpoint(
          positions[positions.length - 1],
          "Destination",
          Cesium.Color.fromCssColorString("#ff5a5f")
        );

        const routeSphere = Cesium.BoundingSphere.fromPoints(positions);
        viewer.camera.flyToBoundingSphere(
          new Cesium.BoundingSphere(routeSphere.center, Math.max(routeSphere.radius, 18)),
          {
            offset: new Cesium.HeadingPitchRange(
              Cesium.Math.toRadians(20),
              Cesium.Math.toRadians(-38),
              Math.max(70, routeSphere.radius * 2.4)
            ),
            duration: 1.2,
          }
        );
        requestRender();
      };

      const resetView = () => flyToFloor("all");
      const topView = () => {
        if (!viewer || !targetMatrix) return;
        const center = Cesium.Matrix4.multiplyByPoint(
          targetMatrix,
          new Cesium.Cartesian3(0, 0, 3),
          new Cesium.Cartesian3()
        );
        viewer.camera.flyToBoundingSphere(new Cesium.BoundingSphere(center, 55), {
          offset: new Cesium.HeadingPitchRange(
            0,
            Cesium.Math.toRadians(-89),
            145
          ),
          duration: 1.2,
        });
      };

      clickHandler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);
      clickHandler.setInputAction((movement: CesiumTypes.ScreenSpaceEventHandler.PositionedEvent) => {
        if (!viewer) return;
        const pickedFeature = viewer.scene.pick(movement.position);
        if (!Cesium.defined(pickedFeature)) {
          setPicked("");
          if (pickMarkerRef.current) {
            viewer.entities.remove(pickMarkerRef.current);
            pickMarkerRef.current = null;
          }
          requestRender();
          return;
        }

        let cartesian: CesiumTypes.Cartesian3 | undefined;
        try {
          cartesian = viewer.scene.pickPosition(movement.position);
        } catch {
          cartesian = undefined;
        }
        if (!cartesian) {
          cartesian = viewer.camera.pickEllipsoid(
            movement.position,
            viewer.scene.globe.ellipsoid
          );
        }
        if (!cartesian) return;

        const cartographic = Cesium.Cartographic.fromCartesian(cartesian);
        const lat = Cesium.Math.toDegrees(cartographic.latitude);
        const lon = Cesium.Math.toDegrees(cartographic.longitude);
        setPicked(
          `${lat.toFixed(6)}, ${lon.toFixed(6)} · ${cartographic.height.toFixed(1)} m`
        );

        if (pickMarkerRef.current) {
          viewer.entities.remove(pickMarkerRef.current);
        }
        pickMarkerRef.current = viewer.entities.add({
          position: cartesian,
          point: {
            pixelSize: 11,
            color: Cesium.Color.fromCssColorString("#ffd700"),
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 2,
          },
        });
        requestRender();
      }, Cesium.ScreenSpaceEventType.LEFT_CLICK);

      viewerApiRef.current = {
        setFloor: (nextFloor) => {
          activeFloor = nextFloor;
          applyFloorToAll();
          flyToFloor(nextFloor);
        },
        drawRoute,
        clearRoute: clearRouteEntities,
        resetView,
        topView,
      };

      setStatus("3D ready");
      await viewer.zoomTo(
        tileset,
        new Cesium.HeadingPitchRange(
          Cesium.Math.toRadians(25),
          Cesium.Math.toRadians(-32),
          135
        )
      );
      applyFloorToAll();
      setCameraPitch(Cesium.Math.toDegrees(viewer.camera.pitch));
      requestRender();
    };

    init().catch((error: unknown) => {
      console.error(error);
      setStatus("3D load failed");
      setRouteError(
        error instanceof Error ? error.message : "The 3D viewer could not be initialized."
      );
    });

    return () => {
      disposed = true;
      viewerApiRef.current = null;
      clickHandler?.destroy();
      if (viewer && handleCameraChanged) {
        viewer.camera.changed.removeEventListener(handleCameraChanged);
      }
      if (viewer && !viewer.isDestroyed()) {
        viewer.destroy();
      }
      window.viewer = undefined;
      window.activeTileset = undefined;
      viewer = null;
      tileset = null;
      targetMatrix = null;
      routeEntities.length = 0;
      storeyTiles.clear();
    };
  }, []);

  useEffect(() => {
    viewerApiRef.current?.setFloor(floor);
  }, [floor]);

  const handleFindRoute = () => {
    if (!network || !effectiveStartId || !effectiveEndId) {
      setRouteError("Select a start and destination room.");
      return;
    }

    setIsRouting(true);
    setRouteError("");
    const result = findPath(network, effectiveStartId, effectiveEndId);
    if ("error" in result) {
      setRoute(null);
      setRouteError(result.error);
      viewerApiRef.current?.clearRoute();
      setIsRouting(false);
      return;
    }

    setRoute(result);
    viewerApiRef.current?.drawRoute(result.path_details);
    setIsRouting(false);
  };

  const handleClearRoute = () => {
    setRoute(null);
    setRouteError("");
    viewerApiRef.current?.clearRoute();
  };

  const startNode = roomNodes.find((node) => node.id === effectiveStartId);
  const endNode = roomNodes.find((node) => node.id === effectiveEndId);

  return (
    <div className="bulwark app-shell">
      <header className="nav">
        <div className="nav-inner px-6">
          <div className="brand">
            <span className="brand-mark">D</span>
            <div>
              <div className="brand-title">DeKUT Digital Twin</div>
              <div className="brand-sub">School of Engineering · Indoor navigation</div>
            </div>
          </div>
          <nav className="nav-links hidden md:flex">
            <a href="#viewer" className="active">
              3D Viewer
            </a>
            <a href="#routing">Routing</a>
            <a href="#data">Data</a>
          </nav>
          <div className="status-pill">
            <span className="status-dot" />
            {status}
          </div>
        </div>
      </header>

      <main id="viewer" className="viewer-shell">
        <div ref={containerRef} className="cesium-container" />
        <div className="viewer-vignette" />

        <aside className="hud hud-left glass">
          <div className="hud-kicker">BUILDING / DEDO</div>
          <h1>School of Engineering</h1>
          <p className="hud-copy">
            Georeferenced BIM model with three storeys and a live indoor routing
            network.
          </p>
          <div className="coord-grid">
            <div>
              <span>Latitude</span>
              <strong>{building?.lat.toFixed(6) ?? "—"}</strong>
            </div>
            <div>
              <span>Longitude</span>
              <strong>{building?.lon.toFixed(6) ?? "—"}</strong>
            </div>
            <div>
              <span>Ground elevation</span>
              <strong>{building ? `${building.alt.toFixed(1)} m` : "—"}</strong>
            </div>
            <div>
              <span>North rotation</span>
              <strong>{building ? `${building.north_rotation}°` : "—"}</strong>
            </div>
          </div>
          <div className="hud-actions">
            <button className="btn btn-neon" onClick={() => viewerApiRef.current?.resetView()}>
              Reset 3D view
            </button>
            <button className="btn btn-ghost" onClick={() => viewerApiRef.current?.topView()}>
              Top view
            </button>
          </div>
        </aside>

        <aside id="routing" className="hud hud-right glass">
          <div className="panel-head">
            <span>Floor filter</span>
            <span className="mono">{floor === "all" ? "ALL" : floor.toUpperCase()}</span>
          </div>
          <div className="floor-tabs">
            {FLOOR_OPTIONS.map((option) => (
              <button
                key={option}
                className={`floor-tab ${floor === option ? "active" : ""}`}
                onClick={() => setFloor(option)}
              >
                {option === "all" ? "All" : option}
              </button>
            ))}
          </div>

          <div className="divider" />

          <div className="panel-head">
            <span>Indoor route</span>
            <span className="mono">DIJKSTRA</span>
          </div>
          <label className="field">
            <span>From</span>
            <select value={effectiveStartId} onChange={(event) => setStartId(event.target.value)}>
              {roomNodes.map((node) => (
                <option key={node.id} value={node.id}>
                  {nodeLabel(node)} · {node.floor}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>To</span>
            <select value={effectiveEndId} onChange={(event) => setEndId(event.target.value)}>
              {roomNodes.map((node) => (
                <option key={node.id} value={node.id}>
                  {nodeLabel(node)} · {node.floor}
                </option>
              ))}
            </select>
          </label>

          <div className="route-actions">
            <button
              className="btn btn-neon"
              onClick={handleFindRoute}
              disabled={!network || isRouting}
            >
              {isRouting ? "Solving" : "Find shortest path"}
            </button>
            <button className="btn btn-ghost" onClick={handleClearRoute}>
              Clear
            </button>
          </div>

          {route ? (
            <div className="route-card">
              <div className="route-summary">
                <strong>{route.distance.toFixed(1)} m</strong>
                <span>{route.steps} steps</span>
              </div>
              <div className="route-floors">{route.floors.join(" → ")}</div>
              <div className="route-path">
                {startNode ? nodeLabel(startNode) : route.path[0]} →{" "}
                {endNode ? nodeLabel(endNode) : route.path[route.path.length - 1]}
              </div>
            </div>
          ) : null}

          {routeError ? <div className="route-error">{routeError}</div> : null}
        </aside>

        <div id="data" className="hud hud-bottom glass">
          <div className="stat">
            <span className="stat-num">{network?.nodes.length ?? "—"}</span>
            <span className="stat-label">routing nodes</span>
          </div>
          <div className="stat">
            <span className="stat-num">{network?.edges.length ?? "—"}</span>
            <span className="stat-label">walkable edges</span>
          </div>
          <div className="stat">
            <span className="stat-num">3</span>
            <span className="stat-label">storeys</span>
          </div>
          <div className="stat">
            <span className="stat-num">{tileCount ?? "n/a"}</span>
            <span className="stat-label">3D Tiles</span>
          </div>
          <div className="stat">
            <span className="stat-num">
              {cameraPitch === null ? "n/a" : `${cameraPitch.toFixed(0)}°`}
            </span>
            <span className="stat-label">camera pitch</span>
          </div>
          <div className="picked">{picked || "Click the model to inspect a point"}</div>
        </div>
      </main>
    </div>
  );
}
