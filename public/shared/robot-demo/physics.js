import * as THREE from "three";
import RAPIER from "./vendor/rapier.js";
let initialization;
const identity = { x: 0, y: 0, z: 0, w: 1 };
export async function createPhysics(
  scene,
  assets,
  excluded,
  region,
  boxes,
  cart,
  support,
  equipment = null,
) {
  await (initialization ||= RAPIER.init());
  const world = new RAPIER.World({ x: 0, y: 0, z: -9.81 });
  world.timestep = 1 / 60;
  world.numSolverIterations = 8;
  world.maxCcdSubsteps = 4;
  world.integrationParameters.normalizedAllowedLinearError = 0.0002;
  world.numAdditionalFrictionIterations = 4;
  const staticHandles = new Set(),
    staticNames = new Map(),
    collisionBounds = new Map();
  function fixed(shape, name, bounds) {
    const c = world.createCollider(shape);
    staticHandles.add(c.handle);
    staticNames.set(c.handle, name);
    collisionBounds.set(c.handle, { bounds });
    return c;
  }
  fixed(
    RAPIER.ColliderDesc.cuboid(30, 30, 0.04)
      .setTranslation(0, 0, -0.04)
      .setFriction(0.85),
    "floor",
    new THREE.Box3(
      new THREE.Vector3(-30, -30, -0.08),
      new THREE.Vector3(30, 30, 0),
    ),
  );
  // Clipped triangle proxies preserve openings in racks, pipework and benches.
  // A single enclosing box for those assets would incorrectly close the aisle.
  const roi = new THREE.Box3(
    new THREE.Vector3(...region.min),
    new THREE.Vector3(...region.max),
  );
  let triangles = 0;
  scene.updateMatrixWorld(true);
  for (const asset of assets.values()) {
    if (excluded.has(asset.id) || !roi.intersectsBox(asset.bounds)) continue;
    const vertices = [],
      indices = [];
    for (const mesh of asset.meshes) {
      if (!mesh.visible) continue;
      const box = new THREE.Box3().setFromObject(mesh);
      if (box.max.z < 0.02 || box.min.z > roi.max.z || !box.intersectsBox(roi))
        continue;
      const position = mesh.geometry.attributes.position,
        index = mesh.geometry.index;
      const points = Array.from({ length: position.count }, (_, i) =>
        new THREE.Vector3()
          .fromBufferAttribute(position, i)
          .applyMatrix4(mesh.matrixWorld),
      );
      const count = index?.count || position.count;
      const remap = new Map();
      for (let i = 0; i < count; i += 3) {
        const ids = [0, 1, 2].map((j) => (index ? index.getX(i + j) : i + j)),
          tri = ids.map((id) => points[id]);
        if (!roi.intersectsBox(new THREE.Box3().setFromPoints(tri))) continue;
        // Ground contact is handled by the continuous floor proxy.
        if (tri.every((p) => p.z < 0.025)) continue;
        for (const id of ids) {
          if (!remap.has(id)) {
            remap.set(id, vertices.length / 3);
            vertices.push(...points[id].toArray());
          }
          indices.push(remap.get(id));
        }
      }
    }
    if (indices.length) {
      triangles += indices.length / 3;
      fixed(
        RAPIER.ColliderDesc.trimesh(
          new Float32Array(vertices),
          new Uint32Array(indices),
        ).setFriction(0.8),
        asset.id,
        asset.bounds.clone().intersect(roi),
      );
    }
  }
  if (support)
    fixed(
      RAPIER.ColliderDesc.cuboid(...support.half)
        .setTranslation(...support.center)
        .setFriction(0.9),
      "workbench top",
      new THREE.Box3(
        new THREE.Vector3(...support.center).sub(
          new THREE.Vector3(...support.half),
        ),
        new THREE.Vector3(...support.center).add(
          new THREE.Vector3(...support.half),
        ),
      ),
    );
  const collisionNames = new Map(staticNames);
  let robotShapes = [],
    boundRig;
  let cartBody;
  if (cart) {
    cartBody = world.createRigidBody(
      RAPIER.RigidBodyDesc.kinematicPositionBased(),
    );
    // Use the rendered trolley, including its rim, child seat, handle and wires.
    // An enclosing hull would incorrectly seal the basket opening.
    cart.updateMatrixWorld(true);
    const inverse = cart.matrixWorld.clone().invert();
    let meshCount = 0;
    cart.traverse((mesh) => {
      if (!mesh.isMesh) return;
      const matrix = inverse.clone().multiply(mesh.matrixWorld);
      const position = mesh.geometry.attributes.position;
      const vertices = new Float32Array(position.count * 3);
      const point = new THREE.Vector3();
      for (let i = 0; i < position.count; i++) {
        point.fromBufferAttribute(position, i).applyMatrix4(matrix);
        point.toArray(vertices, i * 3);
      }
      const indices = mesh.geometry.index
        ? new Uint32Array(mesh.geometry.index.array)
        : Uint32Array.from({ length: position.count }, (_, i) => i);
      const collider = world.createCollider(
        RAPIER.ColliderDesc.trimesh(vertices, indices).setFriction(0.9),
        cartBody,
      );

      collisionBounds.set(collider.handle, {
        bounds: new THREE.Box3().setFromBufferAttribute(
          new THREE.BufferAttribute(vertices, 3),
        ),
        object: cart,
      });
      collisionNames.set(collider.handle, "trolley / " + mesh.name);
      meshCount++;
    });
    if (!meshCount) throw Error("Trolley collision geometry is missing");
  }

  for (const box of boxes) {
    box.body = world.createRigidBody(
      RAPIER.RigidBodyDesc.kinematicPositionBased()
        .setCcdEnabled(true)
        .setLinearDamping(0.35)
        .setAngularDamping(0.6),
    );
    box.collider = world.createCollider(
      RAPIER.ColliderDesc.cuboid(...box.size.map((s) => s / 2))
        .setMass(2)
        .setFriction(0.9)
        .setRestitution(0),
      box.body,
    );
    collisionNames.set(box.collider.handle, box.id);
    collisionBounds.set(box.collider.handle, {
      bounds: new THREE.Box3(
        new THREE.Vector3(...box.size).multiplyScalar(-0.5),
        new THREE.Vector3(...box.size).multiplyScalar(0.5),
      ),
      object: box.group,
    });
  }
  let caseBody;
  const caseParts = [],
    caseHandles = new Set();
  const localPose = (mesh) => {
    const matrix = equipment.chest.matrixWorld
      .clone()
      .invert()
      .multiply(mesh.matrixWorld);
    const position = new THREE.Vector3(),
      rotation = new THREE.Quaternion(),
      scale = new THREE.Vector3();
    matrix.decompose(position, rotation, scale);
    return { position, rotation, scale };
  };
  if (equipment) {
    equipment.chest.updateMatrixWorld(true);
    caseBody = world.createRigidBody(
      RAPIER.RigidBodyDesc.kinematicPositionBased().setCcdEnabled(true),
    );
    equipment.chest.traverse((mesh) => {
      if (!mesh.isMesh || !mesh.userData.demoCollider) return;
      const pose = localPose(mesh),
        attr = mesh.geometry.attributes.position;
      const points = new Float32Array(attr.count * 3);
      for (let i = 0; i < attr.count; i++) {
        points[i * 3] = attr.getX(i) * pose.scale.x;
        points[i * 3 + 1] = attr.getY(i) * pose.scale.y;
        points[i * 3 + 2] = attr.getZ(i) * pose.scale.z;
      }
      const desc = RAPIER.ColliderDesc.convexHull(points);
      if (!desc) throw Error("Invalid case part: " + mesh.name);
      const collider = world.createCollider(
        desc
          .setTranslation(...pose.position.toArray())
          .setRotation(pose.rotation)
          .setDensity(45)
          .setFriction(0.95)
          .setRestitution(0),
        caseBody,
      );
      let movingLid = false;
      for (let n = mesh; n && n !== equipment.chest; n = n.parent)
        if (n === equipment.lid || equipment.latches.includes(n))
          movingLid = true;
      caseParts.push({ mesh, collider, movingLid });
      caseHandles.add(collider.handle);
      collisionNames.set(collider.handle, "case / " + mesh.name);
      if (!mesh.geometry.boundingBox) mesh.geometry.computeBoundingBox();
      collisionBounds.set(collider.handle, {
        bounds: mesh.geometry.boundingBox,
        object: mesh,
      });
    });
    caseBody.setTranslation(equipment.chest.position, true);
    caseBody.setRotation(equipment.chest.quaternion, true);
  }
  function syncCaseParts() {
    equipment.chest.updateMatrixWorld(true);
    for (const { mesh, collider } of caseParts) {
      const pose = localPose(mesh);
      collider.setTranslationWrtParent(pose.position);
      collider.setRotationWrtParent(pose.rotation);
    }
  }
  const predicate = (c) =>
    staticHandles.has(c.handle) && staticNames.get(c.handle) !== "floor";
  function sweep(
    from,
    to,
    rotation,
    shape,
    skin = 0.003,
    filter = predicate,
    stopAtPenetration = true,
  ) {
    const delta = new THREE.Vector3().subVectors(to, from);
    if (delta.lengthSq() < 1e-12) return null;
    const hit = world.castShape(
      from,
      rotation,
      delta,
      shape,
      skin,
      1,
      stopAtPenetration,
      undefined,
      undefined,
      undefined,
      undefined,
      filter,
    );
    return hit ? collisionNames.get(hit.collider.handle) : null;
  }
  return {
    world,
    triangles,
    bindRobot(rig) {
      if (boundRig === rig) return;
      if (boundRig) throw Error("Physics is already bound to another robot");
      boundRig = rig;
      rig.root.updateMatrixWorld(true);
      rig.root.traverse((mesh) => {
        if (!mesh.isMesh) return;
        const position = mesh.geometry.attributes.position;
        const scale = mesh.getWorldScale(new THREE.Vector3());
        const points = new Float32Array(position.count * 3);
        for (let i = 0; i < position.count; i++) {
          points[i * 3] = position.getX(i) * scale.x;
          points[i * 3 + 1] = position.getY(i) * scale.y;
          points[i * 3 + 2] = position.getZ(i) * scale.z;
        }
        const desc = RAPIER.ColliderDesc.convexHull(points);
        if (!desc) throw Error("Invalid robot collision hull: " + mesh.name);
        // Query-only sensors: contacts are checked before accepting a pose.
        const collider = world.createCollider(
          desc.setSensor(true).setCollisionGroups(0),
        );
        if (!mesh.geometry.boundingBox) mesh.geometry.computeBoundingBox();
        robotShapes.push({ mesh, collider });
      });
    },
    robotContacts() {
      if (!boundRig) return [];
      boundRig.root.updateMatrixWorld(true);
      equipment?.chest.updateMatrixWorld(true);
      const contacts = [];
      const obstacles = [];
      world.colliders.forEach((c) => {
        if (collisionNames.has(c.handle)) {
          const entry = collisionBounds.get(c.handle),
            bounds = entry.bounds.clone();
          if (entry.object) {
            entry.object.updateMatrixWorld(true);
            bounds.applyMatrix4(entry.object.matrixWorld);
          }
          obstacles.push({ collider: c, bounds });
        }
      });
      for (const { mesh, collider } of robotShapes) {
        collider.setTranslation(mesh.getWorldPosition(new THREE.Vector3()));
        collider.setRotation(mesh.getWorldQuaternion(new THREE.Quaternion()));
        const bounds = mesh.geometry.boundingBox
          .clone()
          .applyMatrix4(mesh.matrixWorld);
        for (const entry of obstacles) {
          if (!bounds.intersectsBox(entry.bounds)) continue;
          const other = entry.collider;
          const contact = collider.contactCollider(other, 0);
          if (contact && contact.distance < -0.001)
            contacts.push({
              mesh: mesh.name,
              obstacle: collisionNames.get(other.handle),
              depth: -contact.distance,
            });
        }
      }
      return contacts;
    },
    capture() {
      const snapshot = [
        ...boxes.map((b) => b.body),
        ...(cartBody ? [cartBody] : []),
        ...(caseBody ? [caseBody] : []),
      ].map((body) => ({
        body,
        position: { ...body.translation() },
        rotation: { ...body.rotation() },
        velocity: { ...body.linvel() },
        angular: { ...body.angvel() },
      }));
      if (equipment) snapshot.articulation = [equipment.angle, equipment.latch];
      return snapshot;
    },
    restore(snapshot) {
      for (const s of snapshot) {
        s.body.setTranslation(s.position, true);
        s.body.setRotation(s.rotation, true);
        s.body.setNextKinematicTranslation(s.position);
        s.body.setNextKinematicRotation(s.rotation);
        s.body.setLinvel(s.velocity, true);
        s.body.setAngvel(s.angular, true);
      }
      for (const box of boxes) {
        box.group.position.copy(box.body.translation());
        box.group.quaternion.copy(box.body.rotation());
      }
      if (cart) {
        cart.position.copy(cartBody.translation());
        cart.quaternion.copy(cartBody.rotation());
      }
      if (equipment) {
        equipment.chest.position.copy(caseBody.translation());
        equipment.chest.quaternion.copy(caseBody.rotation());
        equipment.setArticulation(...snapshot.articulation);
        syncCaseParts();
      }
      world.propagateModifiedBodyPositionsToColliders();
    },
    reset() {
      for (const box of boxes) {
        box.body.setBodyType(RAPIER.RigidBodyType.KinematicPositionBased, true);
        box.body.setTranslation(box.group.position, true);
        box.body.setRotation(box.group.quaternion, true);
        box.body.setNextKinematicTranslation(box.group.position);
        box.body.setNextKinematicRotation(box.group.quaternion);
        box.body.setLinvel({ x: 0, y: 0, z: 0 }, true);
        box.body.setAngvel({ x: 0, y: 0, z: 0 }, true);
        box.dynamic = false;
      }
      if (cart) {
        cartBody.setTranslation(cart.position, true);
        cartBody.setRotation(cart.quaternion, true);
        cartBody.setNextKinematicTranslation(cart.position);
        cartBody.setNextKinematicRotation(cart.quaternion);
      }
      if (equipment) {
        caseBody.setBodyType(RAPIER.RigidBodyType.KinematicPositionBased, true);
        caseBody.setTranslation(equipment.chest.position, true);
        caseBody.setRotation(equipment.chest.quaternion, true);
        caseBody.setNextKinematicTranslation(equipment.chest.position);
        caseBody.setNextKinematicRotation(equipment.chest.quaternion);
        caseBody.setLinvel({ x: 0, y: 0, z: 0 }, true);
        caseBody.setAngvel({ x: 0, y: 0, z: 0 }, true);
        equipment.dynamic = false;
        syncCaseParts();
      }
      world.step();
    },
    moveEquipment(position, angle, latch) {
      if (angle > equipment.angle && latch < 0.999) return "closed latches";
      if (latch < equipment.latch && angle > 0.001) return "open lid";
      const previousPosition = equipment.chest.position.clone(),
        previousAngle = equipment.angle,
        previousLatch = equipment.latch;
      equipment.chest.position.copy(position);
      equipment.setArticulation(angle, latch);
      const blockers = [];
      world.colliders.forEach((c) => {
        if (collisionNames.has(c.handle) && !caseHandles.has(c.handle))
          blockers.push(c);
      });
      let hit = null;
      for (const { mesh, collider, movingLid } of caseParts) {
        const target = mesh.getWorldPosition(new THREE.Vector3()),
          rotation = mesh.getWorldQuaternion(new THREE.Quaternion());
        const filter = (c) =>
          !caseHandles.has(c.handle) &&
          collisionNames.has(c.handle) &&
          (movingLid || !boxes.some((b) => b.collider.handle === c.handle));
        hit = sweep(
          new THREE.Vector3().copy(collider.translation()),
          target,
          rotation,
          collider.shape,
          0.0005,
          filter,
          false,
        );
        if (hit) break;
        const bounds = mesh.geometry.boundingBox
          .clone()
          .applyMatrix4(mesh.matrixWorld);
        for (const c of blockers) {
          if (!filter(c)) continue;
          const entry = collisionBounds.get(c.handle),
            otherBounds = entry.bounds.clone();
          if (entry.object) {
            entry.object.updateMatrixWorld(true);
            otherBounds.applyMatrix4(entry.object.matrixWorld);
          }
          if (!bounds.intersectsBox(otherBounds)) continue;
          const contact = c.contactShape(collider.shape, target, rotation, 0);
          if (contact && contact.distance < -0.0007) {
            hit = collisionNames.get(c.handle);
            break;
          }
        }
        if (hit) break;
      }
      if (hit) {
        equipment.chest.position.copy(previousPosition);
        equipment.setArticulation(previousAngle, previousLatch);
        return hit;
      }
      caseBody.setNextKinematicTranslation(equipment.chest.position);
      caseBody.setNextKinematicRotation(equipment.chest.quaternion);
      syncCaseParts();
      return null;
    },
    releaseCase() {
      caseBody.setBodyType(RAPIER.RigidBodyType.Dynamic, true);
      caseBody.setLinvel({ x: 0, y: 0, z: 0 }, true);
      caseBody.setAngvel({ x: 0, y: 0, z: 0 }, true);
      caseBody.setLinearDamping(2);
      caseBody.setAngularDamping(4);
      equipment.dynamic = true;
    },
    caseSettled() {
      const velocity = caseBody.linvel(),
        angular = caseBody.angvel();
      return (
        Math.hypot(velocity.x, velocity.y, velocity.z) < 0.035 &&
        Math.hypot(angular.x, angular.y, angular.z) < 0.07
      );
    },
    moveBox(box, position, quaternion) {
      const obstacle = sweep(
        box.group.position,
        position,
        quaternion,
        new RAPIER.Cuboid(...box.size.map((s) => s / 2 - 0.0005)),
        0.0005,
        (c) => collisionNames.has(c.handle) && c.handle !== box.collider.handle,
        // A resting carton may separate from its support. The end-pose check
        // still rejects penetration, including source export quantization.
        false,
      );
      if (obstacle) return obstacle;
      // End-pose check also covers pure rotation, which has no linear sweep.
      const blockers = [];
      world.colliders.forEach((c) => {
        if (collisionNames.has(c.handle) && c.handle !== box.collider.handle)
          blockers.push(c);
      });
      for (const c of blockers) {
        const contact = c.contactShape(
          box.collider.shape,
          position,
          quaternion,
          0,
        );
        if (contact && contact.distance < -0.0005)
          return collisionNames.get(c.handle);
      }
      box.group.position.copy(position);
      box.group.quaternion.copy(quaternion);
      box.body.setNextKinematicTranslation(position);
      box.body.setNextKinematicRotation(quaternion);
      return null;
    },
    release(box) {
      box.body.setBodyType(RAPIER.RigidBodyType.Dynamic, true);
      box.body.setLinvel({ x: 0, y: 0, z: 0 }, true);
      box.body.setAngvel({ x: 0, y: 0, z: 0 }, true);
      box.dynamic = true;
    },
    moveCart(position, quaternion) {
      const from = cart.position.clone().add(new THREE.Vector3(0, 0, 0.6)),
        to = position.clone().add(new THREE.Vector3(0, 0, 0.6));
      const obstacle = sweep(
        from,
        to,
        quaternion,
        new RAPIER.Cuboid(0.32, 0.44, 0.5),
      );
      if (obstacle) return obstacle;
      cart.position.copy(position);
      cart.quaternion.copy(quaternion);
      cartBody.setNextKinematicTranslation(position);
      cartBody.setNextKinematicRotation(quaternion);
      return null;
    },
    walk(from, to) {
      const a = from.clone();
      a.z = 0.72;
      const b = to.clone();
      b.z = 0.72;
      return sweep(
        a,
        b,
        new THREE.Quaternion().setFromAxisAngle(
          new THREE.Vector3(1, 0, 0),
          Math.PI / 2,
        ),
        new RAPIER.Capsule(0.43, 0.13),
      );
    },
    limb(a, b, radius = 0.025) {
      const direction = new THREE.Vector3().subVectors(b, a),
        center = a.clone().lerp(b, 0.5);
      const orientation = new THREE.Quaternion().setFromUnitVectors(
        new THREE.Vector3(0, 1, 0),
        direction.clone().normalize(),
      );
      let hit = null;
      world.intersectionsWithShape(
        center,
        orientation,
        new RAPIER.Capsule(direction.length() / 2, radius),
        (collider) => {
          hit = staticNames.get(collider.handle);
          return false;
        },
        undefined,
        undefined,
        undefined,
        undefined,
        predicate,
      );
      return hit;
    },
    step() {
      world.step();
      if (equipment?.dynamic) {
        equipment.chest.position.copy(caseBody.translation());
        equipment.chest.quaternion.copy(caseBody.rotation());
      }
      for (const box of boxes)
        if (box.dynamic) {
          box.group.position.copy(box.body.translation());
          box.group.quaternion.copy(box.body.rotation());
        }
    },
    settled(box) {
      const v = box.body.linvel(),
        w = box.body.angvel();
      return (
        Math.hypot(v.x, v.y, v.z) < 0.035 && Math.hypot(w.x, w.y, w.z) < 0.07
      );
    },
    dispose() {
      world.free();
    },
  };
}
