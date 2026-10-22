// Split-view comparison: the raw NavVis LiDAR cloud and the revised RobotGym environment,
// drawn by one camera into one canvas with a movable scissor split.
// Both assets share the scan frame: metres, Z up, floor at z = 0.
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { MeshoptDecoder } from "three/addons/libs/meshopt_decoder.module.js";
import { createFactoryLighting } from "./factory-render.js?v=20261020-spots";
import { createRobotDemo } from "/shared/robot-demo/demo.js?v=20261013-fix1";
import { createDeskDemo } from "/shared/domain-rand/desk.js?v=20261013-desk5";
import { createSceneEditor } from "/shared/scene-editor/editor.js?v=20261013-fix1";
import { createMotionQuality } from "/shared/motion-quality.js?v=20261020-mq1";
import { warmUp } from "/shared/warmup.js?v=20261020-warm1";

const params = new URLSearchParams(location.search);
const coarse = matchMedia("(pointer: coarse)").matches;
const POINT_BUDGET = THREE.MathUtils.clamp(Number(params.get("points")) || (coarse ? 2_000_000 : 5_000_000), 100_000, 5_000_000);
const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
const TOUR_SECONDS = 90;
// The PLY used offset.npy Z=-0.89495009; native USD used frame.json
// Z=-0.82495010. Convert the display cloud into the native scene frame.
const CLOUD_TO_SCENE_Z = -0.07;

const $ = (id) => document.getElementById(id);
const canvas = $("view");
const stage = $("stage");
let editor = null, robot = null, domains = null;
const lightingStatus = $("lightingStatus");
if (params.has('embed')) document.body.dataset.embedded = 'true';
// ---------- renderer, scenes, camera ----------
// Progressive passes update only the right-hand side. Preserve the completed
// LiDAR draw between them instead of redrawing five million points per tile.
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: "high-performance", preserveDrawingBuffer: true });
// 1.5x keeps text-sharp detail on Retina screens at well under half the pixels of 2x (the cloud's point
// size is derived from this ratio in resize()). While the camera moves only part of the cloud is drawn
// (it is pre-shuffled, so any prefix is an even sample); about 180 ms after it stops, one full redraw.
renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5));
const MOVING_POINTS = 1_500_000;
let cloudPoints = null;
const quality = createMotionQuality({ onChange(state) {
  if (!cloudPoints) return;
  const full = Math.min(cloudPoints.geometry.attributes.position.count, POINT_BUDGET);
  cloudPoints.geometry.setDrawRange(0, state === "moving" ? Math.min(full, MOVING_POINTS) : full);
  viewDirty = true;
} });
renderer.toneMapping = THREE.NeutralToneMapping;
renderer.toneMappingExposure = 1.05;

const BG = new THREE.Color(0x0a0b12);
const cloudScene = new THREE.Scene();
cloudScene.background = BG;
const simScene = new THREE.Scene();
simScene.background = new THREE.Color(0x1a1c26);

// Diffuse lighting and reflections are baked once from the measured scene.
const camera = new THREE.PerspectiveCamera(60, 1, 0.05, 200);
camera.up.set(0, 0, 1);

// Contact shadows are included in the camera-independent lighting bake.
function renderSim() { renderer.render(simScene, camera); }

