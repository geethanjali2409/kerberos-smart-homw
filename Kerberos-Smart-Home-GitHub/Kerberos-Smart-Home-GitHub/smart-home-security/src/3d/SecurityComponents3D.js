import * as THREE from 'three';

/**
 * Procedural 3D Hardware Component Factory
 * Creates recognizable 3D representations of physical security hardware.
 */

// ============================================================
// 1. ESP32 MICROCONTROLLER BOARD MODEL
// ============================================================
export function createESP32Model() {
  const espGroup = new THREE.Group();
  espGroup.name = 'ESP32_CONTROLLER';

  // PCB Board (Dark matte green/black)
  const pcbGeo = new THREE.BoxGeometry(0.5, 0.05, 0.9);
  const pcbMat = new THREE.MeshStandardMaterial({
    color: 0x0a2e1d,
    roughness: 0.3,
    metalness: 0.2
  });
  const pcb = new THREE.Mesh(pcbGeo, pcbMat);
  pcb.castShadow = true;
  espGroup.add(pcb);

  // ESP-WROOM-32 Metal Shielding Can
  const shieldGeo = new THREE.BoxGeometry(0.32, 0.04, 0.35);
  const shieldMat = new THREE.MeshStandardMaterial({
    color: 0xc0c0c0,
    metalness: 0.9,
    roughness: 0.2
  });
  const shield = new THREE.Mesh(shieldGeo, shieldMat);
  shield.position.set(0, 0.04, -0.15);
  espGroup.add(shield);

  // PCB Trace Antenna (Gold/Yellow trace on top)
  const antGeo = new THREE.BoxGeometry(0.25, 0.01, 0.1);
  const antMat = new THREE.MeshBasicMaterial({ color: 0xdaa520 });
  const antenna = new THREE.Mesh(antGeo, antMat);
  antenna.position.set(0, 0.03, -0.38);
  espGroup.add(antenna);

  // Micro-USB Connector Port
  const usbGeo = new THREE.BoxGeometry(0.12, 0.05, 0.1);
  const usbMat = new THREE.MeshStandardMaterial({ color: 0x888888, metalness: 0.8 });
  const usb = new THREE.Mesh(usbGeo, usbMat);
  usb.position.set(0, 0.03, 0.42);
  espGroup.add(usb);

  // Pin Headers (Left & Right dual rows)
  const pinMat = new THREE.MeshStandardMaterial({ color: 0x111111, metalness: 0.5 });
  const goldPinMat = new THREE.MeshStandardMaterial({ color: 0xffd700, metalness: 0.9 });
  
  for (let z = -0.38; z <= 0.38; z += 0.05) {
    // Left Pin
    const pinL = new THREE.Mesh(new THREE.BoxGeometry(0.04, 0.1, 0.03), goldPinMat);
    pinL.position.set(-0.23, 0, z);
    espGroup.add(pinL);

    // Right Pin
    const pinR = new THREE.Mesh(new THREE.BoxGeometry(0.04, 0.1, 0.03), goldPinMat);
    pinR.position.set(0.23, 0, z);
    espGroup.add(pinR);
  }

  // Status LED (Red/Blue glow)
  const ledGeo = new THREE.SphereGeometry(0.025, 8, 8);
  const ledMat = new THREE.MeshBasicMaterial({ color: 0x00ffcc });
  const led = new THREE.Mesh(ledGeo, ledMat);
  led.position.set(-0.15, 0.04, 0.3);
  led.name = 'ESP32_STATUS_LED';
  espGroup.add(led);

  return espGroup;
}

// ============================================================
// 2. PIR MOTION SENSOR MODEL
// ============================================================
export function createPIRModel() {
  const pirGroup = new THREE.Group();
  pirGroup.name = 'PIR_SENSOR';

  // PIR PCB Base (Cyan/Blue PCB)
  const pcbGeo = new THREE.BoxGeometry(0.35, 0.04, 0.35);
  const pcbMat = new THREE.MeshStandardMaterial({ color: 0x005588, roughness: 0.4 });
  const pcb = new THREE.Mesh(pcbGeo, pcbMat);
  pirGroup.add(pcb);

  // White Fresnel Lens Dome
  const domeGeo = new THREE.SphereGeometry(0.12, 16, 12, 0, Math.PI * 2, 0, Math.PI / 2);
  const domeMat = new THREE.MeshStandardMaterial({
    color: 0xf0f0f0,
    roughness: 0.1,
    transmission: 0.4,
    transparent: true
  });
  const dome = new THREE.Mesh(domeGeo, domeMat);
  dome.position.set(0, 0.02, 0);
  pirGroup.add(dome);

  // PIR Active Sensor Pyro Element inside
  const sensorGeo = new THREE.BoxGeometry(0.08, 0.05, 0.08);
  const sensorMat = new THREE.MeshStandardMaterial({ color: 0x888888, metalness: 0.9 });
  const sensor = new THREE.Mesh(sensorGeo, sensorMat);
  sensor.position.set(0, 0.04, 0);
  pirGroup.add(sensor);

  // Status Light
  const ledGeo = new THREE.SphereGeometry(0.02, 8, 8);
  const ledMat = new THREE.MeshBasicMaterial({ color: 0x00ff00 });
  const led = new THREE.Mesh(ledGeo, ledMat);
  led.position.set(0.12, 0.03, 0.12);
  led.name = 'PIR_LED';
  pirGroup.add(led);

  return pirGroup;
}

