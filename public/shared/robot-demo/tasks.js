// Positions are metres in the authored Z-up worlds. Staging is temporary and
// explicit: existing articles keep their geometry/scale and reset on exit.
export const tasks = {
  linden: {
    title: "Collect & deliver",
    subtitle: "Linden Workshop · 2 cartons",
    inventory: "/lidarsample2/assets/editor-manifest.json?v=20261011-chest1",
    boxes: [
      { id: "carton_v071_p013", center: [3.15, -1.3, 0.14815] },
      { id: "carton_v071_p009", center: [3.15, -1.85, 0.14664] },
    ],
    cart: { id: "red_shopping_cart", position: [3, 1.05, 0], yaw: Math.PI },
    spawn: [3, 2.25, 0.77, -Math.PI / 2],
    region: { min: [2.2, -3.4, 0.025], max: [3.9, 3, 1.65] },
    camera: { position: [3.4, -3.7, 2.3], target: [3, 0.5, 0.75] },
    assumptions:
      "Original cart and two original cartons staged in the aisle. Carton mass 2 kg; friction 0.9. Programmed motion with dynamic carton settling.",
  },
  factory: {
    title: "Pack & dispatch",
    subtitle: "Factory Floor · equipment case",
    inventory:
      "/factory-floor-scan/assets/editor-manifest.json?v=20261011-chest1",
    boxes: [
      {
        id: "Demo_Calibration_Module",
        center: [-1.715, -3.5, 0.696],
        size: [0.18, 0.242, 0.11],
      },
    ],
    props: "factory-props-176dcc4c1765.glb",
    station: [-1.53, -3.13, 0],
    chest: {
      position: [-1.6, -2.88, 0.64],
      destination: [-2.67, -1.67, 0.336],
    },
    spawn: [-2.6, -2.88, 0.77, 0],
    region: { min: [-3.7, -3.9, 0.025], max: [-0.9, -1.05, 1.7] },
    camera: { position: [-4.0, -5.2, 2.1], target: [-1.9, -2.6, 0.75] },
    assumptions:
      "A custom hinged equipment case, calibration module and packing stand are staged beside the original roller conveyor. Case and module are demonstration props. Programmed motion; contents and the released case settle under gravity.",
  },
};

