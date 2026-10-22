import { tasks, buildSequence } from "./tasks.js?v=20261013-fix1";

export function motionSpecification(key, boxes) {
  return JSON.stringify(
    {
      version: 1,
      key,
      spawn: tasks[key].spawn,
      cart: tasks[key].cart,
      boxes: tasks[key].boxes,
      ...(tasks[key].chest
        ? {
            chest: tasks[key].chest,
            station: tasks[key].station,
            props: tasks[key].props,
          }
        : {}),
      sequence: buildSequence(key, boxes),
      sizes: boxes.map((box) =>
        box.size.map((value) => Number(value.toFixed(5))),
      ),
    },
    (_, value) =>
      typeof value === "number" ? Number(value.toFixed(5)) : value,
  );
}

export class MotionClip {
  constructor(buffer, expectedSpecification) {
    const view = new DataView(buffer),
      length = view.getUint32(0, true);
    this.header = JSON.parse(
      new TextDecoder().decode(new Uint8Array(buffer, 4, length)),
    );
    if (
      this.header.version !== 1 ||
      this.header.specification !== expectedSpecification
    )
      throw Error("The robot motion does not match this scene revision");
    this.data = new DataView(buffer, 4 + Math.ceil(length / 4) * 4);
  }
  apply(rig, phase, time) {
    const clip = this.header.phases[phase],
      count = this.header.joints.length;
    const frame = Math.min(time / this.header.step, clip.count - 1);
    const a = Math.floor(frame),
      b = Math.min(a + 1, clip.count - 1),
      blend = frame - a;
    for (let i = 0; i < count; i++) {
      const x = this.data.getUint16((clip.offset + a * count + i) * 2, true);
      const y = this.data.getUint16((clip.offset + b * count + i) * 2, true);
      const [lower, upper] = this.header.limits[i];
      rig.set(
        this.header.joints[i],
        lower + ((x + (y - x) * blend) / 65535) * (upper - lower),
      );
    }
    rig.root.updateMatrixWorld(true);
  }
}

export async function loadMotion(key, boxes) {
  const response = await fetch(
    "/shared/robot-demo/assets/motion-manifest.json?v=20261011-chest1",
  );
  if (!response.ok) throw Error("Robot motion inventory could not load");
  const manifest = await response.json();
  const file = await fetch("/shared/robot-demo/assets/" + manifest[key].file);
  if (!file.ok) throw Error("Robot motion could not load");
  return new MotionClip(
    await file.arrayBuffer(),
    motionSpecification(key, boxes),
  );
}
