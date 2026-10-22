import * as THREE from "three";

// Custom task equipment is isolated to Robot demo. Source reconstruction assets
// retain their canonical transforms in Compare and Object selection.
export function createFactoryProps(model, scene, assets, config) {
  model.rotation.x = Math.PI / 2;
  model.updateMatrixWorld(true);
  const roots = new Map();
  model.traverse((n) => {
    if (n.userData.demoRoot) roots.set(n.userData.demoRoot, n);
  });
  const take = (name) => {
    const node = roots.get(name);
    if (!node) throw Error("Missing Factory task prop: " + name);
    const group = new THREE.Group();
    group.name = name;
    scene.add(group);
    group.attach(node);
    group.traverse((n) => {
      if (n.isMesh) {
        n.castShadow = n.receiveShadow = true;
      }
    });
    return group;
  };
  const chest = take("case"),
    stand = take("stand"),
    payload = take("payload");
  stand.position.fromArray(config.station);
  let lid;
  const latches = [];
  chest.traverse((n) => {
    if (n.userData.demoHinge === "lid") lid = n;
    if (n.userData.demoLatch) latches.push(n);
  });
  if (!lid || latches.length !== 2)
    throw Error("Case articulation is incomplete");
  const closed = lid.quaternion.clone();
  const latchClosed = latches.map((n) => n.quaternion.clone());
  // Blender Y is glTF -Z inside these exported pivot nodes.
  const hingeAxis = new THREE.Vector3(0, 0, -1);
  const register = (id, root) => {
    root.updateMatrixWorld(true);
    const meshes = [];
    root.traverse((n) => {
      if (n.isMesh) meshes.push(n);
    });
    assets.set(id, {
      id,
      root,
      meshes,
      bounds: new THREE.Box3().setFromObject(root),
    });
  };
  register("Demo_Packing_Stand", stand);
  register(config.boxes[0].id, payload);
  const equipment = {
    chest,
    stand,
    payload,
    lid,
    latches,
    angle: 0,
    latch: 0,
    dynamic: false,
    setArticulation(angle, latch) {
      this.angle = angle;
      this.latch = latch;
      lid.quaternion
        .copy(closed)
        .multiply(new THREE.Quaternion().setFromAxisAngle(hingeAxis, angle));
      latches.forEach((node, i) =>
        node.quaternion
          .copy(latchClosed[i])
          .multiply(
            new THREE.Quaternion().setFromAxisAngle(hingeAxis, -latch * 1.35),
          ),
      );
      chest.updateMatrixWorld(true);
    },
    reset() {
      chest.position.fromArray(config.chest.position);
      chest.quaternion.identity();
      this.setArticulation(0, 0);
      this.dynamic = false;
    },
    grip(side, mode) {
      const sign = side === "left" ? 1 : -1;
      let point;
      if (mode === "lid") {
        point = new THREE.Vector3(-0.29, sign * 0.274, 0.012)
          .applyAxisAngle(new THREE.Vector3(0, 1, 0), this.angle)
          .add(new THREE.Vector3(0.17, 0, 0.222));
      } else point = new THREE.Vector3(0, sign * 0.319, 0.142);
      chest.updateMatrixWorld(true);
      return chest.localToWorld(point);
    },
    contains(box) {
      box.group.updateMatrixWorld(true);
      chest.updateMatrixWorld(true);
      for (const x of [-1, 1])
        for (const y of [-1, 1])
          for (const z of [-1, 1]) {
            const p = chest.worldToLocal(
              box.group.localToWorld(
                new THREE.Vector3(
                  (x * box.size[0]) / 2,
                  (y * box.size[1]) / 2,
                  (z * box.size[2]) / 2,
                ),
              ),
            );
            if (
              Math.abs(p.x) > 0.156 ||
              Math.abs(p.y) > 0.246 ||
              p.z < 0.023 ||
              p.z > 0.217
            )
              return false;
          }
      return true;
    },
  };
  equipment.reset();
  return equipment;
}
