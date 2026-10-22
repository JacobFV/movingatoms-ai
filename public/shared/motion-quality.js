// Motion-adaptive detail for the LiDAR sample viewers.
//
// While the camera moves, a viewer draws a lighter version of the frame (a slice of the point cloud:
// the clouds are pre-shuffled, so any prefix is an even sample). Shortly after it stops, it redraws
// once in full. Stills look exactly as before; motion costs a fraction.
//
// The pixel ratio is deliberately NOT switched here: resizing the drawing buffer reallocates the
// antialiased framebuffers, and on a Retina screen that stall cost more than it saved.
//
//   const motion = createMotionQuality({ onChange(state) { setPointBudget(state); invalidate(); } });
//   each frame: if (the camera or the view changed) motion.moved();  then  motion.tick();
//
// onChange receives "moving" or "still".
export function createMotionQuality({ settleMs = 180, onChange = () => {} } = {}) {
  let state = "still", lastMove = 0;
  const apply = (next) => {
    if (state === next) return;
    state = next;
    onChange(next);
  };
  return {
    moved(now = performance.now()) {
      lastMove = now;
      apply("moving");
    },
    // Returns true when it just switched back to full detail (the caller should redraw).
    tick(now = performance.now()) {
      if (state === "moving" && now - lastMove > settleMs) { apply("still"); return true; }
      return false;
    },
    get state() { return state; },
  };
}