export function buildSequence(key, boxes) {
  const config = tasks[key],
    sequence = [];
  let root = config.spawn.slice(0, 3),
    yaw = config.spawn[3],
    lean = 0,
    spread = 0.12,
    toeOut = 0,
    hands = "rest",
    grip = 0;
  function add(name, duration, change = {}) {
    root = change.root || root;
    yaw = change.yaw ?? yaw;
    lean = change.lean ?? lean;
    spread = change.spread ?? spread;
    toeOut = change.toeOut ?? toeOut;
    hands = change.hands ?? hands;
    grip = change.grip ?? grip;
    sequence.push({
      name,
      duration,
      root: [...root],
      yaw,
      lean,
      spread,
      toeOut,
      hands,
      grip,
      ...change,
    });
  }
  if (key === "factory") {
    const chest = config.chest.position,
      module = config.boxes[0].center;
    add("Walk to the packing station", 3, {
      root: [-2.13, chest[1], 0.77],
      walk: true,
    });
    add("Raise hands to the lid corners", 2.5, {
      hands: { anchor: "lid", back: -0.12, up: 0.1 },
      lean: 0.18,
    });
    add("Grip the closed lid", 2, {
      hands: "lid",
      grip: 1,
      action: "graspLid",
    });
    add("Release the case latches", 1.2, { latch: 1 });
    add("Open the chest", 4, {
      root: [-1.99, chest[1], 0.77],
      walk: true,
      lid: 1.15,
    });
    add("Release the open lid", 0.8, { grip: 0, action: "releaseLid" });
    add("Step clear of the open case", 2.5, {
      root: [-2.28, chest[1], 0.77],
      walk: true,
      hands: "hold",
    });
    add("Turn to the component", 3, {
      root: [-2.12, module[1], 0.7],
      walk: true,
      hands: "rest",
      lean: 0,
    });
    add("Reach around the component", 2.5, {
      hands: { anchor: 0, out: 0.06, up: 0.1 },
      lean: 0.28,
    });
    add("Align the component grasp", 2, { hands: 0 });
    add("Pick up the component", 0.8, { grip: 1, action: "grasp", box: 0 });
    add("Lift above the case rim", 3, {
      root: [-2.12, module[1], 0.77],
      box: 0,
      boxTarget: [-1.64, module[1], 1.04],
    });
    add("Carry over the open chest", 4, {
      root: [-2.12, chest[1], 0.77],
      walk: true,
      box: 0,
      boxTarget: [-1.64, chest[1], 1.04],
    });
    add("Release the component inside", 0.8, {
      grip: 0,
      action: "release",
      box: 0,
    });
    add("Withdraw from the opening", 2.5, {
      root: [-2.5, chest[1], 0.77],
      walk: true,
      hands: "hold",
    });
    add("Check the packed component", 2, {
      hands: "rest",
      lean: 0,
      action: "settle",
      box: 0,
    });
    add("Approach the open lid", 3, {
      root: [-1.99, chest[1], 0.77],
      walk: true,
      hands: { anchor: "lid", out: 0.055, up: 0.1 },
      lean: 0.18,
    });
    add("Take hold of the lid", 2, {
      hands: "lid",
      grip: 1,
      action: "graspLid",
    });
    add("Close the chest", 4, {
      root: [-2.13, chest[1], 0.77],
      walk: true,
      noBob: true,
      lid: 0,
    });
    add("Secure the latches", 1.2, { latch: 0 });
    add("Release the closed lid", 0.8, { grip: 0, action: "releaseLid" });
    add("Clear the front of the case", 2.5, {
      root: [-2.3, chest[1], 0.77],
      walk: true,
      hands: "hold",
    });
    add("Reach the carrying handles", 3, {
      root: [-1.99, chest[1], 0.72],
      walk: true,
      noBob: true,
      hands: { anchor: "case", out: 0.06, up: 0.1 },
      lean: 0.22,
    });
    add("Grip both case handles", 2, {
      hands: "case",
      grip: 1,
      action: "graspCase",
    });
    add("Lift the packed chest", 3, {
      root: [-1.99, chest[1], 0.77],
      chestTarget: [-1.6, chest[1], 0.8],
    });
    add("Step away from the packing station", 3, {
      root: [-2.7, chest[1], 0.77],
      walk: true,
      chestTarget: [-2.18, chest[1], 0.8],
    });
    add("Carry around the conveyor end", 3, {
      root: [-3.11, chest[1], 0.77],
      walk: true,
      chestTarget: [-2.67, chest[1], 0.8],
    });
    add("Walk to the roller conveyor", 5, {
      root: [-3.11, -1.67, 0.77],
      walk: true,
      chestTarget: [-2.67, -1.67, 0.8],
    });
    add("Set a stable lowering stance", 2, {
      root: [-3.11, -1.67, 0.68],
      walk: true,
      spread: 0.23,
      toeOut: 0.35,
    });
    add("Lower the chest onto the rollers", 4, {
      root: [-3.11, -1.67, 0.54],
      lean: 0.48,
      chestTarget: [-2.67, -1.67, 0.343],
    });
    add("Release the chest", 0.8, { grip: 0, action: "releaseCase" });
    add("Stand with hands clear", 2.5, {
      root: [-3.11, -1.67, 0.72],
      lean: 0.1,
      hands: "hold",
    });
    add("Step back from the conveyor", 3, {
      root: [-3.4, -1.67, 0.77],
      walk: true,
      hands: "hold",
    });
    add("Check the chest is supported", 2, {
      root: [-3.4, -1.67, 0.77],
      walk: true,
      hands: "rest",
      lean: 0,
      spread: 0.12,
      toeOut: 0,
      action: "settleCase",
    });
    add("Packing and dispatch complete", 2, { action: "complete" });
    return sequence;
  }
  add("Walk to the shopping cart", 3, { root: [3, 1.765, 0.77], walk: true });
  add("Raise hands above the handle", 2.2, {
    hands: { anchor: "cart", up: 0.12, back: -0.18 },
    lean: 0.1,
  });
  add("Align above the handle", 1.4, { hands: { anchor: "cart", up: 0.12 } });
  add("Reach the cart handle", 2.2, { hands: "cart" });
  add("Grip the handle", 0.7, { grip: 1, action: "graspCart" });
  add("Push to the loading position", 6.5, {
    root: [3, 0.515, 0.77],
    walk: true,
    cart: [3, -0.2, 0],
  });
  add("Release the handle", 0.8, { grip: 0, action: "releaseCart" });
  add("Lift hands off the handle", 1.5, { hands: { clear: "cart", up: 0.12 } });
  add("Withdraw from the handle", 1.5, {
    hands: { clear: "cart", back: -0.1 },
  });
  add("Back away with hands clear", 2, {
    root: [3, 0.8, 0.77],
    walk: true,
    hands: { clear: "cart", back: -0.285 },
  });
  add("Lower hands behind the cart", 1.8, { hands: "rest", lean: 0 });
  add("Step beside the cart", 2.8, {
    root: [2.38, 0.8, 0.77],
    yaw: 0,
    walk: true,
    hands: "rest",
    lean: 0,
  });
  for (let i = 0; i < boxes.length; i++) {
    const y = config.boxes[i].center[1];
    add(`Approach carton ${i + 1}`, 5, {
      root: [2.38, y, 0.77],
      walk: true,
      hands: "rest",
      lean: 0,
    });
    add("Set a stable stance", 2.2, {
      root: [2.84, y, 0.7],
      walk: true,
      spread: 0.28,
      toeOut: 0.75,
    });
    add(`Crouch to carton ${i + 1}`, 3.5, {
      root: [2.72, y, 0.39],
      lean: 0.52,
      hands: { anchor: i, out: 0.055 },
    });
    add("Align fingers beside the carton", 1.5, { hands: i });
    add(`Grip carton ${i + 1}`, 1, { grip: 1, action: "grasp", box: i });
    add("Lift and stand", 3.5, {
      root: [2.84, y, 0.7],
      lean: 0.12,
      box: i,
      boxTarget: [3.3, y, 0.94],
    });
    add("Step clear with the carton", 2.5, {
      root: [2.38, y, 0.77],
      walk: true,
      spread: 0.12,
      toeOut: 0,
      box: i,
      boxTarget: [2.84, y, 0.94],
    });
    add("Carry to the lifting position", 3.5, {
      root: [2.4, -0.95, 0.77],
      walk: true,
      box: i,
      boxTarget: [2.86, -0.95, 0.94],
    });
    add("Lift clear of the basket rim", 3, {
      lean: 0.24,
      box: i,
      boxTarget: [2.94, -0.95, 1.19],
    });
    add("Move above the basket opening", 4, {
      root: [2.4, -0.25, 0.77],
      walk: true,
      box: i,
      boxTarget: [2.94, -0.25, 1.19],
    });
    add("Release above the basket", 0.8, {
      grip: 0,
      action: "release",
      box: i,
    });
    add("Let the carton clear the hands", 0.5, { hands: "hold" });
    add("Step away from the basket", 2, {
      root: [2.38, -0.25, 0.77],
      walk: true,
      hands: "hold",
    });
    add("Clear the front of the basket", 3.5, {
      root: [2.38, -0.95, 0.77],
      walk: true,
      hands: "hold",
    });
    add("Check basket placement", 2.5, {
      hands: "rest",
      lean: 0,
      action: "settle",
      box: i,
    });
  }
  add("Return to the handle", 4, { root: [2.38, 0.515, 0.77], walk: true });
  add("Align behind the cart", 2.8, {
    root: [3, 0.515, 0.77],
    yaw: -Math.PI / 2,
    walk: true,
  });
  add("Raise hands above the loaded cart", 2.2, {
    hands: { anchor: "cart", up: 0.12, back: -0.18 },
    lean: 0.1,
  });
  add("Align above the loaded handle", 1.4, {
    hands: { anchor: "cart", up: 0.12 },
  });
  add("Reach the handle", 2, { hands: "cart" });
  add("Grip the loaded cart", 0.7, { grip: 1, action: "graspCart" });
  const turn = Math.atan2(0.2, 2.3);
  add("Deliver the loaded cart", 11, {
    root: [3.2 - Math.sin(turn) * 0.715, -2.5 + Math.cos(turn) * 0.715, 0.77],
    yaw: -Math.PI / 2 + turn,
    cart: [3.2, -2.5, 0],
    cartYaw: Math.PI + turn,
    walk: true,
  });
  add("Release at the delivery point", 0.8, { grip: 0, action: "releaseCart" });
  add("Lift hands from the parked cart", 1.5, {
    hands: { clear: "cart", up: 0.12 },
  });
  add("Withdraw from the parked cart", 1.5, {
    hands: { clear: "cart", back: -0.1 },
  });
  add("Back away from the parked cart", 2, {
    root: [3.2 - Math.sin(turn) * 1.0, -2.5 + Math.cos(turn) * 1.0, 0.77],
    walk: true,
    hands: { clear: "cart", back: -0.285 },
  });
  add("Lower hands behind the parked cart", 1.8, { hands: "rest", lean: 0 });
  add("Step back", 2, {
    root: [3.2 - Math.sin(turn) * 0.97, -2.5 + Math.cos(turn) * 0.97, 0.77],
    walk: true,
    hands: "rest",
    lean: 0,
  });
  add("Delivery complete", 2, { action: "complete" });
  return sequence;
}