// ---------- guided tour (position + look-at splines, closed loop) ----------
const STOPS = [
  // [camera position], [look-at]
  // Positions follow the RobotGym review cameras, which sit in open floor. The scene has no south
  // wall, and IBC stacks fill most of the north half, so the path keeps to the west aisle.
  [[-4.9, -8.1, 3.5], [0.0, -3.0, 1.0]], // south-west corner, whole bay
  [[-2.5, -4.6, 2.5], [0.0, -3.25, 0.9]], // restored workbench and control console
  [[-1.65, -5.75, 1.95], [0.5, -3.7, 1.0]], // workstation and filling equipment
  [[-3.8, -3.8, 2.2], [-1.5, -0.5, 1.6]], // back past the hoist
  [[-3.0, -1.0, 2.1], [-1.0, 1.8, 1.7]], // towards the stock
  [[-4.6, 0.5, 2.3], [-2.0, 3.6, 1.7]], // west aisle
  [[-4.8, 2.6, 2.3], [-1.9, 3.1, 1.7]], // bagged loads
  [[-4.85, 4.8, 2.5], [-1.9, 5.4, 2.1]], // rear stock
  [[-4.55, 7.0, 2.6], [-1.6, 6.5, 1.8]], // north wall
  [[-5.0, 4.2, 3.9], [-2.2, -3.5, 1.0]], // rise and look back down the aisle
  [[-4.8, -2.4, 3.3], [1.0, -4.5, 0.8]], // high over the station
];
const v3 = (a) => new THREE.Vector3(...a);
const posCurve = new THREE.CatmullRomCurve3(STOPS.map((s) => v3(s[0])), true, "centripetal");
const lookCurve = new THREE.CatmullRomCurve3(STOPS.map((s) => v3(s[1])), true, "centripetal");

let tourOn = params.has("tour") && !params.has("free") && !reducedMotion;
let tourU = Number(params.get("u")) || 0; // 0..1 around the loop
const tourPos = new THREE.Vector3();
const tourLook = new THREE.Vector3();
function tourPose(u, pos, look) {
  posCurve.getPointAt(u, pos);
  lookCurve.getPointAt(u, look);
}

// ---------- free look (drag to look, scroll / WASD to move) ----------
let yaw = 0, pitch = 0;
const BOUNDS = new THREE.Box3(new THREE.Vector3(-9, -12, 0.25), new THREE.Vector3(9, 12, 9));
function setLookFromCamera() {
  const d = new THREE.Vector3();
  camera.getWorldDirection(d);
  yaw = Math.atan2(d.y, d.x);
  pitch = Math.asin(THREE.MathUtils.clamp(d.z, -1, 1));
}
function applyLook() {
  const d = new THREE.Vector3(Math.cos(pitch) * Math.cos(yaw), Math.cos(pitch) * Math.sin(yaw), Math.sin(pitch));
  camera.lookAt(camera.position.clone().add(d));
}

// Blend from wherever the user left the camera back onto the tour.
let blend = null; // { t, fromPos, fromQuat }
function setTour(on) {
  if (!on) $("hint").classList.add("gone");
  if (on === tourOn) return;
  tourOn = on;
  if (on) blend = { t: 0, fromPos: camera.position.clone(), fromQuat: camera.quaternion.clone() };
  else setLookFromCamera();
  $("tourBtn").setAttribute("aria-pressed", String(on));
  $("tourLabel").textContent = on ? "Guided tour" : "Resume tour";
}
$("tourBtn").addEventListener("click", () => setTour(!tourOn));

const VIEWS = {
  overview: [[-4.9,-8.1,3.5],[0,-3,1]],
  "filling-station": [[3.5,-7.6,3.7],[1.5,-4.7,1.35]],
  workbench: [[-2.5,-4.6,2.5],[0,-3.25,.9]],
  hoist: [[-3.8,-3.8,2.2],[-1.5,-.5,1.6]],
  conveyor: [[-2.9,-4.0,3.9],[.1,-1.8,.4]],
  pipework: [[1.8,-6.3,1.9],[4.8,-5.3,1.5]],
  "upper-pipework": [[1.0,-6.4,2.70],[4.7,-4.7,3.25]],
  workstand: [[-2.6,-2.4,1.8],[-.7,-.85,.9]],
  "rear-wall": [[-4.75,3.85,2.7],[.1,6.6,3.70]],
  "service-corner": [[.5,.1,1.8],[4.5,-2.2,2.35]],
  forklift: [[-4.5,-8.5,2.25],[-1.8,-6.7,1]],
  storage: [[-4.9,1.1,2.8],[-.9,4.7,1.5]],
  north: [[-4.5,7,2.6],[.6,8,1.6]],
};
function selectView(name, share = true) {
  const pose = VIEWS[name];
  if (!pose) return;
  setTour(false); blend = null;
  camera.position.fromArray(pose[0]); camera.lookAt(...pose[1]); setLookFromCamera();
  $("viewSelect").value = name;
  if (share) {
    const url = new URL(location.href);
    url.searchParams.set('view', name);
    history.replaceState(null, '', url);
    if (parent !== window) parent.postMessage({ type: 'movingatoms:view', scene: 'factory-floor', view: name }, location.origin);
  }
}
$("viewSelect").addEventListener('change', e => selectView(e.target.value));
$("aboutBtn").addEventListener('click', () => { setTour(false); $("aboutDialog").showModal(); });
$("aboutDialog").addEventListener('click', e => { if (e.target === $("aboutDialog")) { const r=e.target.getBoundingClientRect(); if (e.clientX<r.left || e.clientX>r.right || e.clientY<r.top || e.clientY>r.bottom) e.target.close(); } });

