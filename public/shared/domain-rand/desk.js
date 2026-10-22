import * as THREE from "three";
import { loadWorld, previewScene, addWorldLight, sceneModes } from "../scene-runtime/world.js?v=20261011-chest1";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { MeshoptDecoder } from "three/addons/libs/meshopt_decoder.module.js";

// Domain randomization on a desk (demonstration). Uses the per-object editor scene: every variant keeps
// the desk's object slots, moves each object slightly (position + yaw), sometimes swaps it for another
// object type taken from the same scene, and cycles lighting domains. Seeded, so a variant number is repeatable.
//
// Adapter: viewer modeOptions + { desk: { deskId, top:{min:[x,y],max:[x,y],z}, slots:[{id,label}], extras:[[x,y]],
//   pool:[{type,id}], camera:{pos,look,fov}, jitter, yaw,
//   scatter:{min,max,types:[{type,models:[{url,name,zUp?,scale?}]}]} }  scatter = external props dropped in free space
const HOLD = 2.4, MOVE = 0.55;
// lighting domains, cycled with the layouts (light colour/intensity, ambient, exposure)
const LIGHTS = [
  { name: "As captured", note: "Neutral work light", color: [1, 0.95, 0.87], sun: 1, env: 1, exposure: 1 },
  { name: "Night shift", note: "Warm 2,700 K, dimmed", color: [1, 0.62, 0.32], sun: 0.75, env: 0.45, exposure: 0.72 },
  { name: "Cold LED", note: "Cool 6,500 K, bright", color: [0.72, 0.86, 1], sun: 1.35, env: 1.25, exposure: 1.12 },
  { name: "Overcast", note: "Soft daylight, low contrast", color: [0.9, 0.95, 1], sun: 0.45, env: 1.6, exposure: 0.95 },
];
const mulberry = (a) => () => { a |= 0; a = (a + 0x6d2b79f5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };

export function createDeskDemo(options) {
  const { renderer, stage, canvas, comparisonScene, manifestUrl, invalidate, onEnter, onExit, desk } = options;
  const entry = document.getElementById("drBtn");
  if (!entry || !desk) return { active: false, frame() {}, enter() {}, exit() {} };
  const modes = sceneModes(renderer);
  const caption = stage.querySelector(".title p"), originalCaption = caption?.textContent;
  const panel = document.createElement("section");
  panel.className = "dr-panel dr-desk"; panel.hidden = true; panel.setAttribute("aria-label", "Domain randomization");
  panel.innerHTML = `<div class="dr-eyebrow">DOMAIN RANDOMIZATION <span>DEMONSTRATION</span></div>
    <h2>Randomized desk</h2><p class="dr-variant" role="status" aria-live="polite">Loading objects…</p>
    <dl class="dr-desc"><dt>Lighting</dt><dd data-dr-light>—</dd></dl>
    <ol class="dr-slots"></ol><div class="dr-progress"><i></i></div>
    <details><summary>About this demo</summary><p>Every variant starts from the reconstructed desk. Each object is moved slightly, some are swapped for other object types from the same scan, and the scene is re-lit under a different lighting domain. The same variant number always gives the same layout.</p><p>Added props are high-quality third-party models: mugs from Google Scanned Objects (CC BY 4.0), the water bottle from the Khronos glTF samples (CC0) and thermoses and plants from Poly Haven (CC0). <a href="/shared/domain-rand/objects/CREDITS.txt" target="_blank" rel="noopener">Credits ↗</a></p><p>A full pipeline would randomize many more parameters, check physics, and export labels with every variant.</p></details>`;
  const toolbar = document.createElement("div");
  toolbar.className = "dr-toolbar"; toolbar.hidden = true;
  toolbar.innerHTML = `<button type="button" class="pill" data-drc="next">Randomize</button><button type="button" class="pill" data-drc="play" aria-pressed="true">Pause</button><button type="button" class="pill" data-drc="boxes" aria-pressed="true">Outlines</button>`;
  stage.append(panel, toolbar);
  const $ = (s) => panel.querySelector(s), bar = $(".dr-progress i");

  let active = false, ready = false, loading = null, saved = null, savedRenderer = null, scene = null, world = null, light = null, lightBase = null;
  let lightFrom = null, lightTo = null, lightNow = { color: [1, 0.95, 0.87], sun: 1, env: 1, exposure: 1 }, envBase = 0.55, expBase = 1;
  let cam = null, t = 0, holdT = 0, moveT = 1, playing = true, boxes = true, seed = 0;
  const items = new Map(); // key -> { asset-like {root, worldOriginal, center, size, parentInv}, from, to, scaleFrom, scaleTo, helper }
  const originals = new Map(); // id -> asset
  modes.register("dr", exit);

  function prep(asset) {
    asset.root.updateMatrixWorld(true);
    asset.worldOriginal ||= asset.root.matrixWorld.clone();
    asset.parentInv ||= asset.root.parent.matrixWorld.clone().invert();
    asset.center ||= asset.bounds.getCenter(new THREE.Vector3());
    asset.size ||= asset.bounds.getSize(new THREE.Vector3());
    return asset;
  }
  const tmp = new THREE.Matrix4(), rot = new THREE.Matrix4(), sc = new THREE.Matrix4();
  function pose(it, p) {
    // world = T(target) * Rz(yaw) * S(scale) * T(-center) * original; bottom stays on the desk top
    const a = it.asset, dz = desk.top.z - (a.bounds.min.z - a.center.z);
    tmp.makeTranslation(-a.center.x, -a.center.y, -a.center.z);
    sc.makeScale(p.s, p.s, p.s); rot.makeRotationZ(p.yaw);
    const m = new THREE.Matrix4().makeTranslation(p.x, p.y, dz - (1 - p.s) * (a.center.z - a.bounds.min.z)).multiply(rot).multiply(sc).multiply(tmp).multiply(a.worldOriginal);
    a.root.matrix.copy(a.parentInv).multiply(m);
    a.root.matrixAutoUpdate = false; a.root.matrixWorldNeedsUpdate = true;
  }
  function restoreAll() {
    for (const it of items.values()) { it.helper?.removeFromParent(); if (it.clone) it.asset.root.removeFromParent(); }
    items.clear();
    for (const a of originals.values()) { a.root.matrix.copy(a.parentInv).multiply(a.worldOriginal); a.root.matrixAutoUpdate = false; a.root.matrixWorldNeedsUpdate = true; a.root.visible = true; }
  }
  function cloneOf(id, key) {
    const src = prep(world.assets.get(id));
    const root = src.root.clone(true);
    src.root.parent.add(root);
    return { root, bounds: src.bounds, worldOriginal: src.worldOriginal, parentInv: src.parentInv, center: src.center, size: src.size, id, key };
  }
  // desk top is an oriented rectangle: centre, half extents (u along deg, w across), height
  const T = desk.top, TA = THREE.MathUtils.degToRad(T.deg), TC = Math.cos(TA), TS = Math.sin(TA);
  const local = (x, y) => { const dx = x - T.center[0], dy = y - T.center[1]; return [dx * TC + dy * TS, -dx * TS + dy * TC]; };
  const toWorld = (u, w) => [T.center[0] + u * TC - w * TS, T.center[1] + u * TS + w * TC];
  const radius = (a) => 0.5 * Math.hypot(a.size.x, a.size.y) * 0.9;

  function variant(next) {
    seed = next;
    const rng = mulberry(seed * 2654435761);
    const r = (a, b) => a + (b - a) * rng();
    const placed = [], rows = [], keep = new Set();
    const used = new Set();
    const pick = (excludeType) => { const c = desk.pool.filter((p) => p.type !== excludeType && !used.has(p.id) && !desk.slots.some((sl) => sl.id === p.id)); const ch = c[Math.floor(rng() * c.length)]; if (ch) used.add(ch.id); return ch; };
    const spots = desk.slots.map((s) => ({ ...s, origin: prep(originals.get(s.id)) })).concat((desk.extras || []).map((uw, i) => ({ extra: true, xy: toWorld(uw[0], uw[1]), label: "Free space", key: "extra" + i })));
    for (const s of spots) {
      if (s.extra && rng() < 0.45) continue;
      let swap = s.extra || rng() < (desk.swapRate ?? 0.45);
      const choice = swap ? pick(s.type) : null;
      if (swap && !choice) { if (s.extra) continue; swap = false; }
      const key = s.key || s.id;
      const prev = items.get(key);
      let it;
      if (!swap) it = prev && !prev.clone ? prev : { key, asset: s.origin, clone: false };
      else if (prev && prev.clone && prev.asset.id === choice.id) it = prev;
      else it = { key, asset: cloneOf(choice.id, key), clone: true, isNew: true };
      if (prev && prev !== it) { prev.helper?.removeFromParent(); if (prev.clone) prev.asset.root.removeFromParent(); }
      let a = it.asset;
      const base = s.extra ? { x: s.xy[0], y: s.xy[1] } : { x: s.origin.center.x, y: s.origin.center.y };
      const rad = radius(a);
      let x = base.x, y = base.y, yaw = 0, ok = false;
      for (let k = 0; k < 24 && !ok; k++) {
        const j = desk.jitter * (1 - k / 30);
        x = base.x + r(-j, j); y = base.y + r(-j, j); yaw = THREE.MathUtils.degToRad(r(-desk.yaw, desk.yaw)) + (swap && rng() < 0.3 ? Math.PI / 2 : 0);
        const inset = rad * 1.05;
        const [lu, lw] = local(x, y);
        ok = Math.abs(lu) < T.half[0] - inset && Math.abs(lw) < T.half[1] - inset &&
          placed.every((p) => Math.hypot(p.x - x, p.y - y) > (p.r + rad) * 1.02);
      }
      if (!ok && (s.extra || swap)) {
        if (it.clone) it.asset.root.removeFromParent();
        it.helper?.removeFromParent(); items.delete(key);
        if (s.extra) continue;
        // no room for the swapped object: keep the original in its scanned pose
        it = prev && !prev.clone ? prev : { key, asset: s.origin, clone: false };
      }
      if (!ok) { x = base.x; y = base.y; yaw = 0; }
      const swapped = swap && it.clone;
      a = it.asset;
      placed.push({ x, y, r: radius(a) });
      const to = { x, y, yaw, s: 1 };
      const cur = it.now || (it.clone ? { x, y, yaw, s: 0.001 } : { x: base.x, y: base.y, yaw: 0, s: 1 });
      it.from = { ...cur }; it.to = to; it.now = { ...cur };
      keep.add(key); items.set(key, it);
      const name = desk.pool.find((p) => p.id === a.id)?.type || s.label;
      const moved = Math.round(Math.hypot(x - base.x, y - base.y) * 100), deg = Math.round(THREE.MathUtils.radToDeg(yaw));
      rows.push(`<li${swapped ? ' class="swap"' : ""}><b>${name}</b><span>${s.extra ? "added" : swapped ? `swapped from ${s.label}` : "original"} · ${moved} cm · ${deg >= 0 ? "+" : ""}${deg}°</span></li>`);
    }
    // scatter: external high-quality props, random type, model, count, position and heading
    if (desk.scatter && props.size) {
      const S = desk.scatter, n = S.min + Math.floor(rng() * (S.max - S.min + 1));
      // a mix of types: every type once (shuffled), then a second of some; no model used twice
      const order = S.types.map((t) => [rng(), t]).sort((p, q) => p[0] - q[0]).map((p) => p[1]);
      const picks = [...order, ...order.map((t) => [rng(), t]).sort((p, q) => p[0] - q[0]).map((p) => p[1])].slice(0, n);
      const usedModels = new Set();
      for (let i = 0; i < picks.length; i++) {
        const group = picks[i], free = group.models.filter((m) => !usedModels.has(m.url));
        const model = (free.length ? free : group.models)[Math.floor(rng() * (free.length || group.models.length))];
        usedModels.add(model.url);
        const key = "scatter" + i, prev = items.get(key);
        let it = prev && prev.asset.id === model.url ? prev : { key, asset: propInstance(model.url), clone: true, isNew: true };
        if (prev && prev !== it) { prev.helper?.removeFromParent(); prev.asset.root.removeFromParent(); }
        const rad = radius(it.asset), inset = rad * 1.05;
        let x = 0, y = 0, yaw = 0, ok = false;
        for (let k = 0; k < 40 && !ok; k++) {
          [x, y] = toWorld(r(-1, 1) * Math.max(0, T.half[0] - inset), r(-1, 1) * Math.max(0, T.half[1] - inset));
          yaw = r(0, Math.PI * 2);
          ok = placed.every((p) => Math.hypot(p.x - x, p.y - y) > (p.r + rad) * 1.12);
        }
        if (!ok) { it.asset.root.removeFromParent(); it.helper?.removeFromParent(); items.delete(key); continue; }
        placed.push({ x, y, r: rad });
        const cur = prev === it && it.now ? it.now : { x, y, yaw, s: 0.001 };
        it.from = { ...cur }; it.to = { x, y, yaw, s: 1 }; it.now = { ...cur };
        keep.add(key); items.set(key, it);
        rows.push(`<li class="swap"><b>${group.type}</b><span>${model.name} · random pose · ${Math.round(THREE.MathUtils.radToDeg(yaw))}°</span></li>`);
      }
    }
    for (const [key, it] of items) if (!keep.has(key)) { if (it.clone) it.asset.root.removeFromParent(); it.helper?.removeFromParent(); items.delete(key); }
    // originals that were swapped away are hidden; kept ones visible
    for (const s of desk.slots) { const it = items.get(s.id); originals.get(s.id).root.visible = Boolean(it && !it.clone); }
    for (const it of items.values()) {
      it.asset.root.visible = true;
      if (!it.helper || !it.helper.parent) { it.helper = new THREE.BoxHelper(it.asset.root, 0xc1ff00); it.helper.material.transparent = true; it.helper.material.opacity = 0.9; it.helper.material.depthTest = false; it.helper.renderOrder = 3; scene.add(it.helper); }
    }
    // lighting domain: cycle through LIGHTS with the layouts, small seeded jitter on top
    lightFrom = { ...lightNow, color: [...lightNow.color] };
    const L = LIGHTS[seed % LIGHTS.length], jit = r(0.92, 1.08);
    lightTo = { color: L.color, sun: L.sun * jit, env: L.env, exposure: L.exposure };
    $("[data-dr-light]").textContent = `${L.name} · ${L.note}`;
    moveT = 0; holdT = 0;
    $(".dr-variant").textContent = `Variant ${String(seed).padStart(4, "0")} · ${placed.length} objects`;
    $(".dr-slots").innerHTML = rows.filter((x) => x.includes('class="swap"')).concat(rows.filter((x) => !x.includes('class="swap"'))).join("");
    if (caption) caption.textContent = `Variant ${String(seed).padStart(4, "0")}: objects moved and swapped on the desk`;
  }

  const props = new Map();
  async function loadProps() {
    if (!desk.scatter) return;
    const loader = new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
    const models = desk.scatter.types.flatMap((t) => t.models);
    await Promise.all(models.map(async (m) => {
      const gltf = await loader.loadAsync(m.url), root = new THREE.Group();
      if (!m.zUp) gltf.scene.rotation.x = Math.PI / 2;
      gltf.scene.scale.multiplyScalar(m.scale || 1);
      gltf.scene.traverse((o) => { if (o.isMesh) { o.castShadow = o.receiveShadow = true; for (const mt of Array.isArray(o.material) ? o.material : [o.material]) if (mt.map) mt.map.anisotropy = 8; } });
      root.add(gltf.scene); root.updateMatrixWorld(true);
      const bounds = new THREE.Box3().setFromObject(root, true);
      props.set(m.url, { root, bounds, center: bounds.getCenter(new THREE.Vector3()), size: bounds.getSize(new THREE.Vector3()) });
    }));
  }
  function propInstance(url) {
    const t = props.get(url), root = t.root.clone(true);
    scene.add(root);
    return { id: url, root, bounds: t.bounds, center: t.center, size: t.size, worldOriginal: new THREE.Matrix4(), parentInv: new THREE.Matrix4() };
  }
  async function load() {
    [world] = await Promise.all([loadWorld(manifestUrl, renderer), loadProps()]);
    scene = previewScene(comparisonScene);
    light = addWorldLight(scene, world.root, world.manifest);
    lightBase = { intensity: light.intensity, color: light.color.clone() };
    envBase = scene.environmentIntensity;
    for (const s of desk.slots) originals.set(s.id, prep(world.assets.get(s.id)));
    for (const p of desk.pool) if (!world.assets.get(p.id)) throw Error("Missing pool object " + p.id);
    ready = true;
  }
  function setPlaying(on) { playing = on; const b = toolbar.querySelector('[data-drc="play"]'); b.textContent = on ? "Pause" : "Play"; b.setAttribute("aria-pressed", String(on)); }
  toolbar.addEventListener("click", (e) => {
    const c = e.target.closest("[data-drc]")?.dataset.drc;
    if (!ready) return;
    if (c === "next") { setPlaying(false); variant(seed + 1 + Math.floor(Math.random() * 997)); }
    else if (c === "play") { setPlaying(!playing); holdT = 0; }
    else if (c === "boxes") { boxes = !boxes; const b = toolbar.querySelector('[data-drc="boxes"]'); b.setAttribute("aria-pressed", String(boxes)); }
  });
  addEventListener("keydown", (e) => {
    if (!active || e.target.closest?.("input,select,textarea")) return;
    if (e.key === "Escape") exit();
    else if (e.key === " ") { e.preventDefault(); setPlaying(!playing); }
    else if (e.key === "ArrowRight" && ready) { setPlaying(false); variant(seed + 1); }
  });

  async function enter() {
    if (active) return;
    modes.enter("dr");
    saved = onEnter();
    active = true; t = 0;
    savedRenderer = { shadow: renderer.shadowMap.enabled, autoUpdate: renderer.shadowMap.autoUpdate, type: renderer.shadowMap.type, autoClear: renderer.autoClear };
    expBase = renderer.toneMappingExposure;
    renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap; renderer.shadowMap.autoUpdate = true; renderer.autoClear = true;
    document.body.dataset.dr = "true"; entry.setAttribute("aria-pressed", "true");
    panel.hidden = toolbar.hidden = false;
    $(".dr-variant").textContent = "Loading editable objects…";
    cam = new THREE.PerspectiveCamera(desk.camera.fov, 1, 0.03, 120); cam.up.set(0, 0, 1);
    cam.position.fromArray(desk.camera.pos); cam.lookAt(...desk.camera.look);
    cam.userData.base = { pos: cam.position.clone(), quat: cam.quaternion.clone() };
    try {
      loading ||= load();
      await loading;
      if (!active) return;
      setPlaying(true);
      variant(1 + Math.floor(Math.random() * 9000));
    } catch (err) {
      console.error(err); loading = null;
      $(".dr-variant").textContent = "Objects could not load. Return to Compare and try again.";
    }
  }
  function exit() {
    if (!active) return;
    active = false;
    if (ready) { restoreAll(); if (light) { light.intensity = lightBase.intensity; light.color.copy(lightBase.color); scene.environmentIntensity = envBase; } }
    renderer.toneMappingExposure = expBase;
    renderer.shadowMap.enabled = savedRenderer.shadow; renderer.shadowMap.autoUpdate = savedRenderer.autoUpdate; renderer.shadowMap.type = savedRenderer.type; renderer.autoClear = savedRenderer.autoClear;
    modes.leave("dr");
    panel.hidden = toolbar.hidden = true;
    delete document.body.dataset.dr; entry.setAttribute("aria-pressed", "false");
    if (caption) caption.textContent = originalCaption;
    onExit(saved); invalidate();
  }
  entry.addEventListener("click", () => (active ? null : enter()));
  entry.disabled = false;

  const zAxis = new THREE.Vector3(0, 0, 1), q = new THREE.Quaternion();
  const ease = (k) => (k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2);
  function frame(dt) {
    t += dt;
    const w = stage.clientWidth || innerWidth, h = stage.clientHeight || innerHeight, size = renderer.getSize(new THREE.Vector2());
    if (size.x !== w || size.y !== h) { renderer.setSize(w, h, false); size.set(w, h); }
    const { pos, quat } = cam.userData.base;
    q.setFromAxisAngle(zAxis, Math.sin(t * 0.3) * 0.03);
    cam.quaternion.copy(q).multiply(quat);
    cam.position.copy(pos).add(new THREE.Vector3(Math.sin(t * 0.3) * 0.08, Math.cos(t * 0.24) * 0.05, 0));
    cam.aspect = size.x / size.y; cam.fov = desk.camera.fov * (cam.aspect < 1 ? 1.45 : 1); cam.updateProjectionMatrix();
    renderer.setScissorTest(false); renderer.setViewport(0, 0, size.x, size.y); renderer.setRenderTarget(null);
    if (!ready) { renderer.setClearColor(0x0d1018, 1); renderer.clear(); return; }
    if (playing) { holdT += dt; if (holdT >= HOLD + MOVE) variant(seed + 1); }
    if (moveT < 1) moveT = Math.min(1, moveT + dt / MOVE);
    const k = ease(moveT);
    if (lightTo) {
      const a = lightFrom || lightTo, mix = (x, y) => x + (y - x) * k;
      lightNow = { color: [0, 1, 2].map((i) => mix(a.color[i], lightTo.color[i])), sun: mix(a.sun, lightTo.sun), env: mix(a.env, lightTo.env), exposure: mix(a.exposure, lightTo.exposure) };
      light.color.setRGB(...lightNow.color); light.intensity = lightBase.intensity * lightNow.sun;
      scene.environmentIntensity = envBase * lightNow.env; renderer.toneMappingExposure = expBase * lightNow.exposure;
    }
    for (const it of items.values()) {
      const f = it.from, g = it.to;
      it.now = { x: f.x + (g.x - f.x) * k, y: f.y + (g.y - f.y) * k, yaw: f.yaw + (g.yaw - f.yaw) * k, s: f.s + (g.s - f.s) * k };
      pose(it, it.now);
      it.asset.root.updateMatrixWorld(true);
      if (it.helper) { it.helper.visible = boxes; it.helper.update(); }
    }
    bar.style.width = `${playing ? Math.min(100, (holdT / (HOLD + MOVE)) * 100) : 0}%`;
    renderer.render(scene, cam);
  }
  if (new URLSearchParams(location.search).get("mode") === "dr") requestAnimationFrame(() => enter());
  function setCamera(pos, look, fov) { desk.camera = { pos, look, fov }; cam.fov = fov; cam.position.fromArray(pos); cam.lookAt(...look); cam.userData.base = { pos: cam.position.clone(), quat: cam.quaternion.clone() }; }
  return { get active() { return active; }, frame, enter, exit, setCamera, variant: (n) => variant(n), get state() { return { active, ready, seed, objects: items.size, playing }; } };
}
