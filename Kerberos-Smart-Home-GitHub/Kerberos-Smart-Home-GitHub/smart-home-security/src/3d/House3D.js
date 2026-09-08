import * as THREE from 'three';

/**
 * Procedural 3D Realistic House Architecture Generator
 * Builds 5 detailed rooms with realistic furniture, materials, interactive windows, and exterior ground.
 */

export function buildRealisticHouse(scene) {
  const houseGroup = new THREE.Group();
  houseGroup.name = 'REALISTIC_HOUSE_ROOT';

  // Array storing wall meshes for X-Ray transparency toggling
  const wallMeshes = [];
  const windowGroupMap = new Map();

  // ============================================================
  // 1. MATERIAL PALETTE (Realistic architectural surfaces)
  // ============================================================

  const wallMat = new THREE.MeshStandardMaterial({
    color: 0xeeebd9, // Soft off-white plaster
    roughness: 0.7,
    side: THREE.DoubleSide
  });

  const floorWoodMat = new THREE.MeshStandardMaterial({
    color: 0x8b5a2b, // Warm oak hardwood
    roughness: 0.4,
    metalness: 0.1
  });

  const tileMat = new THREE.MeshStandardMaterial({
    color: 0xdddddd, // Marble bathroom tile
    roughness: 0.2,
    metalness: 0.2
  });

  const roofMat = new THREE.MeshStandardMaterial({
    color: 0x3d312a, // Slate shingles
    roughness: 0.8
  });

  const glassMat = new THREE.MeshPhysicalMaterial({
    color: 0xffffff,
    transparent: true,
    opacity: 0.35,
    roughness: 0.05,
    transmission: 0.9,
    ior: 1.5,
    side: THREE.DoubleSide
  });

  const woodFurnitureMat = new THREE.MeshStandardMaterial({ color: 0x5c3a21, roughness: 0.5 });
  const fabricMat = new THREE.MeshStandardMaterial({ color: 0x3b5998, roughness: 0.8 }); // Navy sofa fabric
  const metalMat = new THREE.MeshStandardMaterial({ color: 0x444444, metalness: 0.8, roughness: 0.3 });
  const ceramicMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.1 });

  // ============================================================
  // 2. EXTERIOR GROUND & GARDEN PATHWAY
  // ============================================================

  // Grass Lawn
  const grassGeo = new THREE.PlaneGeometry(30, 24);
  const grassMat = new THREE.MeshStandardMaterial({ color: 0x3a6b35, roughness: 0.9 });
  const grass = new THREE.Mesh(grassGeo, grassMat);
  grass.rotation.x = -Math.PI / 2;
  grass.position.set(0, -0.01, 0);
  grass.receiveShadow = true;
  houseGroup.add(grass);

  // Concrete Entrance Pathway
  const pathGeo = new THREE.PlaneGeometry(2.5, 6);
  const pathMat = new THREE.MeshStandardMaterial({ color: 0x999999, roughness: 0.8 });
  const path = new THREE.Mesh(pathGeo, pathMat);
  path.rotation.x = -Math.PI / 2;
  path.position.set(0, 0, 7.5);
  path.receiveShadow = true;
  houseGroup.add(path);

  // Ground House Slab Foundation
  const slabGeo = new THREE.BoxGeometry(14.4, 0.2, 10.4);
  const slabMat = new THREE.MeshStandardMaterial({ color: 0x555555, roughness: 0.8 });
  const slab = new THREE.Mesh(slabGeo, slabMat);
  slab.position.set(0, 0.1, 0);
  slab.receiveShadow = true;
  houseGroup.add(slab);

  // Interior Hardwood Floor
  const floorGeo = new THREE.PlaneGeometry(14, 10);
  const floor = new THREE.Mesh(floorGeo, floorWoodMat);
  floor.rotation.x = -Math.PI / 2;
  floor.position.set(0, 0.201, 0);
  floor.receiveShadow = true;
  houseGroup.add(floor);

  // ============================================================
  // 3. ARCHITECTURAL WALL LAYOUT (5 Rooms + Hallway)
  // ============================================================

  // Helper function to add walls
  const addWall = (w, h, d, x, y, z, name = 'WALL') => {
    const geo = new THREE.BoxGeometry(w, h, d);
    const mesh = new THREE.Mesh(geo, wallMat.clone());
    mesh.position.set(x, y, z);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    mesh.name = name;
    houseGroup.add(mesh);
    wallMeshes.push(mesh);
    return mesh;
  };

  const wallH = 2.8;
  const wallY = 0.2 + wallH / 2;

  // Exterior Perimeter Walls
  addWall(14, wallH, 0.2, 0, wallY, -5, 'EXT_WALL_BACK');     // Back wall
  addWall(0.2, wallH, 10, -7, wallY, 0, 'EXT_WALL_LEFT');     // Left wall
  addWall(0.2, wallH, 10, 7, wallY, 0, 'EXT_WALL_RIGHT');    // Right wall

  // Front Wall (Split around front door entrance)
  addWall(5.5, wallH, 0.2, -4.25, wallY, 5, 'EXT_WALL_FRONT_L');
  addWall(5.5, wallH, 0.2, 4.25, wallY, 5, 'EXT_WALL_FRONT_R');
  addWall(3, 0.8, 0.2, 0, 0.2 + wallH - 0.4, 5, 'EXT_WALL_FRONT_TOP');

  // Interior Divider Walls
  addWall(0.2, wallH, 6.5, -2, wallY, 1.75, 'INT_WALL_LIVING');  // Living Room divider
  addWall(0.2, wallH, 6.5, 2, wallY, 1.75, 'INT_WALL_BEDROOM');  // Bedroom divider
  addWall(14, wallH, 0.2, 0, wallY, -1.5, 'INT_WALL_HALLWAY');   // Hallway divider

  // Bathroom Dividers (Back Right)
  addWall(0.2, wallH, 3.5, 2.5, wallY, -3.25, 'INT_WALL_BATH_L');

  // Roof Structure (Gable Roof)
  const roofGroup = new THREE.Group();
  roofGroup.name = 'HOUSE_ROOF';
  
  const roofGeo = new THREE.ConeGeometry(10.5, 2.5, 4);
  const roofMesh = new THREE.Mesh(roofGeo, roofMat);
  roofMesh.rotation.y = Math.PI / 4;
  roofMesh.position.set(0, 0.2 + wallH + 1.25, 0);
  roofGroup.add(roofMesh);
  houseGroup.add(roofGroup);

  // ============================================================
  // 4. INTERACTIVE FRONT ENTRANCE DOOR
  // ============================================================

  const doorPivotGroup = new THREE.Group();
  doorPivotGroup.name = 'FRONT_DOOR_PIVOT';
  doorPivotGroup.position.set(-0.9, 0.2, 5); // Pivot at hinges

  const doorPanelGeo = new THREE.BoxGeometry(1.8, 2.4, 0.08);
  const doorPanelMat = new THREE.MeshStandardMaterial({ color: 0x4a2c11, roughness: 0.3 });
  const doorPanel = new THREE.Mesh(doorPanelGeo, doorPanelMat);
  doorPanel.position.set(0.9, 1.2, 0);
  doorPanel.castShadow = true;
  doorPanel.name = 'FRONT_DOOR_PANEL';
  doorPivotGroup.add(doorPanel);

  // Door Handle / Lock Cylinder
  const handleGeo = new THREE.CylinderGeometry(0.02, 0.02, 0.2, 8);
  const handleMat = new THREE.MeshStandardMaterial({ color: 0xffd700, metalness: 0.9, roughness: 0.2 });
  const handle = new THREE.Mesh(handleGeo, handleMat);
  handle.rotation.z = Math.PI / 2;
  handle.position.set(1.6, 1.1, 0.06);
  doorPivotGroup.add(handle);

  houseGroup.add(doorPivotGroup);

  // ============================================================
  // 5. INTERACTIVE WINDOWS (4 Security Zones)
  // ============================================================

  const createWindow = (id, name, width, height, x, y, z, rotY = 0) => {
    const winGroup = new THREE.Group();
    winGroup.name = id;
    winGroup.position.set(x, y, z);
    winGroup.rotation.y = rotY;

    // Outer Wooden Frame
    const frameMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.4 });
    const frameGeo = new THREE.BoxGeometry(width + 0.1, height + 0.1, 0.12);
    const frame = new THREE.Mesh(frameGeo, frameMat);
    winGroup.add(frame);

    // Glass Panes (Transparent)
    const glassGeo = new THREE.BoxGeometry(width, height, 0.02);
    const glass = new THREE.Mesh(glassGeo, glassMat);
    glass.name = `${id}_GLASS`;
    winGroup.add(glass);

    // Sill
    const sillGeo = new THREE.BoxGeometry(width + 0.2, 0.05, 0.2);
    const sill = new THREE.Mesh(sillGeo, frameMat);
    sill.position.set(0, -height / 2 - 0.025, 0);
    winGroup.add(sill);

    houseGroup.add(winGroup);
    windowGroupMap.set(id, winGroup);
    return winGroup;
  };

  // 1. FRONT_WINDOW (Living Room Front)
  createWindow('FRONT_WINDOW', 'Front Living Window', 2.0, 1.4, -4.5, 1.5, 5, 0);

  // 2. SIDE_WINDOW (Dining Side Wall)
  createWindow('SIDE_WINDOW', 'Side Dining Window', 1.8, 1.4, -7, 1.5, 1.5, Math.PI / 2);

  // 3. BEDROOM_WINDOW (Master Bedroom Right Wall)
  createWindow('BEDROOM_WINDOW', 'Bedroom Window', 1.8, 1.4, 7, 1.5, 1.5, -Math.PI / 2);

  // 4. REAR_WINDOW (Kitchen Rear Wall)
  createWindow('REAR_WINDOW', 'Rear Kitchen Window', 2.0, 1.4, -4.0, 1.5, -5, Math.PI);

  // ============================================================
  // 6. ROOM FURNITURE & INTERIOR DETAILS
  // ============================================================

  // --- ROOM 1: LIVING ROOM (Front Left) ---
  const livingGroup = new THREE.Group();
  livingGroup.name = 'ROOM_LIVING';

  // Navy Fabric Sofa
  const sofaBase = new THREE.Mesh(new THREE.BoxGeometry(2.4, 0.4, 0.9), fabricMat);
  sofaBase.position.set(-4.5, 0.4, 3);
  sofaBase.castShadow = true;
  livingGroup.add(sofaBase);

  const sofaBack = new THREE.Mesh(new THREE.BoxGeometry(2.4, 0.6, 0.2), fabricMat);
  sofaBack.position.set(-4.5, 0.8, 3.35);
  sofaBack.castShadow = true;
  livingGroup.add(sofaBack);

  // Coffee Table
  const table = new THREE.Mesh(new THREE.BoxGeometry(1.4, 0.35, 0.7), woodFurnitureMat);
  table.position.set(-4.5, 0.375, 1.8);
  table.castShadow = true;
  livingGroup.add(table);

  // TV & TV Console Stand
  const tvStand = new THREE.Mesh(new THREE.BoxGeometry(2.0, 0.45, 0.4), metalMat);
  tvStand.position.set(-2.4, 0.425, 3);
  tvStand.rotation.y = -Math.PI / 2;
  livingGroup.add(tvStand);

  const tvScreen = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.9, 0.05), new THREE.MeshBasicMaterial({ color: 0x051525 }));
  tvScreen.position.set(-2.4, 1.2, 3);
  tvScreen.rotation.y = -Math.PI / 2;
  livingGroup.add(tvScreen);

  // Living Rug
  const rug = new THREE.Mesh(new THREE.PlaneGeometry(3, 2.5), new THREE.MeshStandardMaterial({ color: 0xc8b598, roughness: 0.9 }));
  rug.rotation.x = -Math.PI / 2;
  rug.position.set(-4.5, 0.202, 2.5);
  livingGroup.add(rug);

  houseGroup.add(livingGroup);

  // --- ROOM 2: KITCHEN & DINING (Rear Left) ---
  const kitchenGroup = new THREE.Group();
  kitchenGroup.name = 'ROOM_KITCHEN';

  // Refrigerator
  const fridge = new THREE.Mesh(new THREE.BoxGeometry(0.9, 2.0, 0.8), new THREE.MeshStandardMaterial({ color: 0xdcdcdc, metalness: 0.7, roughness: 0.2 }));
  fridge.position.set(-6.2, 1.2, -4.2);
  fridge.castShadow = true;
  kitchenGroup.add(fridge);

  // Countertop & Sink
  const counter = new THREE.Mesh(new THREE.BoxGeometry(2.5, 0.9, 0.7), woodFurnitureMat);
  counter.position.set(-4.0, 0.65, -4.3);
  kitchenGroup.add(counter);

  // Dining Table & Chairs
  const diningTable = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.75, 1.0), woodFurnitureMat);
  diningTable.position.set(-4.5, 0.575, -2.5);
  kitchenGroup.add(diningTable);

  houseGroup.add(kitchenGroup);

  // --- ROOM 3: MASTER BEDROOM (Front Right) ---
  const bedroomGroup = new THREE.Group();
  bedroomGroup.name = 'ROOM_BEDROOM';

  // Double Bed Frame & Mattress
  const bedFrame = new THREE.Mesh(new THREE.BoxGeometry(2.0, 0.4, 2.2), woodFurnitureMat);
  bedFrame.position.set(4.5, 0.4, 3);
  bedroomGroup.add(bedFrame);

  const mattress = new THREE.Mesh(new THREE.BoxGeometry(1.8, 0.3, 2.0), ceramicMat);
  mattress.position.set(4.5, 0.65, 3);
  bedroomGroup.add(mattress);

  // Pillows
  const pillow1 = new THREE.Mesh(new THREE.BoxGeometry(0.7, 0.12, 0.4), new THREE.MeshStandardMaterial({ color: 0x4466aa }));
  pillow1.position.set(3.9, 0.82, 3.8);
  bedroomGroup.add(pillow1);

  const pillow2 = new THREE.Mesh(new THREE.BoxGeometry(0.7, 0.12, 0.4), new THREE.MeshStandardMaterial({ color: 0x4466aa }));
  pillow2.position.set(5.1, 0.82, 3.8);
  bedroomGroup.add(pillow2);

  // Wardrobe Closet
  const wardrobe = new THREE.Mesh(new THREE.BoxGeometry(1.8, 2.2, 0.7), woodFurnitureMat);
  wardrobe.position.set(6.2, 1.3, 0.2);
  wardrobe.rotation.y = -Math.PI / 2;
  bedroomGroup.add(wardrobe);

  houseGroup.add(bedroomGroup);

  // --- ROOM 4: BATHROOM (Rear Right) ---
  const bathGroup = new THREE.Group();
  bathGroup.name = 'ROOM_BATHROOM';

  // Toilet
  const toiletBase = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.45, 0.6), ceramicMat);
  toiletBase.position.set(6.2, 0.425, -4.3);
  bathGroup.add(toiletBase);

  // Vanity Sink & Mirror
  const vanity = new THREE.Mesh(new THREE.BoxGeometry(0.9, 0.8, 0.5), ceramicMat);
  vanity.position.set(4.0, 0.6, -4.4);
  bathGroup.add(vanity);

  const mirror = new THREE.Mesh(new THREE.PlaneGeometry(0.7, 0.9), new THREE.MeshStandardMaterial({ color: 0xaaaaaa, metalness: 0.95, roughness: 0.05 }));
  mirror.position.set(4.0, 1.6, -4.89);
  bathGroup.add(mirror);

  // Bathroom Floor Tiles Overlay
  const bathTile = new THREE.Mesh(new THREE.PlaneGeometry(4.3, 3.3), tileMat);
  bathTile.rotation.x = -Math.PI / 2;
  bathTile.position.set(4.75, 0.203, -3.25);
  bathGroup.add(bathTile);

  houseGroup.add(bathGroup);

  scene.add(houseGroup);

  return {
    houseGroup,
    wallMeshes,
    windowGroupMap,
    doorPivotGroup,
    setXrayMode: (isXray) => {
      wallMeshes.forEach((mesh) => {
        mesh.material.transparent = isXray;
        mesh.material.opacity = isXray ? 0.25 : 1.0;
        mesh.material.needsUpdate = true;
      });
      roofMesh.material.transparent = isXray;
      roofMesh.material.opacity = isXray ? 0.15 : 1.0;
    }
  };
}