const keys = new Set();
addEventListener("keydown", (e) => {
  if (robot?.active || editor?.active || e.target.closest?.("button, select, input, summary, a, dialog, [role=slider]")) return;
  const k = e.key.toLowerCase();
  if (k === " ") { setTour(!tourOn); e.preventDefault(); return; }
  if (["w","a","s","d","q","e","arrowup","arrowdown","arrowleft","arrowright"].includes(k)) { keys.add(k); setTour(false); e.preventDefault(); }
});
addEventListener("keyup", (e) => keys.delete(e.key.toLowerCase()));
addEventListener("blur", () => keys.clear());

const pointers = new Map();
let pinchDist = 0;
canvas.addEventListener("pointerdown", (e) => {
  if (robot?.active || editor?.active) return;
  canvas.setPointerCapture(e.pointerId);
  pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
  canvas.classList.add("dragging");
  setTour(false);
});
canvas.addEventListener("pointermove", (e) => {
  if (robot?.active || editor?.active) return;
  const p = pointers.get(e.pointerId);
  if (!p) return;
  if (pointers.size === 2) {
    const [a, b] = [...pointers.values()];
    p.x = e.clientX; p.y = e.clientY;
    const d = Math.hypot(a.x - b.x, a.y - b.y);
    if (pinchDist) moveForward((d - pinchDist) * 0.02);
    pinchDist = d;
    return;
  }
  const dx = e.clientX - p.x, dy = e.clientY - p.y;
  p.x = e.clientX; p.y = e.clientY;
  yaw -= dx * 0.004;
  pitch = THREE.MathUtils.clamp(pitch - dy * 0.004, -1.45, 1.45);
});
const endPointer = (e) => {
  pointers.delete(e.pointerId);
  pinchDist = 0;
  if (!pointers.size) canvas.classList.remove("dragging");
};
canvas.addEventListener("pointerup", endPointer);
canvas.addEventListener("pointercancel", endPointer);
canvas.addEventListener("wheel", (e) => {
  if (robot?.active || editor?.active) return;
  e.preventDefault();
  setTour(false);
  moveForward(-e.deltaY * 0.004);
}, { passive: false });

function moveForward(dist) {
  const d = new THREE.Vector3();
  camera.getWorldDirection(d);
  camera.position.addScaledVector(d, dist);
  BOUNDS.clampPoint(camera.position, camera.position);
}

function updateFree(dt) {
  const speed = 2.2 * dt;
  const fwd = new THREE.Vector3(Math.cos(yaw), Math.sin(yaw), 0);
  const right = new THREE.Vector3(Math.sin(yaw), -Math.cos(yaw), 0);
  if (keys.has("w") || keys.has("arrowup")) camera.position.addScaledVector(fwd, speed);
  if (keys.has("s") || keys.has("arrowdown")) camera.position.addScaledVector(fwd, -speed);
  if (keys.has("d") || keys.has("arrowright")) camera.position.addScaledVector(right, speed);
  if (keys.has("a") || keys.has("arrowleft")) camera.position.addScaledVector(right, -speed);
  if (keys.has("e")) camera.position.z += speed;
  if (keys.has("q")) camera.position.z -= speed;
  BOUNDS.clampPoint(camera.position, camera.position);
  applyLook();
}

