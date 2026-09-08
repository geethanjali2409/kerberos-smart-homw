import * as THREE from 'three';

/**
 * 3D Security Zone & Sensor Coverage Visualizers
 * Handles semi-transparent detection cones, camera field of view, and connection paths.
 */

// ============================================================
// 1. PIR DETECTION RADIUS DOME CONE
// ============================================================
export function createPIRZoneCone(radius = 3.5, angleRad = Math.PI / 3) {
  const coneGeo = new THREE.ConeGeometry(radius * Math.tan(angleRad / 2), radius, 24, 1, true);
  const coneMat = new THREE.MeshBasicMaterial({
    color: 0x00ff88,
    transparent: true,
    opacity: 0.18,
    side: THREE.DoubleSide,
    depthWrite: false
  });
  const cone = new THREE.Mesh(coneGeo, coneMat);
  cone.rotation.x = -Math.PI / 2;
  cone.position.set(0, -radius / 2, 0);
  cone.name = 'PIR_ZONE_CONE';
  return cone;
}

// ============================================================
// 2. ULTRASONIC DIRECTIONAL SONAR BEAM
// ============================================================
export function createUltrasonicZoneCone(rangeCm = 100) {
  const rangeM = Math.min(rangeCm / 50, 4.0); // Map cm to 3D scene units
  const coneGeo = new THREE.ConeGeometry(rangeM * 0.3, rangeM, 16, 1, true);
  const coneMat = new THREE.MeshBasicMaterial({
    color: 0x00c8ff,
    transparent: true,
    opacity: 0.25,
    side: THREE.DoubleSide,
    depthWrite: false
  });
  const cone = new THREE.Mesh(coneGeo, coneMat);
  cone.rotation.x = Math.PI / 2;
  cone.position.set(0, 0, rangeM / 2);
  cone.name = 'ULTRASONIC_ZONE_CONE';
  return cone;
}

// ============================================================
// 3. CAMERA FIELD OF VIEW (FOV) PYRAMID
// ============================================================
export function createCameraFOVFrustum(fovDeg = 80, range = 5) {
  const fovRad = (fovDeg * Math.PI) / 180;
  const aspect = 1.6;
  const height = range * Math.tan(fovRad / 2);
  const width = height * aspect;

  const fovGroup = new THREE.Group();
  fovGroup.name = 'CAMERA_FOV_FRUSTUM';

  // Semi-transparent Wireframe Cone
  const coneGeo = new THREE.ConeGeometry(width, range, 4, 1, true);
  const coneMat = new THREE.MeshBasicMaterial({
    color: 0xffaa00,
    transparent: true,
    opacity: 0.15,
    wireframe: false,
    side: THREE.DoubleSide,
    depthWrite: false
  });
  const frustum = new THREE.Mesh(coneGeo, coneMat);
  frustum.rotation.x = -Math.PI / 2;
  frustum.rotation.z = Math.PI / 4;
  frustum.position.set(0, 0, range / 2);
  fovGroup.add(frustum);

  // Edges Wireframe
  const edgesGeo = new THREE.EdgesGeometry(coneGeo);
  const edgesMat = new THREE.LineBasicMaterial({ color: 0xffcc00, transparent: true, opacity: 0.5 });
  const wireframe = new THREE.LineSegments(edgesGeo, edgesMat);
  wireframe.rotation.x = -Math.PI / 2;
  wireframe.rotation.z = Math.PI / 4;
  wireframe.position.set(0, 0, range / 2);
  fovGroup.add(wireframe);

  return fovGroup;
}

// ============================================================
// 4. ANIMATED SIGNAL CONNECTION PATHS (X-RAY MODE)
// ============================================================
export function createAnimatedConnectionLines(pointsList) {
  const group = new THREE.Group();
  group.name = 'XRAY_SIGNAL_PATHS';

  pointsList.forEach(({ from, to, color = 0x00ffcc, name }) => {
    const curve = new THREE.LineCurve3(from, to);
    const geometry = new THREE.BufferGeometry().setFromPoints(curve.getPoints(20));

    const material = new THREE.LineDashedMaterial({
      color,
      linewidth: 2,
      scale: 1,
      dashSize: 0.15,
      gapSize: 0.1,
      transparent: true,
      opacity: 0.8
    });

    const line = new THREE.Line(geometry, material);
    line.computeLineDistances();
    line.name = name || 'SIGNAL_LINE';
    group.add(line);
  });

  return group;
}