// ============================================================
// 3. HC-SR04 ULTRASONIC SENSOR MODEL
// ============================================================
export function createUltrasonicModel() {
  const hcGroup = new THREE.Group();
  hcGroup.name = 'HC_SR04_SENSOR';

  // Blue PCB
  const pcbGeo = new THREE.BoxGeometry(0.55, 0.25, 0.04);
  const pcbMat = new THREE.MeshStandardMaterial({ color: 0x0044aa, roughness: 0.3 });
  const pcb = new THREE.Mesh(pcbGeo, pcbMat);
  hcGroup.add(pcb);

  // Dual Metallic Transducer Cylinders (Trig & Echo)
  const cylGeo = new THREE.CylinderGeometry(0.09, 0.09, 0.15, 16);
  const cylMat = new THREE.MeshStandardMaterial({ color: 0xd0d0d0, metalness: 0.8, roughness: 0.2 });

  // Trigger Cylinder (Left)
  const trigCyl = new THREE.Mesh(cylGeo, cylMat);
  trigCyl.rotation.x = Math.PI / 2;
  trigCyl.position.set(-0.16, 0, 0.08);
  hcGroup.add(trigCyl);

  // Echo Cylinder (Right)
  const echoCyl = new THREE.Mesh(cylGeo, cylMat);
  echoCyl.rotation.x = Math.PI / 2;
  echoCyl.position.set(0.16, 0, 0.08);
  hcGroup.add(echoCyl);

  // Mesh Grille Covers
  const meshGeo = new THREE.CircleGeometry(0.08, 12);
  const meshMat = new THREE.MeshBasicMaterial({ color: 0x222222 });

  const meshT = new THREE.Mesh(meshGeo, meshMat);
  meshT.position.set(-0.16, 0, 0.16);
  hcGroup.add(meshT);

  const meshE = new THREE.Mesh(meshGeo, meshMat);
  meshE.position.set(0.16, 0, 0.16);
  hcGroup.add(meshE);

  return hcGroup;
}

// ============================================================
// 4. MICRO SERVO MOTOR LOCK MODEL
// ============================================================
export function createServoModel() {
  const servoGroup = new THREE.Group();
  servoGroup.name = 'SERVO_LOCK';

  // Blue Semi-Transparent Plastic Casing
  const caseGeo = new THREE.BoxGeometry(0.28, 0.32, 0.14);
  const caseMat = new THREE.MeshStandardMaterial({ color: 0x0066cc, roughness: 0.3, transparent: true, opacity: 0.95 });
  const casing = new THREE.Mesh(caseGeo, caseMat);
  servoGroup.add(casing);

  // Gear Shaft Tower
  const towerGeo = new THREE.CylinderGeometry(0.05, 0.05, 0.08, 12);
  const towerMat = new THREE.MeshStandardMaterial({ color: 0xffffff });
  const tower = new THREE.Mesh(towerGeo, towerMat);
  tower.position.set(0.06, 0.18, 0);
  servoGroup.add(tower);

  // White Horn Lever (Pivot for lock deadbolt)
  const hornGroup = new THREE.Group();
  hornGroup.name = 'SERVO_HORN';
  hornGroup.position.set(0.06, 0.22, 0);

  const hornGeo = new THREE.BoxGeometry(0.22, 0.02, 0.04);
  const hornMat = new THREE.MeshStandardMaterial({ color: 0xffffff });
  const horn = new THREE.Mesh(hornGeo, hornMat);
  horn.position.set(0.08, 0, 0);
  hornGroup.add(horn);

  // Deadbolt Lock Pin
  const boltGeo = new THREE.CylinderGeometry(0.02, 0.02, 0.2, 8);
  const boltMat = new THREE.MeshStandardMaterial({ color: 0xb0b0b0, metalness: 0.9 });
  const bolt = new THREE.Mesh(boltGeo, boltMat);
  bolt.rotation.z = Math.PI / 2;
  bolt.position.set(0.2, 0, 0);
  hornGroup.add(bolt);

  servoGroup.add(hornGroup);
  return servoGroup;
}

