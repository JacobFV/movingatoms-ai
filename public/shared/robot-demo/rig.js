import * as THREE from "three";

const v = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);
const zAxis = v(0, 0, 1),
  clamp = THREE.MathUtils.clamp;
// Solve a small positive-definite system. Damping also handles straight limbs.
function solve(a, b) {
  const n = b.length,
    m = a.map((row, i) => [...row, b[i]]);
  for (let i = 0; i < n; i++) {
    let p = i;
    for (let j = i + 1; j < n; j++)
      if (Math.abs(m[j][i]) > Math.abs(m[p][i])) p = j;
    [m[i], m[p]] = [m[p], m[i]];
    const d = m[i][i];
    if (Math.abs(d) < 1e-12) return b.map(() => 0);
    for (let k = i; k <= n; k++) m[i][k] /= d;
    for (let j = 0; j < n; j++)
      if (j !== i) {
        const f = m[j][i];
        for (let k = i; k <= n; k++) m[j][k] -= f * m[i][k];
      }
  }
  return m.map((row) => row[n]);
}
export class RobotRig {
  constructor(model) {
    this.root = new THREE.Group();
    this.root.name = "Unitree G1";
    model.rotation.x = Math.PI / 2;
    this.root.add(model);
    this.joints = new Map();
    this.links = new Map();
    this.residuals = {};
    model.traverse((node) => {
      if (node.userData.robotLink)
        this.links.set(node.userData.robotLink, node);
      if (node.userData.jointName && node.userData.jointType !== "fixed")
        this.joints.set(node.userData.jointName, {
          node,
          ...node.userData,
          axis: v(...node.userData.axis),
          q: 0,
        });
      if (node.isMesh) {
        node.castShadow = true;
        node.receiveShadow = true;
      }
    });
    if (this.joints.size !== 43) throw Error("G1 joint inventory mismatch");
    this.chains = {};
    for (const side of ["left", "right"]) {
      this.chains[side + "Leg"] = [
        "hip_pitch",
        "hip_roll",
        "hip_yaw",
        "knee",
        "ankle_pitch",
        "ankle_roll",
      ].map((n) => this.joints.get(side + "_" + n + "_joint"));
      this.chains[side + "Arm"] = [
        "shoulder_pitch",
        "shoulder_roll",
        "shoulder_yaw",
        "elbow",
        "wrist_roll",
        "wrist_pitch",
        "wrist_yaw",
      ].map((n) => this.joints.get(side + "_" + n + "_joint"));
    }
    this.reset();
  }
  set(name, value) {
    const j = this.joints.get(name);
    if (!j) return;
    // Keep carton-carrying elbows outside the carton. These pose constraints
    // stay within the source limits; the handle uses its own arm branch.

    if (this.solveProfile === "box" && name === "left_shoulder_roll_joint")
      value = Math.max(0.05, value);
    if (this.solveProfile === "box" && name === "right_shoulder_roll_joint")
      value = Math.min(-0.05, value);
    j.q = clamp(value, j.lower, j.upper);
    j.node.quaternion.setFromAxisAngle(j.axis, j.q);
  }
  reset() {
    for (const name of this.joints.keys()) this.set(name, 0);
    for (const side of ["left", "right"]) {
      this.set(side + "_hip_pitch_joint", -0.24);
      this.set(side + "_knee_joint", 0.48);
      this.set(side + "_ankle_pitch_joint", -0.24);
      this.set(side + "_shoulder_roll_joint", side === "left" ? 0.1 : -0.1);
      this.set(side + "_elbow_joint", 0.55);
    }
    this.root.position.set(0, 0, 0.76);
    this.root.rotation.set(0, 0, 0);
    this.root.updateMatrixWorld(true);
    this.residuals = {};
  }
  point(link, offset = v()) {
    this.root.updateMatrixWorld(true);
    return this.links.get(link).localToWorld(offset.clone());
  }
  ik(chain, link, offset, target, orientation = null, iterations = 14) {
    const end = this.links.get(link),
      weight = orientation?.weight ?? 0.12;
    for (let iteration = 0; iteration < iterations; iteration++) {
      this.root.updateMatrixWorld(true);
      const point = end.localToWorld(offset.clone()),
        error = target.clone().sub(point);
      let angular = v();
      if (orientation) {
        const q = orientation.quaternion
          .clone()
          .multiply(end.getWorldQuaternion(new THREE.Quaternion()).invert());
        if (q.w < 0) {
          q.x *= -1;
          q.y *= -1;
          q.z *= -1;
          q.w *= -1;
        }
        const length = Math.hypot(q.x, q.y, q.z);
        if (length > 1e-9)
          angular
            .set(q.x, q.y, q.z)
            .multiplyScalar((2 * Math.atan2(length, q.w)) / length);
      }
      if (error.length() < 0.0005 && (!orientation || angular.length() < 0.005))
        break;
      const columns = chain.map((j) => {
        const axis = j.axis
          .clone()
          .applyQuaternion(
            j.node.parent.getWorldQuaternion(new THREE.Quaternion()),
          );
        const lever = point.clone().sub(j.node.getWorldPosition(v()));
        return [
          ...axis.clone().cross(lever).toArray(),
          ...axis.multiplyScalar(orientation ? weight : 0).toArray(),
        ];
      });
      const a = Array.from({ length: 6 }, (_, i) =>
        Array.from(
          { length: 6 },
          (_, k) =>
            columns.reduce((s, c) => s + c[i] * c[k], 0) +
            (i === k ? 0.001 : 0),
        ),
      );
      const solution = solve(a, [
        ...error.toArray(),
        ...angular.multiplyScalar(weight).toArray(),
      ]);
      for (let i = 0; i < chain.length; i++)
        this.set(
          chain[i].jointName,
          chain[i].q +
            clamp(
              columns[i].reduce((s, c, k) => s + c * solution[k], 0),
              -0.18,
              0.18,
            ),
        );
    }
    const residual = this.point(link, offset).distanceTo(target);
    this.residuals[link] = residual;
    return residual;
  }
  foot(side, position, yaw) {
    const rootYaw = this.root.rotation.z;
    const ankle = position
      .clone()
      .sub(v(0.035, 0, -0.03).applyAxisAngle(zAxis, yaw));
    const hip = v(0, side === "left" ? 0.118 : -0.118, -0.134)
      .applyAxisAngle(zAxis, rootYaw)
      .add(this.root.position);
    const delta = ankle.sub(hip).applyAxisAngle(zAxis, -rootYaw);
    const upper = 0.3,
      lower = 0.3176,
      radius = clamp(Math.hypot(delta.x, delta.z), 0.12, 0.616);
    const knee = Math.acos(
      clamp(
        (radius * radius - upper * upper - lower * lower) / (2 * upper * lower),
        -1,
        1,
      ),
    );
    const pitch =
      -Math.atan2(delta.x, -delta.z) -
      Math.atan2(lower * Math.sin(knee), upper + lower * Math.cos(knee));
    const roll = Math.atan2(delta.y, -delta.z);
    this.set(side + "_hip_pitch_joint", pitch);
    this.set(side + "_knee_joint", knee);
    this.set(side + "_hip_roll_joint", roll);
    this.set(side + "_ankle_roll_joint", -roll);
    this.set(
      side + "_hip_yaw_joint",
      Math.atan2(Math.sin(yaw - rootYaw), Math.cos(yaw - rootYaw)),
    );
    this.set(side + "_ankle_pitch_joint", -pitch - knee);
    return this.ik(
      this.chains[side + "Leg"],
      side + "_ankle_roll_link",
      v(0.035, 0, -0.03),
      position,
      {
        quaternion: new THREE.Quaternion().setFromAxisAngle(zAxis, yaw),
        weight: 0.35,
      },
      50,
    );
  }
  handOffset(side, grip = 0, profile = "box") {
    const sign = side === "left" ? 1 : -1;
    if (profile === "cart") return v(0.107, -sign * 0.064, 0);
    return v(0.135, -sign * THREE.MathUtils.lerp(0.061, 0.0725, grip), 0);
  }
  fingers(side, grip = 0, profile = "box") {
    const sign = side === "left" ? 1 : -1;
    const cart = profile === "cart";
    for (const digit of ["index", "middle"]) {
      this.set(
        `${side}_hand_${digit}_0_joint`,
        -sign * (cart ? 0.5 * grip : 0.45 + 0.1 * grip),
      );
      this.set(
        `${side}_hand_${digit}_1_joint`,
        -sign * (cart ? 0.8 * grip : 0.55 + 0.15 * grip),
      );
    }
    this.set(side + "_hand_thumb_0_joint", cart ? 0 : -0.2);
    this.set(side + "_hand_thumb_1_joint", sign * (cart ? 0.4 * grip : 1));
    this.set(side + "_hand_thumb_2_joint", sign * (cart ? 1.3 * grip : 1.6));
  }
  hand(side, position, yaw, grip = 0, pitch = 0, profile = "box") {
    // Palms face inward. The contact frame is the middle of the finger cradle.
    this.solveProfile = profile;
    const sideSign = side === "left" ? 1 : -1;
    const previous = this.chains[side + "Arm"].map((j) => j.q);
    // Author at 60 Hz with a 6 rad/s arm slew limit, then validate contacts.
    const finish = () => {
      this.chains[side + "Arm"].forEach((j, i) =>
        this.set(
          j.jointName,
          previous[i] + clamp(j.q - previous[i], -0.1, 0.1),
        ),
      );
      const residual = this.point(
        side + "_hand_palm_link",
        this.handOffset(side, grip, profile),
      ).distanceTo(position);
      this.residuals[side + "_hand_palm_link"] = residual;
      this.solveProfile = null;
      return residual;
    };
    const orientation = new THREE.Quaternion()
      .setFromAxisAngle(zAxis, yaw)
      .multiply(new THREE.Quaternion().setFromAxisAngle(v(0, 1, 0), pitch))
      .multiply(
        new THREE.Quaternion().setFromAxisAngle(
          v(1, 0, 0),
          profile === "cart" ? (sideSign * Math.PI) / 2 : 0,
        ),
      );
    this.fingers(side, grip, profile);
    // Continue from the previous solved pose to keep the same IK branch.
    // The analytic seed remains a recovery path for a new reach.
    const offset = this.handOffset(side, grip, profile);
    const warmResidual =
      profile === "cart"
        ? Infinity
        : this.ik(
            this.chains[side + "Arm"],
            side + "_hand_palm_link",
            offset,
            position,
            { quaternion: orientation, weight: 0.2 },
            35,
          );
    const warm = this.chains[side + "Arm"].map((j) => j.q);
    const warmAngle = this.links
      .get(side + "_hand_palm_link")
      .getWorldQuaternion(new THREE.Quaternion())
      .angleTo(orientation);
    if (warmResidual < 0.001 && warmAngle < 0.01) return finish();
    // Seed the elbow-down branch analytically. An unconstrained numerical
    // solver can otherwise fold the wrist back and trap itself at a limit
    // when moving from the resting hand position to a high handle.
    this.root.updateMatrixWorld(true);
    const shoulder = this.joints
      .get(side + "_shoulder_pitch_joint")
      .node.getWorldPosition(v());
    const delta = position.clone().sub(shoulder).applyAxisAngle(zAxis, -yaw);
    const upper = 0.185,
      lower = 0.31,
      radius = clamp(Math.hypot(delta.x, delta.z), 0.13, 0.494);
    const bend = Math.acos(
      clamp(
        (radius * radius - upper * upper - lower * lower) / (2 * upper * lower),
        -1,
        1,
      ),
    );
    const shoulderAngle =
      -Math.PI / 2 -
      Math.atan2(delta.z, delta.x) +
      Math.atan2(lower * Math.sin(bend), upper + lower * Math.cos(bend));
    const elbowAngle = Math.PI / 2 - bend;
    this.set(
      side + "_shoulder_pitch_joint",
      shoulderAngle - this.joints.get("waist_pitch_joint").q,
    );
    this.set(side + "_elbow_joint", elbowAngle);
    this.set(side + "_shoulder_roll_joint", sideSign * 0.08);
    this.set(side + "_shoulder_yaw_joint", 0);
    this.set(side + "_wrist_roll_joint", 0);
    this.set(side + "_wrist_yaw_joint", 0);
    this.set(side + "_wrist_pitch_joint", pitch - shoulderAngle - elbowAngle);
    this.ik(
      this.chains[side + "Arm"],
      side + "_hand_palm_link",
      this.handOffset(side, grip, profile),
      position,
      {
        quaternion: orientation,
        weight: 0.2,
      },
      60,
    );
    const continuity = (pose) =>
      (this.continuityWeight || 0) *
      Math.hypot(...pose.map((q, i) => q - previous[i]));
    const warmScore = warmResidual + warmAngle * 0.2 + continuity(warm);
    const score = () =>
      this.point(side + "_hand_palm_link", offset).distanceTo(position) +
      0.2 *
        this.links
          .get(side + "_hand_palm_link")
          .getWorldQuaternion(new THREE.Quaternion())
          .angleTo(orientation) +
      continuity(this.chains[side + "Arm"].map((j) => j.q));
    let best = {
      score: score(),
      pose: this.chains[side + "Arm"].map((j) => j.q),
    };
    if (warmScore < best.score) best = { score: warmScore, pose: warm };
    if (profile === "box" && best.score > 0.001) {
      // A straight, elbow-down seed avoids the folded-arm local minimum near
      // floor pickups. Only use recovery seeds when continuation cannot solve.
      for (const elbow of [0.4, -0.3]) {
        const seed = [-0.6, sideSign * 0.3, 0, elbow, 0, 0, 0];
        this.chains[side + "Arm"].forEach((j, i) =>
          this.set(j.jointName, seed[i]),
        );
        this.ik(
          this.chains[side + "Arm"],
          side + "_hand_palm_link",
          offset,
          position,
          { quaternion: orientation, weight: 0.2 },
          90,
        );
        const value = score();
        if (value < best.score)
          best = {
            score: value,
            pose: this.chains[side + "Arm"].map((j) => j.q),
          };
      }
    }
    this.chains[side + "Arm"].forEach((j, i) =>
      this.set(j.jointName, best.pose[i]),
    );
    return finish();
  }
  get state() {
    return {
      position: this.root.position.toArray(),
      yaw: this.root.rotation.z,
      residuals: { ...this.residuals },
      joints: [...this.joints].map(([name, j]) => ({
        name,
        q: j.q,
        lower: j.lower,
        upper: j.upper,
      })),
    };
  }
}
