import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

import { buildRealisticHouse } from './House3D.js';
import {
  createESP32Model,
  createPIRModel,
  createUltrasonicModel,
  createServoModel,
  createBuzzerModel,
  createReedSwitchModel,
  createSecurityCameraModel
} from './SecurityComponents3D.js';
import {
  createPIRZoneCone,
  createUltrasonicZoneCone,
  createCameraFOVFrustum,
  createAnimatedConnectionLines
} from './CameraFOV3D.js';
import { securityStore } from '../state/securityStore.js';

export default function HouseCanvas({ onSelectObject }) {
  const mountRef = useRef(null);
  const [storeState, setStoreState] = useState(securityStore.getState());

  useEffect(() => {
    const unsubscribe = securityStore.subscribe(setStoreState);
    return () => unsubscribe();
  }, []);

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    // ============================================================
    // 1. THREE.JS SCENE SETUP
    // ============================================================
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0f172a); // Dark navy backdrop
    scene.fog = new THREE.FogExp2(0x0f172a, 0.015);

    const camera = new THREE.PerspectiveCamera(
      50,
      container.clientWidth / container.clientHeight,
      0.1,
      100
    );
    camera.position.set(0, 10, 16);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    container.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.maxPolarAngle = Math.PI / 2 - 0.02; // Don't clip below ground
    controls.minDistance = 3;
    controls.maxDistance = 35;
    controls.target.set(0, 1.5, 0);

    // ============================================================
    // 2. LIGHTING ENGINE (Day / Night Support)
    // ============================================================
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);

    const sunLight = new THREE.DirectionalLight(0xfffaed, 1.4);
    sunLight.position.set(12, 18, 10);
    sunLight.castShadow = true;
    sunLight.shadow.mapSize.width = 2048;
    sunLight.shadow.mapSize.height = 2048;
    sunLight.shadow.camera.near = 0.5;
    sunLight.shadow.camera.far = 40;
    sunLight.shadow.camera.left = -12;
    sunLight.shadow.camera.right = 12;
    sunLight.shadow.camera.top = 12;
    sunLight.shadow.camera.bottom = -12;
    scene.add(sunLight);

    // Interior Room Lights (Night Mode)
    const roomLightsGroup = new THREE.Group();
    
    const livingLight = new THREE.PointLight(0xffaa55, 1.2, 8);
    livingLight.position.set(-4.5, 2.2, 2.5);
    roomLightsGroup.add(livingLight);

    const bedroomLight = new THREE.PointLight(0xffcc88, 1.0, 8);
    bedroomLight.position.set(4.5, 2.2, 2.5);
    roomLightsGroup.add(bedroomLight);

    const kitchenLight = new THREE.PointLight(0xffffff, 1.2, 8);
    kitchenLight.position.set(-4.0, 2.2, -3.0);
    roomLightsGroup.add(kitchenLight);

    const porchLight = new THREE.PointLight(0xff8833, 1.5, 6);
    porchLight.position.set(0, 2.4, 5.2);
    roomLightsGroup.add(porchLight);

    scene.add(roomLightsGroup);

    // ============================================================
    // 3. BUILD REALISTIC HOUSE ARCHITECTURE
    // ============================================================
    const house = buildRealisticHouse(scene);

    // ============================================================
    // 4. INSTANTIATE & PLACE 3D SECURITY HARDWARE
    // ============================================================
    const hardwareGroup = new THREE.Group();
    hardwareGroup.name = 'SECURITY_HARDWARE_GROUP';

    // 1. ESP32 Microcontroller Board
    const esp32 = createESP32Model();
    esp32.position.set(-1.4, 1.6, 4.85);
    esp32.rotation.y = Math.PI / 2;
    hardwareGroup.add(esp32);

    // 2. PIR Motion Sensor (Above Front Door)
    const pir = createPIRModel();
    pir.position.set(0, 2.35, 4.95);
    pir.rotation.x = Math.PI / 6;
    hardwareGroup.add(pir);

    // PIR Detection Cone Visualizer
    const pirCone = createPIRZoneCone(3.5);
    pirCone.position.set(0, 2.3, 4.95);
    pirCone.rotation.x = Math.PI / 3;
    hardwareGroup.add(pirCone);

    // 3. HC-SR04 Ultrasonic Distance Sensor (Front Approach)
    const ultrasonic = createUltrasonicModel();
    ultrasonic.position.set(0.7, 1.6, 4.95);
    hardwareGroup.add(ultrasonic);

    // Ultrasonic Sonar Beam Visualizer
    const sonarBeam = createUltrasonicZoneCone(250);
    sonarBeam.position.set(0.7, 1.6, 4.95);
    hardwareGroup.add(sonarBeam);

    // 4. Servo Motor Door Lock
    const servo = createServoModel();
    servo.position.set(-0.85, 1.25, 4.95);
    hardwareGroup.add(servo);

    // 5. Piezo Alarm Buzzer
    const buzzer = createBuzzerModel();
    buzzer.position.set(-1.4, 1.25, 4.85);
    hardwareGroup.add(buzzer);

    // 6. Physical Magnetic Reed Door Switch
    const reedSwitch = createReedSwitchModel();
    reedSwitch.position.set(-0.9, 1.6, 4.95);
    hardwareGroup.add(reedSwitch);

    // 7. Security Cameras
    const camFront = createSecurityCameraModel('CAM_FRONT_DOOR', 'Front Entrance Cam');
    camFront.position.set(0, 2.6, 5.2);
    camFront.rotation.y = 0;
    hardwareGroup.add(camFront);

    const camFrontFOV = createCameraFOVFrustum(80, 5);
    camFrontFOV.position.set(0, 2.6, 5.2);
    hardwareGroup.add(camFrontFOV);

    const camLiving = createSecurityCameraModel('CAM_FRONT_WINDOW', 'Front Window Cam');
    camLiving.position.set(-4.5, 2.6, 5.2);
    hardwareGroup.add(camLiving);

    const camSide = createSecurityCameraModel('CAM_SIDE_WINDOW', 'Side Yard Cam');
    camSide.position.set(-7.2, 2.6, 1.5);
    camSide.rotation.y = -Math.PI / 2;
    hardwareGroup.add(camSide);

    const camBedroom = createSecurityCameraModel('CAM_BEDROOM_WINDOW', 'Bedroom Cam');
    camBedroom.position.set(7.2, 2.6, 1.5);
    camBedroom.rotation.y = Math.PI / 2;
    hardwareGroup.add(camBedroom);

    scene.add(hardwareGroup);

    // ============================================================
    // 5. X-RAY ANIMATED SIGNAL PATH LINES
    // ============================================================
    const signalLinesGroup = createAnimatedConnectionLines([
      { from: pir.position, to: esp32.position, color: 0x00ff88, name: 'PIR_TO_ESP32' },
      { from: ultrasonic.position, to: esp32.position, color: 0x00c8ff, name: 'HC_TO_ESP32' },
      { from: reedSwitch.position, to: esp32.position, color: 0xffff00, name: 'REED_TO_ESP32' },
      { from: esp32.position, to: servo.position, color: 0xff00ff, name: 'ESP32_TO_SERVO' },
      { from: esp32.position, to: buzzer.position, color: 0xff3333, name: 'ESP32_TO_BUZZER' },
      { from: esp32.position, to: new THREE.Vector3(-1.4, 3.5, 4.85), color: 0x00ffff, name: 'ESP32_TO_WIFI' }
    ]);
    scene.add(signalLinesGroup);

    // ============================================================
    // 6. RAYCASTER OBJECT PICKING (Interactive Clicking)
    // ============================================================
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();

    const handlePointerDown = (event) => {
      const rect = renderer.domElement.getBoundingClientRect();
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      raycaster.setFromCamera(mouse, camera);
      const intersects = raycaster.intersectObjects(scene.children, true);

      if (intersects.length > 0) {
        let hitObj = intersects[0].object;
        while (hitObj.parent && hitObj.parent !== scene && !hitObj.name.startsWith('CAM_') && hitObj.name !== 'ESP32_CONTROLLER' && hitObj.name !== 'PIR_SENSOR' && hitObj.name !== 'HC_SR04_SENSOR' && hitObj.name !== 'SERVO_LOCK' && hitObj.name !== 'ALARM_BUZZER' && hitObj.name !== 'FRONT_DOOR_PANEL' && !hitObj.name.endsWith('_WINDOW')) {
          hitObj = hitObj.parent;
        }

        if (hitObj && hitObj.name) {
          onSelectObject && onSelectObject(hitObj.name);
          securityStore.setSelectedObject(hitObj.name);
        }
      }
    };

    renderer.domElement.addEventListener('pointerdown', handlePointerDown);

    // ============================================================
    // 7. ANIMATION LOOP & DIGITAL TWIN STATE SYNC
    // ============================================================
    let animFrameId;
    let clock = new THREE.Clock();

    const animate = () => {
      animFrameId = requestAnimationFrame(animate);

      const elapsedTime = clock.getElapsedTime();
      const currentState = securityStore.getState();

      // Day / Night Lighting Mode Sync
      if (currentState.dayNightMode === 'NIGHT') {
        scene.background.setHex(0x050814);
        scene.fog.color.setHex(0x050814);
        ambientLight.intensity = 0.15;
        sunLight.intensity = 0.1;
        roomLightsGroup.visible = true;
      } else {
        scene.background.setHex(0x0f172a);
        scene.fog.color.setHex(0x0f172a);
        ambientLight.intensity = 0.6;
        sunLight.intensity = 1.4;
        roomLightsGroup.visible = false;
      }

      // Semi-Transparent X-Ray Wall Mode Sync
      house.setXrayMode(currentState.xrayMode);
      signalLinesGroup.visible = currentState.xrayMode;

      // Servo Lock Horn Rotation Sync
      const horn = servo.getObjectByName('SERVO_HORN');
      if (horn) {
        const targetRot = currentState.actuators.servo.state === 'LOCKED' ? Math.PI / 2 : 0;
        horn.rotation.y = THREE.MathUtils.lerp(horn.rotation.y, targetRot, 0.1);
      }

      // Front Door Open Pivot Rotation Sync
      const doorPivot = house.doorPivotGroup;
      if (doorPivot) {
        const isDoorOpen = currentState.door.state === 'OPEN' || currentState.sensors.doorSwitch.state === 'OPEN';
        const targetDoorAngle = isDoorOpen ? -Math.PI / 2.5 : 0;
        doorPivot.rotation.y = THREE.MathUtils.lerp(doorPivot.rotation.y, targetDoorAngle, 0.08);
      }

      // PIR Motion LED & Cone Pulse Sync
      const pirLed = pir.getObjectByName('PIR_LED');
      const isMotion = currentState.sensors.pir.state === 'MOTION';
      if (pirLed) {
        pirLed.material.color.setHex(isMotion ? 0xff0000 : 0x00ff00);
      }
      if (pirCone) {
        pirCone.material.color.setHex(isMotion ? 0xff0044 : 0x00ff88);
        pirCone.material.opacity = isMotion ? 0.35 + Math.sin(elapsedTime * 8) * 0.15 : 0.15;
      }

      // Buzzer Siren Flash Sync
      if (currentState.actuators.buzzer.mode === 2) {
        // Loud alarm flashing red halo
        scene.background.setHex((Math.floor(elapsedTime * 6) % 2 === 0) ? 0x330000 : 0x050814);
      }

      // Dashed Signal Lines Animation
      signalLinesGroup.children.forEach((line) => {
        if (line.material && line.material.dashSize) {
          line.material.dashOffset = -elapsedTime * 1.5;
        }
      });

      controls.update();
      renderer.render(scene, camera);
    };

    animate();

    // Resize Handler
    const handleResize = () => {
      if (!container) return;
      camera.aspect = container.clientWidth / container.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(container.clientWidth, container.clientHeight);
    };

    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(animFrameId);
      renderer.domElement.removeEventListener('pointerdown', handlePointerDown);
      window.removeEventListener('resize', handleResize);
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, []);

  return (
    <div className="relative w-full h-full">
      <div ref={mountRef} className="w-full h-full rounded-xl overflow-hidden shadow-2xl" />
    </div>
  );
}