// ---------- divider ----------
let split = 0.5; // fraction of the width showing the LiDAR scan
let introSweep = null;
const divider = $("divider");
function setSplit(f) {
  if (!Number.isFinite(f)) f = .5;
  split = THREE.MathUtils.clamp(f, 0, 1);
  stage.style.setProperty("--split", `${split * 100}%`);
  divider.setAttribute("aria-valuenow", String(Math.round(split * 100)));
  const w = stage.clientWidth;
  const labelWidth = w < 721 ? 120 : 250;
  $("tagLeft").style.opacity = String(THREE.MathUtils.clamp((split * w - labelWidth) / 40, 0, 1));
  $("tagRight").style.opacity = String(THREE.MathUtils.clamp(((1 - split) * w - labelWidth) / 40, 0, 1));
}
divider.addEventListener("pointerdown", (e) => {
  divider.setPointerCapture(e.pointerId);
  divider.classList.add("active");
  introSweep = null;
  e.stopPropagation();
});
divider.addEventListener("pointermove", (e) => {
  if (divider.hasPointerCapture(e.pointerId)) setSplit(e.clientX / stage.clientWidth);
});
const releaseDivider = (e) => { divider.releasePointerCapture?.(e.pointerId); divider.classList.remove("active"); };
divider.addEventListener("pointerup", releaseDivider);
divider.addEventListener("pointercancel", releaseDivider);
divider.addEventListener("keydown", (e) => {
  const step = e.shiftKey ? 0.1 : 0.02;
  if (e.key === "ArrowLeft") setSplit(split - step);
  else if (e.key === "ArrowRight") setSplit(split + step);
  else if (e.key === "Home") setSplit(0);
  else if (e.key === "End") setSplit(1);
  else return;
  introSweep = null;
  e.preventDefault();
});

// ---------- point cloud ----------
// factory-lidar.bin: "MAPC", uint32 count, float32 min[3] max[3], uint16 xyz[count], uint8 rgb[count].
// Points are pre-shuffled, so any prefix is an even subsample of the whole scan.
const cloudMaterial = new THREE.ShaderMaterial({
  uniforms: { uSize: { value: 0.022 }, uScale: { value: 1 } },
  vertexShader: /* glsl */ `
    uniform float uSize, uScale;
    attribute vec3 color;
    varying vec3 vColor;
    void main() {
      vColor = color;
      vec4 mv = modelViewMatrix * vec4(position, 1.0);
      gl_Position = projectionMatrix * mv;
      gl_PointSize = clamp(uSize * uScale / -mv.z, 1.0, 14.0);
    }`,
  fragmentShader: /* glsl */ `
    varying vec3 vColor;
    void main() {
      vec2 c = gl_PointCoord - 0.5;
      if (dot(c, c) > 0.25) discard;
      gl_FragColor = vec4(vColor, 1.0);  // scan colours are already sRGB
    }`,
});

function parseCloud(buf) {
  const dv = new DataView(buf);
  if (dv.getUint32(0, true) !== 0x4350414d) throw new Error("not a MAPC point cloud");
  const count = dv.getUint32(4, true);
  if (buf.byteLength !== 32 + count * 9) throw new Error("Incomplete scan data");
  const lo = new Float32Array(buf, 8, 3), hi = new Float32Array(buf, 20, 3);
  const pos = new Uint16Array(buf, 32, count * 3);
  const col = new Uint8Array(buf, 32 + count * 6, count * 3);
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.BufferAttribute(pos, 3, true));
  g.setAttribute("color", new THREE.BufferAttribute(col, 3, true));
  g.setDrawRange(0, Math.min(count, POINT_BUDGET));
  const pts = new THREE.Points(g, cloudMaterial);
  pts.frustumCulled = false;
  pts.position.set(lo[0], lo[1], lo[2] + CLOUD_TO_SCENE_Z);
  pts.scale.set(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]);
  $("pointCount").textContent = `${(Math.min(count, POINT_BUDGET) / 1e6).toFixed(1)}M`;
  return pts;
}

