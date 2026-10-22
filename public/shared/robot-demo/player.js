import * as THREE from "three";
import { tasks, buildSequence } from "./tasks.js?v=20261013-fix1";
const v = (...values) => new THREE.Vector3(...values),
  z = v(0, 0, 1),
  ease = (t) => t * t * (3 - 2 * t);
const yawDelta = (a, b) => Math.atan2(Math.sin(b - a), Math.cos(b - a));
export class TaskPlayer {
  constructor(key, rig, boxes, cart, physics, motion = null, equipment = null) {
    Object.assign(this, { key, rig, boxes, cart, physics, motion, equipment });
    this.config = tasks[key];
    rig.continuityWeight = key === "factory" ? 0.01 : 0;
    this.sequence = buildSequence(key, boxes);
    physics.bindRobot(rig);
    this.loops = 0;
    this.reset();
  }
  reset(clearLoops = true) {
    this.rig.reset();
    this.rig.root.position.fromArray(this.config.spawn);
    this.rig.root.rotation.z = this.config.spawn[3];
    for (let i = 0; i < this.boxes.length; i++) {
      this.boxes[i].group.position.fromArray(this.config.boxes[i].center);
      this.boxes[i].group.quaternion.identity();
    }
    if (this.cart) {
      this.cart.position.fromArray(this.config.cart.position);
      this.cart.rotation.set(0, 0, this.config.cart.yaw);
      this.cart.traverse((n) => {
        if (n.userData.rolling || n.userData.steering) n.rotation.set(0, 0, 0);
      });
    }
    this.equipment?.reset();
    this.physics.reset();
    this.index = 0;
    this.time = 0;
    this.elapsed = 0;
    this.loaded = 0;
    this.held = null;
    this.holdingCart = false;
    this.holdingCase = false;
    this.holdingLid = false;
    this.dispatched = false;
    this.error = null;
    this.safePose = null;
    this.collisionChecks = 0;
    this.collision = null;
    this.done = false;
    this.grip = 0;
    this.lean = 0;
    this.spread = 0.12;
    this.toeOut = 0;
    this.start = null;
    this.wheelAngle = 0;
    this.maxFootError = 0;
    this.maxGraspError = 0;
    this.maxContactError = 0;
    this.worstContact = null;
    this.events = [];
    if (clearLoops) this.loops = 0;
    this.feet = {};
    for (const side of ["left", "right"])
      this.feet[side] = {
        position: this.footGoal(
          this.rig.root.position,
          this.config.spawn[3],
          side,
          0.12,
        ),
        yaw: this.config.spawn[3],
      };
    this.handTargets = {};
    for (const side of ["left", "right"])
      this.handTargets[side] = this.restHand(side);
    this.solvePose();
    this.begin();
  }
  fail(message) {
    if (!this.error) {
      if (this.safePose) {
        this.physics.restore(this.safePose.physics);
        this.rig.root.position.copy(this.safePose.position);
        this.rig.root.quaternion.copy(this.safePose.quaternion);
        for (const [name, q] of this.safePose.joints) this.rig.set(name, q);
        this.rig.root.updateMatrixWorld(true);
      }
      this.error = message;
      this.events.push({ time: this.elapsed, event: "blocked", message });
    }
  }
  footGoal(center, yaw, side, spread) {
    const p = v(0.035, side === "left" ? spread : -spread, 0)
      .applyAxisAngle(z, yaw)
      .add(center);
    p.z = 0.012;
    return p;
  }
  restHand(side) {
    return v(0.2, side === "left" ? 0.19 : -0.19, -0.06)
      .applyAxisAngle(z, this.rig.root.rotation.z)
      .add(this.rig.root.position);
  }
  handProfile() {
    const mode = this.sequence[this.index].hands;
    return mode === "cart" || mode?.clear === "cart" || mode?.anchor === "cart"
      ? "cart"
      : "box";
  }
  handGoal(side, mode) {
    const sign = side === "left" ? 1 : -1;
    if (typeof mode === "object" && mode.anchor !== undefined) {
      return this.handGoal(side, mode.anchor)
        .add(
          v(
            mode.back || 0,
            sign * (mode.out || 0),
            mode.up || 0,
          ).applyAxisAngle(z, this.rig.root.rotation.z),
        )
        .add(v(...(mode.shift || [0, 0, 0])));
    }
    if (mode?.clear) {
      return this.start.hands[side]
        .clone()
        .add(
          v(
            mode.back || 0,
            sign * (mode.out || 0),
            mode.up || 0,
          ).applyAxisAngle(z, this.rig.root.rotation.z),
        )
        .add(v(...(mode.shift || [0, 0, 0])));
    }
    if (mode === "case" || mode === "lid")
      return this.equipment.grip(side, mode);
    if (mode === "cart") {
      this.cart.updateMatrixWorld(true);
      return this.cart.localToWorld(v(-sign * 0.2, -0.385, 1.09));
    }
    if (typeof mode === "number") {
      const box = this.boxes[mode];
      box.group.updateMatrixWorld(true);
      return box.group.localToWorld(
        v(0, sign * (box.size[1] / 2 + 0.003), box.size[2] / 2 - 0.032),
      );
    }
    return this.restHand(side);
  }
  begin() {
    const segment = this.sequence[this.index];
    if (!segment) return;
    this.start = {
      arms: Object.fromEntries(
        [...this.rig.joints].map(([name, joint]) => [name, joint.q]),
      ),
      root: this.rig.root.position.clone(),
      yaw: this.rig.root.rotation.z,
      lean: this.lean,
      grip: this.grip,
      spread: this.spread,
      toeOut: this.toeOut,
      hands: Object.fromEntries(
        Object.entries(this.handTargets).map(([s, p]) => [s, p.clone()]),
      ),
      chest: this.equipment?.chest.position.clone(),
      lid: this.equipment?.angle,
      latch: this.equipment?.latch,
      cart: this.cart?.position.clone(),
      cartQ: this.cart?.quaternion.clone(),
      box:
        segment.box !== undefined
          ? this.boxes[segment.box].group.position.clone()
          : null,
      boxQ:
        segment.box !== undefined
          ? this.boxes[segment.box].group.quaternion.clone()
          : null,
    };
    this.steps = [];
    if (segment.walk) {
      const distance = this.start.root.distanceTo(v(...segment.root)),
        turn = Math.abs(yawDelta(this.start.yaw, segment.yaw));
      const count = Math.max(
        2,
        Math.ceil(Math.max(distance / 0.17, turn / 0.25) / 2) * 2,
      );
      const feet = Object.fromEntries(
        Object.entries(this.feet).map(([s, f]) => [
          s,
          { position: f.position.clone(), yaw: f.yaw },
        ]),
      );
      for (let i = 0; i < count; i++) {
        const side = i % 2 ? "right" : "left",
          u = ease(Math.min(1, (i + 2) / count));
        const center = this.start.root.clone().lerp(v(...segment.root), u),
          yaw = this.start.yaw + yawDelta(this.start.yaw, segment.yaw) * u;
        const goal = {
          position: this.footGoal(
            center,
            yaw,
            side,
            THREE.MathUtils.lerp(this.start.spread, segment.spread, u),
          ),
          yaw:
            yaw +
            (side === "left" ? 1 : -1) *
              THREE.MathUtils.lerp(this.start.toeOut, segment.toeOut, u),
        };
        this.steps.push({
          side,
          from: feet[side],
          to: goal,
          stance: feet[side === "left" ? "right" : "left"],
        });
        feet[side] = goal;
      }
    }
    this.events.push({
      time: this.elapsed,
      event: "phase",
      name: segment.name,
    });
  }
  solvePose() {
    const segment = this.sequence[this.index];
    if (this.motion) {
      this.motion.apply(this.rig, this.index, this.time);
      for (const side of ["left", "right"]) {
        const footError = this.rig
          .point(side + "_ankle_roll_link", v(0.035, 0, -0.03))
          .distanceTo(this.feet[side].position);
        this.maxFootError = Math.max(this.maxFootError, footError);
        this.rig.residuals[side + "_ankle_roll_link"] = footError;
        const hand = this.rig.point(
          side + "_hand_palm_link",
          this.rig.handOffset(side, this.grip, this.handProfile()),
        );
        if (["rest", "hold"].includes(segment.hands))
          this.handTargets[side] = hand;
        this.rig.residuals[side + "_hand_palm_link"] = hand.distanceTo(
          this.handTargets[side],
        );
      }
      return;
    }
    this.rig.set("waist_pitch_joint", this.lean);
    for (const side of ["left", "right"]) {
      const foot = this.feet[side];
      const error = this.rig.foot(side, foot.position, foot.yaw);
      this.maxFootError = Math.max(this.maxFootError, error);
      if (segment.hands === "hold") {
        for (const joint of this.rig.chains[side + "Arm"])
          this.rig.set(joint.jointName, this.start.arms[joint.jointName]);
        this.handTargets[side] = this.rig.point(
          side + "_hand_palm_link",
          this.rig.handOffset(side, this.grip, this.handProfile()),
        );
        this.rig.residuals[side + "_hand_palm_link"] = 0;
        continue;
      }
      if (segment.hands === "rest") {
        const envelope = segment.walk
          ? ease(
              Math.min(
                1,
                this.time / 0.6,
                Math.max(0, segment.duration - this.time) / 0.6,
              ),
            )
          : 0;
        const swing =
          Math.sin(
            (this.time / segment.duration) *
              (this.steps?.length || 2) *
              Math.PI,
          ) *
          0.1 *
          envelope;
        const posture = {
          shoulder_pitch: 0.08 + (side === "left" ? swing : -swing),
          shoulder_roll: side === "left" ? 0.08 : -0.08,
          shoulder_yaw: 0,
          elbow: 1.28,
          wrist_roll: 0,
          wrist_pitch: 0,
          wrist_yaw: 0,
        };
        for (const [joint, target] of Object.entries(posture)) {
          const name = `${side}_${joint}_joint`;
          this.rig.set(
            name,
            THREE.MathUtils.lerp(
              this.start?.arms[name] ?? target,
              target,
              this.start ? ease(Math.min(1, this.time / 0.6)) : 1,
            ),
          );
        }
        this.handTargets[side] = this.rig.point(
          side + "_hand_palm_link",
          this.rig.handOffset(side, this.grip, this.handProfile()),
        );
        this.rig.residuals[side + "_hand_palm_link"] = 0;
        continue;
      }
      const crouch = THREE.MathUtils.clamp(
        (0.65 - this.rig.root.position.z) / 0.26,
        0,
        1,
      );
      const upward = THREE.MathUtils.clamp(
        (this.handTargets[side].z - this.rig.root.position.z - 0.25) / 0.35,
        0,
        1,
      );
      const pitch =
        this.handProfile() === "cart"
          ? 0
          : crouch * 0.8 - upward * 0.7 * (1 - crouch);
      this.rig.hand(
        side,
        this.handTargets[side],
        this.rig.root.rotation.z,
        this.grip,
        pitch,
        this.handProfile(),
      );
      if (this.start && this.sequence[this.index - 1]?.hands === "rest") {
        const blend = ease(Math.min(1, this.time / 0.6));
        for (const joint of [
          ...this.rig.chains[side + "Arm"],
          ...[...this.rig.joints.values()].filter((j) =>
            j.jointName.startsWith(side + "_hand_"),
          ),
        ])
          this.rig.set(
            joint.jointName,
            THREE.MathUtils.lerp(
              this.start.arms[joint.jointName],
              joint.q,
              blend,
            ),
          );
        this.rig.residuals[side + "_hand_palm_link"] = this.rig
          .point(
            side + "_hand_palm_link",
            this.rig.handOffset(side, this.grip, this.handProfile()),
          )
          .distanceTo(this.handTargets[side]);
      }
    }
  }
  inDestination(box) {
    if (this.cart) {
      box.group.updateMatrixWorld(true);
      this.cart.updateMatrixWorld(true);
      for (const x of [-1, 1])
        for (const y of [-1, 1])
          for (const zSign of [-1, 1]) {
            const p = this.cart.worldToLocal(
              box.group.localToWorld(
                v(
                  (x * box.size[0]) / 2,
                  (y * box.size[1]) / 2,
                  (zSign * box.size[2]) / 2,
                ),
              ),
            );
            const width = THREE.MathUtils.clamp(
              0.255 + (p.z - 0.525) * 0.1,
              0.25,
              0.3,
            );
            const rear =
              -0.16 - THREE.MathUtils.clamp(p.z - 0.49, 0, 0.49) * 0.286;
            const floor = 0.51435 + p.y * 0.15217;
            if (
              Math.abs(p.x) > width + 0.008 ||
              p.y < rear - 0.012 ||
              p.y > 0.306 ||
              p.z < floor - 0.012 ||
              p.z > 1.2
            )
              return false;
          }
      return true;
    }
    return this.equipment?.contains(box) || false;
  }
  finish(segment) {
    const residual = Math.max(
      ...["left", "right"].map(
        (s) => this.rig.residuals[s + "_hand_palm_link"] || 0,
      ),
    );
    if (
      ["grasp", "graspCart", "graspLid", "graspCase"].includes(segment.action)
    ) {
      if (residual > 0.025) {
        this.fail("Hand alignment failed. Restart to reset the task.");
        return false;
      }
      this.maxGraspError = Math.max(this.maxGraspError, residual);
      if (segment.action === "grasp") this.held = segment.box;
      else if (segment.action === "graspLid") this.holdingLid = true;
      else if (segment.action === "graspCase") {
        if (
          this.equipment.angle > 0.001 ||
          this.equipment.latch > 0.001 ||
          !this.boxes.every((b) => this.inDestination(b))
        ) {
          this.fail("Close and secure the packed case before lifting.");
          return false;
        }
        this.holdingCase = true;
      } else this.holdingCart = true;
    }
    if (segment.action === "release") {
      this.physics.release(this.boxes[segment.box]);
      this.held = null;
    }
    if (segment.action === "releaseLid") this.holdingLid = false;
    if (segment.action === "releaseCase") {
      this.physics.releaseCase();
      this.holdingCase = false;
    }
    if (segment.action === "settleCase") {
      if (
        !this.physics.caseSettled() ||
        this.equipment.chest.position.distanceTo(
          v(...this.config.chest.destination),
        ) > 0.035 ||
        !this.boxes.every((b) => this.inDestination(b))
      ) {
        if (this.time < segment.duration + 4) return false;
        this.fail("The loaded case did not settle on the conveyor.");
        return false;
      }
      this.dispatched = true;
      this.events.push({ time: this.elapsed, event: "dispatched" });
    }
    if (segment.action === "releaseCart") this.holdingCart = false;
    if (segment.action === "settle") {
      const box = this.boxes[segment.box];
      if (!this.physics.settled(box) || !this.inDestination(box)) {
        if (this.time < segment.duration + 4) return false;
        this.fail(
          "Placement did not settle inside the target. Restart to try again.",
        );
        return false;
      }
      this.loaded++;
      this.events.push({
        time: this.elapsed,
        event: "placed",
        box: box.id,
        position: box.group.position.toArray(),
      });
    }
    if (segment.action === "complete") {
      const destination = this.sequence.findLast((s) => s.cart)?.cart;
      if (
        (this.equipment &&
          (!this.dispatched ||
            this.equipment.angle > 0.001 ||
            this.equipment.latch > 0.001)) ||
        this.loaded !== this.boxes.length ||
        !this.boxes.every((b) => this.inDestination(b)) ||
        (destination && this.cart.position.distanceTo(v(...destination)) > 0.02)
      ) {
        this.fail("Delivery check failed. Restart to reset.");
        return false;
      }
      this.done = true;
      this.loops++;
      this.events.push({ time: this.elapsed, event: "complete" });
      return false;
    }
    return true;
  }
  step(dt = 1 / 60) {
    if (this.error || this.done) return;
    const s = this.sequence[this.index];
    this.safePose = {
      physics: this.physics.capture(),
      position: this.rig.root.position.clone(),
      quaternion: this.rig.root.quaternion.clone(),
      joints: [...this.rig.joints].map(([name, joint]) => [name, joint.q]),
    };
    this.time += dt;
    this.elapsed += dt;
    const t = Math.min(this.time / s.duration, 1),
      u = ease(t);
    const position = this.start.root.clone().lerp(v(...s.root), u);
    if (s.walk && !s.noBob)
      position.z -= 0.03 * ease(Math.min(1, t / 0.15, (1 - t) / 0.15));
    const obstacle = this.physics.walk(this.rig.root.position, position);
    if (obstacle) {
      this.fail("Route obstructed by " + obstacle + ". Restart to reset.");
      return;
    }
    this.rig.root.position.copy(position);
    this.rig.root.rotation.z =
      this.start.yaw + yawDelta(this.start.yaw, s.yaw) * u;
    this.lean = THREE.MathUtils.lerp(this.start.lean, s.lean, u);
    this.grip = THREE.MathUtils.lerp(this.start.grip, s.grip, u);
    this.spread = THREE.MathUtils.lerp(this.start.spread, s.spread, u);
    this.toeOut = THREE.MathUtils.lerp(this.start.toeOut, s.toeOut, u);
    if (s.cart) {
      const next = this.start.cart.clone().lerp(v(...s.cart), u),
        distance = next.distanceTo(this.cart.position);
      const casters = [];
      this.cart.updateMatrixWorld(true);
      this.cart.traverse((n) => {
        if (n.userData.steering)
          casters.push({ node: n, before: n.getWorldPosition(v()) });
      });
      const rotation = this.start.cartQ
        .clone()
        .slerp(
          new THREE.Quaternion().setFromAxisAngle(
            z,
            s.cartYaw ?? this.config.cart.yaw,
          ),
          u,
        );
      const hit = this.physics.moveCart(next, rotation);
      if (hit) {
        this.fail("Cart route obstructed by " + hit);
        return;
      }
      this.wheelAngle += distance / 0.053;
      this.cart.updateMatrixWorld(true);
      for (const { node, before } of casters) {
        const travel = node.getWorldPosition(v()).sub(before);
        if (travel.lengthSq() < 1e-12) continue;
        node.rotation.y = yawDelta(
          this.cart.rotation.z + Math.PI / 2,
          Math.atan2(travel.y, travel.x),
        );
        const wheel = node.children.find((n) => n.userData.rolling);
        if (wheel) wheel.rotation.x -= travel.length() / 0.053;
      }
    }
    if (
      this.equipment &&
      (s.chestTarget || s.lid !== undefined || s.latch !== undefined)
    ) {
      if (
        (s.chestTarget && !this.holdingCase) ||
        (s.lid !== undefined && !this.holdingLid)
      ) {
        this.fail("Establish hand contact before moving the case or lid.");
        return;
      }
      const next = s.chestTarget
        ? this.start.chest.clone().lerp(v(...s.chestTarget), u)
        : this.equipment.chest.position;
      const hit = this.physics.moveEquipment(
        next,
        s.lid === undefined
          ? this.equipment.angle
          : THREE.MathUtils.lerp(this.start.lid, s.lid, u),
        s.latch === undefined
          ? this.equipment.latch
          : THREE.MathUtils.lerp(this.start.latch, s.latch, u),
      );
      if (hit) {
        this.fail("Case movement blocked by " + hit);
        return;
      }
    }
    if (s.boxTarget && this.held === s.box) {
      const box = this.boxes[s.box],
        next = this.start.box.clone().lerp(v(...s.boxTarget), u);
      const q = this.start.boxQ
        .clone()
        .slerp(
          new THREE.Quaternion().setFromAxisAngle(v(1, 0, 0), s.boxTilt || 0),
          u,
        );
      const hit = this.physics.moveBox(box, next, q);
      if (hit) {
        this.fail("Carried object obstructed by " + hit);
        return;
      }
    }
    if (this.steps.length) {
      const f = Math.min(t * this.steps.length, this.steps.length - 1e-9),
        k = Math.floor(f),
        step = this.steps[k],
        local = f - k;
      this.feet[step.side] = {
        position: step.from.position
          .clone()
          .lerp(step.to.position, ease(local)),
        yaw: step.from.yaw + yawDelta(step.from.yaw, step.to.yaw) * ease(local),
      };
      this.feet[step.side].position.z += Math.sin(Math.PI * local) * 0.055;
      const other = step.side === "left" ? "right" : "left";
      this.feet[other] = {
        position: step.stance.position.clone(),
        yaw: step.stance.yaw,
      };
    }
    this.physics.step();
    for (const side of ["left", "right"]) {
      const target = this.handGoal(side, s.hands),
        attached =
          this.held !== null ||
          this.holdingCart ||
          this.holdingCase ||
          this.holdingLid;
      this.handTargets[side] = attached
        ? target
        : this.start.hands[side].clone().lerp(target, u);
    }
    this.solvePose();
    const contacts = this.physics.robotContacts();
    this.collisionChecks++;
    if (contacts.length) {
      const c = contacts.sort((a, b) => b.depth - a.depth)[0];
      this.collision = { ...c, phase: s.name, time: this.time };
      this.fail("Motion stopped to avoid a collision. Restart to reset.");
      return;
    }
    // The root capsule cannot detect a bent knee entering a low carton.
    // Check the knee casing against every carton in its own oriented frame.
    for (const side of ["left", "right"])
      for (const box of this.boxes) {
        box.group.updateMatrixWorld(true);
        const knee = box.group.worldToLocal(
          this.rig.point(side + "_knee_link"),
        );
        const closest = knee
          .clone()
          .clamp(
            v(...box.size).multiplyScalar(-0.5),
            v(...box.size).multiplyScalar(0.5),
          );
        if (closest.distanceTo(knee) < 0.055) {
          this.fail("Knee clearance blocked by an object. Restart to reset.");
          return;
        }
      }
    if (
      this.held !== null ||
      this.holdingCart ||
      this.holdingCase ||
      this.holdingLid
    ) {
      const residual = Math.max(
        ...["left", "right"].map(
          (side) => this.rig.residuals[side + "_hand_palm_link"],
        ),
      );
      if (residual > this.maxContactError) {
        this.maxContactError = residual;
        this.worstContact = {
          phase: s.name,
          time: this.time,
          position: this.rig.root.position.toArray(),
          targets: Object.fromEntries(
            Object.entries(this.handTargets).map(([side, p]) => [
              side,
              p.toArray(),
            ]),
          ),
        };
      }
      if (residual > 0.025) {
        this.fail("Hand contact drifted. Restart to reset the task.");
        return;
      }
    }
    for (const side of ["left", "right"])
      for (const [a, b] of [
        ["shoulder_yaw_link", "elbow_link"],
        ["elbow_link", "wrist_roll_link"],
      ]) {
        const hit = this.physics.limb(
          this.rig.point(side + "_" + a),
          this.rig.point(side + "_" + b),
        );
        if (hit) {
          this.fail("Arm clearance blocked by " + hit + ". Restart to reset.");
          return;
        }
      }
    if (t === 1 && this.finish(s)) {
      this.index++;
      this.time = 0;
      this.begin();
    }
  }
  get state() {
    return {
      phase: this.sequence[this.index]?.name,
      index: this.index,
      time: this.time,
      elapsed: this.elapsed,
      loaded: this.loaded,
      total: this.boxes.length,
      done: this.done,
      error: this.error,
      loops: this.loops,
      held: this.held,
      holdingCart: this.holdingCart,
      holdingCase: this.holdingCase,
      holdingLid: this.holdingLid,
      dispatched: this.dispatched,
      chest: this.equipment
        ? {
            position: this.equipment.chest.position.toArray(),
            quaternion: this.equipment.chest.quaternion.toArray(),
            lidAngle: this.equipment.angle,
            latchOpen: this.equipment.latch,
            dynamic: this.equipment.dynamic,
          }
        : null,
      collisionChecks: this.collisionChecks,
      collision: this.collision,
      maxFootError: this.maxFootError,
      maxGraspError: this.maxGraspError,
      maxContactError: this.maxContactError,
      robot: this.rig.state,
      worstContact: this.worstContact,
      cart: this.cart?.position.toArray(),
      wheelAngle: this.wheelAngle,
      boxes: this.boxes.map((b) => ({
        id: b.id,
        size: b.size,
        position: b.group.position.toArray(),
        quaternion: b.group.quaternion.toArray(),
        dynamic: b.dynamic,
        settled: this.physics.settled(b),
      })),
    };
  }
}
