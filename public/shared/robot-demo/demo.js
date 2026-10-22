import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import {
  loadModel,
  loadWorld,
  previewScene,
  addWorldLight,
  sceneModes,
} from "../scene-runtime/world.js?v=20261011-chest1";
import { createFactoryProps } from "./factory-props.js?v=20261011-chest1";
import { tasks } from "./tasks.js?v=20261013-fix1";
import { loadMotion } from "./motion.js?v=20261013-fix1";

export function createRobotDemo({
  key,
  renderer,
  camera: comparisonCamera,
  canvas,
  stage,
  comparisonScene,
  onEnter,
  onExit,
  invalidate,
}) {
  const entry = document.getElementById("robotBtn");
  if (!entry) return { active: false, frame() {} };
  const modes = sceneModes(renderer),
    scene = previewScene(comparisonScene),
    camera = comparisonCamera.clone();
  camera.up.set(0, 0, 1);
  camera.layers.enable(1);
  const config = tasks[key];
  let active = false,
    ready = false,
    loading = false,
    error = null,
    loadPromise,
    world,
    rig,
    player,
    physics,
    cart,
    equipment,
    boxes = [];
  let savedRenderer,
    adapterState,
    orbit,
    dirty = true,
    paused = false,
    loop = true,
    speed = 1,
    follow = true,
    accumulator = 0,
    completedWait = 0,
    drawnFrames = 0,
    epoch = 0,
    staticLight,
    movingLight;
  const caption = stage.querySelector(".title p"),
    originalCaption = caption?.textContent;
  const panel = document.createElement("aside");
  panel.className = "robot-panel";
  panel.hidden = true;
  panel.innerHTML = `<div class="robot-eyebrow">UNITREE G1 <span>PROGRAMMED DEMO</span></div><h2>${config.title}</h2><p class="robot-phase" role="status" aria-live="polite">Loading embodiment…</p><div class="robot-progress"><i></i></div><p class="robot-count">${config.subtitle}</p><details><summary>About this task</summary><p>${config.assumptions}</p><p>This is a kinematic demonstration, with object collisions and settling. It is not a validated walking policy or a real-world autonomy test.</p><a href="/shared/robot-demo/assets/UNITREE-LICENSE.txt" target="_blank" rel="noopener">Unitree model · BSD license ↗</a></details>`;
  const toolbar = document.createElement("div");
  toolbar.className = "robot-toolbar";
  toolbar.hidden = true;
  toolbar.innerHTML = `<button type="button" class="pill" data-robot="pause" disabled>Pause</button><button type="button" class="pill" data-robot="restart" disabled>Restart</button><button type="button" class="pill" data-robot="loop" aria-pressed="true">Loop on</button><label class="pill robot-speed">Speed <select aria-label="Robot playback speed"><option value="0.5">0.5×</option><option value="1" selected>1×</option><option value="1.5">1.5×</option><option value="2">2×</option></select></label><button type="button" class="pill" data-robot="camera" aria-pressed="false">Free camera</button>`;
  stage.append(panel, toolbar);
  const phase = panel.querySelector(".robot-phase"),
    count = panel.querySelector(".robot-count"),
    bar = panel.querySelector(".robot-progress i");
  const button = (name) => toolbar.querySelector(`[data-robot="${name}"]`);
  function redraw() {
    dirty = true;
    invalidate();
  }
  function updateUI() {
    button("pause").textContent = paused ? "Play" : "Pause";
    button("pause").setAttribute("aria-pressed", String(paused));
    button("loop").textContent = loop ? "Loop on" : "Loop off";
    button("loop").setAttribute("aria-pressed", String(loop));
    button("camera").textContent = follow ? "Follow robot" : "Free camera";
    button("camera").setAttribute("aria-pressed", String(follow));
    if (!ready) return;
    const state = player.state,
      message = error || state.error || state.phase;
    if (phase.textContent !== message) phase.textContent = message;
    count.textContent =
      key === "factory"
        ? `${state.dispatched ? "Case delivered to conveyor" : state.loaded ? "Component packed · " + (state.chest.lidAngle < 0.01 ? "case closed" : "case open") : "0 / 1 components packed"}${state.loops ? " · " + state.loops + " completed" : ""}`
        : `${state.loaded} / ${state.total} cartons ${key === "linden" ? "loaded" : "placed"}${state.loops ? " · " + state.loops + " completed" : ""}`;
    bar.style.width =
      (state.done
        ? 100
        : ((state.index +
            Math.min(state.time / player.sequence[state.index].duration, 1)) /
            player.sequence.length) *
          100) + "%";
    button("pause").disabled = Boolean(error || state.error);
    button("restart").disabled = false;
  }
  function followCamera(amount) {
    const target = rig
      ? rig.root.position.clone()
      : new THREE.Vector3(...config.spawn.slice(0, 3));
    // Portrait screens need room in front of the robot for the carried article.
    if (stage.clientWidth < 720) {
      const yaw = rig?.root.rotation.z ?? config.spawn[3];
      target.x += Math.cos(yaw) * 0.18;
      target.y += Math.sin(yaw) * 0.18;
    }
    target.z += 0.1;
    const desired = target.clone().add(new THREE.Vector3(0.4, -2.6, 1.3));
    if (
      camera.position.distanceToSquared(desired) < 1e-8 &&
      orbit.target.distanceToSquared(target) < 1e-8
    )
      return;
    camera.position.lerp(desired, amount);
    orbit.target.lerp(target, amount);
    orbit.update();
    dirty = true;
  }
  function cameraHome() {
    camera.position.fromArray(config.camera.position);
    camera.fov = 48;
    camera.updateProjectionMatrix();
    orbit.target.fromArray(config.camera.target);
    if (follow) followCamera(1);
    orbit.update();
    redraw();
  }
  // Several large files load in parallel; report their combined bytes so a slow
  // connection shows movement instead of a static "Loading" line.
  const downloads = new Map();
  function tracker(name) {
    return (event) => {
      downloads.set(name, [event.loaded, event.lengthComputable ? event.total : 0]);
      if (!active || ready) return;
      let loaded = 0, total = 0;
      for (const [l, t] of downloads.values()) { loaded += l; total += t; }
      const mb = (v) => (v / 1048576).toFixed(v < 10485760 ? 1 : 0);
      phase.textContent = total >= loaded && total
        ? `Loading G1 and scene objects · ${mb(loaded)} / ${mb(total)} MB`
        : `Loading G1 and scene objects · ${mb(loaded)} MB`;
      bar.style.width = (total ? Math.min(100, (loaded / total) * 100) : 0) + "%";
    };
  }
  async function load() {
    const [
      loadedWorld,
      robotModel,
      cartModel,
      propsModel,
      { RobotRig },
      { TaskPlayer },
      { createPhysics },
    ] = await Promise.all([
      loadWorld(config.inventory, renderer, tracker("world")),
      loadModel("/shared/robot-demo/assets/g1-1e0b497db803.glb", tracker("g1")),
      config.cart
        ? loadModel("/shared/robot-demo/assets/cart-aa2fba3d0e5e.glb", tracker("cart"))
        : null,
      config.props
        ? loadModel("/shared/robot-demo/assets/" + config.props, tracker("props"))
        : null,
      import("./rig.js?v=20261011-chest1"),
      import("./player.js?v=20261013-fix1"),
      import("./physics.js?v=20261011-chest1"),
    ]);
    world = loadedWorld;
    const light = addWorldLight(scene, world.root, world.manifest);
    staticLight = light;
    // A bounded shadow camera covers the task, not the entire building.
    const center = new THREE.Vector3().fromArray(config.camera.target);
    center.z = 0.5;
    light.position.copy(center).add(new THREE.Vector3(-3, -4, 7));
    light.target.position.copy(center);
    Object.assign(light.shadow.camera, {
      left: -4,
      right: 4,
      top: 4,
      bottom: -4,
      near: 1,
      far: 14,
    });
    light.shadow.camera.updateProjectionMatrix();
    light.intensity *= 0.5;
    light.shadow.autoUpdate = false;
    light.shadow.needsUpdate = true;
    movingLight = light.clone();
    movingLight.target = light.target;
    movingLight.shadow = light.shadow.clone();
    movingLight.shadow.camera.layers.set(1);
    movingLight.shadow.autoUpdate = false;
    movingLight.shadow.needsUpdate = true;
    movingLight.shadow.mapSize.setScalar(
      matchMedia("(pointer: coarse)").matches ? 512 : 1024,
    );
    scene.add(movingLight);
    rig = new RobotRig(robotModel);
    scene.add(rig.root);
    if (cartModel) {
      world.assets.get(config.cart.id).root.visible = false;
      cart = new THREE.Group();
      cart.name = "Demo cart";
      cartModel.rotation.x = Math.PI / 2;
      cart.add(cartModel);
      scene.add(cart);
      cart.traverse((n) => {
        if (n.isMesh) {
          n.castShadow = true;
          n.receiveShadow = true;
        }
      });
    }
    if (propsModel)
      equipment = createFactoryProps(propsModel, scene, world.assets, config);
    boxes = config.boxes.map(({ id, size }) => {
      const asset = world.assets.get(id);
      if (!asset) throw Error("Missing task article " + id);
      if (size) return { id, group: asset.root, size };
      const bounds = new THREE.Box3().setFromObject(asset.root),
        center = bounds.getCenter(new THREE.Vector3());
      const group = new THREE.Group();
      group.position.copy(center);
      scene.add(group);
      group.attach(asset.root);
      return { id, group, size: bounds.getSize(new THREE.Vector3()).toArray() };
    });
    // Cache shadows of architecture/furniture once. Only task objects enter the
    // small moving-shadow pass; the building is not redrawn into a shadow map
    // for every robot joint update.
    for (const root of [
      rig.root,
      cart,
      equipment?.chest,
      ...boxes.map((b) => b.group),
    ].filter(Boolean))
      root.traverse((n) => {
        if (n.isMesh) n.layers.set(1);
      });
    phase.textContent = "Preparing contacts and task…";
    physics = await createPhysics(
      scene,
      world.assets,
      new Set([...config.boxes.map((b) => b.id), config.cart?.id]),
      config.region,
      boxes,
      cart,
      config.support,
      equipment,
    );
    const motion = await loadMotion(key, boxes);
    player = new TaskPlayer(key, rig, boxes, cart, physics, motion, equipment);
    ready = true;
    button("pause").disabled = button("restart").disabled = false;
  }
  async function enter() {
    if (active) return;
    modes.enter("robot");
    const token = ++epoch;
    active = true;
    loading = !ready;
    error = null;
    adapterState = onEnter();
    savedRenderer = {
      shadow: renderer.shadowMap.enabled,
      type: renderer.shadowMap.type,
      autoUpdate: renderer.shadowMap.autoUpdate,
      autoClear: renderer.autoClear,
      pixelRatio: renderer.getPixelRatio(),
    };
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.shadowMap.autoUpdate = false;
    renderer.autoClear = true;
    renderer.setPixelRatio(
      Math.min(
        devicePixelRatio,
        matchMedia("(pointer: coarse)").matches ? 1 : 1.5,
      ),
    );
    document.body.dataset.robot = "true";
    panel.hidden = toolbar.hidden = false;
    if (caption)
      caption.textContent =
        "A programmed robot task in the reconstructed world.";
    orbit ||= new OrbitControls(camera, canvas);
    orbit.enableDamping = false;
    orbit.minDistance = 0.35;
    orbit.maxDistance = 20;
    if (!orbit.userData) {
      orbit.userData = {};
      orbit.addEventListener("change", redraw);
      orbit.addEventListener("start", () => {
        follow = false;
        updateUI();
      });
    }
    orbit.enabled = true;
    cameraHome();
    paused =
      matchMedia("(prefers-reduced-motion: reduce)").matches ||
      new URLSearchParams(location.search).has("paused");
    phase.textContent = "Loading G1 and scene objects…";
    if (!ready) bar.style.width = "0%";
    updateUI();
    redraw();
    try {
      loadPromise ||= load();
      await loadPromise;
      if (!active || token !== epoch) return;
      loading = false;
      player.reset();
      accumulator = completedWait = 0;
      renderer.shadowMap.needsUpdate = true;
      updateUI();
      redraw();
      canvas.focus({ preventScroll: true });
    } catch (failure) {
      loadPromise = null;
      // Dispose a partial instance before retrying; cached geometry remains reusable.
      physics?.dispose();
      physics = null;
      scene.clear();
      boxes = [];
      ready = false;
      if (!active || token !== epoch) return;
      loading = false;
      error = failure.message;
      phase.textContent =
        "Robot demo could not load. Return to Compare and try again.";
      console.error(failure);
      redraw();
    }
  }
  function exit() {
    if (!active) return;
    epoch++;
    active = false;
    accumulator = completedWait = 0;
    if (ready) player.reset();
    if (orbit) orbit.enabled = false;
    panel.hidden = toolbar.hidden = true;
    delete document.body.dataset.robot;
    if (caption) caption.textContent = originalCaption;
    renderer.shadowMap.enabled = savedRenderer.shadow;
    renderer.shadowMap.type = savedRenderer.type;
    renderer.shadowMap.autoUpdate = savedRenderer.autoUpdate;
    renderer.autoClear = savedRenderer.autoClear;
    renderer.setPixelRatio(savedRenderer.pixelRatio);
    modes.leave("robot");
    onExit(adapterState);
    invalidate();
  }
  function restart(clearLoops = true) {
    if (!ready) return;
    player.reset(clearLoops !== false);
    cameraHome();
    error = null;
    accumulator = completedWait = 0;
    renderer.shadowMap.needsUpdate = true;
    updateUI();
    redraw();
  }
  function pause(value = !paused) {
    paused = value;
    accumulator = 0;
    updateUI();
    redraw();
  }
  modes.register("robot", exit);
  // Warm the small robot assets once the comparison view is up (the scene objects are
  // shared with Object selection, which preloads them), so entering is near-instant.
  // Inside the /lidarsample switcher (embedded) this waits until the visitor reaches for the
  // button, so it never competes with the next scene loading.
  let warmed = false;
  const warm = () => {
    if (warmed) return;
    warmed = true;
    loadModel("/shared/robot-demo/assets/g1-1e0b497db803.glb").catch(() => {});
    import("./player.js?v=20261013-fix1").catch(() => {});
    import("./physics.js?v=20261011-chest1").catch(() => {});
  };
  if (!matchMedia("(pointer: coarse)").matches && !navigator.connection?.saveData) {
    if (document.body.dataset.embedded === "true") entry.addEventListener("pointerenter", warm, { once: true });
    else setTimeout(warm, 6000);
  }
  entry.addEventListener("focus", warm, { once: true });
  entry.disabled = false;
  entry.addEventListener("click", enter);
  button("pause").addEventListener("click", () => {
    if (player?.done) restart();
    pause();
  });
  button("restart").addEventListener("click", restart);
  button("loop").addEventListener("click", () => {
    loop = !loop;
    updateUI();
  });
  button("camera").addEventListener("click", () => {
    follow = !follow;
    updateUI();
    redraw();
  });
  toolbar.querySelector("select").addEventListener("change", (e) => {
    speed = Number(e.target.value);
    accumulator = 0;
  });
  addEventListener("keydown", (e) => {
    if (!active || e.target.closest?.("button,input,select,summary,a")) return;
    if (e.code === "Space") {
      e.preventDefault();
      pause();
    }
    if (e.key === "Escape") exit();
  });
  document.addEventListener("visibilitychange", () => {
    accumulator = 0;
  });
  addEventListener("pagehide", exit);
  canvas.addEventListener("webglcontextrestored", () => {
    if (staticLight) staticLight.shadow.needsUpdate = true;
    renderer.shadowMap.needsUpdate = true;
    redraw();
  });
  const api = {
    enter,
    exit,
    restart,
    pause,
    get active() {
      return active;
    },
    frame(dt) {
      if (!active || document.hidden) return;
      const width = stage.clientWidth,
        height = stage.clientHeight;
      if (!width || !height) return;
      if (
        renderer.getSize(new THREE.Vector2()).x !== width ||
        camera.aspect !== width / height
      ) {
        renderer.setSize(width, height, false);
        camera.aspect = width / height;
        camera.updateProjectionMatrix();
        dirty = true;
      }
      if (ready && !paused && !player.error) {
        accumulator += Math.min(dt, 0.1) * speed;
        let steps = 0;
        while (accumulator >= 1 / 60 && steps++ < 9) {
          player.step();
          accumulator -= 1 / 60;
          dirty = true;
        }
        if (player.done) {
          completedWait += dt;
          if (loop && completedWait > 2) {
            restart(false);
          } else if (!loop) pause(true);
        }
        renderer.shadowMap.needsUpdate = true;
        updateUI();
      }
      if (follow && ready) followCamera(1 - Math.exp(-dt * 5));
      if (!dirty) return;
      if (movingLight) movingLight.shadow.needsUpdate = true;
      renderer.setScissorTest(false);
      renderer.setViewport(0, 0, width, height);
      renderer.clear();
      renderer.render(scene, camera);
      drawnFrames++;
      dirty = false;
    },
    get state() {
      return {
        active,
        ready,
        loading,
        error,
        paused,
        loop,
        speed,
        follow,
        drawnFrames,
        physicsTriangles: physics?.triangles,
        rendererCalls: renderer.info.render.calls,
        resources: {
          ...renderer.info.memory,
          bodies: physics?.world.bodies.len(),
          colliders: physics?.world.colliders.len(),
          events: player?.events.length,
        },
        ...player?.state,
      };
    },
    // Deterministic fixed-step validation exercises the same controller as RAF.
    advance(seconds) {
      if (!Number.isFinite(seconds) || seconds < 0 || seconds > 600)
        throw Error("Invalid playback interval");
      if (!ready || !active) throw Error("Robot mode is not ready");
      for (let i = 0; i < Math.ceil(seconds * 60); i++) player.step();
      if (follow) followCamera(1);
      renderer.shadowMap.needsUpdate = true;
      updateUI();
      redraw();
      return api.state;
    },
    get phases() {
      return player?.sequence.map(({ name, duration }, i) => ({
        name,
        duration,
        steps: player.motion.header.phases[i].count - 1,
      }));
    },
  };
  if (new URLSearchParams(location.search).get("mode") === "robot")
    setTimeout(enter, 0);
  return api;
}
