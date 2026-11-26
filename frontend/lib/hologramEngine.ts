import * as THREE from "three";

export type HologramType = "orb" | "mobius" | "arc_reactor" | "quantum_lattice" | "torus_knot" | "tachyon_loop" | "car" | "aircraft" | "drone" | "helmet" | "generic_object";

export interface HologramEngineApi {
  setHologramType: (type: HologramType) => void;
  update: (timeSec: number) => void;
  dispose: () => void;
  getGroup: () => THREE.Group;
}

export function createHologramEngine(scene: THREE.Scene): HologramEngineApi {
  const group = new THREE.Group();
  scene.add(group);

  // 3D Stark Blueprint Floor Grid
  const gridHelper = new THREE.GridHelper(16, 32, 0x00f3ff, 0x004466);
  gridHelper.position.y = -2.2;
  (gridHelper.material as THREE.Material).transparent = true;
  (gridHelper.material as THREE.Material).opacity = 0.5;
  group.add(gridHelper);

  let currentMesh: THREE.Object3D | null = null;
  let activeType: HologramType = "mobius";

  // Cyan Stark Neon Hologram Colors
  const cyanColor = new THREE.Color(0x00f3ff);
  const goldColor = new THREE.Color(0xffaa30);

  const wireframeMaterial = new THREE.MeshBasicMaterial({
    color: cyanColor,
    wireframe: true,
    transparent: true,
    opacity: 0.75,
  });

  const goldWireframe = new THREE.MeshBasicMaterial({
    color: goldColor,
    wireframe: true,
    transparent: true,
    opacity: 0.85,
  });

  const nodeMaterial = new THREE.PointsMaterial({
    color: 0x00ffff,
    size: 0.08,
    transparent: true,
    opacity: 0.9,
  });

  function clearCurrent() {
    if (currentMesh) {
      group.remove(currentMesh);
      currentMesh.traverse((child) => {
        if ((child as THREE.Mesh).geometry) {
          (child as THREE.Mesh).geometry.dispose();
        }
      });
      currentMesh = null;
    }
  }

  // 0. Classic J.A.R.V.I.S. Audio Orb (Old Design)
  function createClassicOrb(): THREE.Group {
    const orbGroup = new THREE.Group();
    // Inner glowing core
    const coreGeom = new THREE.IcosahedronGeometry(1.2, 3);
    const coreMat = new THREE.MeshBasicMaterial({ color: 0x00f3ff, wireframe: true, transparent: true, opacity: 0.85 });
    const coreMesh = new THREE.Mesh(coreGeom, coreMat);
    orbGroup.add(coreMesh);

    // Outer wireframe sphere
    const outerGeom = new THREE.SphereGeometry(2.0, 24, 20);
    const outerMesh = new THREE.Mesh(outerGeom, goldWireframe);
    orbGroup.add(outerMesh);

    // Equatorial Ring 1
    const ringGeom1 = new THREE.TorusGeometry(2.5, 0.05, 16, 80);
    const ring1 = new THREE.Mesh(ringGeom1, wireframeMaterial);
    ring1.rotation.x = Math.PI / 2;
    orbGroup.add(ring1);

    // Equatorial Ring 2 (Tilted Gold Ring)
    const ringGeom2 = new THREE.TorusGeometry(2.8, 0.04, 16, 80);
    const ring2 = new THREE.Mesh(ringGeom2, goldWireframe);
    ring2.rotation.x = Math.PI / 4;
    ring2.rotation.y = Math.PI / 6;
    orbGroup.add(ring2);

    return orbGroup;
  }

  // 1. Möbius Strip Generator (Tony Stark Endgame Time-Travel Loop)
  function createMobiusStrip(): THREE.Group {
    const mobiusGroup = new THREE.Group();
    const uSegments = 80;
    const vSegments = 20;
    const geometry = new THREE.BufferGeometry();
    const positions: number[] = [];
    const indices: number[] = [];

    const R = 2.2;
    const width = 0.9;

    for (let i = 0; i <= uSegments; i++) {
      const u = (i / uSegments) * Math.PI * 2;
      for (let j = 0; j <= vSegments; j++) {
        const v = (j / vSegments - 0.5) * width;
        const x = (R + v * Math.cos(u / 2)) * Math.cos(u);
        const y = (R + v * Math.cos(u / 2)) * Math.sin(u);
        const z = v * Math.sin(u / 2);
        positions.push(x, y, z);
      }
    }

    for (let i = 0; i < uSegments; i++) {
      for (let j = 0; j < vSegments; j++) {
        const a = i * (vSegments + 1) + j;
        const b = (i + 1) * (vSegments + 1) + j;
        const c = (i + 1) * (vSegments + 1) + (j + 1);
        const d = i * (vSegments + 1) + (j + 1);
        indices.push(a, b, d);
        indices.push(b, c, d);
      }
    }

    geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
    geometry.setIndex(indices);
    geometry.computeVertexNormals();

    const mesh = new THREE.Mesh(geometry, wireframeMaterial);
    const points = new THREE.Points(geometry, nodeMaterial);
    
    mobiusGroup.add(mesh);
    mobiusGroup.add(points);
    return mobiusGroup;
  }

  // 2. Flying Car / Futuristic Vehicle 3D Model
  function createCar(): THREE.Group {
    const carGroup = new THREE.Group();
    // Body chassis
    const bodyGeom = new THREE.BoxGeometry(3.2, 0.8, 1.6, 6, 2, 4);
    const bodyMesh = new THREE.Mesh(bodyGeom, wireframeMaterial);
    carGroup.add(bodyMesh);

    // Cabin/Windshield
    const cabinGeom = new THREE.ConeGeometry(1.0, 0.9, 4);
    cabinGeom.rotateY(Math.PI / 4);
    const cabinMesh = new THREE.Mesh(cabinGeom, goldWireframe);
    cabinMesh.position.set(-0.2, 0.7, 0);
    carGroup.add(cabinMesh);

    // 4 Hover Thrusters/Wheels
    const wheelPositions = [
      [1.1, -0.4, 0.9],
      [1.1, -0.4, -0.9],
      [-1.1, -0.4, 0.9],
      [-1.1, -0.4, -0.9],
    ];
    wheelPositions.forEach(([x, y, z]) => {
      const wheelGeom = new THREE.CylinderGeometry(0.4, 0.4, 0.2, 12);
      wheelGeom.rotateX(Math.PI / 2);
      const wheelMesh = new THREE.Mesh(wheelGeom, wireframeMaterial);
      wheelMesh.position.set(x, y, z);
      carGroup.add(wheelMesh);
    });

    return carGroup;
  }

  // 3. Sci-Fi Aircraft / Jet
  function createAircraft(): THREE.Group {
    const jetGroup = new THREE.Group();
    // Fuselage
    const fuseGeom = new THREE.ConeGeometry(0.8, 4.0, 12);
    fuseGeom.rotateX(Math.PI / 2);
    const fuseMesh = new THREE.Mesh(fuseGeom, wireframeMaterial);
    jetGroup.add(fuseMesh);

    // Wings
    const wingGeom = new THREE.BoxGeometry(4.2, 0.08, 1.4);
    const wingMesh = new THREE.Mesh(wingGeom, goldWireframe);
    wingMesh.position.set(0, 0, -0.4);
    jetGroup.add(wingMesh);

    return jetGroup;
  }

  // 4. Quadcopter Drone
  function createDrone(): THREE.Group {
    const droneGroup = new THREE.Group();
    const center = new THREE.Mesh(new THREE.SphereGeometry(0.6, 8, 8), goldWireframe);
    droneGroup.add(center);

    const armCoords = [[1.2, 1.2], [1.2, -1.2], [-1.2, 1.2], [-1.2, -1.2]];
    armCoords.forEach(([x, z]) => {
      const armGeom = new THREE.CylinderGeometry(0.08, 0.08, 1.8);
      armGeom.rotateZ(Math.PI / 4);
      const arm = new THREE.Mesh(armGeom, wireframeMaterial);
      arm.position.set(x / 2, 0, z / 2);
      droneGroup.add(arm);

      const rotor = new THREE.Mesh(new THREE.TorusGeometry(0.5, 0.05, 8, 20), wireframeMaterial);
      rotor.position.set(x, 0, z);
      rotor.rotateX(Math.PI / 2);
      droneGroup.add(rotor);
    });

    return droneGroup;
  }

  // 5. Iron Man Helmet
  function createHelmet(): THREE.Group {
    const helmetGroup = new THREE.Group();
    const dome = new THREE.Mesh(new THREE.SphereGeometry(1.4, 16, 12), wireframeMaterial);
    helmetGroup.add(dome);

    const visor = new THREE.Mesh(new THREE.BoxGeometry(1.6, 0.4, 0.6), goldWireframe);
    visor.position.set(0, 0.2, 1.0);
    helmetGroup.add(visor);

    const jaw = new THREE.Mesh(new THREE.ConeGeometry(1.2, 1.2, 4), goldWireframe);
    jaw.position.set(0, -0.8, 0.4);
    jaw.rotateX(Math.PI);
    helmetGroup.add(jaw);

    return helmetGroup;
  }

  // 6. Generic Polyhedron Mesh
  function createGenericObject(): THREE.Group {
    const gGroup = new THREE.Group();
    const poly = new THREE.Mesh(new THREE.DodecahedronGeometry(1.8, 1), wireframeMaterial);
    const outerRing = new THREE.Mesh(new THREE.TorusGeometry(2.6, 0.08, 12, 50), goldWireframe);
    gGroup.add(poly);
    gGroup.add(outerRing);
    return gGroup;
  }

  // Arc Reactor Core
  function createArcReactor(): THREE.Group {
    const reactorGroup = new THREE.Group();
    const torusGeom = new THREE.TorusGeometry(2.0, 0.4, 16, 60);
    const ringMesh = new THREE.Mesh(torusGeom, wireframeMaterial);
    reactorGroup.add(ringMesh);

    const coreGeom = new THREE.IcosahedronGeometry(0.9, 3);
    const coreMat = new THREE.MeshBasicMaterial({ color: 0x00ffff, wireframe: true, transparent: true, opacity: 0.8 });
    const coreMesh = new THREE.Mesh(coreGeom, coreMat);
    reactorGroup.add(coreMesh);

    const ringGeom2 = new THREE.TorusGeometry(1.2, 0.08, 12, 40);
    const ringMesh2 = new THREE.Mesh(ringGeom2, new THREE.MeshBasicMaterial({ color: goldColor, wireframe: true }));
    ringMesh2.rotation.x = Math.PI / 3;
    reactorGroup.add(ringMesh2);

    return reactorGroup;
  }

  // Quantum Lattice
  function createQuantumLattice(): THREE.Group {
    const latticeGroup = new THREE.Group();
    const size = 4;
    const spacing = 0.9;
    const positions: number[] = [];

    for (let x = -size / 2; x <= size / 2; x++) {
      for (let y = -size / 2; y <= size / 2; y++) {
        for (let z = -size / 2; z <= size / 2; z++) {
          positions.push(x * spacing, y * spacing, z * spacing);
        }
      }
    }

    const geom = new THREE.BufferGeometry();
    geom.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
    const points = new THREE.Points(geom, new THREE.PointsMaterial({ color: 0x00f3ff, size: 0.1, transparent: true, opacity: 0.85 }));
    const boxGeom = new THREE.BoxGeometry(size * spacing, size * spacing, size * spacing);
    const boxMesh = new THREE.Mesh(boxGeom, wireframeMaterial);
    
    latticeGroup.add(points);
    latticeGroup.add(boxMesh);
    return latticeGroup;
  }

  // Torus Knot
  function createTorusKnot(): THREE.Group {
    const knotGroup = new THREE.Group();
    const geom = new THREE.TorusKnotGeometry(1.5, 0.4, 120, 16, 2, 3);
    const mesh = new THREE.Mesh(geom, wireframeMaterial);
    const points = new THREE.Points(geom, nodeMaterial);
    knotGroup.add(mesh);
    knotGroup.add(points);
    return knotGroup;
  }

  function setHologramType(type: HologramType) {
    activeType = type;
    clearCurrent();

    switch (type) {
      case "orb":
        currentMesh = createClassicOrb();
        break;
      case "mobius":
        currentMesh = createMobiusStrip();
        break;
      case "car":
        currentMesh = createCar();
        break;
      case "aircraft":
        currentMesh = createAircraft();
        break;
      case "drone":
        currentMesh = createDrone();
        break;
      case "helmet":
        currentMesh = createHelmet();
        break;
      case "arc_reactor":
        currentMesh = createArcReactor();
        break;
      case "quantum_lattice":
        currentMesh = createQuantumLattice();
        break;
      case "torus_knot":
      case "tachyon_loop":
        currentMesh = createTorusKnot();
        break;
      case "generic_object":
      default:
        currentMesh = createGenericObject();
        break;
    }

    if (currentMesh) {
      group.add(currentMesh);
    }
  }

  // Initial set
  setHologramType("mobius");

  return {
    setHologramType,
    update: (timeSec: number) => {
      if (group) {
        group.rotation.y = timeSec * 0.4;
        group.rotation.x = Math.sin(timeSec * 0.3) * 0.15;
      }
      if (currentMesh && activeType === "mobius") {
        currentMesh.rotation.z = Math.sin(timeSec * 0.5) * 0.2;
      }
    },
    dispose: () => {
      clearCurrent();
      scene.remove(group);
    },
    getGroup: () => group,
  };
}