// ---------- loading ----------
const progress = { cloud: 0, sim: 0 };
function showProgress() {
  const f = progress.cloud * 0.9 + progress.sim * 0.1;
  $("loadBar").style.width = `${(f * 100).toFixed(1)}%`;
  $("loadText").textContent = `Loading scan and scene · ${Math.round(f * 100)}%`;
}

async function fetchWithProgress(url, key) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`${url}: HTTP ${res.status}`);
  const total = Number(res.headers.get("content-length")) || 0;
  if (!res.body || !total) { const b = await res.arrayBuffer(); progress[key] = 1; showProgress(); return b; }
  const out = new Uint8Array(total);
  const reader = res.body.getReader();
  let got = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    out.set(value, got);
    got += value.length;
    progress[key] = got / total;
    showProgress();
  }
  return out.buffer;
}

async function loadSim() {
  const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
  const [gltf, lighting] = await Promise.all([
    loader.loadAsync("./assets/factory-corrected-31cd2a87303a.glb", e => {
      if (e.total) { progress.sim = e.loaded / e.total; showProgress(); }
    }),
    createFactoryLighting(renderer, simScene, ["./assets/factory-work-light-6df33785bd16.exr", "./assets/factory-storage-light-fa1ee1022a15.exr"]),
  ]);
  gltf.scene.rotation.x = Math.PI / 2;
  lighting.apply(gltf.scene);
  progress.sim = 1; showProgress();
  return gltf.scene;
}

// ---------- frame loop ----------
let viewDirty = true;
let drawnFrames = 0;
let lastViewState = '';
canvas.addEventListener('webglcontextrestored', () => { viewDirty = true; });
function resize() {
  viewDirty = true;
  const w = stage.clientWidth, h = stage.clientHeight;
  renderer.setSize(w, h, false);

  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  cloudMaterial.uniforms.uScale.value = (h * renderer.getPixelRatio()) / (2 * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)));
  setSplit(split);
}
addEventListener("resize", resize);

const clock = new THREE.Clock();
const ease = (t) => t * t * (3 - 2 * t);
function frame() {
  if (document.hidden) return;
  const dt = Math.min(clock.getDelta(), 0.1);
  if (domains?.active) { domains.frame(dt); return; }
  if (robot?.active) { robot.frame(dt); return; }
  if (editor?.active) { editor.frame(dt); return; }

  if (introSweep) {
    introSweep.t += dt / 2.2;
    const t = Math.min(introSweep.t, 1);
    setSplit(1 - 0.5 * ease(t));
    if (t >= 1) introSweep = null;
  }

  if (tourOn) {
    if (!params.has("hold")) tourU = (tourU + dt / TOUR_SECONDS) % 1;
    tourPose(tourU, tourPos, tourLook);
    if (blend) {
      blend.t = Math.min(blend.t + dt / 1.8, 1);
      const k = ease(blend.t);
      camera.position.lerpVectors(blend.fromPos, tourPos, k);
      const q = new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().lookAt(tourPos, tourLook, camera.up));
      camera.quaternion.slerpQuaternions(blend.fromQuat, q, k);
      if (blend.t >= 1) blend = null;
    } else {
      camera.position.copy(tourPos);
      camera.lookAt(tourLook);
    }
  } else {
    updateFree(dt);
  }

  const w = stage.clientWidth, h = stage.clientHeight, sx = Math.round(split * w);
  const cameraState = [...camera.position.toArray(), ...camera.quaternion.toArray(), w, h].join(',');
  const viewState = cameraState + ',' + sx;
  if (viewState !== lastViewState && lastViewState) quality.moved();
  quality.tick();
  if (!viewDirty && viewState === lastViewState) return;
  viewDirty = false; lastViewState = viewState;
  drawnFrames++;
  renderer.setScissorTest(true);
  if (sx > 0) { renderer.setScissor(0, 0, sx, h); renderer.render(cloudScene, camera); }
  if (sx < w) { renderer.setScissor(sx, 0, w - sx, h); renderSim(); }
  renderer.setScissorTest(false);
}