// ============================================================
// 5. PIEZO ALARM BUZZER MODEL
// ============================================================
export function createBuzzerModel() {
  const buzzerGroup = new THREE.Group();
  buzzerGroup.name = 'ALARM_BUZZER';

  // Black Plastic Cylinder Casing
  const cylGeo = new THREE.CylinderGeometry(0.12, 0.12, 0.12, 16);
  const cylMat = new THREE.MeshStandardMaterial({ color: 0x1a1a1a, roughness: 0.6 });
  const casing = new THREE.Mesh(cylGeo, cylMat);
  buzzerGroup.add(casing);

  // Top Hole Aperture
  const holeGeo = new THREE.CircleGeometry(0.03, 12);
  const holeMat = new THREE.MeshBasicMaterial({ color: 0x000000 });
  const hole = new THREE.Mesh(holeGeo, holeMat);
  hole.rotation.x = -Math.PI / 2;
  hole.position.set(0, 0.061, 0);
  buzzerGroup.add(hole);

  // Plus Sign Indicator (+ Pin)
  const plusMat = new THREE.MeshBasicMaterial({ color: 0xff3333 });
  const p1 = new THREE.Mesh(new THREE.BoxGeometry(0.04, 0.001, 0.01), plusMat);
  p1.position.set(-0.06, 0.062, 0.06);
  const p2 = new THREE.Mesh(new THREE.BoxGeometry(0.01, 0.001, 0.04), plusMat);
  p2.position.set(-0.06, 0.062, 0.06);
  buzzerGroup.add(p1);
  buzzerGroup.add(p2);

  return buzzerGroup;
}

// ============================================================
// 6. PHYSICAL MAGNETIC DOOR REED SWITCH
// ============================================================
export function createReedSwitchModel() {
  const reedGroup = new THREE.Group();
  reedGroup.name = 'DOOR_REED_SWITCH';

  const blockMat = new THREE.MeshStandardMaterial({ color: 0xf5f5f5, roughness: 0.3 });

  // Fixed Frame Switch Block
  const switchGeo = new THREE.BoxGeometry(0.08, 0.25, 0.08);
  const switchMesh = new THREE.Mesh(switchGeo, blockMat);
  switchMesh.position.set(-0.05, 0, 0);
  reedGroup.add(switchMesh);

  // Moving Door Magnet Block
  const magnetMesh = new THREE.Mesh(switchGeo, blockMat);
  magnetMesh.position.set(0.05, 0, 0);
  magnetMesh.name = 'REED_MAGNET';
  reedGroup.add(magnetMesh);

  return reedGroup;
}

// ============================================================
// 7. SECURITY CAMERA MODEL
// ============================================================
export function createSecurityCameraModel(id, name) {
  const camGroup = new THREE.Group();
  camGroup.name = id;

  // Wall Mount Base Plate
  const baseGeo = new THREE.CylinderGeometry(0.08, 0.1, 0.04, 12);
  const baseMat = new THREE.MeshStandardMaterial({ color: 0x333333, metalness: 0.5 });
  const base = new THREE.Mesh(baseGeo, baseMat);
  base.rotation.x = Math.PI / 2;
  camGroup.add(base);

  // Articulated Mount Arm
  const armGeo = new THREE.CylinderGeometry(0.03, 0.03, 0.2, 8);
  const arm = new THREE.Mesh(armGeo, baseMat);
  arm.rotation.x = Math.PI / 4;
  arm.position.set(0, 0, 0.1);
  camGroup.add(arm);

  // Bullet Camera Body Housing
  const bodyGeo = new THREE.CylinderGeometry(0.08, 0.08, 0.3, 16);
  const bodyMat = new THREE.MeshStandardMaterial({ color: 0xeeeeee, roughness: 0.2 });
  const body = new THREE.Mesh(bodyGeo, bodyMat);
  body.rotation.x = Math.PI / 2;
  body.position.set(0, -0.05, 0.22);
  camGroup.add(body);

  // Dark Front Glass Shield
  const glassGeo = new THREE.CircleGeometry(0.075, 16);
  const glassMat = new THREE.MeshStandardMaterial({ color: 0x050505, roughness: 0.1, metalness: 0.9 });
  const glass = new THREE.Mesh(glassGeo, glassMat);
  glass.position.set(0, -0.05, 0.371);
  camGroup.add(glass);

  // Camera Lens Center
  const lensGeo = new THREE.CylinderGeometry(0.03, 0.03, 0.02, 12);
  const lensMat = new THREE.MeshBasicMaterial({ color: 0x001133 });
  const lens = new THREE.Mesh(lensGeo, lensMat);
  lens.rotation.x = Math.PI / 2;
  lens.position.set(0, -0.05, 0.375);
  camGroup.add(lens);

  // IR LED Ring
  const irGeo = new THREE.SphereGeometry(0.01, 8, 8);
  const irMat = new THREE.MeshBasicMaterial({ color: 0xff0055 });
  for (let a = 0; a < Math.PI * 2; a += Math.PI / 3) {
    const ir = new THREE.Mesh(irGeo, irMat);
    ir.position.set(Math.cos(a) * 0.05, -0.05 + Math.sin(a) * 0.05, 0.373);
    camGroup.add(ir);
  }

  // Active Status LED
  const statusLedGeo = new THREE.SphereGeometry(0.015, 8, 8);
  const statusLedMat = new THREE.MeshBasicMaterial({ color: 0x00ff00 });
  const statusLed = new THREE.Mesh(statusLedGeo, statusLedMat);
  statusLed.position.set(0.06, -0.01, 0.37);
  statusLed.name = `${id}_STATUS_LED`;
  camGroup.add(statusLed);

  return camGroup;
}