async function main() {
  resize();
  setSplit(1);
  tourPose(tourU, tourPos, tourLook);
  camera.position.copy(tourPos);
  camera.lookAt(tourLook);
  if (params.has("cam")) {
    // Debug/share link: ?cam=x,y,z&look=x,y,z opens in free look at that pose.
    camera.position.fromArray(params.get("cam").split(",").map(Number));
    camera.lookAt(new THREE.Vector3().fromArray((params.get("look") || "0,0,1").split(",").map(Number)));
    tourOn = false;
  }
  setLookFromCamera();
  if (params.has('view')) selectView(params.get('view'), false);
  if (!tourOn) { $("tourBtn").setAttribute("aria-pressed", "false"); $("tourLabel").textContent = "Start tour"; }

  try {
    const cloudUrl = POINT_BUDGET <= 2_000_000 ? './assets/lidar-mobile-e7e258e9aab3.bin' : './assets/lidar-1c0f7a354857.bin';
    const [cloudBuf, sim] = await Promise.all([fetchWithProgress(cloudUrl, "cloud"), loadSim()]);
    cloudPoints = parseCloud(cloudBuf);
    cloudScene.add(cloudPoints);
    simScene.add(sim);
  } catch (err) {
    $("loadText").textContent = 'The scene could not load. Check your connection and refresh to try again.';
    throw err;
  }
  // Upload textures and compile shaders in slices and in parallel, instead of inside the first render.
  await warmUp(renderer, [simScene, cloudScene], camera, { status: (text) => { $("loadText").textContent = text; } });
  const modeOptions = { renderer, camera, canvas, stage, comparisonScene: simScene,
    manifestUrl: '/factory-floor-scan/assets/editor-manifest.json?v=20261012-corrected',
    invalidate() { viewDirty = true; },
    onEnter() {
      const saved = { tourOn, tourU, blend, introSweep };
      setTour(false); keys.clear(); pointers.clear(); introSweep = null; blend = null;
      return saved;
    },
    onExit(saved) {
      setTour(saved.tourOn); tourU = saved.tourU; blend = saved.blend; introSweep = saved.introSweep;
      setLookFromCamera(); resize(); lastViewState = ''; viewDirty = true;
    },
  };
  editor = createSceneEditor(modeOptions);
  robot = createRobotDemo({...modeOptions,key:'factory'});
  // Domain randomization demo: objects on the scanned workbench are moved and swapped per variant.
  domains = createDeskDemo({ ...modeOptions, desk: {
    deskId: 'Scan_Workbench',
    top: { center: [-0.042, -3.426], half: [0.34, 0.765], deg: 176, z: 0.832 },
    slots: [
      { id: 'Scan_Bench_Carton', label: 'Carton', type: 'Carton' },
      { id: 'Scan_Bench_Pail_A', label: 'Pail', type: 'Pail' },
      { id: 'Scan_Bench_Pail_B', label: 'Pail', type: 'Pail' },
      { id: 'Scan_Bench_Vise', label: 'Vise', type: 'Vise' },
    ],
    extras: [],
    pool: [
      { type: 'Pail', id: 'Scan_Floor_Pail_South' },
      { type: 'Tall pail', id: 'Scan_Floor_Pail_East' },
      { type: 'Lined pail', id: 'Measured_Workstand_Pail' },
      { type: 'Container', id: 'Scan_North_Support_Container' },
    ],
    camera: { pos: [-1.55, -4.55, 1.95], look: [-0.02, -3.4, 0.9], fov: 55 },
    jitter: 0.05, yaw: 30, swapRate: 0.65,
  } });
  window.domainDemo = domains;
  window.robotDemo = robot;
  window.sceneEditor = editor;
  $("loader").classList.add("done");
  if (params.has("split")) setSplit(Number(params.get("split")));
  else if (reducedMotion || params.has('view')) setSplit(.5);
  else introSweep = { t: 0 };
  renderer.setAnimationLoop(frame);
}
window.factorySample = {
  setTour, selectView, setSplit,
  get state() { return { lighting: 'cycles-baked', tourOn, split, drawnFrames, camera: camera.position.toArray(), quaternion: camera.quaternion.toArray() }; },
};
main();
